import logging
import asyncio
from typing import AsyncGenerator
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv

# AgentCore SDK をインポート
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext

# .envファイルから環境変数をロード（もしあれば）
load_dotenv()

# AgentCore アプリケーションを作成
app = BedrockAgentCoreApp()

# ログ設定
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)


# カスタムツールの定義
@tool
def weather_tool(location: str) -> str:
    """
    指定された場所の天気情報を取得します。
    
    Args:
        location (str): 天気を確認したい場所（例: 東京、大阪、ニューヨーク）
    
    Returns:
        str: 天気情報
    """
    # 実際のAPIを呼ぶ代わりにダミーデータを返す
    weather_data = {
        "東京": "晴れ、気温22度",
        "大阪": "曇り、気温20度",
        "ニューヨーク": "雨、気温15度",
        "ロンドン": "曇り、気温12度",
    }
    return weather_data.get(location, f"{location}の天気情報: 晴れのち曇り、気温18度")


@tool
def calculator(expression: str) -> str:
    """
    数式を計算します。
    
    Args:
        expression (str): 計算する数式（例: "2 + 2", "10 * 5"）
    
    Returns:
        str: 計算結果
    """
    try:
        # セキュリティのため、evalは実際のプロダクションでは避けるべき
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {str(e)}"


@tool
def text_analyzer(text: str) -> str:
    """
    テキストを分析して文字数や単語数を返します。
    
    Args:
        text (str): 分析するテキスト
    
    Returns:
        str: 分析結果
    """
    char_count = len(text)
    word_count = len(text.split())
    lines = text.split('\n')
    line_count = len(lines)
    
    return f"""テキスト分析結果:
- 文字数: {char_count}
- 単語数: {word_count}
- 行数: {line_count}
"""


# AgentCore用のエントリーポイント
@app.entrypoint
async def invoke(payload: dict, context: RequestContext) -> AsyncGenerator[str, None]:
    """AgentCore用のハンドラー（ストリーミング対応）"""
    print("=== AgentCore経由でのストリーミング呼び出し ===\n")
    
    # BedrockModelの作成
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-west-2",
        temperature=0.7,
    )
    
    # エージェントの作成（ツール付き）
    streaming_agent = Agent(
        model=bedrock_model,
        tools=[weather_tool, calculator, text_analyzer]
    )
    
    # ユーザーメッセージを取得
    user_message = payload.get(
        "prompt", 
        "No prompt found in input, please provide a 'prompt' key in the payload"
    )
    
    print(f"質問: {user_message}\n")
    
    # ストリーミングデータを蓄積
    accumulated_data = []
    event_logs = []
    
    # ストリーミング処理
    async for event in streaming_agent.stream_async(user_message):
        # イベントライフサイクルの処理
        if event.get("init_event_loop", False):
            msg = "🔄 イベントループ初期化\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        elif event.get("start_event_loop", False):
            msg = "▶️  イベントループサイクル開始\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        elif "message" in event:
            msg = f"📬 新しいメッセージ作成: {event['message']['role']}\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        elif event.get("complete", False):
            msg = "✅ サイクル完了\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        elif event.get("force_stop", False):
            msg = f"🛑 イベントループ強制停止: {event.get('force_stop_reason', '不明な理由')}\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        
        # ツール使用の処理
        if "current_tool_use" in event and event["current_tool_use"].get("name"):
            tool_name = event["current_tool_use"]["name"]
            msg = f"🔧 ツール使用中: {tool_name}\n"
            print(msg, end="")
            event_logs.append(msg)
            yield msg
        
        # データチャンクの処理
        if "data" in event:
            data = event["data"]
            accumulated_data.append(data)
            print(data, end="", flush=True)
            
            data_snippet = event["data"][:20] + ("..." if len(event["data"]) > 20 else "")
            msg = f"📟 Text: {data_snippet}"
            print(msg)
            #yield data
            yield f"{msg}\n"
    
    # 最終サマリーを出力
    full_response = "".join(accumulated_data)
    summary = f"\n\n{'='*80}\n✅ ストリーミング完了\n{'='*80}\n\n📊 最終結果:\n{full_response}\n\n{'='*80}\n"
    print(summary)
    yield summary


if __name__ == "__main__":
    # AgentCore サーバーを起動
    app.run()
