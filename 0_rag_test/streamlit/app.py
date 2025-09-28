import os
import re
from typing import TYPE_CHECKING
from dotenv import load_dotenv

import streamlit as st
import boto3

from logics.rag_logics import call_rag



# 環境変数の読込
load_dotenv(".env", verbose=True)

KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"
REGION = "us-west-2"

agents_for_bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)

def split_answer_and_thinking(llm_output: str) -> dict:
    """
    LLMから生成された出力内容が<thinking></thinking>タグと<answer></answer>タグで囲まれているのでそれぞれ分離する。
    """
    result = {"answer": "", "thinking": ""}
    # <thinking></thinking>タグの内容を抽出する
    # re.DOTALLは、ワイルドカードである.(DOT)に対して改行を含めるオプション
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', llm_output, re.DOTALL)

    if thinking_match:
        result["thinking"] = thinking_match.group(1).strip() # .strip()は文字列の先頭と末尾の空白文字を削除

    # answerタグの内容を抽出する
    answer_match = re.search(r'<answer>(.*?)</answer>', llm_output, re.DOTALL)
    if answer_match:
        result["answer"] = answer_match.group(1).strip()

    return result

def main():
    # Streamlitアプリケーション
    st.title("Bedrock Chat App")
    st.sidebar.title("LLM の出力した思考過程")
    thinking_display = st.sidebar.empty()
    st.sidebar.title("検索結果")
    content_display = st.sidebar.empty()

    # セッション状態の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # チャット履歴の表示
    for message in st.session_state.messages: # messagesにチャット履歴が保存されているので、それを表示している
        with st.chat_message(message["role"]): # message["role"]で話者を指定 "user" or "assistant"
            st.markdown(message["content"])

    # ユーザー入力
    if question := st.chat_input("あなたの質問を入力してください"):
        # ユーザーの質問をセッションに保存
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        
        # RAGを呼び出して回答を取得
        response, context = call_rag(
            question,
            KNOWLEDGE_BASE_ID,
            agents_for_bedrock_runtime,
            bedrock_runtime,
            MODEL_ID
        )
        splitted_output = split_answer_and_thinking(response)

        # サイドバーに LLM の思考過程を表示
        with thinking_display.container():
            st.markdown(splitted_output["thinking"])
        # サイドバーに検索結果を表示
        with content_display.container():
            st.json(context)
        
        # 応答の表示
        st.session_state.messages.append({"role": "assistant", "content": splitted_output["answer"]})
        with st.chat_message("assistant"):
            st.markdown(splitted_output["answer"])
    
if __name__ == "__main__":
    main()





