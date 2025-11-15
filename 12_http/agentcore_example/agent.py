"""
WebSocket統合用のAgentCore Agent サンプル
"""
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Agentの初期化
agent = Agent()

# AgentCore Appの初期化
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    """
    WebSocketから受信したメッセージを処理する

    Args:
        payload: WebSocketから送信されたデータ
                 {"prompt": "質問内容", "sessionId": "session-id"}

    Returns:
        str: Agentからのレスポンス（JSON serializable）
    """
    # プロンプトの取得
    user_message = payload.get("prompt", "")

    if not user_message:
        return "メッセージが空です。質問を送信してください。"

    # Agentに質問を送信
    response = agent(user_message)

    # レスポンスを返す（文字列に変換）
    return str(response)


if __name__ == "__main__":
    # ローカルテスト用
    app.run()
