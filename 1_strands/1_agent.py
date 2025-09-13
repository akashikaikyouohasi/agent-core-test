from dotenv import load_dotenv
from strands import Agent
import boto3
from botocore.exceptions import ClientError

# .envファイルから環境変数をロード
load_dotenv(dotenv_path="../.env")

try:
    # エージェントの初期化
    agent = Agent("us.anthropic.claude-3-5-haiku-20241022-v1:0")
    # エージェントの実行
    agent("JAWS-UGって何？")
except ClientError as e:
    if e.response['Error']['Code'] == 'ExpiredTokenException':
        print("AWS認証トークンが期限切れです。認証情報を更新してください。")
    else:
        print(f"AWS エラー: {e}")
except Exception as e:
    print(f"エラー: {e}")