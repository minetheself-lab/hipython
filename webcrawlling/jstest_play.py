from playwright.sync_api import sync_playwright
import time  # 1. time 모듈 추가

def run_crawler():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("http://127.0.0.1:5500/webcrawlling/jstest.html")
        page.fill("#nameInput", "파이썬 크롤러")
        page.click("#submitBtn")
        
        result_text = page.inner_text("#resultName")
        print(f"화면에 출력된 이름 : {result_text}")
        
        # ⭐️ 추가된 부분: 결과 확인을 위해 5초간 브라우저 유지
        print("결과 확인을 위해 5초간 대기합니다...")
        time.sleep(5) 
        
        browser.close()

run_crawler()