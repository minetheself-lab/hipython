import streamlit as st
import pandas as pd

st.set_page_config(page_title="공장 전력 피크 관리 시스템", layout="wide")

# -----------------------------------
# 기본 데이터 생성
# -----------------------------------
time = pd.date_range("2021-08-01 00:00:00", periods=24, freq="H")

predicted_power = [
    700, 720, 730, 750, 780, 820,
    850, 880, 920, 950, 970, 990,
    1010, 1040, 1020, 980, 950, 930,
    900, 880, 860, 830, 800, 760
]

df = pd.DataFrame({
    "datetime": time,
    "predicted_power": predicted_power
})

df["hour"] = df["datetime"].dt.hour
df["date"] = df["datetime"].dt.date

# -----------------------------------
# 사이드바 메뉴
# -----------------------------------
st.sidebar.title("메뉴")
menu = st.sidebar.radio(
    "이동할 화면을 선택하세요",
    ["전력 예측", "피크 경보", "DR 경제성"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("공통 설정")

threshold = st.sidebar.slider("피크 기준 전력(kW)", 800, 1200, 1000, 10)

reduction_ratio = st.sidebar.slider("감축 비율", 0.00, 0.30, 0.10, 0.01)
dr_price = st.sidebar.number_input("DR 단가(원/kWh)", min_value=0, value=120, step=10)
production_loss = st.sidebar.number_input("생산 손실 비용(원)", min_value=0, value=5000, step=1000)

# -----------------------------------
# 함수 정의
# -----------------------------------
def get_alert_level(power, threshold):
    ratio = power / threshold

    if ratio < 0.80:
        return "정상"
    elif ratio < 0.90:
        return "관심"
    elif ratio < 0.95:
        return "주의"
    elif ratio < 1.00:
        return "경계"
    else:
        return "심각"

def calculate_dr(row, reduction_ratio, dr_price, production_loss):
    power = row["predicted_power"]
    reduction = power * reduction_ratio

    # 예시용 시간대 요금
    if 0 <= row["hour"] < 9:
        tou_rate = 70
    elif 9 <= row["hour"] < 18:
        tou_rate = 110
    else:
        tou_rate = 150

    saving = reduction * tou_rate
    reward = reduction * dr_price
    profit = saving + reward - production_loss

    return pd.Series({
        "reduction": reduction,
        "tou_rate": tou_rate,
        "saving": saving,
        "reward": reward,
        "expected_profit": profit
    })

df["alert_level"] = df["predicted_power"].apply(lambda x: get_alert_level(x, threshold))

dr_result = df.apply(
    lambda row: calculate_dr(row, reduction_ratio, dr_price, production_loss),
    axis=1
)

df = pd.concat([df, dr_result], axis=1)

def recommend_dr(row):
    if row["alert_level"] in ["경계", "심각"] and row["expected_profit"] > 0:
        return "참여 추천"
    elif row["alert_level"] == "주의" and row["expected_profit"] > 0:
        return "참여 검토"
    else:
        return "비참여"

df["dr_recommendation"] = df.apply(recommend_dr, axis=1)

# -----------------------------------
# 공통 지표
# -----------------------------------
max_power = df["predicted_power"].max()
avg_power = df["predicted_power"].mean()
peak_time = df.loc[df["predicted_power"].idxmax(), "datetime"]
total_profit = df["expected_profit"].sum()

# -----------------------------------
# 1. 전력 예측 메뉴
# -----------------------------------
if menu == "전력 예측":
    st.title("전력 예측")

    col1, col2, col3 = st.columns(3)
    col1.metric("최대 예측 전력", f"{max_power:,.1f} kW")
    col2.metric("평균 예측 전력", f"{avg_power:,.1f} kW")
    col3.metric("피크 시간", str(peak_time))

    st.subheader("시간대별 예측 전력")
    st.line_chart(df.set_index("datetime")["predicted_power"])

    st.subheader("원본 데이터")
    show_count = st.slider("표시할 행 개수", 5, 24, 10)
    st.dataframe(df.head(show_count))

# -----------------------------------
# 2. 피크 경보 메뉴
# -----------------------------------
elif menu == "피크 경보":
    st.title("피크 경보")

    highest_order = {"정상": 0, "관심": 1, "주의": 2, "경계": 3, "심각": 4}
    current_max_alert = max(df["alert_level"], key=lambda x: highest_order[x])

    if current_max_alert == "심각":
        st.error("심각 : 기준 전력을 초과했습니다. 즉시 대응이 필요합니다.")
    elif current_max_alert == "경계":
        st.warning("경계 : 피크 직전 상태입니다. DR 참여를 검토하세요.")
    elif current_max_alert == "주의":
        st.warning("주의 : 전력 사용량이 빠르게 증가하고 있습니다.")
    elif current_max_alert == "관심":
        st.info("관심 : 전력 사용량을 모니터링하세요.")
    else:
        st.success("정상 : 현재 상태는 안정적입니다.")

    st.subheader("경보 단계 분포")
    alert_counts = df["alert_level"].value_counts().reindex(
        ["정상", "관심", "주의", "경계", "심각"], fill_value=0
    )
    st.bar_chart(alert_counts)

    st.subheader("경보 단계별 필터")
    selected_levels = st.multiselect(
        "보고 싶은 경보 단계를 선택하세요",
        ["정상", "관심", "주의", "경계", "심각"],
        default=["주의", "경계", "심각"]
    )

    filtered_alert = df[df["alert_level"].isin(selected_levels)]
    st.dataframe(filtered_alert[["datetime", "predicted_power", "alert_level"]])

# -----------------------------------
# 3. DR 경제성 메뉴
# -----------------------------------
elif menu == "DR 경제성":
    st.title("DR 경제성")

    col1, col2, col3 = st.columns(3)
    col1.metric("총 예상 절감액", f"{df['saving'].sum():,.0f} 원")
    col2.metric("총 DR 보상", f"{df['reward'].sum():,.0f} 원")
    col3.metric("총 예상 순이익", f"{total_profit:,.0f} 원")

    if total_profit > 0:
        st.success("경제성 판단 : DR 참여가 유리합니다.")
    else:
        st.error("경제성 판단 : DR 참여가 불리합니다.")

    st.subheader("시간대별 순이익")
    st.line_chart(df.set_index("datetime")["expected_profit"])

    st.subheader("DR 참여 추천 결과")
    rec_counts = df["dr_recommendation"].value_counts()
    st.bar_chart(rec_counts)

    selected_rec = st.selectbox(
        "추천 결과로 필터링",
        ["전체", "참여 추천", "참여 검토", "비참여"]
    )

    if selected_rec == "전체":
        result_df = df
    else:
        result_df = df[df["dr_recommendation"] == selected_rec]

    st.dataframe(
        result_df[
            [
                "datetime",
                "predicted_power",
                "alert_level",
                "saving",
                "reward",
                "expected_profit",
                "dr_recommendation"
            ]
        ]
    )