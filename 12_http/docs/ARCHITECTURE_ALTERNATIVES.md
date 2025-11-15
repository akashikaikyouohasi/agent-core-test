# WebSocket → AgentCore Runtime アーキテクチャの選択肢

## 要件

Client → API Gateway WebSocket → AgentCore Runtime HTTPエンドポイント

できるだけLambdaを介さずに直接呼び出したい。

## オプション分析

### ❌ Option 1: Lambda完全削除（不可能）

```
Client (WebSocket)
    ↓
API Gateway WebSocket (HTTP Integration)
    ↓
AgentCore Runtime HTTP Endpoint
```

**問題点:**
- ✗ AWS Signature V4認証がAPI Gateway単体では生成できない
- ✗ WebSocketの `@connections` APIへのレスポンス送信ができない
- ✗ セッションID管理ロジックが実装できない

**結論:** 技術的に不可能

---

### ✅ Option 2: 薄いLambdaプロキシ（推奨）

現在の実装を最小化したバージョン。

```
Client (WebSocket)
    ↓
API Gateway WebSocket
    ↓
Lambda (最小限のプロキシ)
    ├─ SigV4署名
    ├─ セッションID管理
    └─ レスポンス送信
    ↓
AgentCore Runtime HTTP
```

**メリット:**
- ✓ 必要最小限のロジックのみ
- ✓ セキュリティ確保（SigV4認証）
- ✓ 双方向通信の実現

**実装例:**

```python
# 最小限のプロキシLambda
import json
import boto3
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

def lambda_handler(event, context):
    # 1. WebSocket情報取得
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event.get('body', '{}'))
    
    # 2. SigV4署名付きリクエスト作成
    response = call_agentcore_with_sigv4(body)
    
    # 3. WebSocketにレスポンス送信
    send_to_websocket(connection_id, response)
    
    return {'statusCode': 200}
```

**コスト:**
- Lambda実行時間: 平均 100-500ms（AgentCoreレスポンス待ち時間含む）
- 料金: $0.0000002 per request (無料枠: 月100万リクエスト)

---

### 🔄 Option 3: Step Functions経由（オーバースペック）

```
Client (WebSocket)
    ↓
API Gateway WebSocket
    ↓
Lambda (WebSocket Handler)
    ↓
Step Functions
    └─ HTTP Task (AgentCore Runtime)
    ↓
Lambda (Response Sender)
```

**問題点:**
- ✗ 複雑すぎる
- ✗ コストが高い
- ✗ レイテンシーが増加
- ✗ SigV4認証が依然として必要

**結論:** 不要な複雑性

---

### 🌐 Option 4: AppSync + HTTP Resolver（WebSocket代替）

AWS AppSyncを使用してGraphQL WebSocketを提供し、HTTP Resolverで直接呼び出す。

```
Client (AppSync GraphQL WebSocket)
    ↓
AppSync
    ├─ HTTP Resolver (SigV4対応)
    └─ AgentCore Runtime HTTP
```

**メリット:**
- ✓ AppSyncがSigV4署名をサポート
- ✓ Lambdaなしで実現可能
- ✓ リアルタイムサブスクリプション機能

**デメリット:**
- ✗ GraphQLスキーマ定義が必要
- ✗ クライアント実装が複雑になる
- ✗ AgentCore RuntimeがGraphQLをネイティブサポートしていない
- ✗ コストがAPI Gateway + Lambdaより高い

**実装例:**

```graphql
# AppSync Schema
type Mutation {
  invokeAgent(prompt: String!, sessionId: String!): String
    @http(
      method: POST,
      endpoint: "https://bedrock-agentcore.ap-northeast-1.amazonaws.com/runtimes/${ARN}/invocations"
      headers: {
        name: "Content-Type",
        value: "application/json"
      }
    )
}

type Subscription {
  onAgentResponse: String
    @aws_subscribe(mutations: ["invokeAgent"])
}
```

**問題:** AppSyncのHTTP Resolverは**AWS SigV4署名をサポートしていますが、AgentCore RuntimeのARNエンコーディングとカスタムヘッダー要件に対応できない可能性が高い**。

---

## 結論と推奨

### 🏆 推奨アーキテクチャ: Option 2（現在の実装）

**理由:**
1. **セキュリティ**: SigV4認証を確実に実装
2. **シンプル**: 最小限のコンポーネント
3. **コスト効率**: Lambda無料枠で十分カバー可能
4. **保守性**: 標準的なAWSパターン
5. **柔軟性**: 将来の拡張が容易

### Lambda最小化の実装例

現在の`lambda/websocket_handler/app.py`は既に最小化されています：

```python
# 必要最小限の処理のみ
def lambda_handler(event, context):
    route_key = event['requestContext']['routeKey']
    
    if route_key == '$default':
        # 1. メッセージ受信
        # 2. AgentCore呼び出し（SigV4署名）
        # 3. レスポンス送信
        return handle_message(event, connection_id)
    
    return {'statusCode': 200}
```

**処理フロー:**
1. WebSocketメッセージ受信: ~1ms
2. SigV4署名生成: ~5ms
3. AgentCore Runtime呼び出し: ~100-5000ms（AIの処理時間）
4. WebSocketレスポンス送信: ~10ms

**Lambda内での処理時間: わずか16ms程度**（AgentCoreの処理時間を除く）

### コスト試算

**前提:**
- 月間リクエスト: 100,000回
- 平均Lambda実行時間: 500ms (AgentCore待ち含む)
- メモリ: 128MB

**料金:**
- リクエスト料金: 100,000 × $0.0000002 = **$0.02**
- 実行時間料金: 100,000 × 0.5s × $0.0000166667 = **$0.83**
- **合計: $0.85/月** (無料枠適用後)

つまり、**Lambdaのコストは無視できるレベル**です。

---

## 技術的な制約まとめ

### API Gateway WebSocketの制限

| 機能 | サポート状況 |
|------|------------|
| VTL (Velocity Template) | ✓ サポート |
| HTTP統合 | ✓ サポート |
| AWS SigV4署名生成 | ✗ **サポートなし** |
| カスタムヘッダー追加 | ✓ サポート（VTLで可能） |
| `@connections` API呼び出し | ✗ Lambda経由が必須 |
| URLエンコーディング | ✓ VTLで可能 |

**結論:** SigV4署名と`@connections` APIの2点で、Lambdaが必須。

---

## 最終推奨事項

### ✅ DO（やるべきこと）

1. **現在の実装（Lambda Proxy）を維持**
   - 最小限のコードで必要な機能を実現
   - セキュリティと信頼性を確保

2. **Lambda内部の最適化**
   - 不要なロギングを削減
   - メモリサイズの最適化（128MBで十分）
   - タイムアウトの調整（AgentCoreに合わせて120秒）

3. **モニタリングの実装**
   - CloudWatch Metricsでレイテンシー監視
   - X-Rayでトレーシング（必要に応じて）

### ❌ DON'T（避けるべきこと）

1. **Lambdaの完全削除を試みる**
   - 技術的に不可能、時間の無駄

2. **過度な複雑化**
   - Step Functions、EventBridge等の追加は不要
   - シンプルな構成がベスト

3. **AppSyncへの移行**
   - GraphQLのオーバーヘッドが大きい
   - AgentCore Runtimeとのミスマッチあり

---

## FAQ

### Q1: Lambdaのコールドスタートが心配です

**A:** 
- Python 3.11のLambdaコールドスタートは平均 200-500ms
- プロビジョニング済み同時実行（Provisioned Concurrency）を使用すれば解決
- ただし、AgentCoreの処理時間（数秒〜数分）に比べれば無視できるレベル

### Q2: Lambda関数をさらに最小化できませんか？

**A:** 
現在の実装は既に最小化されています：
- ライブラリ: boto3, urllib3のみ（標準ライブラリ）
- コード: ~200行（コメント含む）
- 処理: 署名、API呼び出し、レスポンス送信のみ

これ以上削減すると、エラーハンドリングやロギングが犠牲になります。

### Q3: API Gateway HTTP APIは使えませんか？

**A:** 
HTTP APIはWebSocketをサポートしていません：
- HTTP API: REST/HTTPのみ（WebSocket非対応）
- WebSocket API: WebSocketのみ（現在使用中）

双方向通信が必要な場合、WebSocket APIが必須です。

---

## 参考資料

### AWS公式ドキュメント

1. [API Gateway WebSocket API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
2. [AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html)
3. [Amazon Bedrock AgentCore Runtime](https://aws.amazon.com/bedrock/agentcore/)

### ブログ記事

- [Set up custom domain names for Amazon Bedrock AgentCore Runtime agents](https://aws.amazon.com/jp/blogs/machine-learning/set-up-custom-domain-names-for-amazon-bedrock-agentcore-runtime-agents/)

### 関連する制限事項

- API Gateway WebSocket API Quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html
- Lambda Quotas: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html
