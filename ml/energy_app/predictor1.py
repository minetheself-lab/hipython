# ================================================================
# predictor1.py
# 역할  : DB 11개 컬럼 → 22개 피처 자동 생성 → XGBoost 예측
# 의존  : energy_pipeline_v4.pkl (같은 폴더 또는 models/ 안)
# 실행  : python predictor1.py  (단독 테스트)
# ================================================================

import os
import sqlite3
import joblib
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ── 상수 정의 ─────────────────────────────────────────────────
SMP_2021 = {
    1: 70.47,  2: 75.25,  3: 83.78,  4: 75.97,
    5: 78.93,  6: 82.72,  7: 87.04,  8: 93.41,
    9: 98.21, 10:107.53, 11:126.83, 12:142.46
}

TARIFF = {  # 계절별 전력량 요금 원/kWh
    'summer': 191.6,   # 6~8월
    'winter': 109.8,   # 11~2월
    'other':  167.2,   # 봄/가을
}

WORKER_MEAN = {  # 생산구분별 평균 공장인원 (훈련 데이터 통계)
    0: 0.00, 1: 0.72, 2: 0.69, 3: 1.81, 4: 6.34
}

# pkl 탐색 경로 (같은 폴더 우선, 없으면 models/ 서브폴더)
_PKL_CANDIDATES = [
    'energy_pipeline_v4.pkl',
    'models/energy_pipeline_v4.pkl',
    os.path.join(os.path.dirname(__file__), 'energy_pipeline_v4.pkl'),
    os.path.join(os.path.dirname(__file__), 'models', 'energy_pipeline_v4.pkl'),
    # v3도 fallback으로 지원
    'energy_pipeline_v3.pkl',
    'models/energy_pipeline_v3.pkl',
]

_pipeline = None  # 모듈 수준 캐시

def _load_pipeline():
    """pkl 파일 로드 (한 번만 로드 후 캐시)"""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    for path in _PKL_CANDIDATES:
        if os.path.exists(path):
            print(f"[predictor1] pkl 로드: {path}")
            _pipeline = joblib.load(path)
            return _pipeline
    raise FileNotFoundError(
        "pkl 파일을 찾을 수 없습니다.\n"
        "energy_pipeline_v4.pkl 또는 models/energy_pipeline_v4.pkl 경로를 확인하세요."
    )

# ── TOU 구간 계산 ─────────────────────────────────────────────
def _get_tou(month: int, hour: int, is_holiday: int, is_weekend: int):
    """
    TOU 구간(bucket)과 단가(price) 반환
    0=경부하(95.7), 1=중간(121.5), 2=최대(155.0)
    """
    if is_holiday or is_weekend:
        return 0, 95.7
    if month in [6, 7, 8]:            # 여름
        if hour in [10,11,12,13,14,15,16,17]:
            return 2, 155.0
        if hour in [22,23, 0, 1, 2, 3, 4, 5]:
            return 0, 95.7
        return 1, 121.5
    elif month in [11, 12, 1, 2]:     # 겨울
        if hour in [9, 10, 17, 18, 19]:
            return 2, 155.0
        if hour in [22,23, 0, 1, 2, 3, 4, 5]:
            return 0, 95.7
        return 1, 121.5
    else:                              # 봄/가을
        if hour in [10,11,12,13,14,15,16,17]:
            return 1, 121.5
        if hour in [22,23, 0, 1, 2, 3, 4, 5]:
            return 0, 95.7
        return 1, 121.5

# ── 피처 자동 생성 ────────────────────────────────────────────
def _build_features(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    DB 11개 컬럼 입력 → 22개 피처 자동 생성
    
    입력 컬럼 (대소문자 무관):
      Date, hour, temperature, humidity, windspeed, rainfall,
      op_code, output, weekday, weekend, holiday
    """
    df = df_input.copy()

    # ── 컬럼명 정규화 (영문 → 내부 한글/영문 통일) ──────────
    rename_map = {
        'Date': '날짜', 'date': '날짜',
        'temperature': '기온', 'temp': '기온',
        'humidity': '습도', 'hum': '습도',
        'windspeed': '풍속', 'wind': '풍속', 'wind_speed': '풍속',
        'rainfall': '강수량', 'rain': '강수량',
        'op_code': 'GMM생산구분',
        'output': '생산량',
        'weekday': 'weekday',
        'weekend': 'is_weekend',
        'holiday': 'is_holiday',
        'hour': '시간',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # ── 날짜 파싱 → m, d, day ────────────────────────────────
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['m']   = df['날짜'].dt.month
    df['d']   = df['날짜'].dt.day
    df['day'] = df['날짜'].dt.weekday + 1   # 1=월 ~ 7=일

    # ── NaN 감지 → 행별 적용 Set 자동 결정 ──────────────────
    # Set 판별: 결측치 채우기 전에 먼저 확인
    has_weather = df['기온'].notna() if '기온' in df.columns else pd.Series([False]*len(df), index=df.index)
    has_prod    = df['생산량'].notna() if '생산량' in df.columns else pd.Series([False]*len(df), index=df.index)

    df['_applied_set'] = [
        ('Set_C' if (w and p) else 'Set_B' if w else 'Set_A')
        for w, p in zip(has_weather, has_prod)
    ]

    # ── 결측치 처리 (Set 판별 후 채움) ───────────────────────
    df['강수량']   = df['강수량'].fillna(0)
    df['풍속']     = df['풍속'].fillna(0)
    df['기온']     = df['기온'].fillna(df['기온'].median() if df['기온'].notna().any() else 15.0)
    df['습도']     = df['습도'].fillna(df['습도'].median() if df['습도'].notna().any() else 60.0)
    df['생산량']   = df['생산량'].fillna(0)
    df['is_weekend'] = df['is_weekend'].fillna(0).astype(int)
    df['is_holiday'] = df['is_holiday'].fillna(0).astype(int)
    df['GMM생산구분'] = df['GMM생산구분'].fillna(0).astype(int)

    # ── 달력 파생변수 ─────────────────────────────────────────
    df['주간여부'] = df['시간'].apply(lambda h: 1 if 9 <= h <= 18 else 0)

    # ── 생산 파생변수 ─────────────────────────────────────────
    df['가동여부'] = (df['생산량'] > 0).astype(int)
    df['공장인원'] = df['GMM생산구분'].map(WORKER_MEAN).fillna(0)

    # ── furnace_on (열처리로 역추론) ──────────────────────────
    df['furnace_on'] = 0
    df.loc[df['가동여부'] == 1, 'furnace_on'] = 1
    # 생산량 0이지만 피크 정보가 없으므로 구분1~3이면 1로
    df.loc[df['GMM생산구분'].isin([1, 2, 3]), 'furnace_on'] = 1

    # ── 인건비 할증 ───────────────────────────────────────────
    df['인건비'] = df['시간'].apply(lambda h: 1.0 if 9 <= h <= 18 else 1.5)

    # ── 전기요금(계절) ────────────────────────────────────────
    def tariff(m):
        if m in [6, 7, 8]:    return TARIFF['summer']
        if m in [11,12,1,2]:  return TARIFF['winter']
        return TARIFF['other']
    df['전기요금(계절)'] = df['m'].apply(tariff)

    # ── TOU / SMP ─────────────────────────────────────────────
    tou_result = df.apply(
        lambda r: _get_tou(r['m'], r['시간'], r['is_holiday'], r['is_weekend']),
        axis=1
    )
    df['tou_bucket'] = [x[0] for x in tou_result]
    df['tou_price']  = [x[1] for x in tou_result]
    df['smp_land']   = df['m'].map(SMP_2021)

    # ── log1p 변환 (학습 때와 동일하게 적용) ─────────────────
    for col in ['생산량', '강수량', '공장인원', '풍속']:
        df[col] = np.log1p(df[col])

    return df

# ── 메인 예측 함수 ────────────────────────────────────────────
def predict(df_input: pd.DataFrame) -> dict:
    """
    피크 전력 예측

    Parameters
    ----------
    df_input : DataFrame
        DB에서 가져온 데이터 (11개 컬럼)
        필수: Date, hour, temperature, humidity, windspeed, rainfall,
              op_code, output, weekday, weekend, holiday

    Returns
    -------
    dict : {
        'Set_A': [{'peak15': float, 'peak30': float, 'peak45': float, 'peak60': float}, ...],
        'Set_B': [...],
        'Set_C': [...],
    }
    peak15=15분, peak30=30분, peak45=45분, peak60=60분 피크 예측값 (kW)
    """
    pipeline = _load_pipeline()
    models       = pipeline['models']
    feature_sets = pipeline['feature_sets']
    scalers      = pipeline['scalers']

    df = _build_features(df_input)

    results = {}
    target_map = {'15분': 'peak15', '30분': 'peak30', '45분': 'peak45', '60분': 'peak60'}

    for set_name, feat_cols in feature_sets.items():
        # 실제로 존재하는 컬럼만 사용
        valid_cols = [c for c in feat_cols if c in df.columns]
        if not valid_cols:
            continue

        X = df[valid_cols]

        # 스케일링 (Set별 scaler 적용)
        if set_name in scalers:
            try:
                X_scaled = scalers[set_name].transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values

        # 행별 결과 초기화
        row_results = [{'peak15': 0.0, 'peak30': 0.0, 'peak45': 0.0, 'peak60': 0.0}
                       for _ in range(len(df))]

        for target, y_key in target_map.items():
            if set_name in models.get(target, {}):
                model = models[target][set_name]
                try:
                    preds = model.predict(X if hasattr(model, 'n_estimators') else X_scaled)
                except Exception:
                    preds = model.predict(X_scaled)
                preds = np.maximum(preds, 0)   # 음수 방지
                for i, val in enumerate(preds):
                    row_results[i][y_key] = round(float(val), 2)

        results[set_name] = row_results

    return results

# ── Set_C DataFrame 반환 함수 ─────────────────────────────────
def predict_df(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Set_C 예측 결과를 DataFrame으로 반환

    Parameters
    ----------
    df_input : DataFrame
        predict()와 동일한 11개 컬럼 입력

    Returns
    -------
    DataFrame : 컬럼 구성
        hour   | peak15 | peak30 | peak45 | peak60
        (int)  | (float)| (float)| (float)| (float)

    사용 예시
    ---------
    df_result = predict_df(df_input)
    df_result['peak15']          # 15분 피크 Series
    df_result['peak15'].max()    # 최대 피크
    df_result.iloc[10]['peak15'] # 10번째 행 15분 피크
    """
    result = predict(df_input)
    set_c  = result.get('Set_C', [])

    if not set_c:
        return pd.DataFrame(columns=['feature_set', 'hour', 'peak15', 'peak30', 'peak45', 'peak60'])

    # hour 컬럼 추출 (입력 df에서)
    df_in = df_input.copy()
    # hour 컬럼명 정규화
    if 'hour' in df_in.columns:
        hours = df_in['hour'].values
    elif '시간' in df_in.columns:
        hours = df_in['시간'].values
    else:
        hours = list(range(len(set_c)))

    rows = []
    for i, r in enumerate(set_c):
        rows.append({
            'feature_set': 'Set_C',
            'hour':   int(hours[i]) if i < len(hours) else i,
            'peak15': r['peak15'],
            'peak30': r['peak30'],
            'peak45': r['peak45'],
            'peak60': r['peak60'],
        })

    return pd.DataFrame(rows)


# ── 입력 행별 자동 Set 감지 + 결과 붙여서 반환 ──────────────
def predict_with_input(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    입력 DataFrame의 NaN 패턴을 보고 행마다 Set_A/B/C 자동 선택 후
    입력 컬럼 + peak 결과 컬럼이 합쳐진 DataFrame 반환

    Set 자동 선택 기준 (행별):
        날씨 NaN + 생산 NaN → Set_A (달력만)
        날씨 있음 + 생산 NaN → Set_B (달력 + 날씨)
        날씨 있음 + 생산 있음 → Set_C (전체)

    반환 컬럼:
        입력 컬럼 전체 + applied_set + peak15 + peak30 + peak45 + peak60

    사용 예시
    ---------
    df_result = predict_with_input(df_input)

    # 결과 확인
    print(df_result[['Date','hour','applied_set','peak15','peak30','peak45','peak60']])

    # Set별 필터
    df_result[df_result['applied_set']=='Set_C']
    """
    pipeline     = _load_pipeline()
    models       = pipeline['models']
    feature_sets = pipeline['feature_sets']
    scalers      = pipeline['scalers']

    # _build_features 호출 (내부에서 _applied_set 컬럼 생성됨)
    df_feat = _build_features(df_input.copy())

    target_map = {'15분': 'peak15', '30분': 'peak30', '45분': 'peak45', '60분': 'peak60'}

    # 결과 컬럼 초기화
    df_feat['peak15'] = 0.0
    df_feat['peak30'] = 0.0
    df_feat['peak45'] = 0.0
    df_feat['peak60'] = 0.0

    # Set별로 그룹핑해서 예측
    for set_name, feat_cols in feature_sets.items():
        # 해당 Set에 해당하는 행 인덱스
        mask = df_feat['_applied_set'] == set_name
        if not mask.any():
            continue

        valid_cols = [c for c in feat_cols if c in df_feat.columns]
        if not valid_cols:
            continue

        X = df_feat.loc[mask, valid_cols]

        if set_name in scalers:
            try:
                X_scaled = scalers[set_name].transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values

        for target, peak_col in target_map.items():
            if set_name in models.get(target, {}):
                model = models[target][set_name]
                try:
                    preds = model.predict(
                        X if hasattr(model, 'n_estimators') else X_scaled
                    )
                except Exception:
                    preds = model.predict(X_scaled)
                preds = np.maximum(preds, 0)
                df_feat.loc[mask, peak_col] = np.round(preds, 2)

    # 반환: 입력 원본 컬럼 + applied_set + peak 컬럼
    input_cols = list(df_input.columns)
    out_cols   = input_cols + ['applied_set', 'peak15', 'peak30', 'peak45', 'peak60']

    # df_feat에서 applied_set, peak 컬럼 꺼내서 df_input에 붙이기
    df_out = df_input.copy().reset_index(drop=True)
    df_out['applied_set'] = df_feat['_applied_set'].values
    df_out['peak15']      = df_feat['peak15'].values
    df_out['peak30']      = df_feat['peak30'].values
    df_out['peak45']      = df_feat['peak45'].values
    df_out['peak60']      = df_feat['peak60'].values

    return df_out


# ── DB에서 날짜로 자동 조회 ───────────────────────────────────
def predict_from_db(db_path: str, date: str) -> dict:
    """
    DB의 WeatherForecast + Calendar + ElectricityTariff를 조합해
    해당 날짜 24시간 전체를 예측

    Parameters
    ----------
    db_path : str   예: 'db/PowerMgt.db'
    date    : str   예: '2021-07-05'

    Returns
    -------
    dict (predict() 동일 구조)
    """
    conn = sqlite3.connect(db_path)

    # 날짜 형식 통일
    date_obj  = pd.to_datetime(date)
    date_str  = date_obj.strftime('%Y-%m-%d')
    date_ymd  = date_obj.strftime('%Y%m%d')

    # WeatherForecast 조회
    wf = pd.read_sql_query(
        "SELECT * FROM WeatherForecast WHERE date = ?",
        conn, params=(date_str,)
    )
    if wf.empty:
        # date 컬럼이 YYYYMMDD 형식인 경우도 시도
        wf = pd.read_sql_query(
            "SELECT * FROM WeatherForecast WHERE date = ?",
            conn, params=(date_ymd,)
        )

    # Calendar 조회
    cal = pd.read_sql_query(
        "SELECT * FROM Calendar WHERE date = ? OR date = ?",
        conn, params=(date_str, date_ymd)
    )
    conn.close()

    if wf.empty:
        print(f"[predictor1] WeatherForecast에 {date} 데이터 없음 → 기본값으로 대체")
        # 기본값으로 24시간 생성
        hours = list(range(24))
        wf = pd.DataFrame({
            'date': [date_str] * 24,
            'hour': hours,
            'temperature': [20.0] * 24,
            'humidity':    [60.0] * 24,
            'windspeed':   [ 2.0] * 24,
            'rainfall':    [ 0.0] * 24,
        })

    # Calendar에서 weekend/holiday 가져오기
    weekend = 0
    holiday = 0
    if not cal.empty:
        row = cal.iloc[0]
        weekend = int(row.get('weekend', 0))
        holiday = int(row.get('holiday', 0))
    else:
        wd = date_obj.weekday()
        weekend = 1 if wd >= 5 else 0

    # 컬럼 이름 통일 (DB 컬럼명이 다를 수 있음)
    col_map = {
        'temp': 'temperature', 'hum': 'humidity',
        'wind': 'windspeed', 'rain': 'rainfall',
    }
    wf = wf.rename(columns=col_map)

    # 예측용 DataFrame 조립
    df_pred = pd.DataFrame({
        'Date':        [date_str] * len(wf),
        'hour':        wf['hour'].values,
        'temperature': wf.get('temperature', pd.Series([20.0]*len(wf))).values,
        'humidity':    wf.get('humidity',    pd.Series([60.0]*len(wf))).values,
        'windspeed':   wf.get('windspeed',   pd.Series([ 2.0]*len(wf))).values,
        'rainfall':    wf.get('rainfall',    pd.Series([ 0.0]*len(wf))).values,
        'op_code':     [0] * len(wf),    # 비가동 기본값 (호출부에서 덮어씌움)
        'output':      [0] * len(wf),
        'weekday':     [date_obj.weekday() + 1] * len(wf),
        'weekend':     [weekend] * len(wf),
        'holiday':     [holiday] * len(wf),
    })

    return predict(df_pred)

# ── 단독 테스트 ───────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("predictor1.py — 단독 테스트")
    print("=" * 60)

    # 테스트용 샘플 데이터 (2021-07-05 10시, 고생산)
    test_data = pd.DataFrame([{
        'Date':        '2021-07-05',
        'hour':        10,
        'temperature': 28.5,
        'humidity':    72.0,
        'windspeed':    2.1,
        'rainfall':     0.0,
        'op_code':      1,      # 고생산
        'output':     500,
        'weekday':      1,      # 월요일
        'weekend':      0,
        'holiday':      0,
    }])

    print("\n[입력 데이터]")
    print(test_data.to_string(index=False))

    print("\n[예측 실행 중...]")
    try:
        result = predict(test_data)

        print("\n[예측 결과]")
        for set_name, rows in result.items():
            r = rows[0]
            print(f"  {set_name}: "
                  f"15분={r['peak15']:.1f}kW  "
                  f"30분={r['peak30']:.1f}kW  "
                  f"45분={r['peak45']:.1f}kW  "
                  f"60분={r['peak60']:.1f}kW")

        print("\n✅ predictor1.py 정상 작동")

        # ── predict_df() 테스트 ───────────────────────────────
        print("\n[predict_df() 테스트 — Set_C DataFrame]")
        df_result = predict_df(test_data)
        print(df_result.to_string(index=False))
        print(f"\n  peak15 값: {df_result['peak15'].values[0]} kW")
        print(f"  peak30 값: {df_result['peak30'].values[0]} kW")
        print("✅ predict_df() 정상 작동")

    except FileNotFoundError as e:
        print(f"\n❌ pkl 파일 없음: {e}")
        print("→ energy_pipeline_v4.pkl 파일을 이 폴더에 넣어주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    # ── predict_with_input() 테스트 ──────────────────────────
    print("\n[predict_with_input() 테스트 — NaN 자동 Set 감지]")

    # Set A: 날짜만 (날씨·생산 NaN)
    # Set B: 날씨만 있음 (생산 NaN)
    # Set C: 전부 있음
    mixed_data = pd.DataFrame([
        # Set A 구간 (0~2시: 날씨·생산 NaN)
        {'Date':'2021-07-05','hour':0,'temperature':None,'humidity':None,
         'windspeed':None,'rainfall':None,'op_code':None,'output':None,
         'weekday':1,'weekend':0,'holiday':0},
        {'Date':'2021-07-05','hour':1,'temperature':None,'humidity':None,
         'windspeed':None,'rainfall':None,'op_code':None,'output':None,
         'weekday':1,'weekend':0,'holiday':0},
        # Set B 구간 (9시: 날씨만 있음)
        {'Date':'2021-07-05','hour':9,'temperature':28.5,'humidity':72.0,
         'windspeed':2.1,'rainfall':0.0,'op_code':None,'output':None,
         'weekday':1,'weekend':0,'holiday':0},
        # Set C 구간 (10시: 전부 있음)
        {'Date':'2021-07-05','hour':10,'temperature':28.5,'humidity':72.0,
         'windspeed':2.1,'rainfall':0.0,'op_code':1,'output':500,
         'weekday':1,'weekend':0,'holiday':0},
    ])

    try:
        df_result = predict_with_input(mixed_data)
        print("\n[결과 DataFrame]")
        print(df_result[['Date','hour','applied_set','peak15','peak30','peak45','peak60']].to_string(index=True))
        print("\n✅ predict_with_input() 정상 작동")
        print("   → 0,1시: Set_A / 9시: Set_B / 10시: Set_C 자동 선택")
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback; traceback.print_exc()

    # DB 연동 테스트 (PowerMgt.db가 있을 때만)
    db_paths = ['db/PowerMgt.db', 'PowerMgt.db']
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n[DB 연동 테스트] {db_path}")
            try:
                result_db = predict_from_db(db_path, '2021-07-05')
                print(f"  Set_C 결과 (0시): {result_db.get('Set_C', [{}])[0]}")
                print("✅ DB 연동 정상")
            except Exception as e:
                print(f"❌ DB 오류: {e}")
            break
    else:
        print("\n[DB 테스트 생략] PowerMgt.db 파일을 찾을 수 없음")
        print("→ db/PowerMgt.db 경로에 파일을 배치하세요.")
