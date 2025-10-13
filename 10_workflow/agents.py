import logging
import os
from strands import Agent, tool
from strands_tools import calculator, current_time
from strands.models import BedrockModel

# tools.py からのインポート例
from tools.weather import get_tools

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
    model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2",
    temperature=0.3,
)

agent = Agent(
    model=bedrock_model,
    tools=[calculator, current_time, letter_counter, *get_tools()]
)

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

# エージェントを呼び出すエントリポイント関数を指定します
@app.entrypoint
def invoke(payload: dict, context: RequestContext) -> dict:
    """Handler for agent invocation"""
    user_message = payload.get(
        "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    )
    result = agent(user_message)
    # result.message が文字列の場合とオブジェクトの場合に対応
    message_content = result.message if isinstance(result.message, str) else str(result.message)

    return {"result": message_content}

if __name__ == "__main__":
    app.run()