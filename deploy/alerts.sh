#!/bin/bash
# 서버 오류 알림 만들기(여러 번 돌려도 됨): EC2 서버 → SQS 큐 → Lambda → SNS 주제 → 관리자 이메일.
# Lambda가 3번 실패한 메시지는 DLQ로 가고, DLQ에 메시지가 생기면 CloudWatch 경보가 같은 SNS 주제로 알린다.
#   ALERT_EMAIL=관리자@메일 AWS_PROFILE=tae ./deploy/alerts.sh
# 처음 한 번은 받은 메일의 "Confirm subscription"을 눌러야 메일이 온다.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${ALERT_EMAIL:?ALERT_EMAIL=관리자 이메일 을 붙여 실행}"
R=ap-northeast-2
P="--profile ${AWS_PROFILE:-tae} --region $R"
ACC=010539085740
I=i-079608471f3730473
Q=careerlens-alerts DLQ=careerlens-alerts-dlq T=careerlens-alerts FN=careerlens-alerts ROLE=careerlens-alerts-lambda
T_DIR=$(mktemp -d); trap 'rm -rf "$T_DIR"' EXIT

# 1. DLQ(14일 보관)와 본 큐(3번 받고도 못 지우면 DLQ로). 보이지 않는 시간은 Lambda 제한 시간(30초)의 6배
DLQ_URL=$(aws sqs create-queue $P --queue-name $DLQ --attributes MessageRetentionPeriod=1209600 --query QueueUrl --output text)
DLQ_ARN=arn:aws:sqs:$R:$ACC:$DLQ
jq -n --arg d "$DLQ_ARN" '{VisibilityTimeout:"180", MessageRetentionPeriod:"345600",
  RedrivePolicy:({deadLetterTargetArn:$d, maxReceiveCount:"3"}|tojson)}' > "$T_DIR/q.json"
Q_URL=$(aws sqs create-queue $P --queue-name $Q --attributes file://"$T_DIR/q.json" --query QueueUrl --output text)
Q_ARN=arn:aws:sqs:$R:$ACC:$Q

# 2. SNS 주제와 이메일 구독
T_ARN=$(aws sns create-topic $P --name $T --query TopicArn --output text)
aws sns subscribe $P --topic-arn "$T_ARN" --protocol email --notification-endpoint "$ALERT_EMAIL" >/dev/null

# 3. Lambda 역할: 로그 + 본 큐 읽기·지우기 + 주제에 보내기만
if ! aws iam get-role $P --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role $P --role-name $ROLE --assume-role-policy-document \
    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy $P --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
fi
aws iam put-role-policy $P --role-name $ROLE --policy-name alerts --policy-document "$(jq -n --arg q "$Q_ARN" --arg t "$T_ARN" \
  '{Version:"2012-10-17",Statement:[{Effect:"Allow",Action:["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],Resource:$q},
                                    {Effect:"Allow",Action:"sns:Publish",Resource:$t}]}')"

# 4. Lambda 함수(있으면 코드만 새로)
(cd deploy/alerts && python3 -m zipfile -c "$T_DIR/fn.zip" lambda_function.py)
if aws lambda get-function $P --function-name $FN >/dev/null 2>&1; then
  aws lambda update-function-code $P --function-name $FN --zip-file fileb://"$T_DIR/fn.zip" >/dev/null
else
  for n in 1 2 3 4 5 6; do   # 방금 만든 역할은 몇 초 뒤에야 Lambda가 쓸 수 있다
    aws lambda create-function $P --function-name $FN --runtime python3.12 --handler lambda_function.handler \
      --role arn:aws:iam::$ACC:role/$ROLE --zip-file fileb://"$T_DIR/fn.zip" --timeout 30 --memory-size 128 \
      --environment "Variables={TOPIC_ARN=$T_ARN}" >/dev/null && break
    [ $n = 6 ] && exit 1; sleep 10
  done
  aws lambda wait function-active-v2 $P --function-name $FN
fi

# 5. 큐 → Lambda 연결: 최대 10건을 60초까지 모아 메일 한 통으로
if [ -z "$(aws lambda list-event-source-mappings $P --function-name $FN --event-source-arn "$Q_ARN" --query 'EventSourceMappings[0].UUID' --output text | grep -v None)" ]; then
  aws lambda create-event-source-mapping $P --function-name $FN --event-source-arn "$Q_ARN" \
    --batch-size 10 --maximum-batching-window-in-seconds 60 >/dev/null
fi

# 6. DLQ에 메시지가 1건이라도 생기면 경보 → 같은 주제로 메일(Lambda가 메일을 못 보낸 경우를 알림)
aws cloudwatch put-metric-alarm $P --alarm-name careerlens-alerts-dlq --namespace AWS/SQS --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=$DLQ --statistic Maximum --period 300 --evaluation-periods 1 --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold --treat-missing-data notBreaching --alarm-actions "$T_ARN"

# 7. EC2 역할에 본 큐 보내기 권한, 서버에 큐 주소를 넣고 다시 시작
aws iam put-role-policy $P --role-name careerlens-ec2 --policy-name alerts-send --policy-document "$(jq -n --arg q "$Q_ARN" \
  '{Version:"2012-10-17",Statement:[{Effect:"Allow",Action:"sqs:SendMessage",Resource:$q}]}')"
CMD="set -e; mkdir -p /etc/systemd/system/careerlens.service.d && printf '[Service]\nEnvironment=CL_ALERT_QUEUE=$Q_URL\n' > /etc/systemd/system/careerlens.service.d/alerts.conf && systemctl daemon-reload && systemctl restart careerlens && for i in \$(seq 30); do curl -sf localhost:8000/api/health && exit 0; sleep 1; done; exit 1"
C=$(aws ssm send-command $P --instance-ids $I --document-name AWS-RunShellScript \
      --parameters "$(jq -n --arg c "$CMD" '{commands:[$c]}')" --query Command.CommandId --output text)
aws ssm wait command-executed $P --command-id "$C" --instance-id $I || true
aws ssm get-command-invocation $P --command-id "$C" --instance-id $I --query '[Status,StandardOutputContent,StandardErrorContent]' --output text
echo "큐 $Q_URL / DLQ $DLQ_URL / 주제 $T_ARN"
echo "시험 메일: aws sqs send-message $P --queue-url $Q_URL --message-body '{\"kind\":\"server\",\"where\":\"test\",\"error\":\"Test\",\"message\":\"알림 시험\"}'"
