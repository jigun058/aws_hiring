#!/bin/bash
# 코드·화면 다시 배포: 커밋된 코드(git HEAD)와 새로 빌드한 frontend/dist를 S3에 올리고, EC2에서 풀어 서비스를 다시 띄운다.
# 큰 데이터(backend/data, 엔진 입력)가 바뀌었을 때만 DATA=1 ./deploy/redeploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."
P="--profile ${AWS_PROFILE:-tae} --region ap-northeast-2"
B=careerlens-deploy-010539085740
I=i-079608471f3730473
T=$(mktemp -d)

[ -z "$(git status --porcelain)" ] || echo "주의: 커밋 안 한 변경은 배포되지 않는다(git HEAD만 올림)"
(cd frontend && npm run build >/dev/null)
git archive --format=tar.gz -o "$T/code.tar.gz" HEAD
tar czf "$T/dist.tar.gz" frontend/dist
aws s3 cp "$T/code.tar.gz" "s3://$B/" $P --only-show-errors
aws s3 cp "$T/dist.tar.gz" "s3://$B/" $P --only-show-errors
GET="/snap/bin/aws s3 cp --only-show-errors s3://$B/code.tar.gz /tmp/ && tar xzmf /tmp/code.tar.gz && /snap/bin/aws s3 cp --only-show-errors s3://$B/dist.tar.gz /tmp/ && tar xzmf /tmp/dist.tar.gz"
if [ "${DATA:-0}" = 1 ]; then
  tar czf "$T/data.tar.gz" backend/data backend/vendor/engine/out backend/vendor/engine/work frontend/dist
  aws s3 cp "$T/data.tar.gz" "s3://$B/" $P --only-show-errors
  GET="$GET && /snap/bin/aws s3 cp --only-show-errors s3://$B/data.tar.gz /tmp/ && tar xzmf /tmp/data.tar.gz"
fi
CMD="set -e; export AWS_DEFAULT_REGION=ap-northeast-2; cd /opt/careerlens && $GET && .venv/bin/pip install -q -r backend/requirements.txt && chown -R ubuntu:ubuntu /opt/careerlens && systemctl restart careerlens && for i in \$(seq 30); do curl -sf localhost:8000/api/health && exit 0; sleep 1; done; exit 1"
C=$(aws ssm send-command $P --instance-ids $I --document-name AWS-RunShellScript \
      --parameters "$(jq -n --arg c "$CMD" '{commands:[$c]}')" --query Command.CommandId --output text)
aws ssm wait command-executed $P --command-id "$C" --instance-id $I || true
aws ssm get-command-invocation $P --command-id "$C" --instance-id $I --query '[Status,StandardOutputContent,StandardErrorContent]' --output text
rm -rf "$T"
