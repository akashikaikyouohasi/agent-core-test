#!/bin/bash

# AgentCore Runtime Direct API Test Script
# このスクリプトはAgentCore RuntimeのHTTPエンドポイントに直接アクセスします

set -e

# 設定
AGENT_RUNTIME_ARN="arn:aws:bedrock-agentcore:ap-northeast-1:206863353204:runtime/websocketagent-TCNFrUBi67"
REGION="ap-northeast-1"
SESSION_ID="test-session-$(date +%s)000000000000000000000"  # 33文字以上

# ARNをURLエンコード
ENCODED_ARN=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${AGENT_RUNTIME_ARN}', safe=''))")

# エンドポイントURL
ENDPOINT_URL="https://bedrock-agentcore.${REGION}.amazonaws.com/runtimes/${ENCODED_ARN}/invocations"

echo "=========================================="
echo "AgentCore Runtime Direct API Test"
echo "=========================================="
echo "Agent ARN: ${AGENT_RUNTIME_ARN}"
echo "Region: ${REGION}"
echo "Session ID: ${SESSION_ID}"
echo "Endpoint: ${ENDPOINT_URL}"
echo "=========================================="
echo ""

# リクエストペイロード
PAYLOAD=$(cat <<EOF
{
  "prompt": "こんにちは！あなたは何ができますか？",
  "sessionId": "${SESSION_ID}"
}
EOF
)

echo "Request Payload:"
echo "${PAYLOAD}" | jq '.'
echo ""

# 方法1: awscurl を使用（推奨）
echo "方法1: awscurl を使用"
echo "----------------------------------------"

if ! command -v awscurl &> /dev/null; then
    echo "❌ awscurl がインストールされていません"
    echo "インストール方法:"
    echo "  pip install awscurl"
    echo ""
else
    echo "✓ awscurl でリクエスト送信中..."
    echo ""
    
    awscurl --service bedrock-agentcore \
        --region "${REGION}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: ${SESSION_ID}" \
        -d "${PAYLOAD}" \
        "${ENDPOINT_URL}" | jq '.'
    
    echo ""
    echo "✓ リクエスト完了"
fi

echo ""
echo "=========================================="
echo ""

# 方法2: AWS CLI + Python を使用
echo "方法2: AWS CLI の署名機能を使用"
echo "----------------------------------------"
echo "このスクリプトは参考用です。実際の実行にはaws4authライブラリが必要です。"
echo ""

cat <<'PYTHON_SCRIPT'
# Python スクリプト例
import json
import urllib.parse
from requests_aws4auth import AWS4Auth
import requests
import boto3

# AWS認証情報を取得
session = boto3.Session()
credentials = session.get_credentials()

# AWS SigV4 認証
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'ap-northeast-1',
    'bedrock-agentcore',
    session_token=credentials.token
)

# エンドポイント
agent_arn = 'arn:aws:bedrock-agentcore:ap-northeast-1:206863353204:runtime/websocketagent-TCNFrUBi67'
encoded_arn = urllib.parse.quote(agent_arn, safe='')
url = f'https://bedrock-agentcore.ap-northeast-1.amazonaws.com/runtimes/{encoded_arn}/invocations'

# リクエスト
payload = {
    'prompt': 'こんにちは！',
    'sessionId': 'test-session-12345678901234567890123'
}

headers = {
    'Content-Type': 'application/json',
    'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': payload['sessionId']
}

response = requests.post(url, json=payload, headers=headers, auth=auth)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "テスト完了"
echo "=========================================="
