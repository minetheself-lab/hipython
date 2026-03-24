import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 0. 외부 파일에서 함수 불러오기
try:
    from power_db_operations import get_weather_info, get_daily_result, get_prediction_variables
    # from predictor import predict
except ImportError:
    print("Custom Function Import Error!!!")
    
    # 테스트용 가상 함수 (DB 연동 시 자동 대체됨)
    # def get_weather_info():
    #     now = datetime.now()
    #     return {'date': now.strftime('%Y-%m-%d'), 'hour': now.hour, 'temperature': 11.4, 'status': '맑음', 'humidity': 49, 'windspeed': 2.6, 'rainfall': 0}
    # def get_daily_peak(d): return pd.DataFrame() 
    # def predict_daily_peak(d): return pd.DataFrame()

# 1. 전체 구조 설정
st.set_page_config(page_title="순간최대전력 관리 시스템", layout="wide")

# --- 데이터 변환 유틸리티 ---
def transform_to_timeseries(df, target_date):
    if df is None or df.empty: return pd.DataFrame()
    df = df[df['date'].astype(str) == str(target_date)].copy()
    if df.empty: return pd.DataFrame()

    rows = []
    for _, row in df.iterrows():
        base_dt = pd.to_datetime(f"{row['date']} {int(row['hour'])}:00:00")
        for m, col in zip([7.5, 22.5, 37.5, 52.5], ['peak_15', 'peak_30', 'peak_45', 'peak_60']):
            rows.append({
                'mid_time': base_dt + timedelta(minutes=m),
                'val': row[col],
                'interval': f"{int(row['hour']):02d}:{int(m-7.5):02d} - {int(row['hour']):02d}:{int(m+7.5):02d}"
            })
    res = pd.DataFrame(rows)
    res['color'] = res['mid_time'].dt.hour.apply(lambda x: 'rgba(31, 119, 180, 0.85)' if x % 2 == 0 else 'rgba(100, 149, 237, 0.7)')
    return res

# --- 세션 상태 초기화 ---
if 'contract_power' not in st.session_state:
    st.session_state.contract_power = 200

# --- 사이드바 ---
with st.sidebar:
    st.header("📌 메뉴")
    menu = st.radio("이동할 페이지 선택", ["대시보드", "분석내용"])

st.title("⚡ 순간최대전력 관리")
st.divider()

if menu == "대시보드":
    # 2.1 & 2.2 상단 영역
    top_col1, top_col2 = st.columns(2)
    with top_col1:
        w_h1, w_h2 = st.columns([4, 1])
        w_h1.subheader("📍 현재 날씨")
        if w_h2.button("🔄 날씨 갱신"): st.rerun()
        w = get_weather_info()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("상태", f"☀️ {w['status']}"); c2.metric("온도", f"{w['temperature']}°C")
        c3.metric("습도", f"{int(w['humidity'])}%"); c4.metric("풍속", f"{w['windspeed']}m/s")
        c5.metric("강수", f"{w['rainfall']}mm")
        st.caption(f"🏠 울산 울주군 삼동면 암리 | {w['date']} {w['hour']}:00 기준")

    with top_col2:
        st.subheader("📋 기준 정보")
        with st.container(border=True):
            st.write(f"**현재 계약전력:** {st.session_state.contract_power} kWh")
            e1, e2 = st.columns([3, 1])
            new_val = e1.number_input("변경", value=st.session_state.contract_power, label_visibility="collapsed")
            if e2.button("수정 적용"):
                st.session_state.contract_power = new_val
                st.rerun()

    st.divider()

    # 2.3 그래프 영역 레이아웃 수정
    st.subheader("📈 순간최대전력 예측/실제")
    
    # 일자 선택 및 조회 버튼 (한 줄 배치)
    search_col1, search_col2, search_col3 = st.columns([2, 2, 5])
    with search_col1:
        target_date = st.date_input("조회 일자 선택", datetime.now().date())
    with search_col2:
        st.write(" ") # 수직 정렬용 공백
        st.write(" ")
        btn_search = st.button("📊 최대전력량 예측/결과", use_container_width=True)

    # 데이터 호출 (버튼 클릭 시 또는 페이지 로드 시)
    # df_res_raw = get_daily_peak(target_date)
    target_dtstr = target_date.strftime('%Y-%m-%d')
    df_res_raw = get_daily_result(target_dtstr)
    # df_pre_raw = predict(get_prediction_variables(target_dtstr))
    
    # df_pre_raw = predict_daily_peak(target_dtstr)
    
    df_actual = transform_to_timeseries(df_res_raw, target_date)
    # df_predict = transform_to_timeseries(df_pre_raw, target_date)
    df_predict = pd.DataFrame() 

    fig = go.Figure()

    # 파란색 피크 데이터 (실제)
    if not df_actual.empty:
        fig.add_trace(go.Bar(
            x=df_actual['mid_time'], y=df_actual['val'],
            customdata=df_actual['interval'], name='실제 피크값',
            marker_color=df_actual['color'], width=15*60*1000, offset=0,
            hovertemplate='<b>구간: %{customdata}</b><br>실제: %{y:.1f}kWh<extra></extra>'
        ))

    # 빨간색 예측치 데이터
    if not df_predict.empty:
        fig.add_trace(go.Scatter(
            x=df_predict['mid_time'], y=df_predict['val'],
            customdata=df_predict['interval'], name='예상 피크값',
            mode='lines+markers', line=dict(color='#d62728', width=1.5, dash='dot'),
            marker=dict(size=6, symbol='circle'),
            hovertemplate='<b>구간: %{customdata}</b><br>예측: %{y:.1f}kWh<extra></extra>'
        ))

    # 계약전력 가로 실선
    fig.add_hline(y=st.session_state.contract_power, line_dash="solid", line_color="#d62728", line_width=2,
                  annotation_text=f"계약전력 ({st.session_state.contract_power}kW)", annotation_position="top left")

    fig.update_layout(
        hovermode="x unified", height=550, template="plotly_white", bargap=0,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(title="시간", tickformat="%H시", dtick=3600000, 
                   range=[pd.to_datetime(target_date), pd.to_datetime(target_date) + timedelta(days=1)]),
        yaxis=dict(title="전력량 (kWh)", range=[0, st.session_state.contract_power * 1.1], dtick=20)
    )

    if df_actual.empty and df_predict.empty:
        st.info("조회된 데이터가 없습니다. 날짜를 선택 후 버튼을 클릭하세요.")
    else:
        st.plotly_chart(fig, use_container_width=True)

elif menu == "분석내용":
    st.info("데이터 분석 결과 페이지입니다.")
