# from dotenv import load_dotenv
# import os

# load_dotenv()

# OPENAI_API_KEY    = os.environ['OPENAI_API_KEY']
# MIELI_SEARCH_KEY  = os.environ['MIELI_SEARCH_KEY']   # ← 추가

# print("API 키 로드 완료")
# print(f"OpenAI Key:      {OPENAI_API_KEY[:10]}...")
# print(f"MeiliSearch Key: {MIELI_SEARCH_KEY[:10]}...")


import meilisearch
client = meilisearch.Client('http://127.0.0.1:7700', 
      '4yfoYv8JwLILYozlGI_bUOnpWdqvZhybqCkkuzTJFs0')

def stock_search(query):
  return client.index('nasdaq').search(query)
