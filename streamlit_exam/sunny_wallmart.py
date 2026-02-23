import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="Walmart Strategic Dashboard", layout="wide")

# --- 2. 데이터 준비 ---
@st.cache_data
def get_data():
    # 성별/연령별 기본 데이터
    male = pd.DataFrame({
        'Age': ['0-17', '18-25', '26-35', '36-45', '46-50', '51-55', '55+'],
        'visit_count': [10019, 75032, 168835, 82843, 32502, 28607, 16421],
        'total_purchase': [92527205, 708372833, 1588794345, 783130921, 304136539, 277633647, 154984610],
        'avg_purchase': [9235.17, 9440.94, 9410.33, 9453.19, 9357.47, 9705.09, 9438.19],
        'Gender': 'Male'
    })
    female = pd.DataFrame({
        'Age': ['0-17', '18-25', '26-35', '36-45', '46-50', '51-55', '55+'],
        'visit_count': [5083, 24628, 50752, 27170, 13199, 9894, 5083],
        'total_purchase': [42385978, 205475842, 442976233, 243438963, 116706864, 89465997, 45782765],
        'avg_purchase': [8338.77, 8343.18, 8728.25, 8959.84, 8842.09, 9042.44, 9007.03],
        'Gender': 'Female'
    })
    
    # 도시별/결혼여부별 추가 데이터
    city_df = pd.DataFrame({
        'City': ['A', 'B', 'C', 'A', 'B', 'C'],
        'Gender': ['Male', 'Male', 'Male', 'Female', 'Female', 'Female'],
        'Purchase': [1200000000, 1500000000, 900000000, 400000000, 500000000, 300000000]
    })
    marital_df = pd.DataFrame({
        'Status': ['미혼', '기혼', '미혼', '기혼'],
        'Gender': ['Male', 'Male', 'Female', 'Female'],
        'Avg_Purchase': [9210, 9580, 8350, 8820]
    })
    
    return pd.concat([male, female]).reset_index(drop=True), city_df, marital_df

df, city_df, marital_df = get_data()

# --- 3. 상단 탭 정의 ---
tabs = st.tabs(["🏠 요약", "📂 데이터 정보", "⚙️ 분석 프로세스", "📊 상세 결과"])

# --- Tab 1: 요약 ---
with tabs[0]:
    st.markdown("""
        <div style="background-color: #1e2124; height: 100px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 25px;">
            <h1 style="color: #ffffff; margin: 0; font-family: 'Arial'; font-size: 26px;">📊 WALMART STRATEGIC INSIGHTS</h1>
        </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 매출액", "$3.32B", "Target High")
    m2.metric("총 방문 횟수", "582,519회")
    m3.metric("남성 매출 비중", "76.4%", "핵심군")
    m4.metric("주력 소비 연령", "26-35세", "Primary")

    st.divider()

    col_viz, col_txt = st.columns([1, 1.2])
    
    with col_viz:
        fig_pie, ax_pie = plt.subplots(figsize=(5, 5))
        colors = ['#0071ce', '#e83e8c']
        ax_pie.pie([76.4, 23.6], labels=['Male', 'Female'], autopct='%1.1f%%', 
                   startangle=90, colors=colors, pctdistance=0.85, textprops={'fontsize': 12})
        centre_circle = plt.Circle((0,0), 0.70, fc='white')
        fig_pie.gca().add_artist(centre_circle)
        st.pyplot(fig_pie)
        st.markdown("<p style='text-align: center; color: gray;'>[성별 매출 기여도 비중]</p>", unsafe_allow_html=True)

    with col_txt:
        st.markdown("### 🎯 핵심 고객 페르소나")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border: 1px solid #dee2e6;">
            <span style="background-color: #0071ce; color: white; padding: 5px 15px; border-radius: 20px; font-size: 13px; font-weight: bold;">BEST SEGMENT</span>
            <h3 style="margin-top: 15px; color: #333;">26-35세 남성 (City B 거주)</h3>
            <p style="color: #555; font-size: 1.05em; line-height: 1.6;">
                이 그룹은 전체 매출의 <b>40% 이상</b>을 차지하는 핵심 타겟입니다. 
                특히 블랙 프라이데이 기간 중 가전제품 및 IT 기기에 대해 압도적인 구매 화력을 보유하고 있습니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("##### 🚀 마케팅 액션플랜")
        st.info("👨 **남성**: 고단가 가전 번들 및 VIP 전용 리워드 강화")
        st.success("👩 **여성**: 패션/리빙 타임세일을 통한 방문 빈도 유도")

# --- Tab 2: 데이터 정보 ---
with tabs[1]:
    st.header("📂 데이터 설명: 특성 및 구조")
    with st.container(border=True):
        st.subheader("📍 데이터 출처")
        st.write("- **Kaggle Black Friday Sales**: 비식별화된 소비자 구매 패턴 데이터")
    with st.container(border=True):
        st.subheader("📋 주요 항목")
        st.write("- **수치**: Purchase (구매금액)")
        st.write("- **범주**: User_ID, Gender, Age, City_Category, Marital_Status, Product_Category")

# --- Tab 3: 분석 프로세스 ---
with tabs[2]:
    st.header("⚙️ 분석 프로세스")
    step_colors = ["#E3F2FD", "#BBDEFB", "#90CAF9", "#64B5F6", "#42A5F5", "#2196F3", "#1565C0"]
    steps = [
        ("01", "데이터 정제", "범주형 라벨링 작업"),
        ("02", "지표 계산", "방문수 및 구매액 집계"),
        ("03", "데이터 분리", "남성/여성 그룹 분리 분석"),
        ("04", "지역 분석", "도시 등급별 매출 기여 확인"),
        ("05", "라이프스타일", "결혼 여부별 객단가 분석"),
        ("06", "패턴 도출", "핵심 타겟(26-35남성) 확정"),
        ("07", "전략 수립", "데이터 기반 실행 방안 제언")
    ]
    for i, (num, title, desc) in enumerate(steps):
        text_c = "#333" if i < 3 else "white"
        st.markdown(f"""
            <div style="background-color: {step_colors[i]}; color: {text_c}; padding: 15px; border-radius: 50px 15px 15px 50px; display: flex; align-items: center; margin-bottom: 10px;">
                <div style="background-color: white; color: #333; border-radius: 50%; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; margin-right: 20px; font-weight: bold;">{num}</div>
                <div><b>{title}</b>: {desc}</div>
            </div>
        """, unsafe_allow_html=True)
        if i < 6: st.markdown("<div style='text-align:center; color:#ccc; margin-top:-5px;'>↓</div>", unsafe_allow_html=True)

# --- Tab 4: 상세 결과 ---
with tabs[3]:
    st.header("📊 데이터 상세 결과")
    sns.set_theme(style="whitegrid")
    
    # 1. 연령대별 평균 및 총 구매액
    st.subheader("1. 연령대별 평균 및 총 구매액")
    c1, c2 = st.columns(2)
    with c1:
        fig1, ax1 = plt.subplots()
        sns.barplot(data=df, x='Age', y='avg_purchase', hue='Gender', ax=ax1)
        ax1.set_title("Average Purchase by Age")
        st.pyplot(fig1)
    with c2:
        fig2, ax2 = plt.subplots()
        sns.barplot(data=df, x='Age', y='total_purchase', hue='Gender', ax=ax2)
        ax2.set_title("Total Purchase by Age")
        st.pyplot(fig2)

    # 2. 도시 등급 및 성별 매출 규모
    st.subheader("2. 도시 등급 및 성별 매출 규모")
    fig3, ax3 = plt.subplots(figsize=(12, 4))
    sns.barplot(data=city_df, x='City', y='Purchase', hue='Gender', palette='muted', ax=ax3)
    st.pyplot(fig3)

    # 3. 결혼 여부에 따른 성별 객단가 차이
    st.subheader("3. 결혼 여부에 따른 성별 객단가 차이")
    fig4, ax4 = plt.subplots(figsize=(12, 4))
    sns.barplot(data=marital_df, x='Status', y='Avg_Purchase', hue='Gender', palette='coolwarm', ax=ax4)
    st.pyplot(fig4)

    # 4. [추가] 방문 횟수 대비 평균 구매액 산점도
    st.subheader("4. 방문 횟수 대비 평균 구매액 상관관계")
    fig5, ax5 = plt.subplots(figsize=(12, 5))
    # 원의 크기를 총 구매액에 비례하게 설정하여 시각적 효과 부여
    sns.scatterplot(
        data=df, 
        x='visit_count', 
        y='avg_purchase', 
        hue='Gender', 
        size='total_purchase', 
        sizes=(100, 1000), 
        alpha=0.7, 
        palette=['#0071ce', '#e83e8c'],
        ax=ax5
    )
    ax5.set_title("Correlation: Visit Count vs Avg Purchase")
    ax5.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.) # 범례 위치 조정
    st.pyplot(fig5)
    st.caption("※ 버블의 크기가 클수록 해당 그룹의 총 매출 기여도가 높음을 의미합니다.")