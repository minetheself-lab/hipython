import streamlit as st

st.title('안녕하세요')

# 브라우저에 텍스트만 출력
st.write('Hello streamlit!!')

st.divider()

# 사용자 입력을 받는 박스, 입력후 엔터를 치면 브라우저에 출력되는 기능
name=st.text_input('이름: ')

st.write(name)

import pandas as pd
df=pd.read_csv('./data/pew.csv')
#log출력
print(df.info())

st.write(df.head())

#버튼추가
def btn1_click():
  st.write('클릭이 재미있군요!!!')

st.write('')  
btn1=st.button('눌러주세요.')
if btn1 :
  btn1_click()

