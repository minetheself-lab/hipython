from fastmcp import FastMCP
from dotenv import load_dotenv
from notion_client import Client
import json
import os

load_dotenv()

mcp = FastMCP("ExperimentResultServer")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
notion = Client(auth=NOTION_TOKEN)

@mcp.tool()
def read_experiment_result(file_path: str) -> str:
    """
    모델 학습 결과 JSON 파일을 읽어 문자열로 반환합니다.
    file_path: JSON 파일 경로 (예: train_result.json)
    """
    if not os.path.exists(file_path):
        return f"[ERROR] 파일을 찾을 수 없습니다: {file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"[ERROR] 파일 읽기 실패: {str(e)}"
      
@mcp.tool()
def upload_experiment_to_notion(title: str, summary: str) -> str:
    """
    요약된 실험 결과를 Notion 페이지로 업로드합니다.
    title: 페이지 제목
    summary: 본문에 기록할 요약 텍스트
    """
    if not NOTION_PAGE_ID:
        return "[ERROR] NOTION_PAGE_ID가 설정되지 않았습니다."
    try:
        response = notion.pages.create(
            parent={"page_id": NOTION_PAGE_ID},
            properties={
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": summary}}
                        ]
                    }
                }
            ]
        )
        page_url = response.get("url", "URL 없음")
        return f"Notion 업로드 완료: {page_url}"
    except Exception as e:
        return f"[ERROR] Notion 업로드 실패: {str(e)}"
      
if __name__ == "__main__":
    print("MCP Server 실행 중...")
    mcp.run(transport="stdio")