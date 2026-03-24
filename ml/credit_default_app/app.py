import streamlit as st
import pandas as pd
from predict import DefaultPredictor  # 작성하신 predict.py의 클래스 임포트

# 1. 페이지 레이아웃 및 제목
st.set_page_config(page_title="Credit Default Predictor", layout="wide")

st.title("💳 신용카드 채무불이행 예측 AI 서비스")
st.markdown("""
이 대시보드는 고객의 금융 거래 이력과 인구통계학적 정보를 분석하여 **다음 달 채무불이행 가능성**을 예측합니다.
""")
st.divider()

# 2. 추론기(Predictor) 인스턴스 생성 (캐싱하여 속도 최적화)
@st.cache_resource
def get_predictor():
    return DefaultPredictor()

predictor = get_predictor()

# 3. 사용자 입력 섹션
with st.sidebar:
    st.header("👤 고객 기본 정보")
    limit_bal = st.number_input("한도 금액 (LIMIT_BAL)", min_value=0, value=50000, step=1000)
    age = st.slider("나이", 20, 80, 30)
    sex = st.selectbox("성별", options=[1, 2], format_func=lambda x: "남성" if x == 1 else "여성")
    edu = st.selectbox("학력", options=[1, 2, 3, 4], format_func=lambda x: {1:"대학원", 2:"대학교", 3:"고등학교", 4:"기타"}[x])
    marriage = st.selectbox("결혼 상태", options=[1, 2, 3], format_func=lambda x: {1:"기혼", 2:"미혼", 3:"기타"}[x])

st.subheader("📊 거래 및 상환 이력 분석")
col1, col2 = st.columns(2)

with col1:
    st.info("최근 3개월 상환 상태 (-1: 정기, 1: 1개월 연체...)")
    pay_0 = st.number_input("9월 상환상태 (PAY_0)", -2, 8, 0)
    pay_2 = st.number_input("8월 상환상태 (PAY_2)", -2, 8, 0)
    pay_3 = st.number_input("7월 상환상태 (PAY_3)", -2, 8, 0)

with col2:
    st.info("최근 9월 청구액 및 납부액 (NT$)")
    bill_1 = st.number_input("9월 빌링 금액 (BILL_AMT1)", value=1000)
    pay_1 = st.number_input("9월 납부 금액 (PAY_AMT1)", value=1000)

# 4. 분석 실행 및 결과 출력
st.divider()
if st.button("AI 분석 시작", use_container_width=True):
    # 23개 컬럼 전체 데이터 구성 (predict.py가 요구하는 형식)
    # 입력받지 않은 나머지 변수들은 기본값(0)으로 채워 데이터프레임 생성
    input_data = {
        'LIMIT_BAL': limit_bal, 'SEX': sex, 'EDUCATION': edu, 'MARRIAGE': marriage, 'AGE': age,
        'PAY_0': pay_0, 'PAY_2': pay_2, 'PAY_3': pay_3, 'PAY_4': 0, 'PAY_5': 0, 'PAY_6': 0,
        'BILL_AMT1': bill_1, 'BILL_AMT2': 0, 'BILL_AMT3': 0, 'BILL_AMT4': 0, 'BILL_AMT5': 0, 'BILL_AMT6': 0,
        'PAY_AMT1': pay_1, 'PAY_AMT2': 0, 'PAY_AMT3': 0, 'PAY_AMT4': 0, 'PAY_AMT5': 0, 'PAY_AMT6': 0
    }
    
    with st.spinner('AI 모델이 데이터를 분석 중입니다...'):
        try:
            # predict.py의 Predictor 호출
            result = predictor.predict(input_data)
            
            # 결과 레이아웃 구성
            res_col1, res_col2 = st.columns([1, 1])
            
            with res_col1:
                st.subheader("📌 예측 결과")
                if result['is_default'] == 1:
                    st.error(f"### 고위험군: 채무불이행 가능성 높음")
                else:
                    st.success(f"### 저위험군: 정상 상환 가능성 높음")
                
                st.write(f"**신뢰도:** {max(result['probability_normal'], result['probability_default']):.2%}")

            with res_col2:
                st.subheader("📈 확률 분포")
                # 간단한 막대 그래프 시각화
                prob_df = pd.DataFrame({
                    '상태': ['정상', '연체 위험'],
                    '확률': [result['probability_normal'], result['probability_default']]
                })
                st.bar_chart(prob_df.set_index('상태'))

        except Exception as e:
            st.error(f"예측 도중 에러가 발생했습니다: {e}")

# 푸터 (Footer)
st.markdown("---")
st.caption("© 2026 Credit Risk Management AI. Samjong KPMG AX Consultant Course Project.")