import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv(override=True)


async def run():
    async with AsyncExitStack() as stack:
        # 1. MCP Server 연결 (mcp_server.py를 subprocess로 자동 기동)
        params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
        read, write = await stack.enter_async_context(
            stdio_client(params)
        )
        session = await stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()

        # 2. Tool 목록 확인 (디버깅용)
        tools = await load_mcp_tools(session)
        print(f"로드된 Tool: {[t.name for t in tools]}")

        # 3. LLM 준비
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 4. Agent 생성
        agent = create_react_agent(llm, tools)

        # 5. 실행 (순서 명시)
        user_question = """
        다음 순서로 작업해줘.
        1. read_experiment_result 툴로 'train_result.json'을 읽어줘.
        2. 읽은 내용에서 모델명, epoch, global_step, learning_rate, loss, total_floss를 한국어로 요약해줘.
        3. upload_experiment_to_notion 툴을 호출해줘.
           - title: '202604 기준 모델 실험 테스트다시 - step 500'
           - summary: 2번에서 만든 요약 내용
        """
        result = await agent.ainvoke({
            "messages": [("human", user_question)]
        })
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(run())

