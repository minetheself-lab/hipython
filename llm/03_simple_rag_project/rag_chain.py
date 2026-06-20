
from dotenv import load_dotenv
import os

load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def load_rag_chain(pdf_path: str, model: str = "gpt-4o-mini"):
    # 1. PDF 로딩
    loader = PyPDFLoader("data/Samsung_Card_Manual_Korean_1.3.pdf")
    pages = loader.load()  # List[Document] 형태로 반환

    # 2. 텍스트 분할
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs=splitter.split_documents(pages)

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
    # 5. llm 설정
    llm=ChatOpenAI(model='gpt-4o-mini', temperature=0)
    
    # 5. RAG 체인
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain



# 1. 함수를 호출하여 리턴값(체인)을 변수에 저장해야 합니다.
pdf_file = "data/Samsung_Card_Manual_Korean_1.3.pdf"
rag_chain = load_rag_chain(pdf_file) # <--- 이 줄이 반드시 필요합니다!

# 2. 이제 생성된 체인을 사용하여 질문을 던집니다.
query = "이 유틸리티는 동시에 몇 개의 메모리카드나 UFD를 인식할 수 있나?"
answer = rag_chain.invoke(query)

print(answer)