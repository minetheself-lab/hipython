import streamlit as st
import random

# 페이지 설정
st.set_page_config(page_title="환경 상태 대시보드", layout="centered")

st.title("🌿 환경 상태 미니 대시보드")

# 예시 데이터 (실제로는 센서값 등으로 대체 가능)
current_temp = round(random.uniform(18, 30), 1)
previous_temp = 24.0

current_air = random.randint(30, 120)
previous_air = 80

# 변화량 계산
temp_delta = round(current_temp - previous_temp, 1)
air_delta = current_air - previous_air

# 컬럼 2개 생성
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🌡 현재 온도 (°C)",
        value=f"{current_temp} °C",
        delta=f"{temp_delta} °C"
    )

with col2:
    st.metric(
        label="🌫 공기질 지수 (AQI)",
        value=current_air,
        delta=air_delta
    )

st.markdown("---")
st.caption("※ 변화량이 증가하면 빨간색, 감소하면 파란색으로 자동 표시됩니다.")
  
  
  
  