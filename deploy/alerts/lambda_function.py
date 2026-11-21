"""CareerLens 오류 알림 Lambda: SQS 큐(careerlens-alerts)에 쌓인 서버 오류를 한 통의 메일로 묶어 SNS 주제로 보낸다.

SNS 보내기가 실패하면 예외를 그대로 올린다 → SQS가 메시지를 다시 보이게 하고, 3번 실패하면 DLQ(careerlens-alerts-dlq)로 옮긴다.
DLQ에 메시지가 생기면 CloudWatch 경보가 같은 SNS 주제로 알린다(deploy/alerts.sh).
"""
import json
import os

import boto3

TOPIC = os.environ.get('TOPIC_ARN')
KIND = {'server': '서버 오류(500)', 'bedrock': 'AI 호출 실패(규칙 대체로 넘어감)', 'chat': '대화창 응답 실패'}
_sns = None


def summarize(records):
    """SQS 레코드 → (제목, 본문). 형식이 깨진 메시지도 원문 그대로 본문에 넣는다(버리지 않음)."""
    lines, kinds = [], set()
    for r in records:
        try:
            m = json.loads(r['body'])
            kinds.add(m.get('kind'))
            lines.append(f"[{m.get('time')}] {KIND.get(m.get('kind'), m.get('kind'))} · {m.get('where')}\n"
                         f"  {m.get('error')}: {m.get('message')}\n  위치: {m.get('at')} · 서버: {m.get('host')}")
        except (ValueError, AttributeError):
            lines.append(f'(형식을 알 수 없는 메시지) {r.get("body", "")[:500]}')
    head = '서버 오류' if 'server' in kinds else 'AI·대화 오류' if kinds else '알 수 없는 메시지'
    subject = f'[CareerLens] {head} {len(records)}건'
    body = ('CareerLens 서버에서 오류가 생겼습니다. 같은 오류는 5분에 한 번만 보냅니다.\n\n' + '\n\n'.join(lines)
            + '\n\n서버 로그: aws ssm send-command ... "journalctl -u careerlens -n 200"')
    return subject, body


def handler(event, context):
    global _sns
    records = event.get('Records', [])
    if not records:
        return {'sent': 0}
    subject, body = summarize(records)
    _sns = _sns or boto3.client('sns')
    _sns.publish(TopicArn=TOPIC, Subject=subject[:100], Message=body)
    return {'sent': len(records)}
