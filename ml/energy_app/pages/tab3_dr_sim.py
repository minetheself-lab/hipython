# ================================================================
# pages/tab3_dr_sim.py
# 역할 : DR 시뮬레이션 (Tab3) — DR_app.py 이식
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go

# ── 상수 ──────────────────────────────────────────────────────
EMISSION_FACTOR = 0.4781
CARBON_PRICE    = 10_000
BASIC_RATE      = 8320

MONTH_LABELS = {
    1:'1월 (겨울)',   2:'2월 (겨울)',   3:'3월 (봄)',
    4:'4월 (봄)',     5:'5월 (봄)',     6:'6월 (여름)',
    7:'7월 (여름)',   8:'8월 (여름)',   9:'9월 (가을)',
    10:'10월 (가을)', 11:'11월 (겨울)', 12:'12월 (겨울)'
}
SEASON_MAP = {
    1:'겨울', 2:'겨울', 3:'봄',  4:'봄',  5:'봄',
    6:'여름', 7:'여름', 8:'여름', 9:'가을',
    10:'가을', 11:'겨울', 12:'겨울'
}

# TOU 단가 테이블 (월 × 시간) — 한전 고압A 선택I 기준
# 내장 테이블 (xlsx 없을 때 fallback)
def get_tou_price(month, hour):
    if month in [6,7,8]:      # 여름
        if 10 <= hour <= 17:  return 155.0
        if hour <= 5 or hour >= 22: return 95.7
        return 121.5
    elif month in [11,12,1,2]: # 겨울
        if hour in [9,10,17,18,19]: return 155.0
        if hour <= 5 or hour >= 22: return 95.7
        return 121.5
    else:                      # 봄가을
        if 10 <= hour <= 17:  return 121.5
        if hour <= 5 or hour >= 22: return 95.7
        return 121.5

@st.cache_data
def load_rate_table():
    """한전 전기료 xlsx 로드 (없으면 내장 TOU 테이블 사용)"""
    candidates = [
        'data/한전전기료.xlsx',
        '../data/한전전기료.xlsx',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_excel(path, sheet_name=0, index_col=0)
                df.index   = df.index.astype(int)
                df.columns = [int(''.join(filter(str.isdigit, str(c))))
                              for c in df.columns]
                return df, True
            except Exception:
                pass
    # fallback — 내장 테이블 생성
    hours  = list(range(24))
    months = list(range(1,13))
    data   = {m: [get_tou_price(m, h) for h in hours] for m in months}
    df = pd.DataFrame(data, index=hours)
    return df, False

# ── 차트 ──────────────────────────────────────────────────────
def make_dr_chart(hours_label, cbl_line, reduced_line, rate_line):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours_label + hours_label[::-1],
        y=reduced_line + cbl_line[::-1],
        fill='toself', fillcolor='rgba(22,163,74,0.08)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(
        x=hours_label, y=cbl_line,
        name='CBL (기준 사용량)',
        line=dict(color='#d97706', dash='dash', width=2.5)))
    fig.add_trace(go.Scatter(
        x=hours_label, y=reduced_line,
        name='감축 후 목표',
        line=dict(color='#16a34a', width=2.5),
        fill='tozeroy', fillcolor='rgba(22,163,74,0.07)'))
    fig.add_trace(go.Scatter(
        x=hours_label, y=rate_line,
        name='전력 단가 (원/kWh)', yaxis='y2',
        line=dict(color='#7c3aed', dash='dot', width=1.5), opacity=0.8))
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
        xaxis=dict(gridcolor='#e2e8f0', title='시간'),
        yaxis=dict(gridcolor='#e2e8f0', title='전력 (kWh)'),
        yaxis2=dict(overlaying='y', side='right',
                    title='단가 (원/kWh)', showgrid=False,
                    tickfont=dict(color='#7c3aed')),
        legend=dict(bgcolor='rgba(255,255,255,0.9)', orientation='h',
                    yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bordercolor='#e2e8f0', borderwidth=1),
        height=320, margin=dict(l=0, r=0, t=40, b=0))
    return fig

# ── CBL 자동 계산 (CSV 업로드) ────────────────────────────────
def calc_cbl_from_df(df, month, target_hours):
    month_df = df[
        (df['월'] == month) &
        (df['평일여부'] == 1) &
        (df['시간'].isin(target_hours))
    ]
    if month_df.empty:
        return None
    daily_avg = month_df.groupby('날짜')['평균'].mean()
    if len(daily_avg) < 2:
        return None
    return round(daily_avg.nlargest(4).mean(), 2)

# ── 결과 계산 및 표시 ─────────────────────────────────────────
def show_results(cbl, dr_hours, month, dr_unit_price,
                 reduction_pct, monthly_dr_count, peak_months, rate_table):

    season        = SEASON_MAP[month]
    simulated_avg = cbl * (1 - reduction_pct / 100)
    reduction_kwh = cbl - simulated_avg
    total_reduc   = reduction_kwh * len(dr_hours)

    energy_rates = [
        rate_table.loc[h, month]
        if h in rate_table.index and month in rate_table.columns
        else get_tou_price(month, h)
        for h in dr_hours
    ]
    avg_rate      = sum(energy_rates) / len(energy_rates) if energy_rates else 0
    bill_saving   = reduction_kwh * sum(energy_rates)
    dr_reward     = total_reduc * dr_unit_price
    total_benefit = dr_reward + bill_saving

    co2_reduction      = total_reduc * EMISSION_FACTOR
    annual_co2         = co2_reduction * monthly_dr_count * peak_months
    annual_cost_saving = annual_co2 / 1000 * CARBON_PRICE
    annual_benefit     = (dr_reward + bill_saving) * monthly_dr_count * peak_months

    valid_hours  = dr_hours
    hours_label  = [f"{h}시" for h in valid_hours]
    cbl_line     = [cbl] * len(valid_hours)
    reduced_line = [simulated_avg] * len(valid_hours)
    rate_line    = [
        rate_table.loc[h, month]
        if h in rate_table.index and month in rate_table.columns
        else get_tou_price(month, h)
        for h in valid_hours
    ]

    # ── KPI 4개 ───────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("1회 총 감축량",
               f"{total_reduc:.1f} kWh",
               help=f"시간당 {reduction_kwh:.1f}kWh × {len(dr_hours)}시간")
    k2.metric("DR 정산금",
               f"{dr_reward/10000:.1f} 만원",
               delta=f"{dr_unit_price}원/kWh × {total_reduc:.1f}kWh",
               help="한전이 지급하는 DR 보상금")
    k3.metric("전기요금 절감",
               f"{bill_saving/10000:.1f} 만원",
               help=f"감축량 × 평균 TOU단가 {avg_rate:.1f}원/kWh")
    k4.metric("탄소 감축",
               f"{co2_reduction:.2f} kg CO₂",
               help=f"배출계수 {EMISSION_FACTOR} kgCO₂/kWh")

    st.divider()

    # ── 감축 진행 바 ──────────────────────────────────────────
    bar_pct = int((1 - reduction_pct / 100) * 100)
    st.markdown(
        f"<div style='background:#fff;border:1px solid #e2e8f0;"
        f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:12px;margin-bottom:8px;'>"
        f"<span style='font-weight:500;'>⚡ CBL — {cbl:.1f} kWh/h</span>"
        f"<span style='color:#059669;font-weight:700;'>"
        f"감축 목표 {reduction_pct}% 적용</span></div>"
        f"<div style='display:flex;gap:12px;'>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:11px;color:#94A3B8;margin-bottom:4px;'>감축 후 목표</div>"
        f"<div style='background:#E2E8F0;border-radius:5px;height:10px;overflow:hidden;'>"
        f"<div style='height:10px;width:{bar_pct}%;"
        f"background:#4ade80;border-radius:5px;'></div></div>"
        f"<div style='font-size:11px;color:#059669;margin-top:3px;'>"
        f"{simulated_avg:.1f} kWh/h</div></div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:11px;color:#94A3B8;margin-bottom:4px;'>감축량</div>"
        f"<div style='background:#E2E8F0;border-radius:5px;height:10px;overflow:hidden;'>"
        f"<div style='height:10px;width:{reduction_pct}%;"
        f"background:#60a5fa;border-radius:5px;'></div></div>"
        f"<div style='font-size:11px;color:#2563EB;margin-top:3px;'>"
        f"-{reduction_kwh:.1f} kWh/h ({reduction_pct}%)</div>"
        f"</div></div></div>",
        unsafe_allow_html=True)

    # ── 정산 상세 + 차트 ──────────────────────────────────────
    col_l, col_r = st.columns([1, 1.8])

    with col_l:
        st.markdown("**📋 DR 정산 상세**")
        with st.container(border=True):
            rows_data = [
                ("📌 CBL (DR 감축 기준값)",
                 f"{cbl:.1f} kWh/h"),
                (f"📉 감축 후 목표 (CBL × {100-reduction_pct}%)",
                 f"{simulated_avg:.1f} kWh/h"),
                ("⚡ 시간당 감축량",
                 f"{reduction_kwh:.1f} kWh"),
                ("⏱ 발령 시간 수",
                 f"{len(dr_hours)} 시간"),
                ("📦 1회 총 감축량",
                 f"{total_reduc:.1f} kWh"),
                ("💵 DR 정산금 (한전 보상금)",
                 f"{dr_reward:,.0f} 원"),
                ("💰 전기요금 절감",
                 f"{bill_saving:,.0f} 원"),
                ("🌿 탄소 감축",
                 f"{co2_reduction:.2f} kg CO₂"),
            ]
            for label, val in rows_data:
                c1, c2 = st.columns([2, 1])
                c1.markdown(
                    f"<span style='font-size:12px;color:#475569;'>"
                    f"{label}</span>",
                    unsafe_allow_html=True)
                c2.markdown(
                    f"<span style='font-size:12px;font-weight:700;"
                    f"color:#2563EB;font-family:monospace;'>{val}</span>",
                    unsafe_allow_html=True)
                st.divider()

            # 총 이익
            st.markdown(
                f"<div style='text-align:center;padding:10px 0;"
                f"font-size:15px;font-weight:800;color:#059669;'>"
                f"💎 1회 총 예상 이익<br>"
                f"<span style='font-size:20px;'>"
                f"{total_benefit:,.0f} 원</span><br>"
                f"<span style='font-size:11px;color:#94A3B8;'>"
                f"(DR 정산금 + 전기요금 절감액)</span></div>",
                unsafe_allow_html=True)

        st.caption(
            f"📌 {month}월 ({season}) · "
            f"평균 단가: {avg_rate:.1f}원/kWh · "
            f"DR 단가: {dr_unit_price}원/kWh")

    with col_r:
        st.markdown("**📈 CBL vs 감축 목표 비교**")
        st.plotly_chart(
            make_dr_chart(hours_label, cbl_line, reduced_line, rate_line),
            use_container_width=True)

    st.divider()

    # ── ESG 탄소 감축 ─────────────────────────────────────────
    st.markdown("**🌿 ESG 탄소 감축 효과**")
    e1, e2, e3 = st.columns(3)

    with e1:
        before_co2 = cbl * len(dr_hours) * EMISSION_FACTOR
        after_co2  = simulated_avg * len(dr_hours) * EMISSION_FACTOR
        fig_bar = go.Figure(go.Bar(
            x=['DR 전', 'DR 후'],
            y=[before_co2, after_co2],
            marker_color=['#ef4444', '#4ade80'],
            text=[f"{before_co2:.1f}kg", f"{after_co2:.1f}kg"],
            textposition='outside'))
        fig_bar.update_layout(
            title='1회 발령 탄소 배출 비교',
            paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
            yaxis=dict(gridcolor='#e2e8f0', title='kg CO₂'),
            xaxis=dict(gridcolor='#e2e8f0'),
            height=260, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    with e2:
        total_events = monthly_dr_count * peak_months
        cumulative   = [co2_reduction * i for i in range(1, total_events + 1)]
        event_labels = [f"{i}회" for i in range(1, total_events + 1)]
        fig_cum = go.Figure(go.Scatter(
            x=event_labels, y=cumulative,
            fill='tozeroy', fillcolor='rgba(74,222,128,0.12)',
            line=dict(color='#4ade80', width=2.5),
            mode='lines+markers',
            marker=dict(color='#4ade80', size=7)))
        fig_cum.update_layout(
            title=f'연간 누적 탄소 감축 (총 {total_events}회)',
            paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
            yaxis=dict(gridcolor='#e2e8f0', title='누적 kg CO₂'),
            xaxis=dict(gridcolor='#e2e8f0'),
            height=260, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_cum, use_container_width=True)

    with e3:
        st.metric("연간 탄소 감축",
                   f"{annual_co2/1000:.3f} tCO₂",
                   delta=f"월 {monthly_dr_count}회 × {peak_months}개월")
        st.metric("탄소 비용 절감 (연간)",
                   f"{annual_cost_saving:,.0f} 원",
                   help="ETS 10,000원/톤 기준")
        st.metric("연간 DR 총 이익",
                   f"{annual_benefit/10000:.1f} 만원",
                   delta="정산금 + 요금절감")

    st.caption(
        "※ 배출계수 0.4781 kgCO₂/kWh (환경부 고시 2022) | "
        "탄소가격 10,000원/톤 (한국 ETS) | "
        "전기요금 단가: 한전 고압A 선택I 기준")

# ══════════════════════════════════════════════════════════════
def render():
# ══════════════════════════════════════════════════════════════

    rate_table, using_xlsx = load_rate_table()

    # ── 사이드바 ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='background:#1E293B;color:#fff;border-radius:8px;"
            "padding:10px 14px;margin-bottom:14px;font-size:13px;"
            "font-weight:700;'>💰 DR 시뮬레이션 — 발령 조건</div>",
            unsafe_allow_html=True)

        st.markdown("**⚙️ DR 발령 조건**")

        dr_month = st.selectbox(
            "발령 월", list(MONTH_LABELS.keys()), index=6,
            format_func=lambda x: MONTH_LABELS[x],
            key="t3_month",
            help="여름(6~8월)·겨울(11~2월)에 DR 발령이 집중됩니다")

        c1, c2 = st.columns(2)
        with c1:
            dr_start = st.selectbox(
                "시작 시간", list(range(0,23)), index=13,
                format_func=lambda x: f"{x}:00",
                key="t3_start",
                help="보통 오후 2~5시 최대부하 시간대")
        with c2:
            dr_end = st.selectbox(
                "종료 시간", list(range(1,24)), index=16,
                format_func=lambda x: f"{x}:00",
                key="t3_end",
                help="시작보다 커야 합니다")

        dr_unit_price = st.number_input(
            "DR 정산 단가 (원/kWh)",
            100, 600, 300, 50,
            key="t3_price",
            help="한전 DR 계약서 기준. 일반적으로 200~400원/kWh")
        reduction_pct = st.slider(
            "감축 목표율 (%)", 5, 30, 15, 1,
            key="t3_reduce",
            help="평소 전력 대비 감축 비율\n예) 15% → 100kWh → 85kWh")

        st.divider()
        st.caption("📅 연간 DR 효과 설정")
        cd1, cd2 = st.columns(2)
        with cd1:
            monthly_dr_count = st.number_input(
                "월 발령 횟수", 1, 20, 2, 1,
                key="t3_monthly",
                help="피크 시즌 월 2~4회 일반적")
        with cd2:
            peak_months = st.number_input(
                "발령 월 수", 1, 12, 4, 1,
                key="t3_months",
                help="여름3 + 겨울3 = 6개월 일반적")

        # Tab1 연동
        st.divider()
        if "predicted_peak" in st.session_state:
            pred_peak = st.session_state["predicted_peak"]
            pred_month= st.session_state.get("predicted_month", dr_month)
            st.success(
                f"✅ 피크 예측 탭 연동\n\n"
                f"예측 피크: **{pred_peak:.1f} kW**\n\n"
                f"→ CBL 자동 적용 가능",
                icon="✅")
            use_predicted = st.checkbox(
                "예측 피크를 CBL로 사용",
                value=False,
                key="t3_use_pred",
                help="Tab1에서 예측한 피크값을 CBL로 자동 입력합니다")
        else:
            use_predicted = False
            pred_peak = None

    # ── 페이지 헤더 ───────────────────────────────────────────
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;"
        "margin-bottom:2px;'>"
        "<div style='background:#1D4ED8;color:#fff;font-weight:700;"
        "font-size:13px;padding:4px 10px;border-radius:6px;'>EP</div>"
        "<span style='font-size:20px;font-weight:700;'>"
        "DR 시뮬레이션 대시보드</span></div>",
        unsafe_allow_html=True)
    st.caption("수요반응(Demand Response) 발령 시 예상 수익 · 탄소 감축 시뮬레이션 | 올라운더팀 2026")

    if not using_xlsx:
        st.info(
            "ℹ️ data/한전전기료.xlsx 파일을 찾지 못해 **내장 TOU 단가 테이블**을 사용합니다. "
            "정확한 계산을 위해 xlsx 파일을 data/ 폴더에 넣어주세요.",
            icon="ℹ️")

    # DR 개념 설명
    with st.expander("💡 DR(수요반응)이란? — 클릭해서 개념 보기"):
        st.markdown(
            "**DR(Demand Response, 수요반응)** 은 여름·겨울 피크 시즌에 "
            "전국 전력 수요가 급증하면, 한전이 공장에 "
            "**'지금 전기를 조금 줄여주세요'** 라고 요청하는 제도입니다.\n\n"
            "공장이 전력을 줄이면 **줄인 만큼 한전이 보상금을 지급**합니다.\n\n"
            "| 구분 | 설명 |\n"
            "|---|---|\n"
            "| CBL | 평소 전력 사용량 기준 (Customer Baseline Load) |\n"
            "| 감축량 | CBL - 실제 사용량 |\n"
            "| 정산금 | 감축량(kWh) × DR 단가(원/kWh) |\n"
            "| 총 편익 | 정산금 + 전기요금 절감액 |")

    st.divider()

    # ── 입력 방식 선택 ────────────────────────────────────────
    st.markdown("**📂 데이터 입력 방식**")
    mode = st.radio(
        "입력 방식",
        ["✏️ 직접 입력", "📁 CSV 파일 업로드"],
        horizontal=True,
        label_visibility="collapsed",
        key="t3_mode")

    st.divider()

    # ══════════════════════════════════════════════════════════
    # 방식 1: 직접 입력
    # ══════════════════════════════════════════════════════════
    if mode == "✏️ 직접 입력":
        st.markdown("**✏️ 공장 전력 정보 입력**")
        st.caption("DR 발령 시간대의 평균 전력 사용량을 입력하세요.")

        inp1, inp2, _ = st.columns([1, 1, 2])
        with inp1:
            # Tab1 예측값 자동 연동
            default_cbl = (
                float(pred_peak) if use_predicted and pred_peak
                else 150.0
            )
            avg_usage = st.number_input(
                "시간당 평균 전력 사용량 (kWh/h)",
                min_value=1.0, max_value=10000.0,
                value=default_cbl, step=10.0,
                key="t3_cbl",
                help="DR 발령 시간대 평균 전력량\n"
                     "이 값이 CBL(감축 기준)이 됩니다\n"
                     "Tab1 예측 피크 연동 시 자동 입력")
        with inp2:
            st.number_input(
                "계약전력 (kW)", 1, 100000, 300, 10,
                key="t3_contract",
                help="한전 계약 최대 전력 용량 (참고용)")

        run_btn = st.button(
            "🚀 DR 시뮬레이션 실행",
            type="primary",
            key="t3_run")

        if run_btn:
            if dr_end <= dr_start:
                st.warning("⚠️ 종료 시간은 시작 시간보다 커야 합니다.")
            else:
                dr_hours = list(range(dr_start, dr_end + 1))
                with st.spinner("시뮬레이션 계산 중..."):
                    show_results(
                        avg_usage, dr_hours, dr_month,
                        dr_unit_price, reduction_pct,
                        monthly_dr_count, peak_months,
                        rate_table)

        elif "t3_last_run" not in st.session_state:
            st.markdown(
                "<div style='text-align:center;padding:50px 0;"
                "color:#94A3B8;'>"
                "<div style='font-size:48px;margin-bottom:12px;'>✏️</div>"
                "<div style='font-size:15px;color:#475569;'>"
                "평균 전력 사용량을 입력하고<br>"
                "<b>🚀 DR 시뮬레이션 실행</b> 버튼을 누르세요"
                "</div></div>",
                unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # 방식 2: CSV 업로드
    # ══════════════════════════════════════════════════════════
    else:
        st.markdown("**📁 CSV 파일 업로드**")
        st.caption(
            "필수 컬럼: **날짜** (YYYYMMDD) · **시간** (0~23) · **평균** (kWh) | "
            "업로드 시 CBL이 자동 계산됩니다 (해당 월 평일 상위 4일 평균)")

        uploaded = st.file_uploader(
            "CSV 파일 선택", type=['csv'],
            key="t3_upload")

        if uploaded:
            try:
                try:
                    user_df = pd.read_csv(uploaded, encoding='utf-8-sig')
                except Exception:
                    uploaded.seek(0)
                    user_df = pd.read_csv(uploaded, encoding='euc-kr')

                required = ['날짜','시간','평균']
                missing  = [c for c in required if c not in user_df.columns]

                if missing:
                    st.error(f"필수 컬럼이 없습니다: {missing}")
                    st.write("업로드된 컬럼:", user_df.columns.tolist())
                else:
                    user_df = user_df[user_df['시간'].between(0,23)].copy()
                    user_df['datetime'] = pd.to_datetime(
                        user_df['날짜'].astype(str) +
                        user_df['시간'].astype(str).str.zfill(2),
                        format='%Y%m%d%H')
                    user_df['월']       = user_df['datetime'].dt.month
                    user_df['요일']     = user_df['datetime'].dt.dayofweek
                    user_df['평일여부'] = (user_df['요일'] < 5).astype(int)

                    cp, cs = st.columns([2, 1])
                    with cp:
                        st.success(
                            f"✅ 업로드 완료: "
                            f"{len(user_df):,}행 × {len(user_df.columns)}열")
                        st.dataframe(
                            user_df[['날짜','시간','평균','월']].head(5),
                            use_container_width=True)
                    with cs:
                        st.metric("데이터 기간",
                                   f"{user_df['날짜'].min()} ~ {user_df['날짜'].max()}")
                        st.metric("총 행수", f"{len(user_df):,}행")

                    run_csv = st.button(
                        "🚀 DR 시뮬레이션 실행 (CSV)",
                        type="primary", key="t3_run_csv")

                    if run_csv:
                        if dr_end <= dr_start:
                            st.warning("⚠️ 종료 시간은 시작 시간보다 커야 합니다.")
                        else:
                            dr_hours = list(range(dr_start, dr_end + 1))
                            cbl = calc_cbl_from_df(user_df, dr_month, dr_hours)
                            if cbl is None:
                                st.warning(
                                    "⚠️ 선택한 월·시간대의 데이터가 부족합니다. "
                                    "다른 월을 선택하세요.")
                            else:
                                st.info(
                                    f"📌 CBL 자동 계산 완료: **{cbl:.1f} kWh/h** "
                                    f"(해당 월 평일 상위 4일 평균)")
                                with st.spinner("시뮬레이션 계산 중..."):
                                    show_results(
                                        cbl, dr_hours, dr_month,
                                        dr_unit_price, reduction_pct,
                                        monthly_dr_count, peak_months,
                                        rate_table)
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")
        else:
            st.markdown(
                "<div style='text-align:center;padding:50px 0;"
                "color:#94A3B8;'>"
                "<div style='font-size:48px;margin-bottom:12px;'>📁</div>"
                "<div style='font-size:15px;color:#475569;'>"
                "CSV 파일을 업로드하면 CBL이 자동 계산됩니다<br>"
                "<span style='font-size:12px;'>필수 컬럼: 날짜 / 시간 / 평균</span>"
                "</div></div>",
                unsafe_allow_html=True)

    st.caption("올라운더팀 | KAMP 자원 최적화 AI 프로젝트 2 | 2026")
