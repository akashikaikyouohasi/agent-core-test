# Amazon Bedrock AgentCore Runtime Example

このディレクトリには、WebSocketと統合するAgentCore Agentのサンプルコードが含まれています。

## セットアップ

1. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **Agentの設定**
   ```bash
   # 実行ロールのARNを設定
   export EXECUTION_ROLE_ARN="arn:aws:iam::123456789012:role/your-execution-role"

   # Agentの設定
   agentcore configure \
     --entrypoint agent.py \
     --name websocket-agent \
     --execution-role $EXECUTION_ROLE_ARN \
     --requirements-file requirements.txt
   ```

3. **Agentのデプロイ**
   ```bash
   agentcore launch
   ```

4. **Agent Runtime ARNの取得**
   デプロイ後、出力されるAgent Runtime ARNをメモしてください。
   ```
   Agent Runtime ARN: arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/websocket-agent-xxxxx
   ```

5. **Terraform設定に追加**
   `terraform/terraform.tfvars`ファイルに、取得したARNを設定します：
   ```hcl
   agentcore_runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/websocket-agent-xxxxx"
   ```

## Agentの動作確認

WebSocket経由でAgentに接続して、質問を送信できます：

```json
{
  "prompt": "こんにちは！あなたは何ができますか？",
  "sessionId": "test-session-123"
}
```

## カスタマイズ

`agent.py`ファイルを編集して、Agentの動作をカスタマイズできます。
変更後は、再度`agentcore launch`でデプロイしてください。
