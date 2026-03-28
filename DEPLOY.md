# デプロイ手順

## 前提条件

以下のツールがインストール・設定済みであること。

| ツール | 確認コマンド |
|---|---|
| AWS CLI | `aws --version` |
| SAM CLI | `sam --version` |
| pnpm | `pnpm --version` |
| AWS 認証情報 | `aws sts get-caller-identity` |

必要な IAM 権限: CloudFormation / Lambda / API Gateway / S3 / CloudFront / IAM / EventBridge Scheduler / Aurora DSQL (`dsql:*`)

---

## 初回セットアップ

### 1. Aurora DSQL クラスター作成

```bash
aws dsql create-cluster --region ap-northeast-1
```

出力された `endpoint` を控えておく。

### 2. DB スキーマ適用

```bash
TOKEN=$(aws dsql generate-db-connect-admin-auth-token \
  --hostname <DSQL_ENDPOINT> \
  --region ap-northeast-1 \
  --output text)

PGPASSWORD="$TOKEN" psql \
  "host=<DSQL_ENDPOINT> dbname=postgres user=admin sslmode=require" \
  -f backend/migrations/001_create_aws_updates.sql
```

### 3. Lambda Layer の構築・登録

本プロジェクトでは 2 つの Lambda Layer を使用する。

| Layer | 管理方法 | 内容 |
|---|---|---|
| psycopg3-python314-x86 | 手動登録（初回のみ） | psycopg v3 ドライバー |
| SharedLayer (aws-update-shared) | SAM 自動ビルド | boto3 + db_connection 共通モジュール |

**psycopg3 Layer の手動登録（初回のみ）**

```bash
mkdir -p /tmp/psycopg3-layer/python

pip download "psycopg[binary]==3.3.3" \
  --platform manylinux_2_17_x86_64 \
  --python-version 3.14 \
  --only-binary=:all: \
  -d /tmp/wheels/

pip install /tmp/wheels/*.whl \
  --target /tmp/psycopg3-layer/python \
  --no-deps

cd /tmp/psycopg3-layer && zip -r psycopg3-layer.zip python/

aws lambda publish-layer-version \
  --layer-name psycopg3-python314-x86 \
  --zip-file fileb:///tmp/psycopg3-layer/psycopg3-layer.zip \
  --compatible-runtimes python3.14 \
  --compatible-architectures x86_64 \
  --region ap-northeast-1
```

> `infra/template.yaml` の `Layers` ARN が登録した Layer の ARN と一致していることを確認する。

**SharedLayer は `sam build` 時に自動的にビルド・デプロイされるため手動操作不要。**

### 4. 初回デプロイ（過去 30 日分バックフィル）

カスタムドメインの有無に応じてコマンドを選択する。

**カスタムドメインなし（CloudFront デフォルトドメインで動作）**

```bash
export DSQL_ENDPOINT="<your-dsql-endpoint>"
./infra/deploy.sh --backfill 30 \
  --dsql-cluster-id <cluster-id>
```

デプロイ完了後に表示される `xxxx.cloudfront.net` のURLでアクセスできる。

**カスタムドメインあり**

ACM 証明書を事前に **us-east-1 リージョン** で発行しておく必要がある（CloudFront の要件）。

```bash
# 1. ACM 証明書を us-east-1 で発行（未発行の場合）
aws acm request-certificate \
  --domain-name example.com \
  --validation-method DNS \
  --region us-east-1
# → CertificateArn をメモ。DNS 検証レコードを追加して発行完了を待つ。

# 2. デプロイ
export DSQL_ENDPOINT="<your-dsql-endpoint>"
./infra/deploy.sh --backfill 30 \
  --dsql-cluster-id <cluster-id> \
  --custom-domain example.com \
  --acm-certificate-arn arn:aws:acm:us-east-1:<account-id>:certificate/<cert-id>
```

デプロイ完了後、表示される CNAME レコードを DNS に登録する。

```
example.com -> xxxx.cloudfront.net
```

デプロイ完了後、以下が表示される。

```
===== デプロイ完了 =====
  フロントエンド: https://xxxxxxxxxxxx.cloudfront.net
  API Endpoint  : https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod
```

### 5. title_ja カラムのマイグレーション適用

初回スキーマには `title_ja` カラムが含まれていないため、Lambda 経由で追加する。

```bash
aws lambda invoke \
  --function-name aws-update-crawler \
  --payload '{"run_migration": true}' \
  --cli-binary-format raw-in-base64-out \
  --region ap-northeast-1 \
  response.json && cat response.json
```

---

## 通常デプロイ（バックエンド・インフラ含む全体更新）

Lambda、API Gateway、インフラの変更を含む場合に実行する。

```bash
# カスタムドメインなし
export DSQL_ENDPOINT="<your-dsql-endpoint>"
./infra/deploy.sh --dsql-cluster-id <cluster-id>

# カスタムドメインあり
export DSQL_ENDPOINT="<your-dsql-endpoint>"
./infra/deploy.sh \
  --dsql-cluster-id <cluster-id> \
  --custom-domain example.com \
  --acm-certificate-arn arn:aws:acm:us-east-1:<account-id>:certificate/<cert-id>
```

> `--dsql-cluster-id` を省略すると IAM ポリシーが同アカウント内の全 DSQL クラスターに適用される。本番環境では必ず指定すること。クラスター ID は `aws dsql list-clusters` で確認できる。

---

## フロントエンドのみ更新

フロントエンド（`frontend/src/` 配下）のみ変更した場合は SAM デプロイ不要。

```bash
# 1. API エンドポイントを取得
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name aws-update-collection \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text)

# 2. ビルド
cd frontend
VITE_API_BASE_URL="$API_ENDPOINT" pnpm build

# 3. S3 にアップロード
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name aws-update-collection \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

aws s3 sync dist/ "s3://${BUCKET}/" --delete

# 4. CloudFront キャッシュを無効化
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name aws-update-collection \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*"
```

> `CloudFrontDistributionId` は `infra/template.yaml` への追加分であるため、初回は次の全体デプロイ後に Outputs から取得できるようになる。それ以前は AWS マネジメントコンソールの CloudFront 画面から Distribution ID を確認すること。

---

## 運用コマンド

### Crawler を手動実行

```bash
aws lambda invoke \
  --function-name aws-update-crawler \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  --region ap-northeast-1 \
  response.json && cat response.json
```

### 日本語要約が空のレコードを再処理

```bash
aws lambda invoke \
  --function-name aws-update-crawler \
  --payload '{"reprocess_empty": true}' \
  --cli-binary-format raw-in-base64-out \
  --region ap-northeast-1 \
  response.json && cat response.json
```

### Lambda ログを確認

```bash
# Crawler
aws logs tail /aws/lambda/aws-update-crawler --follow --region ap-northeast-1

# API
aws logs tail /aws/lambda/aws-update-api --follow --region ap-northeast-1
```

---

## スタックの削除

```bash
# S3 バケットを先に空にする
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name aws-update-collection \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

aws s3 rm "s3://${BUCKET}" --recursive

# スタック削除
aws cloudformation delete-stack \
  --stack-name aws-update-collection \
  --region ap-northeast-1
```

> Aurora DSQL クラスターは CloudFormation 管理外のため、別途削除する。
> ```bash
> aws dsql delete-cluster --identifier <cluster-identifier> --region ap-northeast-1
> ```
