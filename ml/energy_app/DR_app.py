# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="DR 시뮬레이션",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* ── 전체 배경: 밝은 회색 ── */
    .stApp {
        background-color: #f4f6f9;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ── 폰트 ── */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    }

    /* ── 지표 카드 ── */
    .metric-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px 22px;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #3b82f6;
        text-align: left;
        transition: transform 0.15s, box-shadow 0.15s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    .metric-card.green  { border-left-color: #16a34a; }
    .metric-card.yellow { border-left-color: #d97706; }
    .metric-card.blue   { border-left-color: #2563eb; }
    .metric-card.purple { border-left-color: #7c3aed; }

    .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1e293b;
        line-height: 1.1;
    }
    .metric-unit {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 5px;
    }
    .metric-green  { color: #16a34a; }
    .metric-blue   { color: #2563eb; }
    .metric-yellow { color: #d97706; }
    .metric-purple { color: #7c3aed; }

    /* ── 섹션 타이틀 ── */
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 18px;
    }

    /* ── 정산 결과 박스 ── */
    .result-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .result-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 11px 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.5;
    }
    .result-row:last-child { border-bottom: none; }
    .result-val {
        font-weight: 700;
        color: #2563eb;
        font-size: 0.95rem;
        white-space: nowrap;
        margin-left: 12px;
    }
    .result-total {
        text-align: center;
        padding-top: 16px;
        margin-top: 4px;
        font-size: 1.25rem;
        font-weight: 800;
        color: #16a34a;
    }

    /* ── 정보 태그 ── */
    .info-tag {
        display: inline-block;
        background: #eff6ff;
        color: #2563eb;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.74rem;
        margin-top: 6px;
        margin-right: 4px;
        border: 1px solid #bfdbfe;
        font-weight: 600;
    }

    /* ── DR 개념 설명 박스 ── */
    .dr-intro {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 28px;
    }
    .dr-intro-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1d4ed8;
        margin-bottom: 10px;
    }
    .dr-intro-text {
        color: #334155;
        font-size: 0.9rem;
        line-height: 1.9;
    }

    /* ── 진행 바 ── */
    .progress-wrap {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .progress-bar-bg {
        background: #e2e8f0;
        border-radius: 6px;
        height: 10px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 10px;
        border-radius: 6px;
    }

    /* ── 버튼 ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.55rem 2rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 상수 및 요금 테이블
# ─────────────────────────────────────────
@st.cache_data
def load_rate_table():
    rate_df = pd.read_excel('data/한전전기료.xlsx', sheet_name=0, index_col=0)
    rate_df.index = rate_df.index.astype(int)
    rate_df.columns = [int(''.join(filter(str.isdigit, str(c)))) for c in rate_df.columns]
    return rate_df

EMISSION_FACTOR = 0.4781
CARBON_PRICE    = 10_000

MONTH_LABELS = {
    1:'1월 (겨울)',  2:'2월 (겨울)',  3:'3월 (봄)',
    4:'4월 (봄)',    5:'5월 (봄)',    6:'6월 (여름)',
    7:'7월 (여름)',  8:'8월 (여름)',  9:'9월 (가을)',
    10:'10월 (가을)', 11:'11월 (겨울)', 12:'12월 (겨울)'
}
SEASON_MAP = {
    1:'겨울', 2:'겨울', 3:'봄',  4:'봄',  5:'봄',
    6:'여름', 7:'여름', 8:'여름', 9:'가을',
    10:'가을', 11:'겨울', 12:'겨울'
}


# ─────────────────────────────────────────
# 차트 생성 함수
# ─────────────────────────────────────────
def make_dr_chart(hours_label, cbl_line, reduced_line, rate_line):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours_label + hours_label[::-1],
        y=reduced_line + cbl_line[::-1],
        fill='toself', fillcolor='rgba(22,163,74,0.08)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False, hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=hours_label, y=cbl_line,
        name='CBL (기준 사용량)',
        line=dict(color='#d97706', dash='dash', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=hours_label, y=reduced_line,
        name='감축 후 목표',
        line=dict(color='#16a34a', width=2.5),
        fill='tozeroy', fillcolor='rgba(22,163,74,0.07)'
    ))
    fig.add_trace(go.Scatter(
        x=hours_label, y=rate_line,
        name='전력 단가 (원/kWh)', yaxis='y2',
        line=dict(color='#7c3aed', dash='dot', width=1.5), opacity=0.8
    ))
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
        font=dict(color='#334155', family='Malgun Gothic, 맑은 고딕, sans-serif'),
        xaxis=dict(gridcolor='#e2e8f0', title='시간', color='#64748b'),
        yaxis=dict(gridcolor='#e2e8f0', title='전력 (kWh)', color='#64748b'),
        yaxis2=dict(overlaying='y', side='right', title='단가 (원/kWh)',
                    showgrid=False, tickfont=dict(color='#7c3aed'), color='#7c3aed'),
        legend=dict(bgcolor='rgba(255,255,255,0.9)', orientation='h',
                    yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bordercolor='#e2e8f0', borderwidth=1),
        height=340, margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig


# ─────────────────────────────────────────
# CBL 계산 함수 (CSV 업로드 방식)
# ─────────────────────────────────────────
def calc_cbl_from_df(df, month, target_hours):
    month_df = df[(df['월'] == month) & (df['평일여부'] == 1) & (df['시간'].isin(target_hours))]
    if month_df.empty:
        return None
    daily_avg = month_df.groupby('날짜')['평균'].mean()
    if len(daily_avg) < 2:
        return None
    return round(daily_avg.nlargest(4).mean(), 2)


# ─────────────────────────────────────────
# 결과 출력 함수
# ─────────────────────────────────────────
def show_results(cbl, dr_hours, month, dr_unit_price, reduction_pct,
                 monthly_dr_count, peak_months, rate_table):

    season        = SEASON_MAP[month]
    simulated_avg = cbl * (1 - reduction_pct / 100)
    reduction_kwh = cbl - simulated_avg
    total_reduc   = reduction_kwh * len(dr_hours)

    energy_rates  = [rate_table.loc[h, month] for h in dr_hours if h in rate_table.index]
    avg_rate      = sum(energy_rates) / len(energy_rates) if energy_rates else 0
    bill_saving   = reduction_kwh * sum(energy_rates)
    dr_reward     = total_reduc * dr_unit_price
    total_benefit = dr_reward + bill_saving

    co2_reduction      = total_reduc * EMISSION_FACTOR
    annual_co2         = co2_reduction * monthly_dr_count * peak_months
    annual_cost_saving = annual_co2 / 1000 * CARBON_PRICE
    annual_benefit     = (dr_reward + bill_saving) * monthly_dr_count * peak_months

    valid_hours  = [h for h in dr_hours if h in rate_table.index]
    hours_label  = [f"{h}시" for h in valid_hours]
    cbl_line     = [cbl] * len(valid_hours)
    reduced_line = [simulated_avg] * len(valid_hours)
    rate_line    = [rate_table.loc[h, month] for h in valid_hours]

    # 상단 지표 카드
    m1, m2, m3, m4 = st.columns(4)
    for col, label, val, unit, color_cls, card_cls in [
        (m1, "1회 총 감축량",  f"{total_reduc:.1f}",       "kWh",    "metric-blue",   "blue"),
        (m2, "DR 정산금",      f"{dr_reward/10000:.1f}",   "만원",   "metric-green",  "green"),
        (m3, "전기요금 절감",  f"{bill_saving/10000:.1f}", "만원",   "metric-yellow", "yellow"),
        (m4, "탄소 감축",      f"{co2_reduction:.2f}",     "kg CO₂", "metric-purple", "purple"),
    ]:
        col.markdown(f"""
        <div class="metric-card {card_cls}">
            <div class="metric-label">{label}</div>
            <div class="metric-value {color_cls}">{val}</div>
            <div class="metric-unit">{unit}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 감축 진행 바 (CBL vs 목표)
    bar_pct = int((1 - reduction_pct/100) * 100)
    st.markdown(f"""
    <div class="progress-wrap">
        <div class="progress-label">
            <span>⚡ CBL (현재 기준 사용량) — {cbl:.1f} kWh/h</span>
            <span style="color:#4ade80;">감축 목표 {reduction_pct}% 적용</span>
        </div>
        <div style="display:flex; gap:6px; align-items:center;">
            <div style="flex:1;">
                <div style="font-size:0.75rem; color:#8b9ab8; margin-bottom:3px;">감축 후 목표</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width:{bar_pct}%; background:linear-gradient(90deg,#4ade80,#22c55e);"></div>
                </div>
                <div style="font-size:0.8rem; color:#4ade80; margin-top:3px;">{simulated_avg:.1f} kWh/h</div>
            </div>
            <div style="flex:1;">
                <div style="font-size:0.75rem; color:#8b9ab8; margin-bottom:3px;">감축량</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width:{reduction_pct}%; background:linear-gradient(90deg,#60a5fa,#3b82f6);"></div>
                </div>
                <div style="font-size:0.8rem; color:#60a5fa; margin-top:3px;">-{reduction_kwh:.1f} kWh/h ({reduction_pct}%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 정산 상세 + 차트
    col_l, col_r = st.columns([1, 1.8])
    with col_l:
        st.markdown('<div class="section-title">📋 DR 정산 상세</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-box">
            <div class="result-row">
                <span>📌 CBL <span style="font-size:0.75rem;color:#6b7280;">(DR 감축 기준값)</span></span>
                <span class="result-val">{cbl:.1f} kWh/h</span>
            </div>
            <div class="result-row">
                <span>📉 감축 후 목표 <span style="font-size:0.75rem;color:#6b7280;">(CBL × {100-reduction_pct}%)</span></span>
                <span class="result-val">{simulated_avg:.1f} kWh/h</span>
            </div>
            <div class="result-row">
                <span>⚡ 시간당 감축량 <span style="font-size:0.75rem;color:#6b7280;">(CBL - 목표)</span></span>
                <span class="result-val">{reduction_kwh:.1f} kWh</span>
            </div>
            <div class="result-row">
                <span>⏱ 발령 시간 수</span>
                <span class="result-val">{len(dr_hours)} 시간</span>
            </div>
            <div class="result-row">
                <span>📦 1회 총 감축량 <span style="font-size:0.75rem;color:#6b7280;">(시간당 감축 × 발령시간)</span></span>
                <span class="result-val">{total_reduc:.1f} kWh</span>
            </div>
            <div class="result-row">
                <span>💵 DR 정산금 <span style="font-size:0.75rem;color:#6b7280;">(한전 보상금)</span></span>
                <span class="result-val">{dr_reward:,.0f} 원</span>
            </div>
            <div class="result-row">
                <span>💰 전기요금 절감 <span style="font-size:0.75rem;color:#6b7280;">(줄인 전력 × 요금단가)</span></span>
                <span class="result-val">{bill_saving:,.0f} 원</span>
            </div>
            <div class="result-row">
                <span>🌿 탄소 감축 <span style="font-size:0.75rem;color:#6b7280;">(감축량 × 배출계수)</span></span>
                <span class="result-val">{co2_reduction:.2f} kg CO₂</span>
            </div>
            <div class="result-total">💎 1회 총 예상 이익: {total_benefit:,.0f} 원<br>
                <span style="font-size:0.8rem; color:#86efac;">(DR 정산금 + 전기요금 절감액)</span>
            </div>
        </div>
        <div style="margin-top:10px;">
            <span class="info-tag">{month}월 ({season})</span>
            <span class="info-tag">평균 단가: {avg_rate:.1f}원/kWh</span>
            <span class="info-tag">DR 단가: {dr_unit_price}원/kWh</span>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-title">📈 CBL vs 감축 목표 비교</div>', unsafe_allow_html=True)
        st.plotly_chart(make_dr_chart(hours_label, cbl_line, reduced_line, rate_line),
                        use_container_width=True)

    st.markdown("<br>")
    st.markdown("---")

    # ESG 탄소 감축
    st.markdown('<div class="section-title">🌿 ESG 탄소 감축 효과</div>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)

    with e1:
        before_co2 = cbl * len(dr_hours) * EMISSION_FACTOR
        after_co2  = simulated_avg * len(dr_hours) * EMISSION_FACTOR
        fig_bar = go.Figure(go.Bar(
            x=['DR 전', 'DR 후'], y=[before_co2, after_co2],
            marker_color=['#ef4444', '#4ade80'],
            text=[f"{before_co2:.1f}kg", f"{after_co2:.1f}kg"],
            textposition='outside', textfont=dict(color='#374151', size=12)
        ))
        fig_bar.update_layout(
            title='1회 발령 탄소 배출 비교',
            font=dict(color='#334155', family='Malgun Gothic, 맑은 고딕, sans-serif'),
            paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
            yaxis=dict(gridcolor='#e2e8f0', title='kg CO₂', color='#64748b'),
            xaxis=dict(gridcolor='#e2e8f0', color='#64748b'),
            height=280, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with e2:
        total_events = monthly_dr_count * peak_months
        cumulative   = [co2_reduction * i for i in range(1, total_events + 1)]
        event_labels = [f"{i}회" for i in range(1, total_events + 1)]
        fig_cum = go.Figure(go.Scatter(
            x=event_labels, y=cumulative,
            fill='tozeroy', fillcolor='rgba(74,222,128,0.12)',
            line=dict(color='#4ade80', width=2.5),
            mode='lines+markers', marker=dict(color='#4ade80', size=7)
        ))
        fig_cum.update_layout(
            title=f'연간 누적 탄소 감축 (총 {total_events}회)',
            paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',
            font=dict(color='#334155', family='Malgun Gothic, 맑은 고딕, sans-serif'),
            yaxis=dict(gridcolor='#e2e8f0', title='누적 kg CO₂', color='#64748b'),
            xaxis=dict(gridcolor='#e2e8f0', color='#64748b'),
            height=280, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    with e3:
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:12px;">
            <div class="metric-label">연간 탄소 감축</div>
            <div class="metric-value metric-green">{annual_co2/1000:.3f}</div>
            <div class="metric-unit">톤 CO₂ (월{monthly_dr_count}회 × {peak_months}개월)</div>
        </div>
        <div class="metric-card" style="margin-bottom:12px;">
            <div class="metric-label">탄소 비용 절감 (연간)</div>
            <div class="metric-value metric-blue">{annual_cost_saving:,.0f}</div>
            <div class="metric-unit">원 (ETS 10,000원/톤 기준)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">연간 DR 총 이익</div>
            <div class="metric-value metric-green">{annual_benefit/10000:.1f}</div>
            <div class="metric-unit">만원 (정산금 + 요금절감)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        "<br><div style='color:#6b7280; font-size:0.78rem;'>"
        "※ 배출계수 0.4781 kgCO₂/kWh (환경부 고시 2022) | "
        "탄소가격 10,000원/톤 (한국 ETS) | "
        "전기요금 단가: 한전 고압A 선택I 기준"
        "</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════
# 메인 UI
# ══════════════════════════════════════════
rate_table = load_rate_table()

st.markdown("## ⚡ DR 시뮬레이션 대시보드")

# DR 개념 설명 박스
st.markdown("""
<div class="dr-intro">
    <div class="dr-intro-title">💡 DR(수요반응, Demand Response)이란?</div>
    <div class="dr-intro-text">
        여름·겨울 피크 시즌에 전국 전력 수요가 급증하면,
        한전이 공장에 <b style="color:#fbbf24;">"지금 전기를 조금 줄여주세요"</b> 라고 요청합니다.
        이것을 <b style="color:#fbbf24;">DR 발령</b>이라고 해요.<br>
        공장이 전력을 줄이면 <b style="color:#4ade80;">줄인 만큼 한전이 보상금을 지급</b>합니다.
        이 시뮬레이터는 DR 발령 시 예상 이익을 미리 계산해드립니다.
    </div>
</div>
""", unsafe_allow_html=True)

# ── 입력 방식 선택 ───────────────────────
st.markdown('<div class="section-title">📂 데이터 입력 방식 선택</div>', unsafe_allow_html=True)

mode = st.radio(
    "입력 방식",
    ["✏️  직접 입력", "📁  CSV 파일 업로드"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# ── 공통 DR 조건 ─────────────────────────
st.markdown('<div class="section-title">⚙️ DR 발령 조건 설정</div>', unsafe_allow_html=True)
st.caption("한전이 전력 감축을 요청하는 조건을 설정합니다. 모르는 항목은 기본값을 그대로 사용하세요.")

cc1, cc2, cc3, cc4, cc5 = st.columns(5)
with cc1:
    dr_month = st.selectbox(
        "발령 월",
        list(MONTH_LABELS.keys()),
        index=6,
        format_func=lambda x: MONTH_LABELS[x],
        help="DR이 주로 발생하는 계절을 선택하세요.\n여름(6-8월)과 겨울(11-2월)에 전국 전력 수요가 급증해 DR 발령이 많습니다."
    )
with cc2:
    dr_start = st.selectbox(
        "감축 시작 시간",
        list(range(0, 23)),
        index=13,
        format_func=lambda x: f"{x}:00",
        help="한전이 전력 감축을 요청하는 시작 시간입니다.\n보통 오후 2시-5시(최대부하 시간대)에 발령됩니다."
    )
with cc3:
    dr_end = st.selectbox(
        "감축 종료 시간",
        list(range(1, 24)),
        index=16,
        format_func=lambda x: f"{x}:00",
        help="한전이 전력 감축 요청을 끝내는 시간입니다.\n시작-종료 사이의 시간 동안 전력을 줄여야 합니다."
    )
with cc4:
    dr_unit_price = st.number_input(
        "DR 정산 단가 (원/kWh)",
        100, 600, 300, 50,
        help="전력 1kWh를 줄일 때마다 한전이 지급하는 보상 단가입니다.\n한전 DR 계약서에 명시된 값을 입력하세요. (일반적으로 200-400원/kWh)"
    )
with cc5:
    reduction_pct = st.slider(
        "감축 목표율 (%)",
        5, 30, 15, 1,
        help="평소 전력 사용량 대비 얼마나 줄일지 설정합니다.\n예) 15% → 평소 100kWh 사용 시 85kWh로 줄이는 것"
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.caption("📅 연간 DR 효과 계산을 위한 설정입니다.")
cd1, cd2, _ = st.columns([1, 1, 3])
with cd1:
    monthly_dr_count = st.number_input(
        "월 DR 발령 횟수",
        1, 20, 2, 1,
        help="한 달에 DR 발령이 몇 번 있는지 입력합니다.\n일반적으로 피크 시즌에 월 2-4회 발령됩니다."
    )
with cd2:
    peak_months = st.number_input(
        "연간 DR 발령 월 수",
        1, 12, 4, 1,
        help="1년 중 DR이 발령되는 달이 몇 달인지 입력합니다.\n보통 여름(3개월) + 겨울(3개월) = 6개월이지만\n실제 계약에 따라 다를 수 있습니다."
    )

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════
# 방식 1: 직접 입력
# ══════════════════════════════════════════
if mode == "✏️  직접 입력":
    st.markdown('<div class="section-title">✏️ 공장 전력 정보 입력</div>', unsafe_allow_html=True)
    st.caption("우리 공장의 전력 사용 정보를 입력하세요. 전기요금 고지서나 한전 계약 내역에서 확인할 수 있습니다.")

    inp1, inp2, _ = st.columns([1, 1, 2])
    with inp1:
        avg_usage = st.number_input(
            "시간당 평균 전력 사용량 (kWh/h)",
            min_value=1.0, max_value=10000.0, value=150.0, step=10.0,
            help="DR 발령 시간대에 우리 공장이 평균적으로 사용하는 전력량입니다.\n이 값이 DR 감축의 기준(CBL)이 됩니다.\n예) 오후 2-5시에 평균 150kWh 사용 → 150 입력"
        )
    with inp2:
        st.number_input(
            "계약전력 (kW)",
            1, 100000, 300, 10,
            help="한전과 계약한 최대 전력 용량입니다.\n전기요금 고지서 또는 한전 계약서에서 확인할 수 있습니다. (참고용)"
        )

    run = st.button("🚀 시뮬레이션 실행", type="primary")
    st.markdown("---")

    if run:
        if dr_end <= dr_start:
            st.warning("⚠️ 종료 시간은 시작 시간보다 커야 합니다.")
        else:
            dr_hours = list(range(dr_start, dr_end + 1))
            show_results(avg_usage, dr_hours, dr_month, dr_unit_price,
                         reduction_pct, monthly_dr_count, peak_months, rate_table)
    else:
        st.markdown("""
        <div style="text-align:center; padding:80px 0; color:#8b8fa8;">
            <div style="font-size:3.5rem;">✏️</div>
            <div style="font-size:1.1rem; margin-top:12px; color:#94a3b8;">
                평균 전력 사용량을 입력하고 실행하세요
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════
# 방식 2: CSV 업로드
# ══════════════════════════════════════════
else:
    st.markdown('<div class="section-title">📁 CSV 파일 업로드</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="color:#8b8fa8; font-size:0.85rem; margin-bottom:12px;">
    CSV 파일에 아래 컬럼이 필요합니다:
    <b style="color:#93c5fd;">날짜</b> (YYYYMMDD),
    <b style="color:#93c5fd;">시간</b> (0~23),
    <b style="color:#93c5fd;">평균</b> (kWh),
    <b style="color:#93c5fd;">생산량</b> (선택)
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("CSV 파일 선택", type=['csv'])

    if uploaded_file:
        try:
            # 인코딩 자동 감지
            try:
                user_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            except:
                uploaded_file.seek(0)
                user_df = pd.read_csv(uploaded_file, encoding='euc-kr')

            # 필수 컬럼 확인
            required = ['날짜', '시간', '평균']
            missing  = [c for c in required if c not in user_df.columns]

            if missing:
                st.error(f"필수 컬럼이 없습니다: {missing}")
                st.write("업로드된 컬럼:", user_df.columns.tolist())
            else:
                # 전처리
                user_df = user_df[user_df['시간'].between(0, 23)].copy()
                user_df['datetime'] = pd.to_datetime(
                    user_df['날짜'].astype(str) + user_df['시간'].astype(str).str.zfill(2),
                    format='%Y%m%d%H'
                )
                user_df['월']      = user_df['datetime'].dt.month
                user_df['요일']    = user_df['datetime'].dt.dayofweek
                user_df['평일여부'] = (user_df['요일'] < 5).astype(int)

                # 데이터 미리보기
                col_p, col_s = st.columns([2, 1])
                with col_p:
                    st.success(f"✅ 업로드 완료: {len(user_df):,}행 × {len(user_df.columns)}열")
                    st.dataframe(user_df[['날짜','시간','평균','월']].head(5),
                                 use_container_width=True)
                with col_s:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-top:4px;">
                        <div class="metric-label">데이터 기간</div>
                        <div class="metric-value" style="font-size:1rem;">
                            {str(user_df['날짜'].min())} - {str(user_df['날짜'].max())}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                run = st.button("🚀 시뮬레이션 실행", type="primary")
                st.markdown("---")

                if run:
                    if dr_end <= dr_start:
                        st.warning("⚠️ 종료 시간은 시작 시간보다 커야 합니다.")
                    else:
                        dr_hours = list(range(dr_start, dr_end + 1))
                        cbl = calc_cbl_from_df(user_df, dr_month, dr_hours)

                        if cbl is None:
                            st.warning("⚠️ 선택한 월/시간대의 데이터가 부족합니다. 다른 월을 선택하세요.")
                        else:
                            st.info(f"📌 CBL 자동 계산 완료: **{cbl:.1f} kWh/h** (해당 월 평일 상위 4일 평균)")
                            show_results(cbl, dr_hours, dr_month, dr_unit_price,
                                         reduction_pct, monthly_dr_count, peak_months, rate_table)
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")
    else:
        st.markdown("""
        <div style="text-align:center; padding:80px 0; color:#8b8fa8;">
            <div style="font-size:3.5rem;">📁</div>
            <div style="font-size:1.1rem; margin-top:12px; color:#94a3b8;">
                CSV 파일을 업로드하면 CBL이 자동 계산됩니다
            </div>
            <div style="margin-top:8px; font-size:0.85rem;">
                필수 컬럼: 날짜 / 시간 / 평균
            </div>
        </div>
        """, unsafe_allow_html=True)
