import streamlit as st
import pandas as pd
from predict import DefaultPredictor

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(page_title="Credit Default Predictor", layout="wide")

st.title("💳 신용카드 채무불이행 예측 AI 서비스")
st.markdown("""
이 대시보드는 고객의 금융 거래 이력과 인구통계학적 정보를 분석하여  
**다음 달 채무불이행 가능성**을 예측합니다.
""")
st.divider()


# --------------------------------------------------
# 2. 모델 로드
# --------------------------------------------------
@st.cache_resource
def get_predictor():
    return DefaultPredictor()

try:
    predictor = get_predictor()
except Exception as e:
    st.error(f"모델 로딩 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 3. 유효성 검사 함수
# --------------------------------------------------
def validate_inputs(limit_bal, age, sex, edu, marriage, pay_0, pay_2, pay_3, bill_1, pay_1):
    errors = []

    if limit_bal < 0:
        errors.append("한도 금액(LIMIT_BAL)은 0 이상이어야 합니다.")

    if not (20 <= age <= 80):
        errors.append("나이는 20세 이상 80세 이하만 가능합니다.")

    if sex not in [1, 2]:
        errors.append("성별 값이 올바르지 않습니다.")

    if edu not in [1, 2, 3, 4]:
        errors.append("학력 값이 올바르지 않습니다.")

    if marriage not in [1, 2, 3]:
        errors.append("결혼 상태 값이 올바르지 않습니다.")

    for col_name, value in {
        "PAY_0": pay_0,
        "PAY_2": pay_2,
        "PAY_3": pay_3
    }.items():
        if not (-2 <= value <= 8):
            errors.append(f"{col_name} 값은 -2 ~ 8 범위여야 합니다.")

    if bill_1 < 0:
        errors.append("9월 빌링 금액(BILL_AMT1)은 0 이상이어야 합니다.")

    if pay_1 < 0:
        errors.append("9월 납부 금액(PAY_AMT1)은 0 이상이어야 합니다.")

    # 간단한 논리 검증
    if limit_bal == 0 and bill_1 > 0:
        errors.append("한도 금액이 0인데 빌링 금액이 존재합니다. 입력값을 확인해주세요.")

    if bill_1 == 0 and pay_1 > 0:
        errors.append("빌링 금액이 0인데 납부 금액이 입력되었습니다. 입력값을 확인해주세요.")

    if bill_1 > 0 and pay_1 > bill_1 * 3:
        errors.append("납부 금액이 청구 금액 대비 비정상적으로 큽니다. 입력값을 확인해주세요.")

    return len(errors) == 0, errors


def validate_prediction_result(result):
    required_keys = ["is_default", "probability_normal", "probability_default"]

    for key in required_keys:
        if key not in result:
            return False, f"예측 결과에 '{key}' 값이 없습니다."

    pred = result["is_default"]
    p_normal = result["probability_normal"]
    p_default = result["probability_default"]

    if not (0 <= p_normal <= 1):
        return False, "정상 확률 값이 유효 범위를 벗어났습니다."

    if not (0 <= p_default <= 1):
        return False, "연체 확률 값이 유효 범위를 벗어났습니다."

    if abs((p_normal + p_default) - 1.0) > 0.01:
        return False, "정상 확률과 연체 확률의 합이 1이 아닙니다."

    if pred not in [0, 1]:
        return False, "예측 결과 값(is_default)이 올바르지 않습니다."

    return True, ""


def get_risk_grade(p_default):
    if p_default >= 0.7:
        return "위험", "🔴", "채무불이행 가능성이 매우 높습니다."
    elif p_default >= 0.5:
        return "경고", "🟠", "채무불이행 위험이 높아 주의가 필요합니다."
    elif p_default >= 0.3:
        return "주의", "🟡", "상환 패턴을 지속적으로 모니터링할 필요가 있습니다."
    else:
        return "안전", "🟢", "정상 상환 가능성이 높습니다."


def get_action_guide(grade):
    if grade == "위험":
        return "한도 조정, 추가 모니터링, 고객 상담 등 적극적인 리스크 관리가 필요합니다."
    elif grade == "경고":
        return "거래 추이를 모니터링하고 한도 축소 여부를 검토할 수 있습니다."
    elif grade == "주의":
        return "당분간 결제 패턴을 관찰하고 이상 징후 여부를 확인하는 것이 좋습니다."
    else:
        return "현재 상태는 비교적 안정적입니다."


# --------------------------------------------------
# 4. 사용자 입력
# --------------------------------------------------
with st.sidebar:
    st.header("👤 고객 기본 정보")
    limit_bal = st.number_input("한도 금액 (LIMIT_BAL)", min_value=0, value=50000, step=1000)
    age = st.slider("나이", 20, 80, 30)
    sex = st.selectbox("성별", options=[1, 2], format_func=lambda x: "남성" if x == 1 else "여성")
    edu = st.selectbox(
        "학력",
        options=[1, 2, 3, 4],
        format_func=lambda x: {1: "대학원", 2: "대학교", 3: "고등학교", 4: "기타"}[x]
    )
    marriage = st.selectbox(
        "결혼 상태",
        options=[1, 2, 3],
        format_func=lambda x: {1: "기혼", 2: "미혼", 3: "기타"}[x]
    )

st.subheader("📊 거래 및 상환 이력 분석")
col1, col2 = st.columns(2)

with col1:
    st.info("최근 3개월 상환 상태 (-1: 정상 납부, 1: 1개월 연체, 2: 2개월 연체 ...)")
    pay_0 = st.number_input("9월 상환상태 (PAY_0)", min_value=-2, max_value=8, value=0, step=1)
    pay_2 = st.number_input("8월 상환상태 (PAY_2)", min_value=-2, max_value=8, value=0, step=1)
    pay_3 = st.number_input("7월 상환상태 (PAY_3)", min_value=-2, max_value=8, value=0, step=1)

with col2:
    st.info("최근 9월 청구액 및 납부액 (NT$)")
    bill_1 = st.number_input("9월 빌링 금액 (BILL_AMT1)", min_value=0, value=1000, step=100)
    pay_1 = st.number_input("9월 납부 금액 (PAY_AMT1)", min_value=0, value=1000, step=100)


# --------------------------------------------------
# 5. 분석 실행
# --------------------------------------------------
st.divider()

if st.button("AI 분석 시작", use_container_width=True):
    # 5-1. 입력값 검증
    is_valid_input, input_errors = validate_inputs(
        limit_bal, age, sex, edu, marriage, pay_0, pay_2, pay_3, bill_1, pay_1
    )

    if not is_valid_input:
        st.error("입력값 검증에 실패했습니다. 아래 내용을 확인해주세요.")
        for err in input_errors:
            st.write(f"- {err}")
        st.stop()

    # 5-2. 모델 입력 데이터 구성
    input_data = {
        'LIMIT_BAL': limit_bal,
        'SEX': sex,
        'EDUCATION': edu,
        'MARRIAGE': marriage,
        'AGE': age,
        'PAY_0': pay_0,
        'PAY_2': pay_2,
        'PAY_3': pay_3,
        'PAY_4': 0,
        'PAY_5': 0,
        'PAY_6': 0,
        'BILL_AMT1': bill_1,
        'BILL_AMT2': 0,
        'BILL_AMT3': 0,
        'BILL_AMT4': 0,
        'BILL_AMT5': 0,
        'BILL_AMT6': 0,
        'PAY_AMT1': pay_1,
        'PAY_AMT2': 0,
        'PAY_AMT3': 0,
        'PAY_AMT4': 0,
        'PAY_AMT5': 0,
        'PAY_AMT6': 0
    }

    with st.spinner("AI 모델이 데이터를 분석 중입니다..."):
        try:
            # 5-3. 예측 수행
            result = predictor.predict(input_data)

            # 5-4. 예측값 범위 검사
            is_valid_result, result_error = validate_prediction_result(result)
            if not is_valid_result:
                st.error(f"AI 예측 결과가 유효 범위를 벗어났습니다. {result_error}")
                st.stop()

            # 5-5. 결과 해석
            p_normal = result["probability_normal"]
            p_default = result["probability_default"]
            pred = result["is_default"]

            grade, icon, grade_msg = get_risk_grade(p_default)
            action_guide = get_action_guide(grade)
            confidence = max(p_normal, p_default)

            # --------------------------------------------------
            # 6. 결과 출력
            # --------------------------------------------------
            st.success("분석이 완료되었습니다.")

            res_col1, res_col2 = st.columns(2)

            with res_col1:
                st.subheader("📌 예측 결과")

                if grade == "위험":
                    st.error(f"{icon} 위험 등급: {grade}")
                elif grade == "경고":
                    st.warning(f"{icon} 위험 등급: {grade}")
                elif grade == "주의":
                    st.info(f"{icon} 위험 등급: {grade}")
                else:
                    st.success(f"{icon} 위험 등급: {grade}")

                st.write(f"**예측 상태:** {'채무불이행 위험' if pred == 1 else '정상 상환 가능성 높음'}")
                st.write(f"**위험 등급 설명:** {grade_msg}")
                st.write(f"**연체 확률:** {p_default:.2%}")
                st.write(f"**정상 확률:** {p_normal:.2%}")
                st.write(f"**신뢰도:** {confidence:.2%}")
                st.write(f"**권장 조치:** {action_guide}")

            with res_col2:
                st.subheader("📈 확률 분포")
                prob_df = pd.DataFrame({
                    "상태": ["정상", "연체 위험"],
                    "확률": [p_normal, p_default]
                })
                st.bar_chart(prob_df.set_index("상태"))

            st.divider()
            st.subheader("🧾 입력 데이터 요약")
            summary_df = pd.DataFrame([{
                "한도 금액": limit_bal,
                "나이": age,
                "성별": "남성" if sex == 1 else "여성",
                "학력": {1: "대학원", 2: "대학교", 3: "고등학교", 4: "기타"}[edu],
                "결혼 상태": {1: "기혼", 2: "미혼", 3: "기타"}[marriage],
                "9월 상환상태": pay_0,
                "8월 상환상태": pay_2,
                "7월 상환상태": pay_3,
                "9월 빌링 금액": bill_1,
                "9월 납부 금액": pay_1
            }])
            st.dataframe(summary_df, use_container_width=True)

        except Exception as e:
            st.error(f"예측 도중 에러가 발생했습니다: {e}")


# --------------------------------------------------
# 7. 푸터
# --------------------------------------------------
st.markdown("---")
st.caption("© 2026 Credit Risk Management AI. Samjong KPMG AX Consultant Course Project.")