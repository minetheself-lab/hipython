# Generated from: power_db_management.ipynb

import requests
import datetime
import urllib3
import os
import pandas as pd
from urllib.parse import unquote
import dotenv
import sqlite3
import holidays
from datetime import datetime 

# HTTPS 경고 메시지 무시 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_weather_info(target_dt=None):
    """
    지정된 일시(기본값: 현재 시각) 기준 가장 최근 과거의 날씨 정보를 반환
    """
    db_path = './db/PowerMgt.db'
    
    print(target_dt)
    
    # 인자가 없으면 현재 시각 사용
    if target_dt is None:
        target_dt = datetime.now()
    
    target_date = target_dt.strftime('%Y-%m-%d')
    target_hour = target_dt.hour

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 입력 시점 포함, 가장 가까운 과거 데이터 1건 조회
            query = """
                SELECT * FROM WeatherForecast 
                WHERE date = ? AND hour == ?
            """
            
            cur.execute(query, (target_date, target_hour))
            row = cur.fetchone()
            
            return dict(row) if row else None

    except sqlite3.Error as e:
        print(f"DB Error: {e}")
        return None


def get_prediction_variables(target_date):
    """
    OperationForecast에 해당 날짜 데이터가 없거나 부족하면 
    OperationResult 테이블의 데이터를 대체하여 조회합니다.
    """
    db_path = './db/PowerMgt.db'
    conn = sqlite3.connect(db_path)
    
    # 입력된 날짜에서 '월' 추출
    target_month = int(target_date.split('-')[1])

    query = f"""
    WITH RECURSIVE hours(h) AS (
        SELECT 0 UNION ALL SELECT h + 1 FROM hours WHERE h < 23
    ),
    -- 해당 날짜의 Forecast 레코드 개수 확인
    ForecastCount AS (
        SELECT COUNT(*) as cnt FROM OperationForecast WHERE date = '{target_date}'
    ),
    -- 데이터 소스 결정: Forecast가 12개 미만이면 Result 테이블을 사용
    ActualOp AS (
        SELECT 
            h.h,
            CASE WHEN (SELECT cnt FROM ForecastCount) >= 12 THEN O.op_code ELSE R.op_code END AS op_code,
            CASE WHEN (SELECT cnt FROM ForecastCount) >= 12 THEN O.output  ELSE R.output  END AS output
        FROM hours h
        LEFT JOIN OperationForecast O ON O.date = '{target_date}' AND O.hour = h.h
        LEFT JOIN OperationResult   R ON R.date = '{target_date}' AND R.hour = h.h
    )
    SELECT 
        '{target_date}' AS Date, 
        h.h AS hour,
        W.temperature, W.humidity, W.windspeed, W.rainfall,
        A.op_code,
        A.output,
        C.weekday, C.weekend, C.holiday
    FROM hours h
    LEFT JOIN ActualOp A ON A.h = h.h
    LEFT JOIN WeatherForecast W ON W.date = '{target_date}' AND W.hour = h.h
    LEFT JOIN Calendar C ON C.date = '{target_date}'
    ORDER BY h.h ASC;
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        df = df.where(pd.notna(df), None)  # NaN 유지
        return df
    except Exception as e:
        print(f"조회 중 오류 발생: {e}")
        return None
    finally:
        conn.close()


# 사용 예시
# df = get_prediction_variables('2024-05-20')
# print(df)


def get_daily_result(target_date):
    """
    OperationResult 테이블에서 특정 일자(target_date)의 레코드를 조회하여
    Pandas DataFrame으로 리턴하는 함수입니다.
    """
    
    if not target_date.startswith('2021') : 
        target_date = "2021" + target_date[4:]
        
    # 1. 데이터베이스 연결 (실제 파일 경로로 변경 필요, 예: 'my_database.db')
    db_path= './db/PowerMgt.db'
    conn = sqlite3.connect(db_path)
    
    try:
        # 2. SQL 쿼리 작성 (SQL Injection 방지를 위해 파라미터 바인딩 사용)
        query = "SELECT * FROM OperationResult WHERE date = ?"
        
        # 3. pandas의 read_sql_query를 사용하여 DataFrame으로 직접 읽기
        df = pd.read_sql_query(query, conn, params=(target_date,))
        
    finally:
        # 4. 작업 완료 후 연결 종료
        conn.close()
        
    return df

# 사용 예시
# daily_df = get_daily_result('2020-01-01')
# print(daily_df.head())
