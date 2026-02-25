from playwright.sync_api import sync_playwright

with sync_playwright() as p:
  browser = p.chromium.launch(headless=False)
  page = browser.new_page()
    
  page.goto("https://www.example.com/")
  print(page.title())
 
  page_html=page.content()
  print(page_html[:200])
  
  page.wait_for_timeout(10000)
  browser.close()
  
print('크롤링완료')
  