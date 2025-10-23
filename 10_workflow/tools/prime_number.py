from strands import  Agent, tool
from strands.models import BedrockModel

def get_tools() -> list:
    """Return a list of tools including weather-related tools."""
    return [calculate_and_judge_prime_number_workflow]

# Create a BedrockModel
bedrock_model = BedrockModel(
    #model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    region_name="us-west-2",
    temperature=0.3,
)

def process_event_lifecycle(event: dict, event_logs: list) -> str:
    """イベントループのライフサイクルイベントを処理
    
    Note: I/O待機がないため、同期関数で十分
    """
    if event.get("init_event_loop", False):
        msg = "🔄 Event loop initialized"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    elif event.get("start_event_loop", False):
        msg = "▶️ Event loop cycle starting"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    elif "message" in event:
        msg = f"📬 New message created: {event['message']['role']}"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    elif event.get("complete", False):
        msg = "✅ Cycle completed"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    elif event.get("force_stop", False):
        msg = f"🛑 Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    return ""


def process_tool_usage(event: dict, event_logs: list) -> str:
    """ツール使用イベントを処理
    
    Note: I/O待機がないため、同期関数で十分
    """
    if "current_tool_use" in event and event["current_tool_use"].get("name"):
        tool_name = event["current_tool_use"]["name"]
        msg = f"🔧 Using tool: {tool_name}"
        print(msg)
        event_logs.append(msg)
        return f"{msg}\n"
    return ""


def process_data_chunk(event: dict, accumulated_data: list) -> str:
    """データチャンクを処理して蓄積
    
    Note: I/O待機がないため、同期関数で十分
    """
    if "data" in event:
        accumulated_data.append(event["data"])
        # Show only a snippet of text to keep output clean
        data_snippet = event["data"][:20] + ("..." if len(event["data"]) > 20 else "")
        msg = f"📟 Text: {data_snippet}"
        print(msg)
        return f"{msg}\n"
    return ""

@tool
async def calculate_and_judge_prime_number_workflow(user_prompt: str) -> str:
    """
    Calculate a prime number based on the user's prompt and judge if it's prime.
    """
    streaming_agent = Agent(
        model=bedrock_model
    )
    user_message = user_prompt.get(
        "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    )
    stream = streaming_agent.stream_async(user_message)

    # ストリーミングデータを蓄積するための変数
    accumulated_data = []
    event_logs = []

    # イベントストリームの処理
    async for event in stream:
        # イベントライフサイクルの処理（同期関数なのでawait不要）
        lifecycle_msg = process_event_lifecycle(event, event_logs)
        if lifecycle_msg:
            yield lifecycle_msg

        # ツール使用の処理（同期関数なのでawait不要）
        tool_msg = process_tool_usage(event, event_logs)
        if tool_msg:
            yield tool_msg

        # データチャンクの処理（同期関数なのでawait不要）
        data_msg = process_data_chunk(event, accumulated_data)
        if data_msg:
            yield data_msg

    # 最後にまとめて出力
    full_response = "".join(accumulated_data)
    summary = f"\n\n{'='*50}\n📊 最終結果のまとめ\n{'='*50}\n\n{full_response}\n\n{'='*50}\n"
    print(summary)
    yield summary



    agent1_result = summary

    streaming_agent_2 = Agent(
        model=bedrock_model,
            system_prompt="結果が素数か判定するエージェントです。"
    )
    stream_2 = streaming_agent_2.stream_async(agent1_result)

    # ストリーミングデータを蓄積するための変数
    accumulated_data_2 = []
    event_logs_2 = []

    # イベントストリームの処理
    async for event in stream_2:
        # イベントライフサイクルの処理（同期関数なのでawait不要）
        lifecycle_msg = process_event_lifecycle(event, event_logs_2)
        if lifecycle_msg:
            yield lifecycle_msg

        # ツール使用の処理（同期関数なのでawait不要）
        tool_msg = process_tool_usage(event, event_logs_2)
        if tool_msg:
            yield tool_msg

        # データチャンクの処理（同期関数なのでawait不要）
        data_msg = process_data_chunk(event, accumulated_data_2)
        if data_msg:
            yield data_msg

    # 最後にまとめて出力
    full_response_2 = "".join(accumulated_data_2)
    summary_2 = f"\n\n{'='*50}\n📊 最終結果のまとめ\n{'='*50}\n\n{full_response_2}\n\n{'='*50}\n"
    print(summary_2)
    yield summary_2
