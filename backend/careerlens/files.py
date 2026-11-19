"""① 파일에서 글 꺼내기(P3 F3-1 ①). 꺼낸 글은 대화로 쓴 글과 똑같이 /api/interview/start로 간다.
PDF·워드(.docx)·텍스트는 코드가 글자를 뽑고, 사진(자격증·수료증)은 LLM이 글자를 옮겨 적는다.
실패하면 사용자에게 보여 줄 이유를 담은 ValueError.
"""
import io
import logging
import re
import zipfile

from careerlens import llm

MAX_BYTES = 5 * 1024 * 1024
IMAGE = {'jpg', 'jpeg', 'png', 'webp'}
LATER = {'hwp': '한글 파일', 'hwpx': '한글 파일', 'doc': '옛 워드 파일', 'ppt': '파워포인트', 'pptx': '파워포인트'}


def _pdf(data):
    from pypdf import PdfReader
    logging.getLogger('pypdf').setLevel(logging.ERROR)   # 깨진 파일 경고는 ValueError로 알린다
    text = '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(data)).pages)
    # pypdf가 글자 조각 사이에 넣는 공백("8 년 )", "상하차 ,")을 걷는다. 인용 검사는 공백을 무시하므로 보기용
    return re.sub(r' (?=[,.:)\]%])|(?<=[(\[]) |(?<=[\d%]) (?=[가-힣])', '', text)


def _docx(data):
    xml = zipfile.ZipFile(io.BytesIO(data)).read('word/document.xml').decode('utf-8')
    xml = re.sub(r'</w:p>|<w:br/>|<w:tab/>', lambda m: '\t' if 'tab' in m.group(0) else '\n', xml)
    return re.sub(r'<[^>]+>', '', xml).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'")


def _image_format(data):
    if data[:3] == b'\xff\xd8\xff':
        return 'jpeg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


def _txt(data):
    for enc in ('utf-8-sig', 'cp949'):   # 윈도 메모장 한글 파일은 cp949인 경우가 많다
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError('글자를 읽지 못했어요')


def read(name, data):
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if not data:
        raise ValueError('빈 파일이에요')
    if len(data) > MAX_BYTES:
        raise ValueError('파일이 5MB보다 커요')
    if ext in LATER:
        raise ValueError(f'{LATER[ext]}은 아직 못 읽어요. PDF로 저장해서 올려 주세요')
    try:
        if ext == 'pdf':
            text = _pdf(data)
        elif ext == 'docx':
            text = _docx(data)
        elif ext in ('txt', 'md'):
            text = _txt(data)
        elif ext in IMAGE:
            fmt = _image_format(data)   # 화면이 사진을 JPEG로 줄여 보내므로 확장자 말고 내용으로 본다
            if not fmt:
                raise ValueError('사진 파일이 아니거나 손상됐어요')
            text = llm.transcribe_image(data, fmt)
            if text is None:
                raise ValueError('사진을 읽지 못했어요. 잠시 뒤 다시 올려 주세요')
        else:
            raise ValueError('지원하지 않는 형식이에요. PDF, 워드(.docx), 텍스트, 사진(jpg·png)을 올려 주세요')
    except ValueError:
        raise
    except Exception:   # 깨진 PDF·zip 등
        raise ValueError('파일이 손상됐거나 내용을 읽지 못했어요')
    text = re.sub(r'[ \t]+', ' ', re.sub(r'\n\s*\n+', '\n', text)).strip()
    if len(re.findall(r'[가-힣A-Za-z]', text)) < 5:
        raise ValueError('사진만 들어 있는 PDF이거나 글자가 없어요. 사진으로 찍어 올려 주세요' if ext == 'pdf' else '글자를 찾지 못했어요')
    return text
