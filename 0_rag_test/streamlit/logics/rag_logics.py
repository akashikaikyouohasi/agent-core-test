from typing import TYPE_CHECKING
import json

PROMPT_TEMPLATE = \
"""下記<context></context>はユーザーから問い合わせられた質問に対して関係があると思われる検索結果の一覧です。
注意深く詠んでください。
<context>
{context}
</context>
あなたは親切なAIボットです。ユーザーからの質問に対して<context</context>で与えられている情報をもとに誠実に回答します。
ただし、質問に対する答えが<context></context>に書かれていない場合は、正直に「分かりません。」と回答してください。

下記<question></question>がユーザーからの質問です。
<question>
{question}
</question>
ユーザーからの質問に回答してください。

なお、ユーザーからの質問に回答する前に<thinking></thinking>タグで思考過程を記してから回答内容を<answer></answer>に加えてください。
"""

def invoke_llm(prompt: str, model_id: str, bedrock_runtime_client) -> str:
    """
    LLMを呼び出して回答を取得する
    """
    response = bedrock_runtime_client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ],
            }
        ],
        inferenceConfig={
            "temperature": 0.0
        }
    )
    result = response['output']['message']['content'][0]['text']
    return result


# コンテキストを取得する関数
def retrieve_context(query: str, knowledge_base_id: str, client_runtime) -> list[dict]:
    response = client_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'overrideSearchType': 'SEMANTIC',
                'numberOfResults': 3
            }
        },
        retrievalQuery={
            'text': query
        }
    )
    return response['retrievalResults']

def call_rag(
    question: str,
    knowledge_base_id: str,
    client_runtime,
    bedrock_runtime_client,
    model_id: str
) -> tuple[str, list[dict]]:
    """
    質問→検索→LLM→回答 という最もシンプルな流れを実現する
    """
    # ナレッジベースからコンテキストを取得
    context = retrieve_context(
        question,
        knowledge_base_id,
        client_runtime
    )
    # コンテキストをプロンプトに埋め込む
    prompt = PROMPT_TEMPLATE.format(
        context=json.dumps(context, ensure_ascii=False),
        question=question
    )
    # LLMを呼び出す
    llm_response = invoke_llm(prompt, model_id, bedrock_runtime_client)
    return llm_response, context


