"""오류 알림: 서버 쪽(careerlens/alerts.py)과 Lambda(deploy/alerts/lambda_function.py). AWS는 부르지 않는다."""
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from careerlens import alerts


@pytest.fixture(autouse=True)
def _fresh():
    alerts._last.clear()


def _boom(msg='실패'):
    try:
        raise RuntimeError(msg)
    except RuntimeError as e:
        return e


def test_report_masks_pii_and_stays_quiet_for_same_error():
    m = alerts.report('bedrock', 'ask_json', _boom('연락처 010-1234-5678 처리 중 실패'))
    assert m['error'] == 'RuntimeError' and '010-1234-5678' not in m['message'] and m['at'].startswith('test_alerts.py:')
    assert alerts.report('bedrock', 'ask_json', _boom()) is None          # 5분 안 같은 오류는 다시 안 보냄
    assert alerts.report('bedrock', 'transcribe_image', _boom()) is not None   # 위치가 다르면 보냄


def test_unhandled_error_returns_500_and_reports(monkeypatch):
    from careerlens import api
    sent = []
    monkeypatch.setattr(alerts, 'QUEUE', 'q')
    monkeypatch.setattr(alerts, '_send', sent.append)
    monkeypatch.setattr(api.R, 'recommend_cards', lambda *a, **k: 1 / 0)
    card = dict(title='경리', type='job', text='회사에서 5년 동안 경리 업무를 했습니다.')
    r = TestClient(api.app, raise_server_exceptions=False).post('/api/recommend', json=dict(cards=[card]))
    assert r.status_code == 500 and '서버에 문제' in r.json()['detail']
    import time
    for _ in range(50):   # 보내기는 뒤 스레드에서 한다
        if sent:
            break
        time.sleep(0.01)
    m = json.loads(sent[0])
    assert (m['kind'], m['where'], m['error']) == ('server', 'POST /api/recommend', 'ZeroDivisionError')


def _lambda():
    p = Path(__file__).resolve().parents[2] / 'deploy' / 'alerts' / 'lambda_function.py'
    spec = importlib.util.spec_from_file_location('alert_lambda', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_lambda_sends_one_mail_per_batch_and_raises_on_failure():
    L = _lambda()
    ok = json.dumps(alerts.report('server', 'POST /api/recommend', _boom()), ensure_ascii=False)
    event = {'Records': [{'body': ok}, {'body': 'not json'}]}

    class SNS:
        def __init__(self, fail=False):
            self.fail, self.calls = fail, []

        def publish(self, **kw):
            if self.fail:
                raise ConnectionError('sns down')
            self.calls.append(kw)

    L._sns = s = SNS()
    assert L.handler(event, None) == {'sent': 2}
    assert len(s.calls) == 1 and s.calls[0]['Subject'] == '[CareerLens] 서버 오류 2건'
    assert 'POST /api/recommend' in s.calls[0]['Message'] and 'not json' in s.calls[0]['Message']
    L._sns = SNS(fail=True)
    with pytest.raises(ConnectionError):   # 올려야 SQS가 다시 시도하고, 3번 실패하면 DLQ로 옮긴다
        L.handler(event, None)
