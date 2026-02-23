import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 봄 테마 커스텀 CSS
st.set_page_config(page_title="봄맞이 대시보드", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF9FB; }
    [data-testid="stSidebar"] { background-color: #FFF0F5; }
    h1, h2, h3 { color: #FF69B4 !important; }
    .metric-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #FFD1DC;
        text-align: center;
        margin-bottom: 10px;
        min-height: 200px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 사이드바 구성
flower_html = """
<div style="display: flex; align-items: center;">
    <h1 style="margin-right: 10px; font-size: 25px;">봄이 왔어요</h1>
    <span style="font-size: 30px; animation: sway 2s infinite ease-in-out; display: inline-block;">🌸</span>
</div>
<style>
@keyframes sway { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(20deg); } }
</style>
"""
st.sidebar.markdown(flower_html, unsafe_allow_html=True)
st.sidebar.markdown("<p style='color: #666;'>welcome! 메뉴선택해주세요</p>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "메뉴 이동",
    ["봄요약", "봄날씨예보", "올봄 패션", "올봄 먹거리"]
)

# --- [메뉴 1: 봄요약 - 격자 대시보드] ---
if menu == "봄요약":
    st.title("🌸 봄요약 대시보드")
    st.image("https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=1200", use_container_width=True)
    
    st.write("### 🍀 한눈에 보는 봄 소식")
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1:
        st.markdown("<div class='metric-box'><h3>🌦️ 날씨변화</h3><p>기온 및 비 예보</p></div>", unsafe_allow_html=True)
        if st.button("날씨예보 이동 ➡️", key="go_w", use_container_width=True):
            st.info("왼쪽 사이드바에서 '봄날씨예보'를 클릭하세요!")
    with col2:
        st.markdown("<div class='metric-box'><h3>😷 미세먼지</h3><p>실시간 대기질 현황</p></div>", unsafe_allow_html=True)
        st.link_button("미세먼지 확인 🔗", "https://www.airkorea.or.kr", use_container_width=True)
    with col3:
        st.markdown("<div class='metric-box'><h3>👗 올봄 패션</h3><p>올해의 스타일링</p></div>", unsafe_allow_html=True)
        if st.button("패션정보 이동 ➡️", key="go_f", use_container_width=True):
            st.info("왼쪽 사이드바에서 '올봄 패션'을 클릭하세요!")
    with col4:
        st.markdown("<div class='metric-box'><h3>🍓 올봄 먹거리</h3><p>노량진 맛집 가이드</p></div>", unsafe_allow_html=True)
        if st.button("맛집지도 이동 ➡️", key="go_e", use_container_width=True):
            st.info("왼쪽 사이드바에서 '올봄 먹거리'를 클릭하세요!")

# --- [메뉴 2: 봄날씨예보 - 차트 구성] ---
elif menu == "봄날씨예보":
    st.title("☀️ 2월-5월 날씨 전망 (차트)")
    months = ['2월', '3월', '4월', '5월']
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    with c1:
        st.subheader("🌡️ 평균 기온 변화")
        fig1 = px.line(x=months, y=[2, 8, 14, 20], markers=True)
        fig1.update_traces(line_color='#FF69B4')
        st.plotly_chart(fig1, use_container_width=True)
        
    with c2:
        st.subheader("🌫️ 미세먼지 산점도")
        df_dust = pd.DataFrame({'날짜': range(30), '농도': np.random.randint(30, 150, 30)})
        fig2 = px.scatter(df_dust, x='날짜', y='농도', color='농도', color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)
        
    with c3:
        st.subheader("☔ 비 예보 확률 (%)")
        fig3 = px.bar(x=months, y=[15, 20, 45, 25])
        fig3.update_traces(marker_color='#87CEEB')
        st.plotly_chart(fig3, use_container_width=True)
        
    with c4:
        st.subheader("🥶 꽃샘추위 위험 지수")
        fig4 = go.Figure(go.Indicator(mode="gauge+number", value=75, gauge={'bar':{'color':'#FF4B4B'}}))
        fig4.update_layout(height=300)
        st.plotly_chart(fig4, use_container_width=True)

# --- [메뉴 3: 올봄 패션] ---
elif menu == "올봄 패션":
    st.title("👗 봄 스타일링 가이드")
    p1, p2 = st.columns(2)
    with p1:
        st.subheader("⏪ 2025 작년 스타일")
        st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500")
    with p2:
        st.subheader("⏩ 2026 올해 트렌드")
        st.image("https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=500")

# --- [메뉴 4: 올봄 먹거리 - 지도 및 링크] ---
elif menu == "올봄 먹거리":
    st.title("🍴 노량진역 맛집 지도")
    
    # 구글 검색 링크로 더 확실하게 연결
    food_data = [
        {"name": "노량진수산시장", "lat": 37.5149, "lon": 126.9386, "q": "노량진수산시장"},
        {"name": "노량진할머니파전", "lat": 37.5114, "lon": 126.9444, "q": "노량진+할머니파전"},
        {"name": "다독이네 숯불구이", "lat": 37.5129, "lon": 126.9377, "q": "다독이네+숯불구이"},
        {"name": "컵밥거리", "lat": 37.5135, "lon": 126.9456, "q": "노량진+컵밥거리"},
        {"name": "운봉산장", "lat": 37.5080, "lon": 126.9403, "q": "운봉산장"}
    ]
    df = pd.DataFrame(food_data)
    
    col_map, col_list = st.columns([2, 1])
    with col_map:
        st.map(df)
    with col_list:
        st.subheader("📝 맛집 목록")
        for item in food_data:
            # 클릭 시 구글 지도로 이동
            url = f"https://www.google.com/maps/search/{item['q']}"
            st.link_button(f"🍴 {item['name']}", url, use_container_width=True)