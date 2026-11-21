"""서버 오류 알림: 오류 요약을 SQS 큐에 넣는다 → Lambda가 모아 SNS로 관리자 이메일(deploy/alerts.sh).

CL_ALERT_QUEUE(큐 URL)가 없으면 아무것도 하지 않는다(로컬·시험). 보내기는 뒤에서 하므로 요청을 늦추지 않고,
보내다 실패해도 서비스에는 영향이 없다. 사용자 글은 넣지 않고 오류 종류·위치·짧은 메시지(개인정보 가림)만 넣는다.
"""
import json
import os
import socket
import threading
import time
import traceback

QUEUE = os.environ.get('CL_ALERT_QUEUE')
REGION = os.environ.get('CL_REGION', 'ap-northeast-2')
QUIET = 300   # 같은 오류(종류·위치·예외 이름)는 5분에 한 번만. Bedrock 장애 때 메일이 쏟아지지 않게
_last = {}
_lock = threading.Lock()
_sqs = None


def _send(body):
    global _sqs
    try:
        if _sqs is None:
            import boto3
            _sqs = boto3.Session(profile_name=os.environ.get('AWS_PROFILE')).client('sqs', region_name=REGION)
        _sqs.send_message(QueueUrl=QUEUE, MessageBody=body)
    except Exception as e:   # 알림이 서비스를 막으면 안 된다. 서버 로그(journald)에만 남긴다
        print(f'alert send failed: {e!r}', flush=True)


def report(kind, where, exc):
    """kind: 'server'(처리 못 한 오류, 500) | 'bedrock'(AI 호출 실패, 규칙 대체로 넘어감) | 'chat'(대화창이 '잠시 응답 불가' 안내로 넘어감).
    where: API 경로나 함수 이름. 보낸 내용(dict)을 돌려준다. 5분 안에 같은 오류면 None."""
    key = (kind, where, type(exc).__name__)
    now = time.time()
    with _lock:
        if now - _last.get(key, 0) < QUIET:
            return None
        _last[key] = now
    from careerlens.interview import mask_pii
    tb = traceback.extract_tb(exc.__traceback__)
    msg = dict(kind=kind, where=where, error=type(exc).__name__, message=mask_pii(str(exc))[:300],
               at=f'{os.path.basename(tb[-1].filename)}:{tb[-1].lineno} {tb[-1].name}' if tb else '',
               time=time.strftime('%Y-%m-%d %H:%M:%S %z'), host=socket.gethostname())
    if QUEUE:
        threading.Thread(target=_send, args=(json.dumps(msg, ensure_ascii=False),), daemon=True).start()
    return msg
