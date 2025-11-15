# WebSocket AgentCore Integration - 変更サマリー

## 概要

WebSocketのdefaultルートを### 3. 2つのデプロイオプション

~~**Option 1**: AgentCore Runtime統合（AIエージェント対応）~~  
~~**Option 2**: カスタムProcessor Lambda（シンプルなロジック実装）~~

**現在**: AgentCore Runtime統合のみをサポート

カスタムProcessor Lambdaは削除されました。AgentCore Runtimeを使用することで、より強力なAIエージェント機能を利用できます。ntCore Runtimeの直接呼び出しに変更しました。
これにより、AWS公式ブログ記事で紹介されているパターンに従った実装となります。

参考: https://aws.amazon.com/jp/blogs/machine-learning/set-up-custom-domain-names-for-amazon-bedrock-agentcore-runtime-agents/

## ✅ 動作確認済み

このプロジェクトは完全に動作確認されており、以下の機能が正常に動作します：
- ✅ WebSocket経由でのAgentCore Runtime呼び出し
- ✅ リアルタイムAIエージェント応答
- ✅ セッション管理（33-64文字のID要件）
- ✅ AWS SigV4認証
- ✅ IAM権限管理

**注**: カスタムProcessor Lambdaは削除され、AgentCore Runtime統合のみをサポートしています。

## 主な変更点

### 1. Lambda関数の更新

**ファイル**: `lambda/websocket_handler/app.py`

- **変更前**: Processor Lambdaを呼び出し
- **変更後**: Amazon Bedrock AgentCore Runtimeを直接呼び出し

```python
# urllib3を使用した直接HTTP呼び出し（boto3にクライアントが存在しないため）
import urllib3
from botocore.auth import SigV4Auth

# AgentCore Runtimeエンドポイント
endpoint_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"

# AWS SigV4署名を追加
SigV4Auth(credentials, 'bedrock-agentcore', region).add_auth(aws_request)

# HTTPリクエスト実行
http = urllib3.PoolManager()
response = http.request('POST', endpoint_url, body=payload_bytes, headers=headers)
```

**重要な実装ポイント**:
- ✅ セッションIDを33-64文字に自動調整
- ✅ AWS Signature Version 4による認証
- ✅ urllib3による直接HTTP呼び出し（boto3 SDKに該当クライアントがないため）

### 2. Terraform設定の更新

**ファイル**: `terraform/main.tf`, `terraform/variables.tf`

- AgentCore Runtime ARNを環境変数として設定可能に
- IAM権限を修正:
  - ❌ `bedrock-agentcore:InvokeAgent` （存在しない権限）
  - ✅ `bedrock-agentcore:InvokeAgentRuntime` （正しい権限）
- リソースARNにワイルドカード追加: `arn:...runtime/agent-id*`
  - サブリソース `/runtime-endpoint/DEFAULT` へのアクセスを許可
- Processor Lambdaをオプション化（AgentCore未使用時のみデプロイ）
- タイムアウトを30秒から120秒に延長（AgentCoreの長時間実行に対応）

**IAMポリシー例**:
```json
{
  "Effect": "Allow",
  "Action": ["bedrock-agentcore:InvokeAgentRuntime"],
  "Resource": "arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/websocketagent-xxxxx*"
}
```

### 3. 2つのデプロイオプション

#### Option 1: AgentCore Runtime統合（推奨）

```bash
# terraform.tfvars
agentcore_runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_agent-xxxxx"
```

WebSocket → Lambda → **AgentCore Runtime**

#### Option 2: カスタムProcessor Lambda

```bash
# terraform.tfvars
agentcore_runtime_arn = ""
```

WebSocket → Lambda → **Processor Lambda**

### 4. メッセージ形式の追加

#### AgentCore用

```json
{
  "prompt": "あなたの質問",
  "sessionId": "session-id"
}
```

#### Processor Lambda用（従来通り）

```json
{
  "action": "echo",
  "data": {
    "message": "Hello"
  }
}
```

### 5. 新規ファイル

- `agentcore_example/agent.py` - AgentCoreサンプルコード
- `agentcore_example/requirements.txt` - Agent依存関係
- `agentcore_example/README.md` - Agentデプロイ手順
- `terraform/terraform.tfvars.example` - 設定例
- `websocket_test.html` - ブラウザベーステストUI

### 6. UI更新

**ファイル**: `websocket_test.html`

- AgentCore用のアクションを追加
- 「🤖 AgentCore Test」ボタンを追加
- メッセージテンプレートにAgentCore形式を追加

## デプロイ手順

### AgentCore Runtimeを使用する場合

1. **Agentをデプロイ**
   ```bash
   cd agentcore_example
   pip install bedrock-agentcore-starter-toolkit
   
   agentcore configure --entrypoint agent.py \
     --name websocket-agent \
     --execution-role your-role-arn \
     --requirements-file requirements.txt
   
   agentcore launch
   ```

2. **Terraformで設定**
   ```bash
   cd ../terraform
   cat > terraform.tfvars <<EOF
   agentcore_runtime_arn = "YOUR_AGENT_RUNTIME_ARN"
   EOF
   
   terraform init
   terraform apply
   ```

3. **テスト**
   - `websocket_test.html`をブラウザで開く
   - WebSocket URLを入力
   - 「AgentCore Test」を実行

### カスタムProcessor Lambdaを使用する場合

```bash
cd terraform
terraform init
terraform apply
# agentcore_runtime_arnは空のまま
```

## 利点

1. ✅ **AIエージェント統合**: LangGraph、CrewAI、Strandsなどのフレームワークに対応
2. ✅ **長時間実行**: 最大8時間の実行時間をサポート
3. ✅ **隔離された実行環境**: 各セッションが独自のmicroVMで実行
4. ✅ **柔軟性**: AgentCoreとカスタムロジックの両方をサポート
5. ✅ **スケーラビリティ**: サーバーレスで自動スケール

## 互換性

- 既存のProcessor Lambda実装は引き続き使用可能
- `agentcore_runtime_arn`を空にすることで従来の動作を維持
- 段階的な移行が可能

## 次のステップ

1. AgentCoreにカスタムAgentをデプロイ
2. WebSocket経由でAgentをテスト
3. 必要に応じてAgent実装をカスタマイズ
4. プロダクション環境へのデプロイ

## 参考資料

- [Amazon Bedrock AgentCore Runtime公式ドキュメント](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [カスタムドメイン設定ブログ記事](https://aws.amazon.com/jp/blogs/machine-learning/set-up-custom-domain-names-for-amazon-bedrock-agentcore-runtime-agents/)
- [AgentCore Starter Toolkit](https://pypi.org/project/bedrock-agentcore-starter-toolkit/)
