# ================================================================
# pages/tab2_power_query.py
# 역할 : 전력 조회 (Tab2) — 월별 단일 조회 + 기간 범위 조회
# 의존 : data/power_estimate_full_2021.csv
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
import plotly.express as px

# ── 상수 ──────────────────────────────────────────────────────
BASIC_RATE = 8320
EMISSION   = 0.4781
TARIFF     = {
    "여름":  191.6,
    "겨울":  109.8,
    "봄가을":167.2,
}
SEASON_MAP = {
    1:"겨울", 2:"겨울", 3:"봄가을", 4:"봄가을", 5:"봄가을",
    6:"여름",  7:"여름",  8:"여름",
    9:"봄가을",10:"봄가을",11:"겨울",12:"겨울"
}
MONTH_KR = {
    1:"1월", 2:"2월", 3:"3월", 4:"4월", 5:"5월", 6:"6월",
    7:"7월", 8:"8월", 9:"9월",10:"10월",11:"11월",12:"12월"
}

# 2022~2025 시연용 임의 데이터 (월별)
# 형식: kwh, peak_max, peak_avg, prod, man_max, man_avg, work_hours
DEMO_DATA = {
    2022:[
        (43650,192.1,84.7,199841,14.1,1.50,275),
        (43180,193.6,91.8,338726,50.8,2.59,422),
        (53632,192.6,101.6,318465,17.5,1.45,405),
        (48466,186.6,93.4,391733,12.3,1.64,493),
        (45909,186.4,84.7,395194,12.5,1.70,458),
        (53095,193.7,104.6,424312,9.2,1.44,522),
        (54674,207.0,105.2,424267,12.7,1.51,463),
        (43861,209.8,82.7,351454,13.9,1.57,402),
        (42476,197.6,81.1,296801,10.5,1.33,527),
        (33940,189.5,63.1,259309,11.0,1.37,591),
        (36926,193.8,69.4,286638,11.2,1.33,583),
        (39021,193.2,72.2,295769,11.3,1.43,601),
    ],
    2023:[
        (45404,199.1,88.6,215374,14.8,1.57,288),
        (45374,195.6,96.5,331065,53.3,2.72,443),
        (53016,196.5,102.4,318542,18.4,1.52,425),
        (50476,187.9,97.2,395599,12.9,1.72,516),
        (48997,189.9,90.4,397497,13.1,1.78,480),
        (53516,196.3,105.4,448478,9.7,1.51,548),
        (55702,214.6,107.2,414761,13.3,1.58,486),
        (45197,210.7,85.6,368156,14.6,1.64,422),
        (43772,202.4,84.1,317000,11.0,1.40,553),
        (36171,191.7,67.8,270363,11.6,1.44,620),
        (36688,190.7,70.2,289635,11.8,1.40,612),
        (38484,194.1,73.4,313693,11.9,1.50,632),
    ],
    2024:[
        (48902,202.8,94.8,227618,15.5,1.65,301),
        (48206,203.3,102.5,367781,55.9,2.86,465),
        (57072,202.2,110.6,355778,19.3,1.60,446),
        (54314,197.5,104.4,446354,13.5,1.81,542),
        (51886,194.6,95.8,448594,13.8,1.87,504),
        (58533,200.9,115.8,448577,10.2,1.59,576),
        (57912,221.4,111.6,468212,14.0,1.66,510),
        (47663,216.4,89.6,395496,15.3,1.72,443),
        (47033,207.7,90.4,351711,11.5,1.47,580),
        (39257,191.1,73.2,289134,12.2,1.51,651),
        (40493,200.6,77.8,309861,12.4,1.47,642),
        (42273,199.3,81.2,323701,12.5,1.57,663),
    ],
    2025:[
        (48512,209.6,95.6,235575,16.2,1.73,312),
        (48645,201.5,103.6,365708,58.6,3.00,487),
        (60344,208.9,116.4,354337,20.2,1.68,468),
        (56516,199.2,108.6,427824,14.2,1.90,569),
        (53938,198.6,99.4,448643,14.5,1.96,529),
        (59617,201.7,117.6,466805,10.7,1.67,605),
        (58585,225.7,112.9,479510,14.7,1.74,535),
        (49682,220.2,95.6,391797,16.1,1.81,465),
        (47514,212.8,91.5,333353,12.1,1.54,609),
        (39055,193.0,74.2,295041,12.8,1.59,683),
        (41397,198.9,79.5,320560,13.0,1.54,674),
        (42769,202.1,83.8,340872,13.1,1.65,695),
    ],
}

# ── 데이터 로드 ───────────────────────────────────────────────
@st.cache_data
def load_2021():
    candidates = [
        'data/power_estimate_full_2021.csv',
        '../data/power_estimate_full_2021.csv',
        'power_estimate_full_2021.csv',
    ]
    for path in candidates:
        if os.path.exists(path):
            df = pd.read_csv(path, encoding='utf-8-sig')
            return df
    return None

def get_monthly_2021(df):
    """2021 실제 데이터 → 월별 집계"""
    result = []
    for m in range(1, 13):
        sub = df[df['월'] == m]
        working = sub[sub['공장인원'] > 0]
        season  = SEASON_MAP[m]
        tariff  = TARIFF[season]
        kwh     = round(sub['추정사용전력량'].sum(), 1)
        peak_max= round(sub['15분'].max(), 1)
        peak_avg= round(sub['15분'].mean(), 1)
        prod    = int(sub['생산량'].sum())
        man_max = round(sub['공장인원'].max(), 1)
        man_avg = round(working['공장인원'].mean(), 2) if len(working) > 0 else 0.0
        work_h  = int((sub['공장인원'] > 0).sum())
        usage_fee = round(kwh * tariff)
        basic_fee = round(peak_max * BASIC_RATE)
        result.append({
            'm': m, 'season': season,
            'kwh': kwh, 'peak_max': peak_max, 'peak_avg': peak_avg,
            'prod': prod, 'man_max': man_max, 'man_avg': man_avg,
            'work_hours': work_h,
            'usage_fee': usage_fee, 'basic_fee': basic_fee,
            'total_fee': usage_fee + basic_fee,
        })
    return pd.DataFrame(result)

def get_monthly_demo(year):
    """2022~2025 시연용 데이터 → 월별 집계 DataFrame"""
    rows = DEMO_DATA[year]
    result = []
    for m, (kwh, pk_max, pk_avg, prod, man_max, man_avg, work_h) in enumerate(rows, 1):
        season    = SEASON_MAP[m]
        tariff    = TARIFF[season]
        usage_fee = round(kwh * tariff)
        basic_fee = round(pk_max * BASIC_RATE)
        result.append({
            'm': m, 'season': season,
            'kwh': kwh, 'peak_max': pk_max, 'peak_avg': pk_avg,
            'prod': prod, 'man_max': man_max, 'man_avg': man_avg,
            'work_hours': work_h,
            'usage_fee': usage_fee, 'basic_fee': basic_fee,
            'total_fee': usage_fee + basic_fee,
        })
    return pd.DataFrame(result)

def get_monthly_df(year, df_2021):
    if year == 2021 and df_2021 is not None:
        return get_monthly_2021(df_2021)
    elif year in DEMO_DATA:
        return get_monthly_demo(year)
    return None

def get_grade(peak, thr):
    if peak >= thr:          return "초과", "#DC2626"
    if peak >= thr * 0.92:   return "위험", "#EA580C"
    if peak >= thr * 0.80:   return "경고", "#D97706"
    if peak >= thr * 0.65:   return "주의", "#2563EB"
    return                          "양호", "#059669"

def bar_color(season):
    if season == "여름":  return "rgba(234,88,12,0.75)"
    if season == "겨울":  return "rgba(37,99,235,0.65)"
    return                       "rgba(5,150,105,0.70)"

# ══════════════════════════════════════════════════════════════
def render():
# ══════════════════════════════════════════════════════════════

    df_2021 = load_2021()

    # ── 사이드바 ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='background:#1E293B;color:#fff;border-radius:8px;"
            "padding:10px 14px;margin-bottom:14px;font-size:13px;"
            "font-weight:700;'>⚡ 전력 조회 — 조회 조건</div>",
            unsafe_allow_html=True)

        # 조회 모드
        mode = st.radio(
            "조회 방식",
            ["📅 월별 단일 조회", "📆 기간 범위 조회"],
            key="t2_mode",
            help="월별: 특정 달 하나를 딱 찍어서 확인\n"
                 "범위: 연도를 넘나드는 기간 조회")

        st.divider()

        if mode == "📅 월별 단일 조회":
            st.markdown("**조회 연월**")
            c1, c2 = st.columns(2)
            with c1:
                year_m = st.selectbox(
                    "연도", [2021,2022,2023,2024,2025],
                    key="t2_year_m",
                    help="2021년=실제 KAMP 데이터\n2022~2025=시연용 임의 데이터")
            with c2:
                month_m = st.selectbox(
                    "월", range(1,13), index=6,
                    format_func=lambda x: f"{x}월",
                    key="t2_month_m")
        else:
            st.markdown("**시작 연월**")
            c1, c2 = st.columns(2)
            with c1:
                year_from = st.selectbox(
                    "연도", [2021,2022,2023,2024,2025],
                    index=3, key="t2_yf")
            with c2:
                month_from = st.selectbox(
                    "월", range(1,13), index=9,
                    format_func=lambda x: f"{x}월",
                    key="t2_mf")
            st.markdown("**종료 연월**")
            c3, c4 = st.columns(2)
            with c3:
                year_to = st.selectbox(
                    "연도", [2021,2022,2023,2024,2025],
                    index=4, key="t2_yt")
            with c4:
                month_to = st.selectbox(
                    "월", range(1,13), index=2,
                    format_func=lambda x: f"{x}월",
                    key="t2_mt")

        st.divider()
        thr = st.number_input(
            "피크 임계값 (kW)",
            min_value=50, max_value=300, value=190,
            key="t2_thr",
            help="이 값 이상 피크 발생 시 위험 등급으로 강조됩니다\n"
                 "계약 전력 또는 DR 발령 기준에 맞게 설정하세요")

        st.divider()
        query_btn = st.button(
            "⚡ 전력 데이터 조회",
            type="primary",
            use_container_width=True,
            key="t2_btn")

        st.divider()
        st.markdown(
            "<div style='font-size:10px;color:#94A3B8;line-height:1.8;'>"
            "<b style='color:#475569;'>2021년</b> 실제 KAMP 데이터<br>"
            "<b style='color:#475569;'>2022~2025년</b> 시연용 임의 데이터<br><br>"
            "<b style='color:#475569;'>데이터 출처</b><br>"
            "power_estimate_full_2021.csv<br>"
            "OperationResult (DB)</div>",
            unsafe_allow_html=True)

    # ── 페이지 헤더 ───────────────────────────────────────────
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;"
        "margin-bottom:2px;'>"
        "<div style='background:#1D4ED8;color:#fff;font-weight:700;"
        "font-size:13px;padding:4px 10px;border-radius:6px;'>EP</div>"
        "<span style='font-size:20px;font-weight:700;'>전력 조회</span>"
        "</div>",
        unsafe_allow_html=True)
    st.caption("연·월 단위 전력 실적 조회 | 소비량 · 피크 · 인원 · 전기요금")

    if df_2021 is None:
        st.warning(
            "⚠️ power_estimate_full_2021.csv 파일을 찾을 수 없습니다. "
            "2021년 조회 시 실제 데이터 대신 집계 요약값이 사용됩니다.",
            icon="⚠️")

    # ── 초기 안내 ─────────────────────────────────────────────
    if not query_btn and "tab2_result" not in st.session_state:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;color:#94A3B8;'>"
            "<div style='font-size:52px;margin-bottom:16px;'>⚡</div>"
            "<div style='font-size:16px;font-weight:500;color:#475569;"
            "margin-bottom:10px;'>조회 조건을 설정하고 조회 버튼을 눌러주세요</div>"
            "<div style='font-size:13px;line-height:2.0;'>"
            "<b>월별 단일 조회</b> — 특정 달 하나를 딱 찍어서 확인<br>"
            "총 전력량 · 최대/평균 피크 · 인원 min~max · 전기요금<br><br>"
            "<b>기간 범위 조회</b> — 연도를 넘나드는 범위 선택 가능<br>"
            "예: 2024년 10월 ~ 2025년 3월"
            "</div></div>",
            unsafe_allow_html=True)
        return

    # ── 조회 실행 ─────────────────────────────────────────────
    if query_btn:
        with st.spinner("데이터 조회 중..."):
            if mode == "📅 월별 단일 조회":
                df_m = get_monthly_df(year_m, df_2021)
                if df_m is not None:
                    row = df_m[df_m['m'] == month_m].iloc[0]
                    # 전월 데이터
                    prev_row = None
                    if month_m > 1:
                        prev_row = df_m[df_m['m'] == month_m - 1].iloc[0]
                    elif year_m > 2021:
                        df_prev_year = get_monthly_df(year_m - 1, df_2021)
                        if df_prev_year is not None:
                            prev_row = df_prev_year[df_prev_year['m'] == 12].iloc[0]

                    st.session_state["tab2_result"] = {
                        "mode": "single",
                        "year": year_m, "month": month_m,
                        "row": row, "prev_row": prev_row,
                        "thr": thr,
                    }

            else:  # 기간 범위
                rows = []
                for y in range(year_from, year_to + 1):
                    df_y = get_monthly_df(y, df_2021)
                    if df_y is None:
                        continue
                    m_start = month_from if y == year_from else 1
                    m_end   = month_to   if y == year_to   else 12
                    for _, r in df_y[
                        (df_y['m'] >= m_start) & (df_y['m'] <= m_end)
                    ].iterrows():
                        rows.append({**r.to_dict(), 'year': y})
                st.session_state["tab2_result"] = {
                    "mode": "range",
                    "year_from": year_from, "month_from": month_from,
                    "year_to": year_to,     "month_to": month_to,
                    "rows": rows, "thr": thr,
                }

    if "tab2_result" not in st.session_state:
        return

    res = st.session_state["tab2_result"]
    thr = res["thr"]

    # ══════════════════════════════════════════════════════════
    # 월별 단일 조회 결과
    # ══════════════════════════════════════════════════════════
    if res["mode"] == "single":
        year    = res["year"]
        month   = res["month"]
        row     = res["row"]
        prev    = res["prev_row"]
        src_label = "실제 KAMP 데이터" if year == 2021 else "시연용 임의 데이터"
        season  = SEASON_MAP[month]
        tariff  = TARIFF[season]
        grade_label, grade_color = get_grade(row['peak_max'], thr)

        # 결과 헤더
        col_h1, col_h2 = st.columns([4, 1])
        with col_h1:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;"
                f"margin-bottom:4px;'>"
                f"<span style='font-size:18px;font-weight:700;'>"
                f"📅 {year}년 {MONTH_KR[month]} 전력 실적</span>"
                f"<span style='font-size:11px;color:#94A3B8;'>"
                f"{season} · {src_label} · 임계값 {thr}kW</span>"
                f"</div>",
                unsafe_allow_html=True)
        with col_h2:
            st.markdown(
                f"<div style='background:{grade_color}20;border:1px solid "
                f"{grade_color}40;border-radius:8px;padding:6px 14px;"
                f"text-align:center;font-size:13px;font-weight:700;"
                f"color:{grade_color};'>{grade_label}</div>",
                unsafe_allow_html=True)

        # KPI 5개
        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric(
            "총 전력 소비량",
            f"{row['kwh']:,.0f} kWh",
            delta=f"{row['kwh']/1000:.1f} MWh",
            help="월 추정사용전력량 합산")
        k2.metric(
            "최대 피크",
            f"{row['peak_max']:.1f} kW",
            delta=f"평균 {row['peak_avg']:.1f}kW",
            help="15분 최대수요전력 최대값\n연간 기본요금 결정 기준")
        k3.metric(
            "공장 인원 (min~max)",
            f"0 ~ {row['man_max']:.1f} 명",
            delta=f"가동시 평균 {row['man_avg']:.2f}명",
            help="min=0: 비가동(심야·휴일)\n"
                 "max: 피크 시간대 최대 투입 인원\n"
                 "avg: 인원>0 시간대만 평균")
        k4.metric(
            "총 생산량",
            f"{row['prod']/10000:.1f} 만개",
            delta=f"집약도 {row['kwh']/row['prod']:.4f} kWh/개" if row['prod'] > 0 else "",
            help="볼트·너트 총 생산량")
        k5.metric(
            "추정 전기요금",
            f"{row['total_fee']/10000:.1f} 만원",
            delta=f"사용 {row['usage_fee']/10000:.1f} + 기본 {row['basic_fee']/10000:.1f}",
            help=f"사용량요금({tariff}원/kWh × {row['kwh']:,.0f}kWh)\n"
                 f"+ 기본요금({row['peak_max']:.0f}kW × {BASIC_RATE:,}원)\n"
                 f"기후환경요금 미포함 추정치")

        st.divider()

        # 인원 현황 카드
        with st.container(border=True):
            st.markdown("**👷 공장 인원 현황**")
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("최솟값 (비가동)", "0 명",
                        help="심야·주말·공휴일 비가동 시간대")
            mc2.metric("가동 시 평균",    f"{row['man_avg']:.2f} 명",
                        help=f"가동 {row['work_hours']}시간 기준\n"
                             f"(인원>0 시간대만 집계)")
            mc3.metric("최댓값 (피크 시)", f"{row['man_max']:.1f} 명",
                        help="이 달 가장 많이 투입된 시간대 인원")
            mc4.metric("가동 시간",       f"{row['work_hours']}h / 744h",
                        help="744시간 = 31일 기준 월 전체")

            # 가동률 바
            ratio = round(row['work_hours'] / 744 * 100)
            st.markdown(
                f"<div style='display:flex;align-items:center;"
                f"gap:10px;margin-top:8px;font-size:12px;'>"
                f"<span style='color:#475569;min-width:80px;'>"
                f"가동 시간 비율</span>"
                f"<div style='flex:1;height:10px;background:#F1F5F9;"
                f"border-radius:5px;overflow:hidden;'>"
                f"<div style='height:10px;width:{ratio}%;"
                f"background:#059669;border-radius:5px;'></div></div>"
                f"<span style='font-weight:700;color:#059669;'>"
                f"{ratio}% ({row['work_hours']}h)</span></div>",
                unsafe_allow_html=True)
            st.caption("※ min=0은 비가동(심야·주말) 시간대로 정상입니다")

        st.divider()

        # 시간대별 패턴 차트 + 요금 구조
        col_c, col_f = st.columns([3, 2])

        with col_c:
            st.markdown("**📊 시간대별 피크 패턴 (월 평균)**")
            if year == 2021 and df_2021 is not None:
                sub   = df_2021[df_2021['월'] == month]
                hourly_avg = sub.groupby('시간')['15분'].mean().reset_index()
                hours = hourly_avg['시간'].tolist()
                peaks = hourly_avg['15분'].tolist()
            else:
                # 임의 데이터 — 시간대 패턴 시뮬레이션
                hours = list(range(24))
                avg   = row['peak_avg']
                peaks = []
                for h in hours:
                    if   0 <= h <= 6:   v = avg * 0.48
                    elif h in [7,8]:    v = avg * 0.78
                    elif 9 <= h <= 12:  v = avg * 1.05
                    elif h == 13:       v = avg * 0.75
                    elif 14 <= h <= 17: v = avg * 1.08
                    elif h in [18,19]:  v = avg * 0.90
                    elif h in [20,21]:  v = avg * 0.68
                    else:               v = avg * 0.52
                    peaks.append(round(v, 1))

            # TOU 색상
            def tou_color(h, m):
                if m in [6,7,8]:
                    if 10<=h<=17: return "rgba(220,38,38,0.70)"
                    if h<=5 or h>=22: return "rgba(37,99,235,0.55)"
                    return "rgba(217,119,6,0.65)"
                elif m in [11,12,1,2]:
                    if h in [9,10,17,18,19]: return "rgba(220,38,38,0.70)"
                    if h<=5 or h>=22: return "rgba(37,99,235,0.55)"
                    return "rgba(217,119,6,0.65)"
                else:
                    if 10<=h<=17: return "rgba(217,119,6,0.65)"
                    if h<=5 or h>=22: return "rgba(37,99,235,0.55)"
                    return "rgba(217,119,6,0.50)"

            colors = [tou_color(h, month) for h in hours]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=hours, y=peaks,
                marker_color=colors,
                hovertemplate="<b>%{x}시</b><br>평균 피크: %{y:.1f} kW<extra></extra>"))
            fig.add_hline(
                y=row['peak_max'], line_dash="dash",
                line_color="#DC2626", line_width=1.2,
                annotation_text=f"최대 {row['peak_max']}kW",
                annotation_font_size=10,
                annotation_position="bottom right")
            fig.update_layout(
                height=220,
                margin=dict(l=0, r=0, t=8, b=0),
                plot_bgcolor="#F8FAFC",
                paper_bgcolor="#FFFFFF",
                xaxis=dict(title="시간", gridcolor="#E2E8F0",
                           tickmode="linear", dtick=2,
                           tickfont=dict(size=10)),
                yaxis=dict(title="피크 (kW)", gridcolor="#E2E8F0",
                           tickfont=dict(size=10)),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "빨강=최대부하(155원) · 노랑=중간부하(121.5원) · 파랑=경부하(95.7원)\n"
                + ("실측 시간별 평균값" if year==2021 else "월별 통계 기반 시뮬레이션"))

        with col_f:
            st.markdown("**💰 전기요금 구조**")
            with st.container(border=True):
                fc1, fc2 = st.columns(2)
                fc1.metric("사용량 요금",
                            f"{row['usage_fee']/10000:.1f}만원",
                            help=f"{tariff}원/kWh × {row['kwh']:,.0f}kWh")
                fc2.metric("기본요금",
                            f"{row['basic_fee']/10000:.1f}만원",
                            help=f"{row['peak_max']:.0f}kW × {BASIC_RATE:,}원")
                st.metric("추정 합계",
                           f"{row['total_fee']/10000:.1f} 만원")

                # 비율 바
                u_pct = round(row['usage_fee'] / row['total_fee'] * 100)
                b_pct = 100 - u_pct
                st.markdown(
                    f"<div style='height:10px;border-radius:5px;"
                    f"overflow:hidden;display:flex;margin-top:4px;'>"
                    f"<div style='width:{u_pct}%;background:#2563EB;'></div>"
                    f"<div style='width:{b_pct}%;background:#EA580C;'></div>"
                    f"</div>"
                    f"<div style='display:flex;gap:12px;margin-top:5px;"
                    f"font-size:10px;color:#94A3B8;'>"
                    f"<span>🔵 사용량 {u_pct}%</span>"
                    f"<span>🟠 기본요금 {b_pct}%</span></div>",
                    unsafe_allow_html=True)
            st.caption("※ 기후환경요금·연료비조정요금 미포함 추정치")

            # 전월 비교
            if prev is not None:
                st.markdown("**📈 전월 대비**")
                prev_season = SEASON_MAP[prev['m']]
                prev_tariff = TARIFF[prev_season]

                def diff_md(curr, prev_val, fmt=".0f", unit=""):
                    d    = curr - prev_val
                    pct  = d / prev_val * 100 if prev_val != 0 else 0
                    icon = "▲" if d > 0 else "▼" if d < 0 else "━"
                    col  = "#DC2626" if d > 0 else "#059669" if d < 0 else "#94A3B8"
                    return (f"<span style='color:{col};font-weight:700;'>"
                            f"{icon}{abs(pct):.1f}%</span>")

                rows_cmp = [
                    ("소비량", f"{prev['kwh']:,.0f}", f"{row['kwh']:,.0f}", "kWh",
                     row['kwh'], prev['kwh']),
                    ("최대 피크", f"{prev['peak_max']:.1f}", f"{row['peak_max']:.1f}", "kW",
                     row['peak_max'], prev['peak_max']),
                    ("생산량", f"{prev['prod']/10000:.1f}", f"{row['prod']/10000:.1f}", "만개",
                     row['prod'], prev['prod']),
                    ("추정 요금", f"{prev['total_fee']/10000:.1f}", f"{row['total_fee']/10000:.1f}", "만원",
                     row['total_fee'], prev['total_fee']),
                ]
                tbl_html = "<table style='width:100%;font-size:11px;border-collapse:collapse;'>"
                for label, v_prev, v_curr, unit, curr, pv in rows_cmp:
                    d    = curr - pv
                    pct  = d / pv * 100 if pv != 0 else 0
                    icon = "▲" if d > 0 else "▼" if d < 0 else "━"
                    col  = "#DC2626" if d > 0 else "#059669" if d < 0 else "#94A3B8"
                    tbl_html += (
                        f"<tr style='border-bottom:1px solid #F1F5F9;'>"
                        f"<td style='padding:5px 4px;color:#475569;'>{label}</td>"
                        f"<td style='padding:5px 4px;color:#94A3B8;font-family:monospace;'>{v_prev}</td>"
                        f"<td style='padding:5px 4px;color:#475569;'>→</td>"
                        f"<td style='padding:5px 4px;font-family:monospace;font-weight:700;'>{v_curr} {unit}</td>"
                        f"<td style='padding:5px 4px;'>"
                        f"<span style='color:{col};font-weight:700;'>{icon}{abs(pct):.1f}%</span>"
                        f"</td></tr>")
                tbl_html += "</table>"
                st.markdown(tbl_html, unsafe_allow_html=True)

        st.divider()

        # CSV 다운로드
        dl_df = pd.DataFrame({
            "항목": ["연월","계절","총 소비량(kWh)","최대 피크(kW)",
                     "평균 피크(kW)","총 생산량(개)","에너지집약도(kWh/개)",
                     "인원 min","인원 max","가동시 평균 인원(명)",
                     "가동 시간(h)","사용량요금(원)","기본요금(원)","추정합계(원)"],
            "값": [
                f"{year}년 {MONTH_KR[month]}",
                season,
                f"{row['kwh']:,.1f}",
                f"{row['peak_max']:.1f}",
                f"{row['peak_avg']:.1f}",
                f"{row['prod']:,}",
                f"{row['kwh']/row['prod']:.4f}" if row['prod']>0 else "0",
                "0",
                f"{row['man_max']:.1f}",
                f"{row['man_avg']:.2f}",
                f"{row['work_hours']}",
                f"{row['usage_fee']:,}",
                f"{row['basic_fee']:,}",
                f"{row['total_fee']:,}",
            ]
        })
        csv = dl_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "⬇ CSV 다운로드",
            data=csv.encode('utf-8-sig'),
            file_name=f"전력조회_{year}년_{month}월_올라운더.csv",
            mime="text/csv")

    # ══════════════════════════════════════════════════════════
    # 기간 범위 조회 결과
    # ══════════════════════════════════════════════════════════
    else:
        rows     = res["rows"]
        yf, mf   = res["year_from"], res["month_from"]
        yt, mt   = res["year_to"],   res["month_to"]
        span_label = f"{yf}년 {MONTH_KR[mf]} ~ {yt}년 {MONTH_KR[mt]}"

        if not rows:
            st.error("해당 기간의 데이터가 없습니다.")
            return

        total_kwh  = sum(r['kwh']       for r in rows)
        max_peak   = max(r['peak_max']  for r in rows)
        total_prod = sum(r['prod']       for r in rows)
        total_fee  = sum(r['total_fee']  for r in rows)
        avg_man_max= round(sum(r['man_max'] for r in rows) / len(rows), 1)
        peak_row   = next(r for r in rows if r['peak_max'] == max_peak)
        grade_label, grade_color = get_grade(max_peak, thr)

        # 헤더
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;"
            f"margin-bottom:4px;'>"
            f"<span style='font-size:18px;font-weight:700;'>"
            f"📆 {span_label} 전력 실적 ({len(rows)}개월)</span>"
            f"<span style='font-size:11px;color:#94A3B8;'>"
            f"임계값 {thr}kW</span></div>",
            unsafe_allow_html=True)

        # KPI 5개
        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("총 전력 소비량",
                   f"{total_kwh/1000:.1f} MWh",
                   delta=f"월평균 {total_kwh/len(rows)/1000:.1f}MWh")
        k2.metric("최대 피크",
                   f"{max_peak:.1f} kW",
                   delta=f"{peak_row['year']}년 {MONTH_KR[peak_row['m']]}",
                   help="기간 내 가장 높은 15분 최대수요전력")
        k3.metric("최대 인원 평균",
                   f"{avg_man_max:.1f} 명",
                   delta="월별 max 평균",
                   help="각 월 최대 투입 인원의 평균")
        k4.metric("총 생산량",
                   f"{total_prod/10000:.0f} 만개",
                   delta=f"집약도 {total_kwh/total_prod:.4f} kWh/개" if total_prod>0 else "")
        k5.metric("추정 전기요금 합계",
                   f"{total_fee/10000:.0f} 만원",
                   delta=f"월평균 {total_fee/len(rows)/10000:.1f}만원")

        st.divider()

        # 월별 추이 차트
        st.markdown("**📊 월별 전력 소비량 추이**")
        labels = [f"{r['year']}.{r['m']:02d}" for r in rows]
        kwhvals= [r['kwh'] for r in rows]
        colors = [bar_color(r['season']) for r in rows]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=labels, y=kwhvals,
            marker_color=colors,
            hovertemplate="<b>%{x}</b><br>소비량: %{y:,.0f} kWh<extra></extra>"))
        fig2.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#F8FAFC",
            paper_bgcolor="#FFFFFF",
            xaxis=dict(title="연월", gridcolor="#E2E8F0",
                       tickangle=-45, tickfont=dict(size=10)),
            yaxis=dict(title="소비량 (kWh)", gridcolor="#E2E8F0",
                       tickfont=dict(size=10)),
            showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("주황=여름 · 초록=봄가을 · 파랑=겨울")

        # 월별 상세 테이블
        st.markdown("**📋 월별 상세 내역**")
        tbl_rows = []
        for r in rows:
            g_label, g_color = get_grade(r['peak_max'], thr)
            tbl_rows.append({
                "연월":          f"{r['year']}년 {MONTH_KR[r['m']]}",
                "계절":          r['season'],
                "소비량(kWh)":   f"{r['kwh']:,.0f}",
                "최대피크(kW)":  f"{r['peak_max']:.1f}",
                "등급":          g_label,
                "인원 min~max":  f"0 ~ {r['man_max']:.1f}",
                "생산량(만개)":  f"{r['prod']/10000:.1f}",
                "추정요금(만원)":f"{r['total_fee']/10000:.1f}",
            })
        st.dataframe(
            pd.DataFrame(tbl_rows),
            use_container_width=True,
            hide_index=True)

        # CSV 다운로드
        dl_df2 = pd.DataFrame(tbl_rows)
        csv2 = dl_df2.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "⬇ CSV 다운로드",
            data=csv2.encode('utf-8-sig'),
            file_name=f"전력조회_{yf}-{mf}_{yt}-{mt}_올라운더.csv",
            mime="text/csv")

    st.caption("올라운더팀 | KAMP 자원 최적화 AI 프로젝트 2 | 2026")
