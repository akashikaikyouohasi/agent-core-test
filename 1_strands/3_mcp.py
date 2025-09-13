from dotenv import load_dotenv
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# .envファイルから環境変数をロード
load_dotenv(dotenv_path="../.env")

# MCPクライアントを作成
mcp = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["strands-agents-mcp-server"]
    )
))

# MCPクライアントを起動しながら、エージェント実行
with mcp:
    agent = Agent(
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        tools=mcp.list_tools_sync()
    )

    agent("StrandsでA2Aサーバーの最小サンプルコードを書いて！")
