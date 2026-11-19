#!/bin/bash
# CareerLens 첫 부팅: S3에서 코드·데이터를 받아 /opt/careerlens에 풀고 uvicorn을 systemd로 띄운다
set -euxo pipefail
export AWS_DEFAULT_REGION=ap-northeast-2
B=careerlens-deploy-010539085740
apt-get update
apt-get install -y python3-venv
snap install aws-cli --classic
mkdir -p /opt/careerlens && cd /opt/careerlens
/snap/bin/aws s3 cp s3://$B/code.tar.gz /tmp/code.tar.gz && tar xzf /tmp/code.tar.gz
/snap/bin/aws s3 cp s3://$B/data.tar.gz /tmp/data.tar.gz && tar xzf /tmp/data.tar.gz
python3 -m venv .venv && .venv/bin/pip install -q -r backend/requirements.txt
chown -R ubuntu:ubuntu /opt/careerlens
cat > /etc/systemd/system/careerlens.service <<'UNIT'
[Unit]
Description=CareerLens
After=network-online.target
[Service]
User=ubuntu
WorkingDirectory=/opt/careerlens/backend
Environment=CL_REGION=ap-northeast-2
ExecStart=/opt/careerlens/.venv/bin/uvicorn careerlens.api:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now careerlens
