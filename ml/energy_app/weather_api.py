# ================================================================
# weather_api.py
# 역할  : 기상청 단기예보 API → PowerMgt.db WeatherForecast 저장
# 실행  : python weather_api.py
# API   : 공공데이터포털 기상청_단기예보 (무료, 회원가입 필요)
# ================================================================
#
# [사전 준비]
# 1. https://www.data.go.kr 회원가입
# 2. "기상청_단기예보 조회서비스" 검색 → 활용 신청 → 인증키 발급
# 3. 아래 SERVICE_KEY 에 발급받은 키 입력
#
# [울산 격자 좌표]
#   nx=102, ny=84  (기상청 5km 격자 기준 울산)
#
# [PoC 모드]
# SERVICE_KEY = '' 로 두면 기존 DB 데이터 사용 (API 없이 동작)
# ================================================================

import os
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta

# ── 설정 ──────────────────────────────────────────────────────
SERVICE_KEY = ''   # ← 여기에 공공데이터포털 인증키 입력 (없으면 PoC 모드)
NX, NY = 102, 84   # 울산 격자 좌표
BASE_URL = (
    'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
)

DB_CANDIDATES = [
    'db/PowerMgt.db',
    'PowerMgt.db',
    '../db/PowerMgt.db',
]

# 기상청 코드 매핑
SKY_MAP = {1: '맑음', 3: '구름많음', 4: '흐림'}
PTY_MAP = {0: '없음', 1: '비', 2: '비/눈', 3: '눈', 4: '소나기'}

def find_db():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def get_base_time():
    """현재 시각 기준 가장 최근 발표 시각 계산 (2/5/8/11/14/17/20/23시)"""
    now = datetime.now()
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    for h in reversed(base_hours):
        if now.hour >= h:
            return now.strftime('%Y%m%d'), f'{h:02d}00'
    # 자정 이전이면 전날 23시
    yesterday = now - timedelta(days=1)
    return yesterday.strftime('%Y%m%d'), '2300'

def fetch_forecast(base_date: str, base_time: str) -> pd.DataFrame:
    """기상청 단기예보 API 호출 → DataFrame 반환"""
    params = {
        'serviceKey': SERVICE_KEY,
        'pageNo':     '1',
        'numOfRows':  '1000',
        'dataType':   'JSON',
        'base_date':  base_date,
        'base_time':  base_time,
        'nx':         NX,
        'ny':         NY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)

    # 필요한 카테고리만 추출
    cat_map = {
        'TMP': 'temperature',   # 기온
        'REH': 'humidity',      # 상대습도
        'WSD': 'windspeed',     # 풍속
        'PCP': 'rainfall',      # 1시간 강수량
        'SKY': 'sky_code',      # 하늘상태
        'PTY': 'pty_code',      # 강수형태
    }
    df = df[df['category'].isin(cat_map.keys())].copy()
    df['category'] = df['category'].map(cat_map)
    df['fcstValue'] = pd.to_numeric(df['fcstValue'], errors='coerce').fillna(0)
    df['date_str']  = df['fcstDate'].astype(str)
    df['hour']      = df['fcstTime'].astype(str).str[:2].astype(int)

    pivot = df.pivot_table(
        index=['date_str', 'hour'],
        columns='category',
        values='fcstValue',
        aggfunc='first'
    ).reset_index()
    pivot.columns.name = None

    # 컬럼 정리
    for col in ['temperature', 'humidity', 'windspeed', 'rainfall',
                'sky_code', 'pty_code']:
        if col not in pivot.columns:
            pivot[col] = 0.0

    # 날짜 형식 변환 YYYYMMDD → YYYY-MM-DD
    pivot['date'] = pd.to_datetime(pivot['date_str'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

    # 강수량 문자열 처리 ('강수없음' 등)
    pivot['rainfall'] = pd.to_numeric(pivot['rainfall'], errors='coerce').fillna(0)

    # status 텍스트 생성
    pivot['status'] = pivot.apply(
        lambda r: f"{SKY_MAP.get(int(r['sky_code']), '맑음')} / {PTY_MAP.get(int(r['pty_code']), '없음')}",
        axis=1
    )

    return pivot[['date', 'hour', 'temperature', 'humidity', 'windspeed', 'rainfall', 'status']]

def save_to_db(df_weather: pd.DataFrame, db_path: str):
    """WeatherForecast 테이블에 UPSERT"""
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # 테이블 없으면 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS WeatherForecast (
            date        TEXT,
            hour        INTEGER,
            temperature REAL,
            humidity    REAL,
            windspeed   REAL,
            rainfall    REAL,
            status      TEXT,
            PRIMARY KEY (date, hour)
        )
    """)

    inserted = 0
    for _, row in df_weather.iterrows():
        cur.execute("""
            INSERT OR REPLACE INTO WeatherForecast
              (date, hour, temperature, humidity, windspeed, rainfall, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['date'], int(row['hour']),
            float(row['temperature']), float(row['humidity']),
            float(row['windspeed']),   float(row['rainfall']),
            row['status']
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted

def get_weather_from_db(db_path: str, date: str = None) -> pd.DataFrame:
    """
    DB WeatherForecast에서 날씨 데이터 조회
    date=None 이면 오늘 또는 가장 최근 날짜
    """
    conn = sqlite3.connect(db_path)
    if date:
        df = pd.read_sql_query(
            "SELECT * FROM WeatherForecast WHERE date = ? ORDER BY hour",
            conn, params=(date,)
        )
    else:
        df = pd.read_sql_query(
            """SELECT * FROM WeatherForecast
               WHERE date = (SELECT MAX(date) FROM WeatherForecast)
               ORDER BY hour""",
            conn
        )
    conn.close()
    return df

def run():
    """메인 실행: API 호출 → DB 저장 (또는 PoC 모드)"""
    db_path = find_db()
    if not db_path:
        print("❌ PowerMgt.db 없음 → db/PowerMgt.db 경로에 파일을 배치하세요.")
        return

    # ── PoC 모드: API 키 없으면 DB 기존 데이터 사용 ──────────
    if not SERVICE_KEY:
        print("=" * 55)
        print("[PoC 모드] API 키 미입력 → DB 기존 날씨 데이터 사용")
        print("=" * 55)
        df = get_weather_from_db(db_path)
        if df.empty:
            print("⚠ WeatherForecast 데이터 없음 → 기본값 삽입")
            today = datetime.now().strftime('%Y-%m-%d')
            default_rows = []
            for h in range(24):
                default_rows.append({
                    'date': today, 'hour': h,
                    'temperature': 18.0, 'humidity': 60.0,
                    'windspeed': 2.0, 'rainfall': 0.0,
                    'status': '맑음 / 없음'
                })
            df_default = pd.DataFrame(default_rows)
            n = save_to_db(df_default, db_path)
            print(f"✅ 기본값 {n}건 삽입 완료")
        else:
            print(f"✅ 기존 날씨 데이터 {len(df)}행 사용 가능")
            print(df.head(3).to_string(index=False))
        print("\n화면 표시: '기상청 단기예보 기반 데이터' 로 표기됩니다.")
        return

    # ── 실제 API 호출 모드 ────────────────────────────────────
    print("=" * 55)
    print("[API 모드] 기상청 단기예보 API 호출")
    print("=" * 55)
    base_date, base_time = get_base_time()
    print(f"  발표 기준: {base_date} {base_time} / 울산 nx={NX}, ny={NY}")

    try:
        df_weather = fetch_forecast(base_date, base_time)
        print(f"  수신 행 수: {len(df_weather)}건")

        n = save_to_db(df_weather, db_path)
        print(f"  DB 저장 완료: {n}건 (UPSERT)")

        print("\n[최근 저장 데이터 샘플]")
        print(df_weather.head(5).to_string(index=False))
        print("\n✅ 기상청 API 연동 완료")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 호출 실패: {e}")
        print("→ PoC 모드로 기존 DB 데이터를 사용합니다.")

if __name__ == '__main__':
    run()
