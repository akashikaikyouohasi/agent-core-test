# WebSocket Lambda Architecture with Amazon Bedrock AgentCore Runtime

このプロジェクトは、AWS API Gateway WebSocket API、Lambda関数、そしてAmazon Bedrock AgentCore Runtimeを使用したサーバーレスWebSocketアーキテクチャの実装です。

## ✨ 特徴

- ✅ **Amazon Bedrock AgentCore Runtime統合**
  - LangGraph、CrewAI、Strands Agentsなどのフレームワーク対応
  - 最大8時間の長時間実行をサポート
  - 隔離されたmicroVM実行環境
- ✅ **WebSocket双方向通信**
- ✅ **スケーラブルなサーバーレスアーキテクチャ**
- ✅ **ブラウザベースのテストUI付き**（`websocket_test.html`）

## 📋 動作確認済み

このプロジェクトは以下の構成で動作確認済みです：
- ✅ Amazon Bedrock AgentCore Runtimeとの直接統合
- ✅ WebSocket経由でのリアルタイムAIエージェント呼び出し
- ✅ IAM権限による適切なアクセス制御
- ✅ セッション管理（33-64文字のセッションID要件対応）
- ✅ AWS Signature Version 4認証によるセキュアなAPI呼び出し

## 🚀 クイックスタート

### 1. AgentCoreにAgentをデプロイ

```bash
cd agentcore_example

# AgentCore CLIのインストール
pip install bedrock-agentcore-starter-toolkit

# Agentの設定とデプロイ
agentcore configure \
  --entrypoint agent.py \
  --name websocket-agent \
  --execution-role YOUR_EXECUTION_ROLE_ARN \
  --requirements-file requirements.txt

agentcore launch
# 出力されたAgent Runtime ARNをメモ
```

### 2. WebSocket APIをデプロイ

```bash
cd ../terraform

# terraform.tfvarsファイルを作成
cat > terraform.tfvars <<EOF
agentcore_runtime_arn = "YOUR_AGENT_RUNTIME_ARN"
aws_region = "ap-northeast-1"
EOF

# デプロイ
terraform init
terraform apply

# WebSocket URLを取得
terraform output websocket_url
```

### 3. ブラウザでテスト

```bash
# websocket_test.htmlをブラウザで開く
open websocket_test.html

# または VS Code Simple Browserで開く
```

1. WebSocket URLを入力
2. 「接続」をクリック
3. 「🤖 AgentCore Test」をクリックしてテスト！

## アーキテクチャ概要

```
Client (WebSocket)
    ↓
API Gateway (WebSocket API)
    ↓
Lambda Function (WebSocket Handler)
    ↓
Amazon Bedrock AgentCore Runtime
```

### コンポーネント

1. **API Gateway WebSocket API**
   - WebSocket接続のエンドポイントを提供
   - クライアントとの双方向通信を管理

2. **WebSocket Handler Lambda**
   - WebSocket接続の管理 ($connect, $disconnect, $default)
   - メッセージの受信と送信
   - Amazon Bedrock AgentCore Runtimeの呼び出し

3. **Amazon Bedrock AgentCore Runtime**
   - AI Agentの実行環境
   - LangGraph、CrewAI、Strands Agentsなどのフレームワークに対応
   - 最大8時間の長時間実行をサポート

## ディレクトリ構成

```
12_http/
├── terraform/                    # Terraformインフラストラクチャコード
│   ├── main.tf                  # メインのTerraform設定
│   ├── variables.tf             # 変数定義
│   ├── outputs.tf               # 出力定義
│   └── terraform.tfvars.example # 設定例
├── lambda/
│   └── websocket_handler/       # WebSocketハンドラーLambda
│       ├── app.py              # AgentCore Runtime統合
│       └── requirements.txt
├── agentcore_example/           # AgentCore Agentサンプルコード
│   ├── agent.py                # Agentエントリーポイント
│   ├── requirements.txt
│   └── README.md
├── websocket_test.html          # ブラウザベーステストUI
├── websocket_test.http          # VS Code REST Client用テスト
└── README.md
```

## デプロイ方法

### 前提条件

- AWS CLIがインストール・設定済み
- Terraformがインストール済み（v1.0以上）
- Python 3.11
- Amazon Bedrock AgentCore Runtimeにデプロイ済みのAgent

### デプロイ手順

1. **AgentをAgentCore Runtimeにデプロイ**
   ```bash
   # AgentCore Starter Toolkitのインストール
   pip install bedrock-agentcore-starter-toolkit

   # Agentの設定とデプロイ
   agentcore configure --entrypoint your_agent.py \
     --name my_agent \
     --execution-role your-execution-role-arn \
     --requirements-file requirements.txt

   agentcore launch

   # デプロイ後、Agent Runtime ARNをメモする
   # 例: arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_agent-xxxxx
   ```

2. **terraform.tfvarsファイルを作成**
   ```bash
   cd terraform
   cat > terraform.tfvars <<EOF
   agentcore_runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_agent-xxxxx"
   aws_region = "ap-northeast-1"
   EOF
   ```

3. **Terraformの初期化**
   ```bash
   terraform init
   ```

4. **リソースのデプロイ**
   ```bash
   terraform apply
   ```

5. **WebSocket URLの取得**
   ```bash
   terraform output websocket_url
   ```

## 使用方法（ブラウザUI）

1. **`websocket_test.html`をブラウザで開く**
   ```bash
   # ローカルでファイルを開く、または
   open websocket_test.html
   
   # VS Code Simple Browserで開く
   # コマンドパレット（Cmd+Shift+P）→ "Simple Browser: Show"
   ```

2. **WebSocket URLを入力**
   - Terraformの出力から取得したWebSocket URLを入力
   - 例: `wss://xxxxx.execute-api.ap-northeast-1.amazonaws.com/dev`

3. **接続**
   - 「接続」ボタンをクリック
   - ステータスが「接続済み」に変わることを確認

4. **メッセージ送信**
   - 「AgentCore Test」ボタンをクリック、または
   - カスタムメッセージを入力して「送信」

5. **レスポンス確認**
   - メッセージログにAIエージェントからの応答が表示されます

### メッセージ形式

WebSocket経由でAgentCoreにメッセージを送信する際の形式：

```json
{
  "prompt": "あなたの質問やメッセージ",
  "sessionId": "optional-session-id"
}
```

**重要**: セッションIDは33-64文字である必要があります。指定しない場合や短い場合は、自動的にWebSocket接続IDで補完されます。

**レスポンス例**:
```json
{
  "action": "response",
  "data": {
    "result": "AIエージェントからの回答",
    "sessionId": "実際に使用されたセッションID"
  },
  "timestamp": 1763226586731
}
```

### テスト方法

#### ブラウザUI（推奨）

`websocket_test.html`をブラウザで開いて、視覚的にテストできます。

#### コマンドライン (wscat)

```bash
# wscatのインストール
npm install -g wscat

# WebSocketに接続
wscat -c wss://YOUR_WEBSOCKET_URL

# メッセージ送信
{"prompt": "こんにちは", "sessionId": "test-session-12345678901234567890123"}
```

#### Pythonスクリプト

`websocket_client.py`を使用してテストできます：

```bash
python websocket_client.py \
  --url wss://YOUR_WEBSOCKET_URL \
  --interactive
```

または直接Pythonコードで：

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://YOUR_WEBSOCKET_URL"
    async with websockets.connect(uri) as websocket:
        # メッセージ送信
        message = {
            "prompt": "こんにちは！あなたは何ができますか？",
            "sessionId": "test-session-12345678901234567890123"
        }
        await websocket.send(json.dumps(message))

        # レスポンス受信
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

## リソース情報

### 作成されるAWSリソース

- **API Gateway WebSocket API**: WebSocketエンドポイント
- **Lambda関数 (2つ)**:
  - `websocket-lambda-websocket-handler`: WebSocket接続管理
  - `websocket-lambda-processor`: メッセージ処理
- **IAMロール (2つ)**: 各Lambda関数用
- **CloudWatch Log Groups (3つ)**: API GatewayとLambda関数のログ

### 出力値

Terraform applyの実行後、以下の情報が出力されます:

- `websocket_url`: WebSocket接続URL (wss://)
- `websocket_api_id`: API Gateway WebSocket API ID
- `websocket_handler_function_name`: WebSocketハンドラーLambda関数名
- `processor_function_name`: プロセッサーLambda関数名

## モニタリング

### CloudWatch Logs

各Lambda関数のログは以下のロググループに記録されます:

- `/aws/lambda/websocket-lambda-websocket-handler`
- `/aws/lambda/websocket-lambda-processor`
- `/aws/apigateway/websocket-lambda`

### ログの確認

```bash
# WebSocketハンドラーのログ
aws logs tail /aws/lambda/websocket-lambda-websocket-handler --follow

# プロセッサーのログ
aws logs tail /aws/lambda/websocket-lambda-processor --follow
```

## 技術詳細

### AgentCore Runtime統合の実装

このプロジェクトは、AWS公式ブログ記事で紹介されているパターンに基づいています：
[Set up custom domain names for Amazon Bedrock AgentCore Runtime agents](https://aws.amazon.com/jp/blogs/machine-learning/set-up-custom-domain-names-for-amazon-bedrock-agentcore-runtime-agents/)

#### 主要な実装ポイント

1. **直接HTTP API呼び出し**
   - boto3 SDKに `bedrock-agentcore-runtime` クライアントが存在しないため、urllib3を使用した直接HTTP呼び出し
   - エンドポイント: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations`

2. **AWS Signature Version 4認証**
   ```python
   from botocore.auth import SigV4Auth
   from botocore.awsrequest import AWSRequest
   
   # リクエストに署名を追加
   SigV4Auth(credentials, 'bedrock-agentcore', region).add_auth(aws_request)
   ```

3. **セッションID管理**
   - AgentCore Runtimeは33-64文字のセッションIDを要求
   - 不足分はWebSocket接続IDで自動補完
   ```python
   if len(session_id) < 33:
       session_id = f"{session_id}-{connection_id}"[:64]
   ```

4. **IAM権限**
   - `bedrock-agentcore:InvokeAgentRuntime` 権限が必要
   - リソースARNにワイルドカード（`*`）を追加してサブリソースへのアクセスを許可

### アーキテクチャの利点

- **スケーラビリティ**: API GatewayとLambdaによる自動スケール
- **コスト効率**: 使用した分だけの課金（サーバーレス）
- **セキュリティ**: IAMベースのアクセス制御、署名付きリクエスト
- **柔軟性**: AgentCoreとカスタムロジックの両方をサポート
- **長時間実行**: AgentCoreで最大8時間の実行時間をサポート

## クリーンアップ

リソースを削除する場合:

```bash
cd terraform
terraform destroy
```

## トラブルシューティング

### 接続エラー

1. **WebSocket URLが正しいか確認**
   ```bash
   terraform output websocket_url
   ```

2. **Lambda関数のログを確認**
   ```bash
   aws logs tail /aws/lambda/websocket-lambda-websocket-handler --follow --region ap-northeast-1
   ```

### IAM権限エラー

エラー: `User is not authorized to perform: bedrock-agentcore:InvokeAgentRuntime`

**解決方法**: IAM権限が正しく設定されていることを確認
```bash
# Terraformを再適用
cd terraform
terraform apply -auto-approve
```

Lambda関数のIAMロールには以下の権限が必要です：
- `bedrock-agentcore:InvokeAgentRuntime` - AgentCore Runtime呼び出し
- `execute-api:ManageConnections` - WebSocket接続管理
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` - CloudWatch Logs

### セッションIDエラー

エラー: `Member must have length greater than or equal to 33`

**解決方法**: このエラーは現在のコードで自動的に処理されます。セッションIDが33文字未満の場合、WebSocket接続IDで自動的にパディングされます。

### AgentCore Runtime呼び出しエラー

1. **AgentCore Runtime ARNが正しいか確認**
   ```bash
   cat terraform/terraform.tfvars
   ```

2. **Agentがデプロイされているか確認**
   ```bash
   agentcore list
   ```

3. **リージョンが一致しているか確認**
   - AgentCoreとWebSocket APIは同じリージョンにデプロイしてください

### メッセージが処理されない

1. **メッセージ形式の確認**
   - JSONフォーマットが正しいか確認
   - `prompt`フィールドが含まれているか確認
   - セッションIDが33文字以上あるか確認（自動調整されますが）

2. **Lambda関数のログを確認**
   ```bash
   aws logs tail /aws/lambda/websocket-lambda-websocket-handler --follow --region ap-northeast-1
   ```

## カスタマイズ

### Agentのカスタマイズ

`agentcore_example/agent.py`を編集して、Agentの動作をカスタマイズできます：

```python
@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    
    # カスタムロジックを追加
    if "天気" in user_message:
        # 天気情報を取得する処理
        pass
    
    response = agent(user_message)
    return str(response)
```

変更後、再デプロイ：
```bash
agentcore launch
```

## ライセンス

MIT
