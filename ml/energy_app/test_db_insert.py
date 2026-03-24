# ================================================================
# test_db_insert.py
# 역할  : WeatherForecast 테이블에 테스트 날짜 날씨 데이터 삽입
# 실행  : python test_db_insert.py
# ================================================================
import sqlite3
import numpy as np
import os

np.random.seed(42)

DB_PATH  = './db/PowerMgt.db'
TEST_DATE = '2021-03-24'

def make_weather(hour):
    temp = round(8 + 9 * np.sin((hour - 6) * np.pi / 12)
                 + np.random.normal(0, 0.3), 1)
    hum  = round(max(20, 58 - 12 * np.sin((hour - 6) * np.pi / 12)
                     + np.random.normal(0, 1.5)), 1)
    wind = round(max(0.2, 1.8 + np.random.normal(0, 0.4)), 1)
    return temp, hum, wind

if not os.path.exists(DB_PATH):
    print(f"❌ DB 없음: {DB_PATH}")
    exit()

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# 이미 있는지 확인
existing = cur.execute(
    "SELECT COUNT(*) FROM WeatherForecast WHERE date=?", (TEST_DATE,)
).fetchone()[0]

if existing >= 24:
    print(f"✅ {TEST_DATE} 날씨 데이터 이미 존재 ({existing}행) → SKIP")
else:
    print(f"WeatherForecast에 {TEST_DATE} 날씨 24행 삽입 중...")
    for h in range(24):
        t, hu, w = make_weather(h)
        cur.execute("""
            INSERT OR REPLACE INTO WeatherForecast
            (date, hour, temperature, humidity, windspeed, rainfall, status)
            VALUES (?,?,?,?,?,?,?)
        """, (TEST_DATE, h, t, hu, w, 0.0, '맑음'))

    conn.commit()
    print(f"✅ 삽입 완료: {TEST_DATE} 24시간 날씨 데이터")

# Calendar 확인
cal = cur.execute(
    "SELECT * FROM Calendar WHERE date=?", (TEST_DATE,)
).fetchone()
if cal:
    print(f"✅ Calendar {TEST_DATE} 존재: {dict(zip([d[0] for d in cur.description], cal))}")
else:
    print(f"⚠️  Calendar에 {TEST_DATE} 없음 → INSERT 추가")
    cur.execute("""
        INSERT OR IGNORE INTO Calendar
        (date, year, month, day, weekday, weekend, holiday)
        VALUES (?,?,?,?,?,?,?)
    """, (TEST_DATE, 2021, 3, 24, 3, 0, 0))
    conn.commit()
    print(f"✅ Calendar {TEST_DATE} 삽입 완료")

conn.close()
print("\n다음: python test_predict.py")
