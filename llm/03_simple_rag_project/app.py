import streamlit as st
from dotenv import load_dotenv
import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# API 키 로드
load_dotenv(override=True)

# -----------------------------------------------
# RAG 체인 로드 함수
# -----------------------------------------------
@st.cache_resource # 리소스를 캐싱하여 앱 재실행 시마다 다시 로드하지 않음
def load_rag_chain(pdf_path: str, model_name: str = "gpt-4o-mini"):
    # 1. PDF 로딩
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # 2. 텍스트 분할
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.split_documents(pages)

    # 3. 임베딩 + 벡터 DB
    embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(docs, embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # 4. 프롬프트
    prompt = ChatPromptTemplate.from_template("""
너는 삼성전자 메모리카드 매뉴얼 전문 어시스턴트이다.
다음의 참고 문서를 바탕으로 질문에 정확하게 답하라.

[참고문서]
{context}

[질문]
{question}

한글로 간결하고 정확하게 답변하라.
""")

    # 5. LLM 설정
    llm = ChatOpenAI(model=model_name, temperature=0)

    # 6. RAG 체인 구성
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

# -----------------------------------------------
# 페이지 설정
# -----------------------------------------------
st.set_page_config(
    page_title="삼성 메모리카드 매뉴얼 챗봇",
    page_icon="📖",
    layout="centered"
)

st.title("삼성 메모리카드 매뉴얼 챗봇")
st.caption("매뉴얼 기반으로 정확한 답변을 제공합니다.")

# -----------------------------------------------
# RAG 체인 초기화 (최초 1회만 실행)
# -----------------------------------------------
if "rag_chain" not in st.session_state:
    # PDF 파일 경로가 올바른지 확인하세요.
    pdf_path = "data/Samsung_Card_Manual_Korean_1.3.pdf"
    with st.spinner("매뉴얼을 분석 중입니다... 잠시만 기다려 주세요."):
        st.session_state.rag_chain = load_rag_chain(pdf_path)

# -----------------------------------------------
# 대화 히스토리 초기화
# -----------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------
# 이전 대화 출력
# -----------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------------------------
# 사용자 입력 처리
# -----------------------------------------------
if prompt := st.chat_input("질문을 입력하세요."):
    # 사용자 메시지 출력 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성 및 출력
    with st.chat_message("assistant"):
        with st.spinner("답변을 생성하고 있습니다..."):
            response = st.session_state.rag_chain.invoke(prompt)
            st.markdown(response)
    
    # AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response})

