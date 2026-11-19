"""① 파일 올리기(P3 F3-1 ①): 파일 → 개인정보를 가린 글. 사진은 LLM을 가짜로 바꿔 끼운다."""
import base64
import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from careerlens import llm


@pytest.fixture(scope='module')
def client():
    from careerlens.api import app
    return TestClient(app)


def post(client, name, data):
    return client.post('/api/files/read', json=dict(name=name, data=base64.b64encode(data).decode()))


def test_pdf_text_masked_and_spacing_fixed(client):
    r = post(client, '이력서.pdf', (Path(__file__).parent / 'fixtures/resume.pdf').read_bytes())
    t = r.json()['text']
    assert '하루 300건 출고 처리' in t and '지게차운전기능사' in t
    assert '010-1234-5678' not in t and 'park@example.com' not in t


def test_docx(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('word/document.xml', '<w:document><w:body><w:p><w:r><w:t>마트에서 3년 동안 재고 관리</w:t></w:r></w:p>'
                   '<w:p><w:r><w:t>계산 &amp; 진열</w:t></w:r></w:p></w:body></w:document>')
    assert post(client, '경력.docx', buf.getvalue()).json()['text'] == '마트에서 3년 동안 재고 관리\n계산 & 진열'


def test_photo_goes_through_llm(client, monkeypatch):
    seen = {}

    def converse(system, messages, max_tokens=1000, tools=None):
        seen['block'] = messages[0]['content'][0]
        return {'output': {'message': {'content': [{'text': '자격증\n지게차운전기능사\n한국산업인력공단'}]}}}
    monkeypatch.setattr(llm, 'converse', converse)
    assert '지게차운전기능사' in post(client, '자격증.png', b'\xff\xd8\xfffakejpeg').json()['text']
    assert seen['block']['image']['format'] == 'jpeg'


@pytest.mark.parametrize('name,data,why', [
    ('이력서.hwp', b'x', 'PDF로 저장'),
    ('빈.txt', b'', '빈 파일'),
    ('깨짐.pdf', b'%PDF-broken', '읽지 못했'),
    ('a.zip', b'xx', '지원하지 않는 형식'),
    ('가짜.jpg', b'not an image', '사진 파일이 아니'),
    ('큰.pdf', b'x' * (5 * 1024 * 1024 + 1), '5MB'),
])
def test_failures_name_file_and_reason(client, name, data, why):
    r = post(client, name, data)
    assert r.status_code == 422 and r.json()['detail'].startswith(name) and why in r.json()['detail']


def test_photo_llm_down_says_so(client, monkeypatch):
    def down(*a, **k):
        raise RuntimeError('down')
    monkeypatch.setattr(llm, 'converse', down)
    r = post(client, '자격증.png', b'\x89PNG\r\n\x1a\nfake')
    assert r.status_code == 422 and '사진을 읽지 못했' in r.json()['detail']
