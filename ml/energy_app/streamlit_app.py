import streamlit as st

st.set_page_config(
    page_title="전력 피크 예측 · 자원 최적화",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background-color: #F4F6F9; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
[data-testid="stSidebar"] { background-color: #FFFFFF; }
.stButton > button { border-radius: 8px !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  피크 예측",
    "⚡  전력 조회",
    "⚙️  운영 최적화",
    "💰  DR 시뮬레이션",
    "🌿  ESG 리포트"
])

with tab1:
    from pages.tab1_dashboard    import render; render()
with tab2:
    from pages.tab2_power_query  import render; render()
with tab3:
    from pages.tab3_optimization import render; render()
with tab4:
    from pages.tab4_dr_sim       import render; render()
with tab5:
    from pages.tab5_esg          import render; render()