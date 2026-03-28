#!/usr/bin/env bash
# AWS Update Check Collection deploy script
# Usage: ./infra/deploy.sh [--backfill 30] [--custom-domain example.com --acm-certificate-arn arn:aws:acm:us-east-1:...]
set -euo pipefail

STACK_NAME="aws-update-collection"
REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"
BACKFILL_DAYS=1
CUSTOM_DOMAIN=""
ACM_CERT_ARN=""
DSQL_CLUSTER_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backfill)             BACKFILL_DAYS="$2";      shift 2 ;;
    --custom-domain)        CUSTOM_DOMAIN="$2";      shift 2 ;;
    --acm-certificate-arn)  ACM_CERT_ARN="$2";       shift 2 ;;
    --dsql-cluster-id)      DSQL_CLUSTER_ID="$2";    shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---- 事前チェック ----
command -v sam  >/dev/null || { echo "ERROR: sam CLI が見つかりません"; exit 1; }
command -v aws  >/dev/null || { echo "ERROR: aws CLI が見つかりません"; exit 1; }
command -v pnpm >/dev/null || { echo "ERROR: pnpm が見つかりません"; exit 1; }

if [[ -z "${DSQL_ENDPOINT:-}" ]]; then
  echo "ERROR: 環境変数 DSQL_ENDPOINT が設定されていません"
  exit 1
fi

if [[ -n "$CUSTOM_DOMAIN" && -z "$ACM_CERT_ARN" ]]; then
  echo "ERROR: --custom-domain を指定する場合は --acm-certificate-arn も必要です"
  echo "       ACM 証明書は us-east-1 リージョンで発行したものを指定してください"
  exit 1
fi

if [[ -z "$DSQL_CLUSTER_ID" ]]; then
  echo "WARNING: --dsql-cluster-id が指定されていません。IAM ポリシーが全クラスターに適用されます。"
  echo "         本番環境では --dsql-cluster-id <cluster-id> を指定することを推奨します。"
fi

echo "=== [1/4] フロントエンドビルド (仮ビルド) ==="
pushd "$(dirname "$0")/../frontend" >/dev/null
pnpm install
pnpm build
popd >/dev/null

echo "=== [2/4] SAM ビルド ==="
sam build \
  --template-file "$(dirname "$0")/template.yaml"

echo "=== [3/4] SAM デプロイ ==="
PARAM_OVERRIDES=(
  "DsqlEndpoint=${DSQL_ENDPOINT}"
  "BackfillDays=${BACKFILL_DAYS}"
)
if [[ -n "$DSQL_CLUSTER_ID" ]]; then
  PARAM_OVERRIDES+=("DsqlClusterId=${DSQL_CLUSTER_ID}")
fi
if [[ -n "$CUSTOM_DOMAIN" ]]; then
  PARAM_OVERRIDES+=(
    "CustomDomain=${CUSTOM_DOMAIN}"
    "AcmCertificateArn=${ACM_CERT_ARN}"
  )
fi

sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "${PARAM_OVERRIDES[@]}" \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo "=== [4/4] スタック出力を取得 ==="
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

CF_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDomain'].OutputValue" \
  --output text)

API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text)

echo "=== [4/4] フロントエンドをS3にアップロード ==="
pushd "$(dirname "$0")/../frontend" >/dev/null
VITE_API_BASE_URL="$API_ENDPOINT" pnpm build
aws s3 sync dist/ "s3://${BUCKET}/" --delete
popd >/dev/null

if [[ -n "$CUSTOM_DOMAIN" ]]; then
  FRONTEND_URL="https://${CUSTOM_DOMAIN}"
else
  FRONTEND_URL="https://${CF_DOMAIN}"
fi

echo ""
echo "===== デプロイ完了 ====="
echo "  フロントエンド: ${FRONTEND_URL}"
echo "  API Endpoint  : ${API_ENDPOINT}"
if [[ -n "$CUSTOM_DOMAIN" ]]; then
  echo ""
  echo "  カスタムドメインを使用しています。DNS の CNAME レコードを設定してください:"
  echo "    ${CUSTOM_DOMAIN} -> ${CF_DOMAIN}"
fi
