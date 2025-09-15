"""
Memory Hook Provider
会話を自動的にMemoryに保存し、過去の記憶を取得する
"""

from bedrock_agentcore.memory import MemoryClient
from strands.hooks.events import AgentInitializedEvent, MessageAddedEvent
from strands.hooks.registry import HookProvider, HookRegistry
import copy

class MemoryHook(HookProvider):
    """Memory 管理を自動化する Hook"""
    # HookProviderは、フックプロバイダーは、エージェントのライフサイクルにおける様々なイベントをサブスクライブすることで、エージェントの機能を拡張するための構成可能な方法を提供します。
    # このプロトコルにより、エージェントイベントにフックできる再利用可能なコンポーネントを構築できます。

    def __init__(
            self,
            memory_client: MemoryClient,
            memory_id: str,
            actor_id: str,
            session_id: str,
    ):
        """
        Args:
            memory_client: Memory Client
            memory_id: Memry リソースID
            actor_id: 顧客ID
            session_id: セッションID
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.actor_id = actor_id
        self.session_id = session_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """エージェント初期化時に最近の会話履歴を読み込む"""
        try:
            # Memoryから最新の５ターンの会話を取得
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                k=5,
            )

            if recent_turns:
                # 会話履歴をコンテキスト用にフォーマット
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = "assistant" if message["role"] == "ASSISTANT" else "user" # assistant/user に変換
                        content = message["content"]["text"]
                        context_messages.append(
                            {"role": role, "content": [{"text": content}]}
                        )
                # エージェントのシステムプリンプとにコンテキストを追加
                event.agent.system_prompt += """
                ユーザーの嗜好や事実を直接回答しないでください。
                ユーザーの嗜好や事実は、ユーザーをより理解するために厳密に使用してください。
                また、この情報は古い可能性があることに注意してください。
                """
                # 会話履歴をエージェントに設定
                event.agent.messages = context_messages
        except Exception as e:
            print(f"Memory 読込エラー: {e}")
    
    def _add_context_user_query(
        self, namespace: str, query: str, init_content: str, event: MessageAddedEvent
    ):
        """ユーザークエリにコンテキストを追加"""
        content = None
        # Memoryから関連する記憶を取得。
        memories = self.memory_client.retrieve_memories(
            memory_id=self.memory_id, namespace=namespace, query=query, top_k=3
        )

        for memory in memories:
            # 最初の記憶の場合、初期コンテンツを追加
            if not content:
                content = "\n\n" + init_content + "\n\n"
            # 記憶の内容を追加
            content += memory["content"]["text"]
            # ユーザーメッセージにコンテキストを追加
            if content:
                event.agent.messages[-1]["content"][0]["text"] += content + "\n\n"
    
    def on_message_added(self, event: MessageAddedEvent):
        """メッセージが追加された時にMemory に保存"""
        
        messages = copy.deepcopy(event.agent.messages) # メッセージをコピー
        try:
            if messages[-1]["role"] == "user" or messages[-1]["role"] == "assistant":
                # ユーザーメッセージの場合、コンテキストを追加。system prompt は除外
                if "text" not in  messages[-1]["content"][0]:
                    return # text キーがない場合は処理しない
                
                # 長期記憶からユーザーの嗜好と事実を取得してコンテキストに追加
                if messages[-1]["role"] == "user":
                    # ユーザーの嗜好を取得してコンテキストに追加
                    self._add_context_user_query(
                        namespace=f"support/user/{self.actor_id}/preferences",
                        query=messages[-1]["content"][0]["text"],
                        init_content="これらはユーザーの嗜好です:",
                        event=event,
                    )

                    # ユーザーの事実を取得してコンテキストに追加
                    self._add_context_user_query(
                        namespace=f"support/user/{self.actor_id}/facts",
                        query=messages[-1]["content"][0]["text"],
                        init_content="これらはユーザーの事実です:",
                        event=event,
                    )

                # 会話をMemoryに保存し、次の会話で利用できるようにする
                self.memory_client.save_conversation(
                    memory_id=self.memory_id,
                    actor_id=self.actor_id,
                    session_id=self.session_id,
                    messages=[
                        (messages[-1]["content"][0]["text"], messages[-1]["role"])
                    ],# 最新メッセージのみ保存,タプルで (content, role)
                )
            
        except Exception as e:
            raise RuntimeError(f"Memory 保存エラー: {e}")
    
    def register_hooks(self, registry: HookRegistry):
        """フックをレジストリに登録"""
        # イベント タイプとコールバック関数のマッピングを維持し、コールバックを登録してイベントの発生時にそれらを呼び出すためのメソッドを提供します。

        # MessageAddedEventは、エージェントのメッセージリストに新しいメッセージが追加されたときにトリガーされるイベントです。
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        # AgentInitializedEventは、エージェントが初期化されたときにトリガーされるイベントです。
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)

# HookProviderの詳細
# https://strandsagents.com/latest/documentation/docs/api-reference/hooks/ 
