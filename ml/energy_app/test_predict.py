# ================================================================
# test_predict.py
# 역할  : predictor1.py + power_db_operations.py 통합 테스트
# 실행  : python test_predict.py
# 결과  : result_YYYY-MM-DD.csv 저장
# ================================================================
import pandas as pd
import numpy as np
import os, sys

# ── 임포트 ───────────────────────────────────────────────────
from predictor1 import predict_with_input
from power_db_operations import get_prediction_variables

# ── 설정 ─────────────────────────────────────────────────────
TEST_DATE  = '2021-03-24'
OUTPUT_DIR = './test_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print(f"predictor1.py + power_db_operations.py 통합 테스트")
print(f"대상 날짜: {TEST_DATE}")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# 방법 1: DB에서 읽어서 예측
# ═══════════════════════════════════════════════════════════════
print("\n[방법 1] DB → get_prediction_variables → predict_with_input")
print("-" * 50)

input_df = get_prediction_variables(TEST_DATE)

if input_df is None or len(input_df) == 0:
    print("❌ DB에서 데이터 없음 → 방법 2(CSV)로 진행")
    input_df = None
else:
    print(f"✅ DB 조회 완료: {len(input_df)}행 × {len(input_df.columns)}컬럼")
    print("\n[입력 DataFrame]")
    print(input_df.to_string(index=True))

    # NaN 유지 확인 (fillna('') 문제 체크)
    nan_check = input_df.isnull().sum()
    empty_check = (input_df == '').sum()
    if empty_check.sum() > 0:
        print("\n⚠️  빈 문자열('') 감지 → power_db_operations.py의 fillna('') 제거 필요")
        print("   현재는 자동으로 NaN으로 변환해서 처리합니다.")
        # 빈 문자열 → None으로 자동 변환
        input_df = input_df.replace('', None)
        input_df = input_df.where(pd.notna(input_df), None)

    print("\n[예측 실행 중...]")
    try:
        result_db = predict_with_input(input_df)
        out_path  = os.path.join(OUTPUT_DIR, f'result_db_{TEST_DATE}.csv')
        result_db.to_csv(out_path, index=False, encoding='utf-8-sig')

        print("\n[예측 결과 DataFrame]")
        print(result_db[['Date','hour','applied_set',
                          'peak15','peak30','peak45','peak60']].to_string(index=True))
        print(f"\n✅ 저장: {out_path}")

        # Set 분포 확인
        print("\n[적용 Set 분포]")
        print(result_db['applied_set'].value_counts().sort_index())

    except Exception as e:
        print(f"❌ 예측 오류: {e}")
        import traceback; traceback.print_exc()

# ═══════════════════════════════════════════════════════════════
# 방법 2: CSV 파일에서 읽어서 예측 (Set별 개별 테스트)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("[방법 2] CSV → predict_with_input (Set별 개별 테스트)")
print("=" * 60)

test_files = {
    'Set_A (날짜만)':       f'{OUTPUT_DIR}/test_input_SetA.csv',
    'Set_B (날짜+날씨)':    f'{OUTPUT_DIR}/test_input_SetB.csv',
    'Set_C (전체)':         f'{OUTPUT_DIR}/test_input_SetC.csv',
    'Mixed (A+B+C 혼합)':   f'{OUTPUT_DIR}/test_input_mixed.csv',
}

all_results = {}

for label, path in test_files.items():
    if not os.path.exists(path):
        print(f"\n⚠️  {path} 없음 → python test_input_maker.py 먼저 실행")
        continue

    print(f"\n--- {label} ---")
    df_in = pd.read_csv(path, encoding='utf-8-sig')

    # NaN 유지 (CSV 읽으면 NaN으로 로드됨 — 정상)
    nan_cols = df_in.columns[df_in.isnull().any()].tolist()
    print(f"  입력: {len(df_in)}행 | NaN 컬럼: {nan_cols if nan_cols else '없음 (Set_C)'}")

    try:
        df_result = predict_with_input(df_in)
        all_results[label] = df_result

        # Set 분포
        set_dist = df_result['applied_set'].value_counts().to_dict()
        print(f"  적용 Set: {set_dist}")

        # peak15 통계
        p15 = df_result['peak15']
        print(f"  peak15: mean={p15.mean():.1f} max={p15.max():.1f} min={p15.min():.1f}")

        # 저장
        key = label.split('(')[0].strip().replace(' ','_').replace('/','')
        out_path = os.path.join(OUTPUT_DIR, f'result_{key}_{TEST_DATE}.csv')
        df_result.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"  ✅ 저장: {out_path}")

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        import traceback; traceback.print_exc()

# ═══════════════════════════════════════════════════════════════
# Set 간 비교 요약
# ═══════════════════════════════════════════════════════════════
if len(all_results) >= 2:
    print("\n" + "=" * 60)
    print("Set 간 peak15 비교 요약")
    print("=" * 60)
    rows_summary = []
    for label, df in all_results.items():
        p = df['peak15']
        rows_summary.append({
            '구분': label,
            'mean': round(p.mean(), 1),
            'max':  round(p.max(), 1),
            'min':  round(p.min(), 1),
            'std':  round(p.std(), 1),
        })
    df_summary = pd.DataFrame(rows_summary)
    print(df_summary.to_string(index=False))

    # 비교 CSV 저장
    df_summary.to_csv(
        os.path.join(OUTPUT_DIR, f'compare_sets_{TEST_DATE}.csv'),
        index=False, encoding='utf-8-sig'
    )
    print(f"\n✅ 비교표 저장: {OUTPUT_DIR}/compare_sets_{TEST_DATE}.csv")

print("\n" + "=" * 60)
print("테스트 완료! test_data/ 폴더의 CSV 파일을 확인하세요.")
print("=" * 60)
