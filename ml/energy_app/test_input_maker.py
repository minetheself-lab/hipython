# ================================================================
# test_input_maker.py
# 역할  : Set A / B / C / Mixed 테스트용 CSV 파일 4개 생성
# 실행  : python test_input_maker.py
# 생성물: test_input_SetA.csv / SetB.csv / SetC.csv / mixed.csv
# ================================================================
import pandas as pd
import numpy as np
import os

np.random.seed(42)

DATE    = '2021-03-24'   # 테스트 날짜 (수요일, weekday=3)
WEEKDAY = 3
WEEKEND = 0
HOLIDAY = 0

# ── 날씨 기본값 (봄, 울산 3월) ───────────────────────────────
def make_weather(hour):
    temp = round(8 + 9 * np.sin((hour - 6) * np.pi / 12)
                 + np.random.normal(0, 0.3), 1)
    hum  = round(max(20, 58 - 12 * np.sin((hour - 6) * np.pi / 12)
                     + np.random.normal(0, 1.5)), 1)
    wind = round(max(0.2, 1.8 + np.random.normal(0, 0.4)), 1)
    rain = 0.0
    return temp, hum, wind, rain

# ── 생산 기본값 ───────────────────────────────────────────────
def make_production(hour):
    if hour <= 5:
        op = int(np.random.choice([2, 3], p=[0.6, 0.4]))
        out = int(max(0, np.random.normal(180, 70)))
    elif hour == 6:
        op, out = 0, 0
    elif hour in [7, 8]:
        op = 1; out = int(max(0, np.random.normal(800, 200)))
    elif hour in [9, 10, 11]:
        op = 1; out = int(max(0, np.random.normal(1400, 300)))
    elif hour == 12:
        op = 2; out = int(max(0, np.random.normal(100, 40)))
    elif hour in [13, 14, 15, 16]:
        op = 1; out = int(max(0, np.random.normal(1800, 350)))
    elif hour in [17, 18]:
        op = 2; out = int(max(0, np.random.normal(300, 80)))
    elif hour in [19, 20]:
        op = 1; out = int(max(0, np.random.normal(1600, 300)))
    else:
        op = 2; out = int(max(0, np.random.normal(130, 60)))
    return op, out

# ── 공통 행 생성 ──────────────────────────────────────────────
def base_row(hour):
    t, hu, w, r = make_weather(hour)
    op, out     = make_production(hour)
    return {
        'Date': DATE, 'hour': hour,
        'temperature': t, 'humidity': hu,
        'windspeed': w, 'rainfall': r,
        'op_code': op, 'output': out,
        'weekday': WEEKDAY, 'weekend': WEEKEND, 'holiday': HOLIDAY
    }

# ── Set A: 날짜·요일만, 날씨·생산 NaN ─────────────────────────
rows_a = []
for h in range(24):
    r = base_row(h)
    r['temperature'] = None
    r['humidity']    = None
    r['windspeed']   = None
    r['rainfall']    = None
    r['op_code']     = None
    r['output']      = None
    rows_a.append(r)

# ── Set B: 날짜+날씨, 생산 NaN ────────────────────────────────
rows_b = []
for h in range(24):
    r = base_row(h)
    r['op_code'] = None
    r['output']  = None
    rows_b.append(r)

# ── Set C: 전부 있음 ──────────────────────────────────────────
rows_c = [base_row(h) for h in range(24)]

# ── Mixed: A(0~7) + B(8~15) + C(16~23) ───────────────────────
rows_mixed = []
for h in range(24):
    r = base_row(h)
    if h <= 7:       # Set A 구간
        r['temperature'] = None; r['humidity'] = None
        r['windspeed']   = None; r['rainfall'] = None
        r['op_code']     = None; r['output']   = None
    elif h <= 15:    # Set B 구간
        r['op_code'] = None; r['output'] = None
    # else: Set C 그대로
    rows_mixed.append(r)

# ── CSV 저장 ──────────────────────────────────────────────────
os.makedirs('./test_data', exist_ok=True)

files = {
    './test_data/test_input_SetA.csv':   rows_a,
    './test_data/test_input_SetB.csv':   rows_b,
    './test_data/test_input_SetC.csv':   rows_c,
    './test_data/test_input_mixed.csv':  rows_mixed,
}

COLS = ['Date','hour','temperature','humidity','windspeed','rainfall',
        'op_code','output','weekday','weekend','holiday']

for path, rows in files.items():
    df = pd.DataFrame(rows, columns=COLS)
    df.to_csv(path, index=False, encoding='utf-8-sig')
    set_name = path.split('_')[-1].replace('.csv','')
    nan_cols  = df.columns[df.isnull().any()].tolist()
    print(f"✅ {path}")
    print(f"   {len(df)}행 × {len(df.columns)}컬럼 | NaN 컬럼: {nan_cols if nan_cols else '없음'}")

print("\n생성 완료! → test_data/ 폴더 확인")
print("다음: python test_db_insert.py")
