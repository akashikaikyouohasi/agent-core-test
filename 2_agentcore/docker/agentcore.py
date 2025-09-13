from dotenv import load_dotenv
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import os

# .envファイルから環境変数をロード
load_dotenv(dotenv_path="../.env")

print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
print("AWS_SECRET_ACCESS_KEY:", "設定済み" if os.getenv('AWS_SECRET_ACCESS_KEY') else "未設定")
print("AWS_SESSION_TOKEN:", "設定済み" if os.getenv('AWS_SESSION_TOKEN') else "未設定")
print("AWS_DEFAULT_REGION:", os.getenv('AWS_DEFAULT_REGION'))


# Strandsでエージェントを作成
agent = Agent("us.anthropic.claude-3-7-sonnet-20250219-v1:0")

# AgentCoreのサーバーを作成
app = BedrockAgentCoreApp()

# エージェント呼び出し関数を、AgentCoreの開始点に設定
@app.entrypoint
def invoke_agent(payload, context):
    # リクエストのペイロードからプロンプトを取得
    prompt = payload.get("prompt")

    # エージェントを呼び出してレスポンスを返却
    return {"result": agent(prompt).message}

# AgentCoreサーバーを起動
app.run()
