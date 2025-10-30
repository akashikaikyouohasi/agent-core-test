import logging
import asyncio
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv

# .envファイルから環境変数をロード（もしあれば）
load_dotenv()

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


def process_streaming_event(event: dict) -> str:
    """ストリーミング中のイベントを処理する関数"""
    output = ""
    
    # イベントループのトラッキング
    if event.get("init_event_loop", False):
        msg = "🔄 イベントループ初期化"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    elif event.get("start_event_loop", False):
        msg = "▶️  イベントループサイクル開始"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    elif "message" in event:
        msg = f"📬 新しいメッセージ作成: {event['message']['role']}"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    elif event.get("complete", False):
        msg = "✅ サイクル完了"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    elif event.get("force_stop", False):
        msg = f"🛑 イベントループ強制停止: {event.get('force_stop_reason', '不明な理由')}"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    
    # ツール使用のトラッキング
    if "current_tool_use" in event and event["current_tool_use"].get("name"):
        tool_name = event["current_tool_use"]["name"]
        msg = f"🔧 ツール使用中: {tool_name}"
        print(f"\n{msg}")
        output += f"\n{msg}\n"
    
    # テキストストリーミング
    if "data" in event:
        # ストリーミングデータを表示（改行なし）
        print(event["data"], end="", flush=True)
        output += event["data"]
    
    return output


async def test_streaming():
    """ストリーミングレスポンスのテスト（非同期イテレータ使用）"""
    print("=== Strands エージェント - ストリーミングレスポンステスト ===\n")
    
    # BedrockModelの作成
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-west-2",
        temperature=0.7,
    )
    
    # エージェントの作成（ツール付き）
    agent = Agent(
        model=bedrock_model,
        tools=[weather_tool, calculator, text_analyzer]
    )
    
    # テストメッセージ
    message = """
    以下の3つのタスクを実行してください:
    
    1. 東京の天気を教えてください
    2. 123 × 456 を計算してください
    3. 「こんにちは、世界！これはストリーミングテストです。」というテキストを分析してください
    
    それぞれの結果を日本語で説明してください。
    """
    
    print(f"質問: {message}\n")
    print("=" * 80)
    print("📡 ストリーミングレスポンス開始...\n")
    
    # stream_async()を使って非同期イテレータを取得
    accumulated_data = []
    
    async for event in agent.stream_async(message):
        # イベントを処理（画面に表示）
        process_streaming_event(event)
        
        # データを蓄積
        if "data" in event:
            accumulated_data.append(event["data"])
    
    # 最終結果を表示
    full_response = "".join(accumulated_data)
    print("\n\n" + "=" * 80)
    print("✅ ストリーミング完了")
    print("=" * 80)
    print(f"\n📊 最終結果:\n{full_response}\n")
    
    return full_response


async def test_simple_streaming():
    """シンプルなストリーミングテスト（ツールなし、非同期イテレータ使用）"""
    print("=== シンプルなストリーミングテスト ===\n")
    
    # BedrockModelの作成
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-west-2",
        temperature=0.7,
    )
    
    # エージェントの作成（ツールなし）
    agent = Agent(
        model=bedrock_model
    )
    
    message = "日本の有名な観光地を3つ紹介して、それぞれについて簡単に説明してください。"
    
    print(f"質問: {message}\n")
    print("=" * 80)
    print("📡 ストリーミングレスポンス開始...\n")
    
    # stream_async()を使って非同期イテレータを取得
    accumulated_data = []
    
    async for event in agent.stream_async(message):
        # イベントを処理（画面に表示）
        process_streaming_event(event)
        
        # データを蓄積
        if "data" in event:
            accumulated_data.append(event["data"])
    
    # 最終結果を表示
    full_response = "".join(accumulated_data)
    print("\n\n" + "=" * 80)
    print("✅ ストリーミング完了")
    print("=" * 80)
    print(f"\n📊 最終結果:\n{full_response}\n")
    
    return full_response


if __name__ == "__main__":
    async def main():
        """メイン実行関数"""
        try:
            # ツール付きストリーミングテスト
            await test_streaming()
            
            print("\n" + "=" * 80 + "\n")
            
            # シンプルなストリーミングテスト
            await test_simple_streaming()
            
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # 非同期関数を実行
    asyncio.run(main())
