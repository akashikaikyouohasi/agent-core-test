#!/usr/bin/env python3
"""
AgentCore Runtime Direct API Test Script (Python版)

AWS SigV4署名を使用してAgentCore RuntimeのHTTPエンドポイントに直接アクセスします。
"""

import json
import urllib.parse
import sys
from datetime import datetime

try:
    import boto3
    import requests
    from requests_aws4auth import AWS4Auth
except ImportError as e:
    print(f"❌ 必要なライブラリがインストールされていません: {e}")
    print("\nインストール方法:")
    print("  pip install boto3 requests requests-aws4auth")
    sys.exit(1)


def test_agentcore_runtime():
    """AgentCore RuntimeのHTTPエンドポイントをテストします"""
    
    # 設定
    AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:ap-northeast-1:206863353204:runtime/websocketagent-TCNFrUBi67"
    REGION = "ap-northeast-1"
    
    # セッションIDを生成（33-64文字）
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    SESSION_ID = f"test-session-{timestamp}000000000"  # 33文字以上にパディング
    
    print("=" * 60)
    print("AgentCore Runtime Direct API Test (Python)")
    print("=" * 60)
    print(f"Agent ARN: {AGENT_RUNTIME_ARN}")
    print(f"Region: {REGION}")
    print(f"Session ID: {SESSION_ID} (length: {len(SESSION_ID)})")
    print("=" * 60)
    print()
    
    # AWS認証情報を取得
    try:
        session = boto3.Session(region_name=REGION)
        credentials = session.get_credentials()
        
        if not credentials:
            print("❌ AWS認証情報が見つかりません")
            print("AWS CLIの設定を確認してください: aws configure")
            sys.exit(1)
            
        print("✓ AWS認証情報を取得しました")
        
    except Exception as e:
        print(f"❌ AWS認証情報の取得に失敗しました: {e}")
        sys.exit(1)
    
    # AWS SigV4 認証オブジェクトを作成
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        'bedrock-agentcore',
        session_token=credentials.token
    )
    
    # エンドポイントURLを構築
    encoded_arn = urllib.parse.quote(AGENT_RUNTIME_ARN, safe='')
    endpoint_url = f'https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations'
    
    print(f"Endpoint: {endpoint_url}")
    print()
    
    # リクエストペイロード
    payload = {
        'prompt': 'こんにちは！あなたは何ができますか？',
        'sessionId': SESSION_ID
    }
    
    # ヘッダー
    headers = {
        'Content-Type': 'application/json',
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': SESSION_ID
    }
    
    print("Request Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    print("Sending POST request...")
    print()
    
    # リクエスト送信
    try:
        response = requests.post(
            endpoint_url,
            json=payload,
            headers=headers,
            auth=auth,
            timeout=120  # 120秒タイムアウト
        )
        
        print(f"Status Code: {response.status_code}")
        print()
        
        # レスポンスヘッダーを表示
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        
        # レスポンスボディを表示
        print("Response Body:")
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response.text)
        else:
            print(response.text)
        
        print()
        
        # 結果判定
        if response.status_code == 200:
            print("✓ リクエスト成功！")
        else:
            print(f"⚠️  エラーが発生しました (Status: {response.status_code})")
            
    except requests.exceptions.Timeout:
        print("❌ リクエストがタイムアウトしました")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == '__main__':
    test_agentcore_runtime()
