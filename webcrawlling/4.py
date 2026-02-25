from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
  browser = p.chromium.launch(headless=False)
  page = browser.new_page()
  page.goto("http://quotes.toscrape.com/")
  html=page.content()
  soup=BeautifulSoup(html, 'lxml')
  #print(soup.find('span', class_='text').get_text())
  print(soup.select_one('span.text').text)
  print(soup.select_one('small.author').text)
  
  #selector="div.quote"
  #items=soup.select(selector)
  #print (items)
  
quotes=soup.select('div.quote')
quotes_list=[]

for quote in quotes:
  quotes_list.append({'quote':quote.select_one('span.text').text,
                     'author': quote.select_one('small.author').text
                     })
  print(quotes_list)
  #print(quote.select_one('span.text').text)
  #print(quote.select_one('small.author').text)
  #print('*'*20)

import pandas as pd
df=pd.DataFrame(quotes_list)
print(df.head())
 
 