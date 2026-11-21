#!/bin/bash
# 시연 영상: https://d3lowpvdkyf7ly.cloudfront.net/demo/ 페이지가 /media/demo.mp4를 튼다.
# /media/*는 CloudFront가 S3(careerlens-deploy 버킷의 media/ 아래만)에서 낸다. 링크는 그대로 두고 영상만 바꿀 수 있다.
#   AWS_PROFILE=tae ./deploy/demo-video.sh 영상.mp4   # 올리기·바꾸기(처음이면 CloudFront·S3 설정도 함)
#   AWS_PROFILE=tae ./deploy/demo-video.sh            # 설정만
set -euo pipefail
cd "$(dirname "$0")/.."
P="--profile ${AWS_PROFILE:-tae}"
B=careerlens-deploy-010539085740 D=E38S0574VLXD5Q ACC=010539085740
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT

# 1. CloudFront만 S3를 읽게(OAC). 버킷은 계속 비공개
OAC=$(aws cloudfront list-origin-access-controls $P --query "OriginAccessControlList.Items[?Name=='careerlens-media'].Id | [0]" --output text)
if [ "$OAC" = None ]; then
  OAC=$(aws cloudfront create-origin-access-control $P --origin-access-control-config \
    Name=careerlens-media,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3 --query OriginAccessControl.Id --output text)
fi

# 2. 버킷 정책: 이 배포(CloudFront)가 media/ 아래만 읽을 수 있다. 배포 묶음(code·data)은 그대로 비공개
if ! aws s3api get-bucket-policy $P --bucket $B >/dev/null 2>&1; then
  aws s3api put-bucket-policy $P --bucket $B --policy "$(jq -n --arg b $B --arg d "arn:aws:cloudfront::$ACC:distribution/$D" \
    '{Version:"2012-10-17",Statement:[{Sid:"CloudFrontMedia",Effect:"Allow",Principal:{Service:"cloudfront.amazonaws.com"},
      Action:"s3:GetObject",Resource:"arn:aws:s3:::\($b)/media/*",Condition:{StringEquals:{"AWS:SourceArn":$d}}}]}')"
elif ! aws s3api get-bucket-policy $P --bucket $B --query Policy --output text | grep -q CloudFrontMedia; then
  echo "버킷에 다른 정책이 있어 덮어쓰지 않았다. CloudFrontMedia 문장을 직접 더할 것"; exit 1
fi

# 3. CloudFront에 S3 원본과 /media/* 경로 더하기(기본 경로는 그대로 EC2). 바뀐 설정이 퍼지는 데 몇 분 걸린다
aws cloudfront get-distribution-config $P --id $D > "$T/d.json"
if ! jq -e '.DistributionConfig.Origins.Items[] | select(.Id=="media-s3")' "$T/d.json" >/dev/null; then
  jq --arg dom "$B.s3.ap-northeast-2.amazonaws.com" --arg oac "$OAC" '.DistributionConfig
    | .Origins.Items += [{Id:"media-s3", DomainName:$dom, OriginPath:"", CustomHeaders:{Quantity:0},
        S3OriginConfig:{OriginAccessIdentity:""}, OriginAccessControlId:$oac, ConnectionAttempts:3, ConnectionTimeout:10,
        OriginShield:{Enabled:false}}]
    | .Origins.Quantity = (.Origins.Items|length)
    | .CacheBehaviors.Items = ((.CacheBehaviors.Items // []) + [{PathPattern:"/media/*", TargetOriginId:"media-s3",
        ViewerProtocolPolicy:"redirect-to-https", Compress:false, SmoothStreaming:false, FieldLevelEncryptionId:"",
        CachePolicyId:"658327ea-f89d-4fab-a63d-7e88639e58f6",
        AllowedMethods:{Quantity:2, Items:["GET","HEAD"], CachedMethods:{Quantity:2, Items:["GET","HEAD"]}},
        LambdaFunctionAssociations:{Quantity:0}, FunctionAssociations:{Quantity:0},
        TrustedSigners:{Enabled:false, Quantity:0}, TrustedKeyGroups:{Enabled:false, Quantity:0}}])
    | .CacheBehaviors.Quantity = (.CacheBehaviors.Items|length)' "$T/d.json" > "$T/new.json"
  aws cloudfront update-distribution $P --id $D --if-match "$(jq -r .ETag "$T/d.json")" \
    --distribution-config file://"$T/new.json" --query Distribution.Status --output text
  echo "CloudFront 설정 바꿈. 퍼지는 데 몇 분 걸린다(aws cloudfront wait distribution-deployed $P --id $D)"
fi

# 4. 영상 올리기·바꾸기. CloudFront가 캐시한 옛 영상은 무효화로 지운다
if [ -n "${1:-}" ]; then
  aws s3 cp $P "$1" s3://$B/media/demo.mp4 --content-type video/mp4 --cache-control max-age=300
  aws cloudfront create-invalidation $P --distribution-id $D --paths '/media/*' --query Invalidation.Status --output text
  echo "올림: https://d3lowpvdkyf7ly.cloudfront.net/demo/"
fi
