import streamlit as st
import pandas as pd
import numpy as np

# 1. 기본 설정 및 페이지 제목
st.set_page_config(page_title="나의 첫 대시보드", layout="wide")

# 사이드바 - 컨트롤 센터
st.sidebar.title("🎮 컨트롤 센터")
menu = st.sidebar.radio(
    "메뉴를 선택하세요",
    ["메인페이지", "분석보고서", "설정"]
)

# 샘플 데이터 생성 (데이터탭과 차트에서 사용)
chart_data = pd.DataFrame(
    np.random.randint(10, 100, size=(10, 2)),
    columns=['방문자수', '활성사용자']
)

# --- 메인페이지 ---
if menu == "메인페이지":
    st.title("🏠 메인 대시보드")
    
    # 이미지 넣기 (샘플 이미지 URL 사용)
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80", 
             caption="데이터 분석 현황", use_container_width=True)
    
    st.divider() # 구분선
    
    # 2개의 컬럼으로 KPI 메트릭 구성
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="총 방문자수", value="1,250명", delta="12%")
        
    with col2:
        st.metric(label="활성 사용자수", value="890명", delta="-5%")

# --- 분석보고서 페이지 ---
elif menu == "분석보고서":
    st.title("📊 데이터 분석 보고서")
    
    # 탭 구성 (차트, 데이터, 설정)
    tab1, tab2, tab3 = st.tabs(["📈 차트", "🗃️ 데이터", "⚙️ 설정"])
    
    with tab1:
        st.subheader("사용자 방문 현황 그래프")
        st.line_chart(chart_data)
        st.caption("최근 10일간의 데이터를 기반으로 한 꺾은선 그래프입니다.")
        
    with tab2:
        st.subheader("상세 데이터 테이블")
        st.dataframe(chart_data, use_container_width=True)
        
    with tab3:
        st.subheader("분석 옵션 설정")
        st.checkbox("실시간 데이터 업데이트 연결")
        st.checkbox("자동 리포트 생성 활성화")
        st.checkbox("관리자 알림 설정")

# --- 설정 페이지 ---
elif menu == "설정":
    st.title("⚙️ 시스템 설정")
    st.write("대시보드의 기본 환경을 설정하는 페이지입니다.")
    
    user_name = st.text_input("사용자 이름을 입력하세요", "관리자")
    st.success(f"현재 접속자: {user_name}")
  
