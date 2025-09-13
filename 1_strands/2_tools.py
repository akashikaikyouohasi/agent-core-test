from dotenv import load_dotenv
from strands import Agent, tool

# .envファイルから環境変数をロード
load_dotenv(dotenv_path="../.env")

# 文字カウント関数をツールとして定義
@tool
def counter(word: str, letter: str):
    """wordの中にletterがいくつあるか数える"""
    print(f"[Counting tool] Counting '{letter}' in '{word}'")
    return word.lower().count(letter.lower())

# エージェントを構成
agent = Agent(
    model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    tools=[counter]
)

# エージェントの実行
agent("Strandsの中にSはいくつある？")