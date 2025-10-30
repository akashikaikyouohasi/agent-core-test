# WebSocket Lambda Architecture

このプロジェクトは、AWS API Gateway WebSocket API、Lambda関数を使用したサーバーレスWebSocketアーキテクチャの実装です。

## アーキテクチャ概要

```
Client (WebSocket)
    ↓
API Gateway (WebSocket API)
    ↓
Lambda Function (WebSocket Handler)
    ↓
Lambda Function (Processor)
```

### コンポーネント

1. **API Gateway WebSocket API**
   - WebSocket接続のエンドポイントを提供
   - クライアントとの双方向通信を管理

2. **WebSocket Handler Lambda**
   - WebSocket接続の管理 ($connect, $disconnect, $default)
   - メッセージの受信と送信
   - Processor Lambdaの呼び出し

3. **Processor Lambda**
   - 実際のビジネスロジックを処理
   - 複数のアクション（echo, uppercase, reverse, timestamp）をサポート

## ディレクトリ構成

```
12_http/
├── terraform/              # Terraformインフラストラクチャコード
│   ├── main.tf            # メインのTerraform設定
│   ├── variables.tf       # 変数定義
│   └── outputs.tf         # 出力定義
├── lambda/
│   ├── websocket_handler/ # WebSocketハンドラーLambda
│   │   ├── app.py
│   │   └── requirements.txt
│   └── processor/         # プロセッサーLambda
│       ├── app.py
│       └── requirements.txt
├── websocket_test.http    # WebSocket接続テスト用HTTPファイル
└── README.md
```

## デプロイ方法

### 前提条件

- AWS CLIがインストール・設定済み
- Terraformがインストール済み (v1.0以上)
- Python 3.11

### デプロイ手順

1. **Terraformの初期化**
   ```bash
   cd terraform
   terraform init
   ```

2. **リソースのプランニング**
   ```bash
   terraform plan
   ```

3. **リソースのデプロイ**
   ```bash
   terraform apply
   ```

4. **WebSocket URLの取得**
   ```bash
   terraform output websocket_url
   ```

## 使用方法

### サポートされているアクション

Processor Lambdaは以下のアクションをサポートしています:

1. **echo** - 受信したデータをそのまま返す
   ```json
   {
     "action": "echo",
     "data": {"message": "Hello World"}
   }
   ```

2. **uppercase** - テキストを大文字に変換
   ```json
   {
     "action": "uppercase",
     "data": {"text": "hello world"}
   }
   ```

3. **reverse** - テキストを反転
   ```json
   {
     "action": "reverse",
     "data": {"text": "hello"}
   }
   ```

4. **timestamp** - 現在のタイムスタンプを返す
   ```json
   {
     "action": "timestamp",
     "data": {}
   }
   ```

### テスト方法

#### 方法1: HTTPファイルを使用（VS Code + REST Client拡張）

`websocket_test.http` ファイルを使用してWebSocket接続をテストできます。

1. VS Codeで `websocket_test.http` を開く
2. REST Client拡張機能がインストールされていることを確認
3. ファイル内の "Send Request" リンクをクリック

#### 方法2: wscat (コマンドライン)

```bash
# wscatのインストール
npm install -g wscat

# WebSocketに接続
wscat -c wss://YOUR_WEBSOCKET_URL

# メッセージ送信
{"action": "echo", "data": {"message": "test"}}
```

#### 方法3: Pythonスクリプト

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://YOUR_WEBSOCKET_URL"
    async with websockets.connect(uri) as websocket:
        # メッセージ送信
        message = {
            "action": "echo",
            "data": {"message": "Hello from Python"}
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
   - CloudWatch Logsで各Lambda関数のログを確認

3. **IAM権限の確認**
   - Lambda実行ロールに必要な権限があるか確認

### メッセージが処理されない

1. **メッセージ形式の確認**
   - JSONフォーマットが正しいか確認
   - `action`フィールドが含まれているか確認

2. **Processor Lambdaのログ確認**
   - エラーメッセージがないか確認

## カスタマイズ

### 新しいアクションの追加

`lambda/processor/app.py` に新しい処理関数を追加:

```python
def process_custom_action(data):
    """Custom processing logic"""
    result = # your logic here
    return {
        'action': 'custom_action',
        'status': 'success',
        'result': result
    }
```

そして、`lambda_handler` 関数内でアクションを処理:

```python
elif action == 'custom_action':
    result = process_custom_action(data)
```

## ライセンス

MIT
