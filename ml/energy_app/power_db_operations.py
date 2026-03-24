# ================================================================
# power_db_operations.py  (수정본)
# 변경사항: get_prediction_variables()의 df.fillna('') 제거
#           → NaN 유지해야 predictor1.py Set 자동 감지 작동
# ================================================================

import requests
import datetime
import urllib3
import os
import pandas as pd
from urllib.parse import unquote
import sqlite3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_weather_info(target_dt=None):
    """
    지정된 일시(기본값: 현재 시각) 기준 날씨 정보 반환
    반환: dict 또는 None
    """
    db_path = './db/PowerMgt.db'

    if target_dt is None:
        target_dt = datetime.now()

    target_date = target_dt.strftime('%Y-%m-%d')
    target_hour = target_dt.hour

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = """
                SELECT * FROM WeatherForecast
                WHERE date = ? AND hour = ?
            """
            cur.execute(query, (target_date, target_hour))
            row = cur.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"DB Error: {e}")
        return None


def get_prediction_variables(target_date):
    """
    예측용 24시간 DataFrame 조회.
    OperationForecast가 12개 미만이면 OperationResult로 대체.

    반환 컬럼:
        Date, hour, temperature, humidity, windspeed, rainfall,
        op_code, output, weekday, weekend, holiday

    NaN 처리:
        날씨 없으면 temperature/humidity/windspeed/rainfall = NaN  → Set_B or Set_A
        생산 없으면 op_code/output = NaN                          → Set_A or Set_B
        전부 있으면                                               → Set_C
    """
    db_path = './db/PowerMgt.db'
    conn    = sqlite3.connect(db_path)

    query = f"""
    WITH RECURSIVE hours(h) AS (
        SELECT 0 UNION ALL SELECT h + 1 FROM hours WHERE h < 23
    ),
    ForecastCount AS (
        SELECT COUNT(*) as cnt FROM OperationForecast WHERE date = '{target_date}'
    ),
    ActualOp AS (
        SELECT
            h.h,
            CASE WHEN (SELECT cnt FROM ForecastCount) >= 12
                 THEN O.op_code ELSE R.op_code END AS op_code,
            CASE WHEN (SELECT cnt FROM ForecastCount) >= 12
                 THEN O.output  ELSE R.output  END AS output
        FROM hours h
        LEFT JOIN OperationForecast O ON O.date = '{target_date}' AND O.hour = h.h
        LEFT JOIN OperationResult   R ON R.date = '{target_date}' AND R.hour = h.h
    )
    SELECT
        '{target_date}' AS Date,
        h.h             AS hour,
        W.temperature, W.humidity, W.windspeed, W.rainfall,
        A.op_code,
        A.output,
        C.weekday, C.weekend, C.holiday
    FROM hours h
    LEFT JOIN ActualOp        A ON A.h    = h.h
    LEFT JOIN WeatherForecast W ON W.date = '{target_date}' AND W.hour = h.h
    LEFT JOIN Calendar        C ON C.date = '{target_date}'
    ORDER BY h.h ASC;
    """

    try:
        df = pd.read_sql_query(query, conn)

        # ── 수정 포인트 ────────────────────────────────────────
        # 기존: df = df.fillna('')  ← NaN을 ''로 바꿔 Set 감지 불가
        # 변경: NaN 그대로 유지 → predictor1.py가 자동으로 Set_A/B/C 선택
        # df = df.fillna('')  # 이 줄 제거

        return df

    except Exception as e:
        print(f"조회 중 오류 발생: {e}")
        return None
    finally:
        conn.close()


def get_daily_result(target_date):
    """
    OperationResult에서 특정 일자 레코드 조회.
    2021년 외 날짜는 자동으로 2021년으로 변환.
    반환: DataFrame
    """
    if not target_date.startswith('2021'):
        target_date = "2021" + target_date[4:]

    db_path = './db/PowerMgt.db'
    conn    = sqlite3.connect(db_path)

    try:
        query = "SELECT * FROM OperationResult WHERE date = ?"
        df    = pd.read_sql_query(query, conn, params=(target_date,))
    finally:
        conn.close()

    return df


# ── 사용 예시 ─────────────────────────────────────────────────
# from predictor1 import predict_with_input
# from power_db_operations import get_prediction_variables
#
# input_df  = get_prediction_variables('2021-03-24')
# result_df = predict_with_input(input_df)
# result_df.to_csv('result_2021-03-24.csv', index=False)
# print(result_df)
