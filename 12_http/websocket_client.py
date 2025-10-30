#!/usr/bin/env python3
"""
WebSocket Test Client
WebSocket API Gateway接続テスト用のPythonクライアント
"""

import asyncio
import websockets
import json
import argparse
import sys
from datetime import datetime


async def test_websocket(url, action, data):
    """
    WebSocketに接続してメッセージを送信し、レスポンスを受信する

    Args:
        url: WebSocket URL (wss://...)
        action: 実行するアクション (echo, uppercase, reverse, timestamp)
        data: 送信するデータ（JSON文字列またはdict）
    """
    try:
        print(f"Connecting to: {url}")
        print(f"Action: {action}")
        print(f"Data: {data}")
        print("-" * 50)

        async with websockets.connect(url) as websocket:
            print("✓ Connected to WebSocket")

            # データの準備
            if isinstance(data, str):
                try:
                    data_dict = json.loads(data)
                except json.JSONDecodeError:
                    print("Error: Invalid JSON data")
                    return
            else:
                data_dict = data

            # メッセージの送信
            message = {
                "action": action,
                "data": data_dict
            }

            print(f"\nSending message:")
            print(json.dumps(message, indent=2))

            await websocket.send(json.dumps(message))
            print("✓ Message sent")

            # レスポンスの受信
            print("\nWaiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)

            print("\nReceived response:")
            print("-" * 50)

            # JSONとして整形して表示
            try:
                response_data = json.loads(response)
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response)

            print("-" * 50)
            print("✓ Test completed successfully")

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
        sys.exit(1)
    except asyncio.TimeoutError:
        print("✗ Timeout: No response received")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


async def interactive_mode(url):
    """
    対話モードでWebSocketに接続

    Args:
        url: WebSocket URL
    """
    print(f"Connecting to: {url}")
    print("Interactive mode - Type 'quit' to exit")
    print("-" * 50)

    try:
        async with websockets.connect(url) as websocket:
            print("✓ Connected to WebSocket")
            print("\nAvailable actions: echo, uppercase, reverse, timestamp")
            print("\nExample:")
            print('  {"action": "echo", "data": {"message": "hello"}}')
            print('  {"action": "uppercase", "data": {"text": "hello world"}}')
            print("")

            while True:
                # メッセージ入力
                try:
                    message_str = input("Enter message (JSON): ").strip()
                except EOFError:
                    break

                if message_str.lower() in ['quit', 'exit', 'q']:
                    break

                if not message_str:
                    continue

                try:
                    # JSON検証
                    message = json.loads(message_str)

                    # メッセージ送信
                    await websocket.send(json.dumps(message))
                    print("✓ Message sent")

                    # レスポンス受信
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)

                    # レスポンス表示
                    try:
                        response_data = json.loads(response)
                        print("\nResponse:")
                        print(json.dumps(response_data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(f"\nResponse: {response}")

                    print("")

                except json.JSONDecodeError as e:
                    print(f"✗ Invalid JSON: {e}")
                except asyncio.TimeoutError:
                    print("✗ Timeout: No response received")
                except Exception as e:
                    print(f"✗ Error: {e}")

            print("\nDisconnecting...")

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='WebSocket API Gateway Test Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Echo test
  %(prog)s --url wss://xxx.execute-api.ap-northeast-1.amazonaws.com/dev \\
           --action echo --data '{"message": "hello"}'

  # Uppercase test
  %(prog)s --url wss://xxx.execute-api.ap-northeast-1.amazonaws.com/dev \\
           --action uppercase --data '{"text": "hello world"}'

  # Interactive mode
  %(prog)s --url wss://xxx.execute-api.ap-northeast-1.amazonaws.com/dev \\
           --interactive
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='WebSocket URL (wss://...)'
    )

    parser.add_argument(
        '--action',
        choices=['echo', 'uppercase', 'reverse', 'timestamp'],
        help='Action to perform'
    )

    parser.add_argument(
        '--data',
        default='{}',
        help='JSON data to send (default: {})'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )

    args = parser.parse_args()

    # WebSocket URLの検証
    if not args.url.startswith('wss://') and not args.url.startswith('ws://'):
        print("Error: URL must start with wss:// or ws://")
        sys.exit(1)

    # 対話モードまたは単発テスト
    if args.interactive:
        asyncio.run(interactive_mode(args.url))
    else:
        if not args.action:
            print("Error: --action is required in non-interactive mode")
            parser.print_help()
            sys.exit(1)

        asyncio.run(test_websocket(args.url, args.action, args.data))


if __name__ == '__main__':
    main()
