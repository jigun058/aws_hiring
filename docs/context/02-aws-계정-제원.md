# aws 계정 제원

- 출처: https://app.notion.com/p/417746d99efb80138370dd61da05bbe3
- 경로: AI Bootcamp Innovation Challenger 2026 / aws 계정 제원
- Notion 최종 수정: 2026-11-16T18:19:20Z (가져온 날: 2026-11-17)
- 첨부: 없음

## 계정 개요

대회 측이 제공한 계정은 **Innovation Sandbox on AWS** 방식의 대여 계정입니다. IAM 사용자가 아니라 IAM Identity Center(SSO)로 로그인해 임시 역할을 맡는 구조입니다.

| 항목 | 값 |
| --- | --- |
| 로그인 포털 | https://d-9b675698c6.awsapps.com/start |
| 계정 ID | 010539085740 |
| 세션 이름 | kosa03 |
| 역할(Permission Set) | AWSReservedSSO_myisb_IsbUsersPS_228bfbc737abf530 |
| 역할 ARN | arn:aws:sts::010539085740:assumed-role/AWSReservedSSO_myisb_IsbUsersPS_228bfbc737abf530/kosa03 |
| CLI 프로필 이름 | tae |

역할 이름의 `myisb`는 Innovation Sandbox의 기본 네임스페이스, `IsbUsersPS`는 일반 사용자용 Permission Set입니다. 이 구조에서는 다음 특성이 따라옵니다.

- AWS Organizations 멤버 계정이며, 상위 SCP가 권한을 제한할 수 있습니다.
- 대여마다 예산 상한과 기간이 있고, 초과 시 알림, 동결, 정리 조치가 가능합니다.
- 대여 종료 시 계정 내 리소스가 일괄 삭제됩니다. 기본 VPC가 없던 것도 이 정리 때문으로 보입니다.

## CLI 접속 설정

`aws configure sso`로 프로필 `tae`를 만들어 두었습니다. 다른 기기에서 다시 설정할 때는 아래 순서를 따릅니다.

1. `aws configure sso` 실행
2. SSO session name: 임의 지정 (예: `contest`)
3. SSO start URL: `https://d-9b675698c6.awsapps.com/start`
4. SSO region: Identity Center가 설정된 리전
5. SSO registration scopes: 입력 없이 Enter (기본값 `sso:account:access`)
6. 브라우저에서 터미널과 같은 인증 코드인지 확인 후 승인
7. 계정과 역할 선택, 프로필 이름 `tae` 지정

세션은 몇 시간 뒤 만료됩니다. 만료되면 `aws sso login --profile tae`로 갱신합니다.

zsh에서는 `<`, `>`를 리다이렉션으로 해석하므로, 명령에 자리표시 문자를 그대로 넣지 말고 실제 값으로 바꿔야 합니다.

## 확인된 제원 요약

일반 인스턴스는 바로 사용할 수 있고, GPU는 권한은 있지만 할당량이 0이라 현재 사용할 수 없습니다.

| 구분 | 서울 (ap-northeast-2) | 버지니아 (us-east-1) | 근거 |
| --- | --- | --- | --- |
| 리전 접근 | 가능 | 가능 | describe-instances 성공 |
| 일반 인스턴스 할당량 (L-1216C47A) | 256 vCPU | 256 vCPU | Service Quotas 조회 |
| G/VT GPU 할당량 (L-DB2E81BA) | 0 vCPU | 0 vCPU | Service Quotas 조회 |
| P GPU 할당량 (L-417A185B) | 0 vCPU | 0 vCPU | Service Quotas 조회 |
| 기본 VPC | 생성함 (vpc-0e2fa87762933eb25, 172.31.0.0/16) | 없음 | create-default-vpc |
| t3.micro 생성 권한 | 허용 | 미확인 | run-instances dry-run |
| m5.xlarge 생성 권한 | 허용 | 미확인 | run-instances dry-run |
| g5.xlarge 생성 권한 | 허용 (할당량 0으로 실제 생성 불가) | 미확인 | run-instances dry-run |

버지니아의 생성 권한은 기본 VPC가 없어 검증하지 못했습니다. 필요하면 그 리전에도 기본 VPC를 만든 뒤 dry-run을 다시 실행합니다.

## 확인 과정과 결과 해석

| 순서 | 확인 내용 | 결과 | 해석 |
| --- | --- | --- | --- |
| 1 | sts get-caller-identity | assumed-role/AWSReservedSSO_myisb_IsbUsersPS_… | SSO 임시 역할, Innovation Sandbox 구조 |
| 2 | ec2 describe-instances (두 리전) | 빈 목록 반환 | 리전 차단 없음, 실행 중 인스턴스 없음 |
| 3 | run-instances dry-run (VPC 없음) | VPCIdNotSpecified | 파라미터 검증 실패, 권한 판단 불가 |
| 4 | service-quotas 조회 | 일반 256, GPU 0 | GPU는 할당량으로 막힘 |
| 5 | create-default-vpc (서울) | 성공 | VPC/EC2 쓰기 권한 있음 |
| 6 | run-instances dry-run (서울, VPC 생성 후) | 세 타입 모두 DryRunOperation | SCP·IAM이 GPU 타입을 차단하지 않음 |

dry-run 결과는 다음 기준으로 해석합니다.

- `DryRunOperation`: 권한 허용
- `UnauthorizedOperation`: IAM 또는 SCP가 차단
- `InvalidParameter`, `VPCIdNotSpecified` 등: 권한 이전 단계의 파라미터 문제

dry-run은 권한만 검사하고 할당량과 가용 용량은 검사하지 않습니다. 그래서 g5.xlarge가 허용으로 나와도 할당량이 0이면 실제 생성은 실패합니다.

## 미확인 사항과 주의점

예산 한도와 만료일은 멤버 계정에서 조회할 수 없으므로, 대회 측에 직접 확인해야 합니다.

- 대회 측에 대여 예산 한도 문의
- 대회 측에 대여 만료일 문의
- GPU 사용 허용 여부 문의 (필요한 경우)
- 버지니아 리전 생성 권한 검증 (필요한 경우)

주의할 점은 다음과 같습니다.

- **권한이 열려 있다고 마음껏 써도 되는 것은 아닙니다.** 예산을 넘기면 계정이 동결되거나 정리될 수 있습니다.
- **GPU 할당량 증설 요청**은 SCP로 막혀 있거나 승인에 수일이 걸릴 수 있습니다. 요청과 동시에 대회 측에도 문의합니다.
- **인스턴스는 stop이 아니라 terminate까지 확인합니다.** stop 상태에서도 EBS 볼륨 비용이 계속 나갑니다.
- **대여 종료 시 모든 리소스가 삭제됩니다.** 코드와 데이터는 계정 밖에 백업합니다.
- Billing 화면에서는 크레딧이나 비용이 보이지 않을 수 있습니다. 예산은 관리 계정에서 관리됩니다.

## 자주 쓸 명령어

세션 갱신과 신원 확인:

```bash
aws sso login --profile tae
aws sts get-caller-identity --profile tae
```

할당량 일괄 조회:

```bash
for REGION in ap-northeast-2 us-east-1; do
  for CODE in L-1216C47A L-DB2E81BA L-417A185B; do
    VAL=$(aws service-quotas get-service-quota --service-code ec2 \
      --quota-code $CODE --region $REGION --profile tae \
      --query 'Quota.Value' --output text 2>&1)
    echo "$REGION $CODE: $VAL"
  done
done
```

인스턴스 타입별 생성 권한 dry-run (서울):

```bash
AMI=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --region ap-northeast-2 --profile tae \
  --query 'Parameters[0].Value' --output text)

for TYPE in t3.micro m5.xlarge g5.xlarge; do
  echo "== $TYPE"
  aws ec2 run-instances --dry-run --image-id $AMI --instance-type $TYPE \
    --region ap-northeast-2 --profile tae 2>&1 | head -c 300
  echo
done
```

기본 VPC 생성 (다른 리전에 필요할 때):

```bash
aws ec2 create-default-vpc --region us-east-1 --profile tae
```

GPU 할당량 증설 요청과 상태 확인:

```bash
aws service-quotas request-service-quota-increase --service-code ec2 \
  --quota-code L-DB2E81BA --desired-value 8 --region ap-northeast-2 --profile tae

aws service-quotas list-requested-service-quota-change-history \
  --service-code ec2 --region ap-northeast-2 --profile tae
```

실행 중인 인스턴스 점검 (종료 누락 방지):

```bash
aws ec2 describe-instances --region ap-northeast-2 --profile tae \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]' --output table
```
