from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client= OpenAI (api_key=os.getenv("OPENAI_API_KEY"))

res = client.responses.create (
    model = 'gpt-4o-mini',
    input= [
        {"role": "system", "content": "너는 마케팅 전문가야"},
        {"role": "user", "content":"it분야에 적절한 광고문구를 작성해"}
        
    ], 
    temperature=0
)
print(res.output_text)