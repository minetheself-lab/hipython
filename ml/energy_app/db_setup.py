# ================================================================
# db_setup.py
# Phase 1 — Step 2+3
# 역할: PowerMgt.db 점검 + 날짜 오류 수정 + DRResult 테이블 생성
# 실행: python db_setup.py
# ================================================================

import sqlite3
import os
import pandas as pd

# DB 경로 자동 탐색
DB_CANDIDATES = [
    'db/PowerMgt.db',
    'PowerMgt.db',
    '../db/PowerMgt.db',
]

def find_db():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def run_setup():
    db_path = find_db()
    if not db_path:
        print("❌ PowerMgt.db를 찾을 수 없습니다.")
        print("   아래 경로 중 하나에 파일을 배치하세요:")
        for p in DB_CANDIDATES:
            print(f"   - {p}")
        return

    print(f"✅ DB 발견: {db_path}")
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # ── 현재 테이블 목록 확인 ─────────────────────────────────
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\n[현재 테이블 목록] {tables}")

    # ── Step 2: OperationResult 날짜 형식 오류 수정 ──────────
    print("\n" + "="*50)
    print("Step 2: OperationResult 날짜 오류 수정")
    print("="*50)

    if 'OperationResult' in tables:
        df_or = pd.read_sql_query("SELECT * FROM OperationResult LIMIT 10", conn)
        print(f"  현재 행 수: {pd.read_sql_query('SELECT COUNT(*) FROM OperationResult', conn).iloc[0,0]}")
        print(f"  date 컬럼 샘플:")
        dates = pd.read_sql_query("SELECT DISTINCT date FROM OperationResult LIMIT 10", conn)
        print(dates.to_string(index=False))

        # 오류 패턴 확인 ('2021--0-1-' 형태)
        bad_rows = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM OperationResult WHERE date LIKE '%--0%' OR date LIKE '%-%-%-%'",
            conn
        ).iloc[0, 0]
        print(f"\n  날짜 형식 오류 행: {bad_rows}건")

        if bad_rows > 0:
            # 날짜 재파싱 시도
            df_all = pd.read_sql_query("SELECT rowid, date FROM OperationResult", conn)
            fixed = 0
            for _, row in df_all.iterrows():
                d = str(row['date'])
                # 다양한 오류 패턴 처리
                cleaned = d.replace('--0-', '-').replace('-0-', '-').replace('--', '-')
                try:
                    parsed = pd.to_datetime(cleaned).strftime('%Y-%m-%d')
                    if parsed != d:
                        cur.execute(
                            "UPDATE OperationResult SET date=? WHERE rowid=?",
                            (parsed, row['rowid'])
                        )
                        fixed += 1
                except Exception:
                    pass

            conn.commit()
            print(f"  ✅ 날짜 오류 수정 완료: {fixed}건")
        else:
            print("  ✅ 날짜 형식 정상 — 수정 불필요")
    else:
        print("  ⚠ OperationResult 테이블 없음")

    # ── Step 2-B: OperationForecast 확인 ─────────────────────
    print("\n" + "="*50)
    print("Step 2-B: OperationForecast 확인")
    print("="*50)

    if 'OperationForecast' in tables:
        cnt = pd.read_sql_query("SELECT COUNT(*) FROM OperationForecast", conn).iloc[0, 0]
        print(f"  현재 행 수: {cnt}건 (0이면 정상 — 예측 후 채워짐)")
        cols = pd.read_sql_query("PRAGMA table_info(OperationForecast)", conn)
        print(f"  컬럼: {cols['name'].tolist()}")
    else:
        print("  ⚠ OperationForecast 없음 → 생성합니다")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS OperationForecast (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                hour        INTEGER NOT NULL,
                op_code     INTEGER DEFAULT 0,
                manpower    REAL    DEFAULT 0,
                output      INTEGER DEFAULT 0,
                peak_15     REAL,
                peak_30     REAL,
                peak_45     REAL,
                peak_60     REAL,
                PowerUsage  REAL,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()
        print("  ✅ OperationForecast 생성 완료")

    # ── Step 3: DRResult 테이블 생성 ─────────────────────────
    print("\n" + "="*50)
    print("Step 3: DRResult 테이블 생성")
    print("="*50)

    if 'DRResult' in tables:
        cnt = pd.read_sql_query("SELECT COUNT(*) FROM DRResult", conn).iloc[0, 0]
        cols = pd.read_sql_query("PRAGMA table_info(DRResult)", conn)
        print(f"  이미 존재 — 행 수: {cnt}건")
        print(f"  컬럼: {cols['name'].tolist()}")
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS DRResult (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                date            TEXT NOT NULL,          -- DR 발령 날짜 YYYY-MM-DD
                hour_start      INTEGER,                -- 발령 시작 시간
                hour_end        INTEGER,                -- 발령 종료 시간
                cbl_kw          REAL,                   -- 기준부하 (kW)
                predicted_kw    REAL,                   -- AI 예측 피크 (kW)
                actual_kw       REAL,                   -- 실제 사용량 (kW, 이행 후)
                reduction_kw    REAL,                   -- 감축량 = cbl - actual
                request_kw      REAL,                   -- DR 요청량 (kW)
                approved_kw     REAL,                   -- 인정 감축량 (min(감축량, 요청×1.2))
                mgp_price       REAL,                   -- 시장정산단가 (원/kWh)
                revenue_won     INTEGER,                -- DR 정산금 (원)
                tariff_saving   INTEGER,                -- 전기요금 절감액 (원)
                total_benefit   INTEGER,                -- 총 편익 (원)
                approved        INTEGER DEFAULT 0,      -- 0=미결정, 1=이행승인, 2=이행거부
                note            TEXT,                   -- 비고
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()
        print("  ✅ DRResult 테이블 생성 완료")
        print("  컬럼: id, date, hour_start, hour_end, cbl_kw, predicted_kw,")
        print("         actual_kw, reduction_kw, request_kw, approved_kw,")
        print("         mgp_price, revenue_won, tariff_saving, total_benefit,")
        print("         approved, note, created_at")

    # ── 최종 상태 확인 ────────────────────────────────────────
    print("\n" + "="*50)
    print("최종 테이블 현황")
    print("="*50)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [r[0] for r in cur.fetchall()]
    for t in all_tables:
        cnt = pd.read_sql_query(f"SELECT COUNT(*) FROM {t}", conn).iloc[0, 0]
        cols = pd.read_sql_query(f"PRAGMA table_info({t})", conn)
        print(f"  {t:25s} {cnt:6d}행   컬럼 {len(cols)}개")

    # ── WeatherForecast 샘플 확인 ─────────────────────────────
    if 'WeatherForecast' in all_tables:
        print("\n[WeatherForecast 샘플 (최신 3행)]")
        wf = pd.read_sql_query(
            "SELECT * FROM WeatherForecast ORDER BY date DESC, hour DESC LIMIT 3",
            conn
        )
        print(wf.to_string(index=False))

    conn.close()
    print("\n✅ Phase 1 DB 세팅 완료!")
    print("다음 단계: python predictor1.py  ← Step 1 테스트")

if __name__ == '__main__':
    run_setup()
