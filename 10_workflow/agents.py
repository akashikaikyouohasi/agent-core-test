import logging
import os
from datetime import datetime
from typing import AsyncGenerator
from strands import Agent, tool
from strands_tools import calculator, current_time, workflow
from strands.models import BedrockModel

# tools.py からのインポート例
from tools.weather import get_tools
from tools.prime_number import get_tools

# AgentCore SDK をインポートします
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext


# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)

# ログを標準エラー出力にストリームするように設定
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)

# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())


# AgentCore アプリケーションを作成します
app = BedrockAgentCoreApp()

# Create a BedrockModel
bedrock_model = BedrockModel(
    #model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    region_name="us-west-2",
    temperature=0.3,
)

agent = Agent(
    model=bedrock_model,
    #tools=[workflow]
    #tools=[calculator, current_time, letter_counter, workflow, *get_tools()]
)

def event_loop_tracker(**kwargs):
    # Track event loop lifecycle
    if kwargs.get("init_event_loop", False):
        print("🔄 Event loop initialized")
    elif kwargs.get("start_event_loop", False):
        print("▶️ Event loop cycle starting")
    elif "message" in kwargs:
        print(f"📬 New message created: {kwargs['message']['role']}")
    elif kwargs.get("complete", False):
        print("✅ Cycle completed")
    elif kwargs.get("force_stop", False):
        print(f"🛑 Event loop force-stopped: {kwargs.get('force_stop_reason', 'unknown reason')}")

    # Track tool usage
    if "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
        tool_name = kwargs["current_tool_use"]["name"]
        print(f"🔧 Using tool: {tool_name}")

    # Show only a snippet of text to keep output clean
    if "data" in kwargs:
        # Only show first 20 chars of each chunk for demo purposes
        data_snippet = kwargs["data"][:20] + ("..." if len(kwargs["data"]) > 20 else "")
        print(f"📟 Text: {data_snippet}")

def local_test():
    """Local test function to invoke the agent directly"""
    print("=== エージェントのローカルテスト ===\n")
    # Ask the agent a question that uses the available tools
    message = """
    I have 4 requests:

    1. What is the time right now?
    2. Calculate 3111696 / 74088
    3. Tell me how many letter R's are in the word "strawberry" 🍓
    """
    agent(message)


def workflow_test():
    """Local test function to invoke the workflow tool directly"""
    print("=== ワークフローのローカルテスト ===\n")
    # ユニークなIDを日付ベースで生成（例: data_analysis_20251019_143025）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_id = f"data_analysis_{timestamp}"
    print(f"Workflow ID: {workflow_id}\n")

    # Create the workflow
    agent.tool.workflow(
        action="create",
        workflow_id=workflow_id,
        tasks=[
            {
                "task_id": "data_extraction",
                "description": "Extract key financial data from the quarterly report",
                "system_prompt": "You extract and structure financial data from reports.",
                "priority": 5
            },
            {
                "task_id": "trend_analysis",
                "description": "Analyze trends in the data compared to previous quarters",
                "dependencies": ["data_extraction"],
                "system_prompt": "You identify trends in financial time series.",
                "priority": 3
            },
            {
                "task_id": "report_generation",
                "description": "Generate a comprehensive analysis report",
                "dependencies": ["trend_analysis"],
                "system_prompt": "You create clear financial analysis reports.",
                "priority": 2
            }
        ]
    )
    # Start the workflow
    agent.tool.workflow(action="start", workflow_id=workflow_id)
    # Check results
    status = agent.tool.workflow(action="status", workflow_id=workflow_id)
    print(f"Workflow Status: {status}")

# エージェントを呼び出すエントリポイント関数を指定します
#@app.entrypoint
# def invoke(payload: dict, context: RequestContext):
#    """Handler for agent invocation"""
    # print("=== 同期エージェントの呼び出し ===\n") 
    # user_message = payload.get(
    #     "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    # )
    # result = agent(user_message)
    # # result.message が文字列の場合とオブジェクトの場合に対応
    # message_content = result.message if isinstance(result.message, str) else str(result.message)
    #return {"result": message_content}

    #workflow_test()
    #return "OK"


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


@app.entrypoint
async def invoke(payload: dict, context: RequestContext) ->  AsyncGenerator[str, None]:
    """Handler for agent invocation"""
    # print("=== 同期エージェントの呼び出し ===\n") 
    # user_message = payload.get(
    #     "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    # )
    # result = agent(user_message)
    # # result.message が文字列の場合とオブジェクトの場合に対応
    # message_content = result.message if isinstance(result.message, str) else str(result.message)
    #return {"result": message_content}

    #workflow_test()
    #return "OK"

    #========================================================================
    # print("=== エージェントのストリーミング呼び出し by async ===\n") 
    # streaming_agent = Agent(
    #     model=bedrock_model,
    #     tools=[workflow]
    # )
    # user_message = payload.get(
    #     "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    # )
    # stream = streaming_agent.stream_async(user_message)

    # async for event in stream:
    #     if "data" in event:
    #         print(event["data"], end="")
    #         yield event["data"]          # Stream data chunks
    #     elif "message" in event:
    #         print(event["message"], end="")
    #         yield event["message"]       # Stream message parts
    #========================================================================
    # print("=== エージェントのストリーミング呼び出し by async ===\n") 
    # streaming_agent = Agent(
    #     model=bedrock_model
    # )
    # user_message = payload.get(
    #     "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    # )
    # stream = streaming_agent.stream_async(user_message)

    # # ストリーミングデータを蓄積するための変数
    # accumulated_data = []
    # event_logs = []

    # async for event in stream:
    #     # Track event loop lifecycle
    #     if event.get("init_event_loop", False):
    #         print("🔄 Event loop initialized")
    #         event_logs.append("🔄 Event loop initialized")
    #         yield "🔄 Event loop initialized\n"
    #     elif event.get("start_event_loop", False):
    #         print("▶️ Event loop cycle starting")
    #         event_logs.append("▶️ Event loop cycle starting")
    #         yield "▶️ Event loop cycle starting\n"
    #     elif "message" in event:
    #         print(f"📬 New message created: {event['message']['role']}")
    #         event_logs.append(f"📬 New message created: {event['message']['role']}")
    #         yield f"📬 New message created: {event['message']['role']}\n"
    #     elif event.get("complete", False):
    #         print("✅ Cycle completed")
    #         event_logs.append("✅ Cycle completed")
    #         yield "✅ Cycle completed\n"
    #     elif event.get("force_stop", False):
    #         print(f"🛑 Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}")
    #         event_logs.append(f"🛑 Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}")
    #         yield f"🛑 Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}\n"

    #     # Track tool usage
    #     if "current_tool_use" in event and event["current_tool_use"].get("name"):
    #         tool_name = event["current_tool_use"]["name"]
    #         print(f"🔧 Using tool: {tool_name}")
    #         event_logs.append(f"🔧 Using tool: {tool_name}")
    #         yield f"🔧 Using tool: {tool_name}\n"

    #     # データを蓄積
    #     if "data" in event:
    #         accumulated_data.append(event["data"])
    #         # Show only a snippet of text to keep output clean
    #         data_snippet = event["data"][:20] + ("..." if len(event["data"]) > 20 else "")
    #         print(f"📟 Text: {data_snippet}")
    #         yield f"📟 Text: {data_snippet}\n"

    # # 最後にまとめて出力
    # full_response = "".join(accumulated_data)
    # summary = f"\n\n{'='*50}\n📊 最終結果のまとめ\n{'='*50}\n\n{full_response}\n\n{'='*50}\n"
    # print(summary)
    # yield summary
    #========================================================================
    print("=== エージェントのストリーミング呼び出し by async ===\n") 
    streaming_agent = Agent(
        model=bedrock_model
    )
    user_message = payload.get(
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

# @app.entrypoint
# def invoke(payload: dict, context: RequestContext):
#     print("=== コールバックハンドラーありのエージェントの呼び出し ===\n")
#     agent_with_all_callback = Agent(
#         model=bedrock_model,
#         callback_handler=event_loop_tracker
#     )
#     user_message = payload.get(
#         "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
#     )
    
#     # 同期実行して結果を取得
#     result = agent_with_all_callback(user_message)
#     print(f"サーバー側の結果: {result}")  # サーバー側コンソールに表示
    
#     # result.messageを文字列に変換
#     message_content = result.message if isinstance(result.message, str) else str(result.message)
    
#     # クライアント側に返す
#     return message_content





if __name__ == "__main__":
    app.run()