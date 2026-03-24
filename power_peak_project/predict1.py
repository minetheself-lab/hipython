# %% [markdown]
# # Step 1

# %% [markdown]
# # 에너지 사용량 예측 AI 모델
# 
# **데이터셋**: KAMP 자원 최적화 AI 데이터셋 (okm_augumented_2021.csv)  
# **출처**: www.kamp-ai.kr  
# **목표**: 15분 단위 피크 전력(kW) 예측 → 연간 기본 전기료 절감
# 
# ---
# 
# ### 모델링 프로세스 요약
# 
# **Target**: `15분` (15분 단위 최대수요전력, 단위: kW)
# 
# **1단계** 데이터 로드 및 기본 정보 확인 (.info / .describe)  
# **2단계** EDA — 분포 시각화, 타겟 분포, 생산량-전력 관계  
# **3단계** 결측치 / 이상치 확인 및 처리  
# **4단계** 상관관계 분석 (Heatmap)  
# **5단계** 변수 조합 설계 — Feature Set A / B / C  
# **6단계** Train / Test Split + 스케일링  
# **7단계** 모델 학습 — LinearReg / Ridge / DecisionTree / RandomForest / XGBoost / DNN  
# **8단계** 하이퍼파라미터 튜닝 (GridSearchCV / RandomizedSearchCV)  
# **9단계** 최종 모델 선정 및 종합 평가  
# **10단계** 모델 저장 (pipeline.pkl)

# %% [markdown]
# # Step 2

# %%
import subprocess
import sys

required = {
    'xgboost'       : 'xgboost',
    'sklearn'       : 'scikit-learn',
    'pandas'        : 'pandas',
    'numpy'         : 'numpy',
    'matplotlib'    : 'matplotlib',
    'seaborn'       : 'seaborn',
    'joblib'        : 'joblib',
}

print("=== 라이브러리 설치 확인 ===\n")
for import_name, pkg_name in required.items():
    try:
        __import__(import_name)
        print(f"  ✅ {pkg_name:20s} 이미 설치됨")
    except ImportError:
        print(f"  ⚙️  {pkg_name:20s} 설치 중...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                               pkg_name, '--break-system-packages', '-q'])
        print(f"  ✅ {pkg_name:20s} 설치 완료")

print("\n✅ 모든 라이브러리 준비 완료 → STEP 3으로 이동하세요!")

# %% [markdown]
# # 필요 라이브러리 설치 확인 (최초 1회만 실행)
# # !pip install xgboost --break-system-packages
# # !pip install scikit-learn --break-system-packages

# %% [markdown]
# # Step 3

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# ── 한글 폰트 설정 (Windows) ──────────────────────────
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

print("✅ 라이브러리 임포트 완료")
print(f"  pandas  : {pd.__version__}")
print(f"  numpy   : {np.__version__}")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# ── 한글 폰트 설정 (Windows) ──────────────────────────
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

print("✅ 라이브러리 임포트 완료")
print(f"  pandas  : {pd.__version__}")
print(f"  numpy   : {np.__version__}")

# %% [markdown]
# # Step 4

# %%
import os

# 현재 작업 디렉토리 확인
print(f"현재 작업 경로: {os.getcwd()}")

# %%
import os
import pandas as pd

# 가능한 경로 후보 목록
candidates = [
    r'C:\Users\Admin\hipython\data\okm_augumented_2021.csv',
    r'C:\Users\Admin\hipython\ml\data\okm_augumented_2021.csv',
    './data/okm_augumented_2021.csv',
]

# 존재하는 경로 자동 탐지
file_path = None
for path in candidates:
    if os.path.exists(path):
        file_path = path
        print(f"✅ 파일 발견: {file_path}")
        break

if file_path is None:
    print("❌ 파일을 찾지 못했습니다. 경로를 확인하세요.")
    print(f"   현재 작업 경로: {os.getcwd()}")
else:
    df = pd.read_csv(file_path)
    print(f"\n✅ 데이터 로드 완료")
    print(f"   행(row) 수 : {df.shape[0]:,}")
    print(f"   열(col) 수 : {df.shape[1]}")
    print()
    print("=== 컬럼 목록 ===")
    print(df.columns.tolist())
    print()
    print("=== 상위 5행 ===")
    display(df.head())

# %% [markdown]
# # Step 5

# %%
print("=== .info() — 컬럼별 타입 및 결측치 ===")
df.info()

# %% [markdown]
# # Step 6

# %%
print("=== .describe() — 기술통계 ===")
df.describe().T.style.background_gradient(cmap='Blues', subset=['mean','std'])

# %% [markdown]
# # Step 7

# %%
print("=== 결측치 현황 ===")
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)

missing_df = pd.DataFrame({
    '결측치 수': missing,
    '결측률(%)': missing_pct
}).query('`결측치 수` > 0')

print(missing_df)
print(f"\n총 결측치 수 : {missing.sum()}개")
print(f"결측치 있는 컬럼 : {len(missing_df)}개")

# %% [markdown]
# # Step 8

# %%
print("=== 이상치 확인 ===")

# 1) 시간 컬럼: 0~23이 정상
print(f"[시간] 최대값: {df['시간'].max()}  (정상: 0~23)")
print(f"       시간 > 23 인 행: {(df['시간'] > 23).sum()}건")
print()

# 2) 타겟 변수 분포
print(f"[15분 피크전력] 최소: {df['15분'].min()} / 최대: {df['15분'].max()} / 평균: {df['15분'].mean():.1f}")
print(f"                피크전력 = 0 인 행: {(df['15분'] == 0).sum()}건")
print()

# 3) 생산량 0 비율
print(f"[생산량] 0인 행: {(df['생산량'] == 0).sum()}건 ({(df['생산량'] == 0).mean()*100:.1f}%)  ← 비가동 시간")
print()

# 4) 공장인원 분포
print(f"[공장인원] 최소: {df['공장인원'].min():.2f} / 최대: {df['공장인원'].max():.2f}")
print()

# 5) 박스플롯으로 수치 변수 이상치 시각화
fig, axes = plt.subplots(2, 4, figsize=(18, 8))
fig.suptitle('주요 변수 이상치 확인 (Boxplot)', fontsize=14, fontweight='bold')

cols_to_check = ['15분', '30분', '생산량', '기온', '풍속', '습도', '강수량', '공장인원']
for ax, col in zip(axes.flatten(), cols_to_check):
    ax.boxplot(df[col].dropna(), vert=True, patch_artist=True,
               boxprops=dict(facecolor='steelblue', alpha=0.6))
    ax.set_title(col, fontsize=11)
    ax.set_ylabel('값')

plt.tight_layout()
plt.show()

# %% [markdown]
# # Step 9

# %%
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('타겟 변수 (15분 피크전력) 분포 분석', fontsize=13, fontweight='bold')

# 1) 히스토그램
axes[0].hist(df['15분'], bins=40, color='steelblue', edgecolor='white', alpha=0.8)
axes[0].axvline(df['15분'].mean(),   color='red',    linestyle='--', label=f"평균 {df['15분'].mean():.0f}kW")
axes[0].axvline(df['15분'].median(), color='orange', linestyle='--', label=f"중앙값 {df['15분'].median():.0f}kW")
axes[0].set_title('전체 분포 (히스토그램)')
axes[0].set_xlabel('피크전력 (kW)')
axes[0].legend()

# 2) 시간대별 평균 피크전력
hourly = df[df['시간'] <= 23].groupby('시간')['15분'].mean()
axes[1].bar(hourly.index, hourly.values, color='steelblue', alpha=0.8, edgecolor='white')
axes[1].set_title('시간대별 평균 피크전력')
axes[1].set_xlabel('시간 (0~23시)')
axes[1].set_ylabel('평균 피크전력 (kW)')

# 3) 생산량 vs 피크전력 산점도
sample = df[df['시간'] <= 23].sample(500, random_state=42)
axes[2].scatter(sample['생산량'], sample['15분'],
                alpha=0.4, color='steelblue', edgecolor='white', linewidth=0.3)
axes[2].set_title('생산량 vs 피크전력')
axes[2].set_xlabel('생산량')
axes[2].set_ylabel('피크전력 (kW)')

plt.tight_layout()
plt.show()

print(f"\n피크전력 고위험(≥130kW) 비율 : {(df['15분'] >= 130).mean()*100:.1f}%")

# %% [markdown]
# # Step 10

# %%
# 이상치 제거 후 상관관계 계산
df_corr = df[df['시간'] <= 23].copy()

# 상관행렬
corr_matrix = df_corr.corr(numeric_only=True)

plt.figure(figsize=(14, 10))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # 상삼각 마스킹
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f',
            cmap='coolwarm', center=0, linewidths=0.5,
            annot_kws={'size': 9}, vmin=-1, vmax=1)
plt.title('변수 간 상관관계 Heatmap', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# 타겟(15분)과의 상관계수 순위
print("=== 15분 피크전력과의 상관계수 (절대값 내림차순) ===")
target_corr = corr_matrix['15분'].drop(['15분','30분','45분','60분','평균']).abs()
print(target_corr.sort_values(ascending=False).to_string())

# %% [markdown]
# # Step 11

# %%
# ── 전처리 ────────────────────────────────────────────
df_clean = df.copy()

# 1) 이상치 제거: 시간 > 23
before = len(df_clean)
df_clean = df_clean[df_clean['시간'] <= 23]
print(f"[이상치 제거] 시간>23: {before - len(df_clean)}행 제거 → 잔여 {len(df_clean):,}행")

# 2) 결측치 처리
df_clean['풍속']   = df_clean['풍속'].fillna(df_clean['풍속'].median())
df_clean['강수량']  = df_clean['강수량'].fillna(0)   # 강수 없음으로 대체
df_clean['공장인원'] = df_clean['공장인원'].fillna(0)  # 비가동으로 대체
print(f"[결측치 처리] 완료 — 남은 결측치: {df_clean.isnull().sum().sum()}개")

# 3) 타겟 / 피처 분리
# ※ 30분/45분/60분/평균은 Data Leakage → 반드시 제외
TARGET = '15분'
LEAK_COLS = ['30분', '45분', '60분', '평균']  # 타겟과 같은 계열 → 제외
DROP_COLS  = ['날짜'] + LEAK_COLS              # 날짜는 시계열 특성 대신 d/m으로 대체

feature_cols = [c for c in df_clean.columns if c not in [TARGET] + DROP_COLS]

X = df_clean[feature_cols].copy()
y = df_clean[TARGET].copy()

print(f"\n[피처 구성]")
print(f"  사용 피처 수 : {len(feature_cols)}개")
print(f"  피처 목록    : {feature_cols}")
print(f"\n  X shape : {X.shape}")
print(f"  y shape : {y.shape}")
print(f"\n  타겟(y) 통계 → 평균: {y.mean():.1f}kW / 최대: {y.max()}kW / 최소: {y.min()}kW")

# %% [markdown]
# # Step 12

# %% [markdown]
# ## 변수 조합 설계 — Feature Set A / B / C
# 
# 현실에서 공장 담당자가 **예측 시점에 알 수 있는 정보**만으로 피처를 구성합니다.
# 
# | Feature Set | 변수 구성 | 설명 |
# |---|---|---|
# | **Set A (핵심)** | 시간, 생산량, 공장인원, day, d, m | 공정 핵심 변수만 |
# | **Set B (핵심+환경)** | Set A + 기온, 습도, 풍속, 강수량 | 날씨 변수 추가 |
# | **Set C (전체)** | 전체 12개 변수 | 전기요금(계절), 인건비 포함 |
# 
# → 3가지 Feature Set을 모두 학습해서 변수 추가 효과를 비교합니다.

# %% [markdown]
# # Step 13

# %%
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ── Feature Set 정의 ──────────────────────────────────
FEATURE_SETS = {
    'Set_A': ['시간', '생산량', '공장인원', 'day', 'd', 'm'],
    'Set_B': ['시간', '생산량', '공장인원', 'day', 'd', 'm',
              '기온', '습도', '풍속', '강수량'],
    'Set_C': ['시간', '생산량', '공장인원', 'day', 'd', 'm',
              '기온', '습도', '풍속', '강수량', '전기요금(계절)', '인건비'],
}

print("=== Feature Set 구성 ===")
for name, cols in FEATURE_SETS.items():
    print(f"  {name} ({len(cols)}개): {cols}")

# ── Set_C 기준 Train/Test Split (80:20) ──────────────
X_all  = X[FEATURE_SETS['Set_C']]
X_train_all, X_test_all, y_train, y_test = train_test_split(
    X_all, y, test_size=0.2, random_state=42
)

# ── Feature Set별 분할 딕셔너리 ──────────────────────
splits = {}
for name, cols in FEATURE_SETS.items():
    splits[name] = {
        'X_train': X_train_all[cols],
        'X_test' : X_test_all[cols],
    }

# ── 스케일링 (DNN, 선형모델용) ────────────────────────
scalers = {}
for name, cols in FEATURE_SETS.items():
    sc = StandardScaler()
    splits[name]['X_train_sc'] = sc.fit_transform(splits[name]['X_train'])
    splits[name]['X_test_sc']  = sc.transform(splits[name]['X_test'])
    scalers[name] = sc

print(f"\n✅ Split 완료")
print(f"   학습 데이터: {X_train_all.shape[0]:,}행")
print(f"   테스트 데이터: {X_test_all.shape[0]:,}행")

# %% [markdown]
# # Step 14

# %%
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def evaluate_model(model_name, y_true, y_pred):
    """회귀 모델 성능 평가 지표 계산"""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    return {'모델': model_name, 'RMSE': round(rmse,2), 'MAE': round(mae,2), 'R²': round(r2,4)}

all_results = []   # 전체 결과 저장 리스트
print("✅ 평가 함수 정의 완료")

# %% [markdown]
# # Step 15

# %%
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ── Feature Set 정의 ──────────────────────────────────
FEATURE_SETS = {
    'Set_A': ['시간', '생산량', '공장인원', 'day', 'd', 'm'],
    'Set_B': ['시간', '생산량', '공장인원', 'day', 'd', 'm',
              '기온', '습도', '풍속', '강수량'],
    'Set_C': ['시간', '생산량', '공장인원', 'day', 'd', 'm',
              '기온', '습도', '풍속', '강수량', '전기요금(계절)', '인건비'],
}

print("=== Feature Set 구성 ===")
for name, cols in FEATURE_SETS.items():
    print(f"  {name} ({len(cols)}개): {cols}")

# ── Set_C 기준 Train/Test Split (80:20) ──────────────
X_all  = X[FEATURE_SETS['Set_C']]
X_train_all, X_test_all, y_train, y_test = train_test_split(
    X_all, y, test_size=0.2, random_state=42
)

# ── Feature Set별 분할 딕셔너리 ──────────────────────
splits = {}
for name, cols in FEATURE_SETS.items():
    splits[name] = {
        'X_train': X_train_all[cols],
        'X_test' : X_test_all[cols],
    }

# ── 스케일링 (DNN, 선형모델용) ────────────────────────
scalers = {}
for name, cols in FEATURE_SETS.items():
    sc = StandardScaler()
    splits[name]['X_train_sc'] = sc.fit_transform(splits[name]['X_train'])
    splits[name]['X_test_sc']  = sc.transform(splits[name]['X_test'])
    scalers[name] = sc

# ── 결과 저장 리스트 초기화 ───────────────────────────
all_results = []

print(f"\n✅ Split 완료")
print(f"   학습 데이터  : {X_train_all.shape[0]:,}행")
print(f"   테스트 데이터: {X_test_all.shape[0]:,}행")
print(f"   all_results  : 초기화 완료")

# %% [markdown]
# # Step 16

# %%
from sklearn.tree import DecisionTreeRegressor

print("=" * 55)
print("  [모델 3] Decision Tree Regressor")
print("=" * 55)

for fs_name in FEATURE_SETS:
    Xtr = splits[fs_name]['X_train']
    Xte = splits[fs_name]['X_test']

    dt = DecisionTreeRegressor(max_depth=10, min_samples_leaf=5, random_state=42)
    dt.fit(Xtr, y_train)
    res = evaluate_model(f'DecisionTree [{fs_name}]', y_test, dt.predict(Xte))
    all_results.append(res)
    print(f"  DecisionTree {fs_name:6s} | RMSE={res['RMSE']:6.2f} | MAE={res['MAE']:6.2f} | R²={res['R²']:.4f}")

print()
print("💡 단일 트리 해설: R²≈0.88 → 선형 모델 대비 크게 향상")
print("   단, 단일 트리는 분기점에서 과적합 가능성 존재")
print("   → Random Forest(앙상블)로 개선 가능")

# %% [markdown]
# # Step 17

# %%
from sklearn.ensemble import RandomForestRegressor

print("=" * 55)
print("  [모델 4] Random Forest Regressor")
print("=" * 55)

for fs_name in FEATURE_SETS:
    Xtr = splits[fs_name]['X_train']
    Xte = splits[fs_name]['X_test']

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(Xtr, y_train)
    res = evaluate_model(f'RandomForest [{fs_name}]', y_test, rf.predict(Xte))
    all_results.append(res)
    print(f"  RandomForest {fs_name:6s} | RMSE={res['RMSE']:6.2f} | MAE={res['MAE']:6.2f} | R²={res['R²']:.4f}")

# Set_C 모델 저장 (Feature Importance용)
rf_setC = RandomForestRegressor(n_estimators=200, max_depth=15,
                                min_samples_leaf=3, random_state=42, n_jobs=-1)
rf_setC.fit(splits['Set_C']['X_train'], y_train)

print()
print("💡 Random Forest 해설: R²≈0.94 → 현재까지 최고 성능")
print("   200개 트리의 평균 → 단일 트리보다 분산 감소, 과적합 억제")

# %% [markdown]
# # Step 18

# %%
from xgboost import XGBRegressor

print("=" * 55)
print("  [모델 5] XGBoost Regressor")
print("=" * 55)

for fs_name in FEATURE_SETS:
    Xtr = splits[fs_name]['X_train']
    Xte = splits[fs_name]['X_test']

    xgb = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    xgb.fit(Xtr, y_train,
            eval_set=[(Xte, y_test)],
            verbose=False)
    res = evaluate_model(f'XGBoost [{fs_name}]', y_test, xgb.predict(Xte))
    all_results.append(res)
    print(f"  XGBoost {fs_name:6s} | RMSE={res['RMSE']:6.2f} | MAE={res['MAE']:6.2f} | R²={res['R²']:.4f}")

# Set_C 모델 저장
xgb_setC = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                         subsample=0.8, colsample_bytree=0.8,
                         random_state=42, verbosity=0)
xgb_setC.fit(splits['Set_C']['X_train'], y_train, verbose=False)

print()
print("💡 XGBoost 해설: 부스팅(이전 트리의 오차를 다음 트리가 학습)")
print("   learning_rate=0.1: 학습 속도, 낮을수록 신중하게 학습")
print("   subsample=0.8: 매 트리마다 80% 샘플만 사용 → 과적합 방지")

# %% [markdown]
# # Step 19

# %%
from sklearn.neural_network import MLPRegressor

print("=" * 55)
print("  [모델 6] DNN (sklearn MLPRegressor)")
print("=" * 55)
print("  ※ DNN은 스케일링 필수 → StandardScaler 적용 버전 사용")
print()

dnn_configs = {
    'DNN-Shallow [64]'       : (64,),
    'DNN-Medium  [128,64]'   : (128, 64),
    'DNN-Deep    [128,64,32]': (128, 64, 32),
}

# Set_C 기준으로만 DNN 실행
Xtr_sc = splits['Set_C']['X_train_sc']
Xte_sc = splits['Set_C']['X_test_sc']

for dnn_name, layers in dnn_configs.items():
    dnn = MLPRegressor(
        hidden_layer_sizes=layers,
        activation='relu',
        solver='adam',
        max_iter=500,
        early_stopping=True,       # 과적합 방지 자동 조기종료
        validation_fraction=0.1,   # train의 10%를 검증용으로 사용
        random_state=42
    )
    dnn.fit(Xtr_sc, y_train)
    res = evaluate_model(f'{dnn_name} [Set_C]', y_test, dnn.predict(Xte_sc))
    all_results.append(res)
    print(f"  {dnn_name} | RMSE={res['RMSE']:6.2f} | MAE={res['MAE']:6.2f} | R²={res['R²']:.4f}")
    print(f"              → 실제 학습 에포크: {dnn.n_iter_}회 (early stopping)")

# 최적 DNN 저장 (Medium)
dnn_best = MLPRegressor(hidden_layer_sizes=(128,64), activation='relu',
                        solver='adam', max_iter=500, early_stopping=True,
                        validation_fraction=0.1, random_state=42)
dnn_best.fit(Xtr_sc, y_train)

print()
print("💡 DNN 해설: 입력(12) → [128 → 64] → 출력(1)")
print("   ReLU: 음수는 0, 양수는 그대로 통과 → 비선형성 학습")
print("   early_stopping: 검증 손실이 더 이상 줄지 않으면 자동 종료")
print("   ⚠️  DNN은 데이터 수 6,000행에서 RF보다 성능이 낮을 수 있음")
print("      (DNN은 수십만 행 이상에서 진가 발휘)")

# %% [markdown]
# # Step 20

# %%
results_df = pd.DataFrame(all_results)

print("=" * 65)
print("  전체 모델 × Feature Set 비교표 (R² 내림차순)")
print("=" * 65)
print(results_df.sort_values('R²', ascending=False).to_string(index=False))

# %% [markdown]
# # Step 21

# %%
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor

print("=" * 55)
print("  하이퍼파라미터 튜닝 — Random Forest (Set_C)")
print("  ※ Windows 환경: n_jobs=1 로 안정 실행")
print("  ※ 약 3~5분 소요됩니다...")
print("=" * 55)

Xtr = splits['Set_C']['X_train']
Xte = splits['Set_C']['X_test']

param_dist_rf = {
    'n_estimators'    : [100, 200, 300],
    'max_depth'       : [10, 15, 20, None],
    'min_samples_leaf': [1, 3, 5, 10],
    'max_features'    : ['sqrt', 'log2', 0.7],
}

rf_tuned = RandomizedSearchCV(
    estimator           = RandomForestRegressor(random_state=42, n_jobs=1),  # ✅ 수정
    param_distributions = param_dist_rf,
    n_iter              = 20,
    cv                  = 3,
    scoring             = 'r2',
    random_state        = 42,
    n_jobs              = 1,   # ✅ 수정: Windows 병렬처리 충돌 방지
    verbose             = 1
)
rf_tuned.fit(Xtr, y_train)

print(f"\n✅ 최적 파라미터: {rf_tuned.best_params_}")
print(f"   CV R² (학습) : {rf_tuned.best_score_:.4f}")

res = evaluate_model('RF_Tuned [Set_C]', y_test, rf_tuned.predict(Xte))
all_results.append(res)
print(f"   Test  R²     : {res['R²']:.4f} / RMSE: {res['RMSE']} / MAE: {res['MAE']}")

# %% [markdown]
# # Step 22

# %%
from xgboost import XGBRegressor

print("=" * 55)
print("  하이퍼파라미터 튜닝 — XGBoost (Set_C)")
print("  ※ Windows 환경: n_jobs=1 로 안정 실행")
print("  ※ 약 3~5분 소요됩니다...")
print("=" * 55)

param_dist_xgb = {
    'n_estimators'    : [100, 200, 300],
    'max_depth'       : [4, 6, 8],
    'learning_rate'   : [0.05, 0.1, 0.2],
    'subsample'       : [0.7, 0.8, 1.0],
    'colsample_bytree': [0.7, 0.8, 1.0],
    'min_child_weight': [1, 3, 5],
}

xgb_tuned = RandomizedSearchCV(
    estimator           = XGBRegressor(random_state=42, verbosity=0, n_jobs=1),  # ✅ 수정
    param_distributions = param_dist_xgb,
    n_iter              = 20,
    cv                  = 3,
    scoring             = 'r2',
    random_state        = 42,
    n_jobs              = 1,   # ✅ 수정: Windows 병렬처리 충돌 방지
    verbose             = 1
)
xgb_tuned.fit(splits['Set_C']['X_train'], y_train)

print(f"\n✅ 최적 파라미터: {xgb_tuned.best_params_}")
print(f"   CV R² (학습) : {xgb_tuned.best_score_:.4f}")

res = evaluate_model('XGB_Tuned [Set_C]', y_test, xgb_tuned.predict(splits['Set_C']['X_test']))
all_results.append(res)
print(f"   Test  R²     : {res['R²']:.4f} / RMSE: {res['RMSE']} / MAE: {res['MAE']}")

# %% [markdown]
# # Step 23

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('피처 중요도 비교 — Random Forest vs XGBoost (Set_C)', fontsize=13, fontweight='bold')

feature_names = FEATURE_SETS['Set_C']

# RF Feature Importance
fi_rf = pd.Series(rf_setC.feature_importances_, index=feature_names).sort_values(ascending=True)
colors_rf = ['tomato' if v > fi_rf.quantile(0.6) else 'steelblue' for v in fi_rf.values]
axes[0].barh(fi_rf.index, fi_rf.values, color=colors_rf, edgecolor='white')
axes[0].set_title('Random Forest', fontsize=12)
axes[0].set_xlabel('Feature Importance')
for i, val in enumerate(fi_rf.values):
    axes[0].text(val + 0.002, i, f'{val:.4f}', va='center', fontsize=9)

# XGBoost Feature Importance
fi_xgb = pd.Series(xgb_setC.feature_importances_, index=feature_names).sort_values(ascending=True)
colors_xgb = ['tomato' if v > fi_xgb.quantile(0.6) else 'steelblue' for v in fi_xgb.values]
axes[1].barh(fi_xgb.index, fi_xgb.values, color=colors_xgb, edgecolor='white')
axes[1].set_title('XGBoost', fontsize=12)
axes[1].set_xlabel('Feature Importance')
for i, val in enumerate(fi_xgb.values):
    axes[1].text(val + 0.001, i, f'{val:.4f}', va='center', fontsize=9)

plt.tight_layout()
plt.show()

print("\n=== RF Feature Importance Top 5 ===")
print(fi_rf.sort_values(ascending=False).head(5).to_string())
print("\n=== XGBoost Feature Importance Top 5 ===")
print(fi_xgb.sort_values(ascending=False).head(5).to_string())

# %% [markdown]
# # Step 24

# %%
results_df = pd.DataFrame(all_results)

# Set_C 결과만 필터링해서 보기
setC_results = results_df[results_df['모델'].str.contains('Set_C')].sort_values('R²', ascending=False)

print("=" * 65)
print("  최종 모델 성능 비교 (Set_C 기준)")
print("=" * 65)
print(setC_results.to_string(index=False))

# 시각화
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('최종 모델 성능 비교 (Set_C)', fontsize=13, fontweight='bold')

model_labels = [m.split('[')[0].strip() for m in setC_results['모델']]
colors = ['gold' if i == 0 else 'steelblue' for i in range(len(setC_results))]

for ax, metric in zip(axes, ['R²', 'RMSE', 'MAE']):
    bars = ax.bar(model_labels, setC_results[metric], color=colors, edgecolor='white')
    ax.set_title(f'{metric}', fontsize=12)
    ax.set_xticklabels(model_labels, rotation=30, ha='right', fontsize=9)
    for bar, val in zip(bars, setC_results[metric]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    if metric == 'R²':
        ax.set_ylim(0, 1.05)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# %% [markdown]
# # Step 25

# %%
# 최적 모델로 예측
best_model = rf_tuned   # RF_Tuned 또는 XGB_Tuned 중 R²가 높은 것
y_pred_best = best_model.predict(splits['Set_C']['X_test'])

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('최적 모델 — 실제 vs 예측 비교', fontsize=13, fontweight='bold')

# 1) 산점도
axes[0].scatter(y_test, y_pred_best, alpha=0.3, color='steelblue', edgecolor='none', s=15)
lims = [min(y_test.min(), y_pred_best.min()), max(y_test.max(), y_pred_best.max())]
axes[0].plot(lims, lims, 'r--', linewidth=1.5, label='완벽 예측선')
axes[0].set_xlabel('실제 피크전력 (kW)')
axes[0].set_ylabel('예측 피크전력 (kW)')
axes[0].set_title('실제 vs 예측 산점도')
axes[0].legend()

# 2) 처음 200개 시계열 비교
idx = range(200)
axes[1].plot(idx, list(y_test)[:200],      label='실제', color='steelblue', linewidth=1.2)
axes[1].plot(idx, y_pred_best[:200], label='예측', color='tomato',    linewidth=1.2, alpha=0.8)
axes[1].set_xlabel('샘플 인덱스')
axes[1].set_ylabel('피크전력 (kW)')
axes[1].set_title('처음 200개 샘플 — 실제 vs 예측')
axes[1].legend()
axes[1].axhline(130, color='orange', linestyle=':', linewidth=1.5, label='고피크 기준(130kW)')

plt.tight_layout()
plt.show()

rmse_final = np.sqrt(mean_squared_error(y_test, y_pred_best))
print(f"\n최적 모델 최종 성능")
print(f"  RMSE : {rmse_final:.2f} kW  (평균 피크 90kW 대비 오차율 {rmse_final/y.mean()*100:.1f}%)")
print(f"  R²   : {r2_score(y_test, y_pred_best):.4f}")

# %% [markdown]
# # Step 26

# %%
import joblib
import os
from sklearn.pipeline import Pipeline

os.makedirs('./models', exist_ok=True)

# 최적 파라미터로 파이프라인 구성
best_params = rf_tuned.best_params_

final_pipeline = Pipeline([
    ('scaler', StandardScaler()),                        # 스케일링 (RF는 불필요하지만 통일성 유지)
    ('model' , RandomForestRegressor(
        **best_params,
        random_state=42,
        n_jobs=-1
    ))
])

# Set_C 피처로 재학습
final_pipeline.fit(splits['Set_C']['X_train'], y_train)

# 저장
save_path = './models/energy_pipeline.pkl'
joblib.dump({
    'pipeline'    : final_pipeline,
    'feature_cols': FEATURE_SETS['Set_C'],
    'scaler'      : scalers['Set_C'],
    'best_params' : best_params,
}, save_path)

size_mb = os.path.getsize(save_path) / (1024**2)
print(f"✅ 모델 저장 완료: {save_path}  ({size_mb:.2f} MB)")

# 로드 후 검증
loaded = joblib.load(save_path)
y_check = loaded['pipeline'].predict(splits['Set_C']['X_test'])
print(f"   로드 후 R² 검증: {r2_score(y_test, y_check):.4f}  ✅")

# %%


# %%
# 확인용 셀
import pandas as pd

asos_path = r'C:\Users\Admin\hipython\ml\data\asos_solar_2021.csv'
df_check = pd.read_csv(asos_path)
print(f"행 수: {len(df_check):,}")
print(f"날짜 범위: {df_check['날짜_key'].min()} ~ {df_check['날짜_key'].max()}")
print(f"월별 행 수:")
df_check['월'] = df_check['날짜_key'].astype(str).str[4:6].astype(int)
print(df_check.groupby('월').size().to_string())

# %% [markdown]
# # Step 27 데이터 증강 9개월 -> 1년 

# %%
# ================================================
# Step 27: 방법3 개선 — OBS 울산 실제 날씨 기반
# 원본(1/1~9/14) 완전 보존
# 확장(9/15~12/31): OBS 실제날씨 + Top6 규칙 + 추석·공휴일
# ================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# ── 원본 OKM 로드 ─────────────────────────────────
for p in [r'C:\Users\Admin\hipython\ml\data\okm_augumented_2021.csv',
          r'C:\Users\Admin\hipython\data\okm_augumented_2021.csv']:
    if os.path.exists(p):
        df_okm = pd.read_csv(p)
        print(f"OKM 로드: {p}")
        break

df_okm = df_okm[df_okm['시간']<=23].copy()
df_okm['공장인원'] = df_okm['공장인원'].fillna(0)
df_okm['강수량']   = df_okm['강수량'].fillna(0)
df_okm['풍속']     = df_okm['풍속'].fillna(df_okm['풍속'].median())

# 시간 이상치 재매핑 (행 제거 아닌 수정 방식 — 15번 방식 적용)
err_dates = df_okm[
    (df_okm['시간']<0)|(df_okm['시간']>23)
]['날짜'].unique().tolist()
for date in err_dates:
    df_okm.loc[df_okm['날짜']==date, '시간'] = list(range(24))
print(f"시간 이상치 수정: {len(err_dates)}개 날짜")

# ── OBS 울산 날씨 로드 ───────────────────────────
obs_path = r'C:\Users\Admin\hipython\ml\data\OBS_ASOS_TIM_20260319115729.csv'
df_obs = pd.read_csv(obs_path, encoding='cp949')
df_obs['일시']     = pd.to_datetime(df_obs['일시'])
df_obs['날짜_key'] = df_obs['일시'].dt.strftime('%Y%m%d').astype(int)
df_obs['시간_key'] = df_obs['일시'].dt.hour
df_obs = df_obs.rename(columns={
    '기온(°C)' :'asos_ta',
    '풍속(m/s)':'asos_ws',
    '습도(%)'  :'asos_hm',
    '강수량(mm)':'asos_rn',
})
df_obs['asos_rn'] = df_obs['asos_rn'].fillna(0)
df_obs['asos_ws'] = df_obs['asos_ws'].fillna(df_obs['asos_ws'].median())
print(f"OBS 로드: {len(df_obs):,}행 | {df_obs['날짜_key'].min()}~{df_obs['날짜_key'].max()}")

# ── ASOS solar_MJ 병합 (일사량은 기존 파일 사용) ──
asos_path = r'C:\Users\Admin\hipython\ml\data\asos_solar_2021.csv'
if os.path.exists(asos_path):
    df_asos = pd.read_csv(asos_path)
    df_asos['날짜_key'] = df_asos['날짜_key'].astype(int)
    df_asos['시간_key'] = df_asos['시간_key'].astype(int)
    solar_dict = df_asos.set_index(
        ['날짜_key','시간_key'])['solar_MJ'].to_dict()
    df_obs['solar_MJ'] = df_obs.apply(
        lambda r: solar_dict.get(
            (int(r['날짜_key']), int(r['시간_key'])), 0.0), axis=1)
    print("solar_MJ 병합 완료")
else:
    df_obs['solar_MJ'] = 0.0
    print("solar_MJ 없음 → 0으로 처리")

# ── STEP 1: 원본 + OBS 일사량 병합 ───────────────
df_orig = df_okm.copy()
df_orig['날짜_key'] = df_orig['날짜'].astype(int)
df_orig['시간_key'] = df_orig['시간'].astype(int)
df_orig = df_orig.merge(
    df_obs[['날짜_key','시간_key','solar_MJ']],
    on=['날짜_key','시간_key'], how='left')
night = (df_orig['시간']<=5)|(df_orig['시간']>=19)
df_orig.loc[night & df_orig['solar_MJ'].isna(), 'solar_MJ'] = 0.0
df_orig['solar_MJ'] = (df_orig['solar_MJ']
    .interpolate().fillna(0).clip(lower=0))
df_orig = df_orig.drop(columns=['날짜_key','시간_key'])
print(f"원본 준비: {len(df_orig):,}행")

# ── STEP 2: 9/15~12/31 날짜 프레임 생성 ──────────
rows = []
cur  = datetime(2021, 9, 15)
while cur <= datetime(2021, 12, 31, 23):
    rows.append({'날짜': int(cur.strftime('%Y%m%d')),
                 '시간': cur.hour})
    cur += timedelta(hours=1)
df_ext = pd.DataFrame(rows)
df_ext['m']   = df_ext['날짜'].astype(str).str[4:6].astype(int)
df_ext['d']   = df_ext['날짜'].astype(str).str[6:8].astype(int)
df_ext['day'] = pd.to_datetime(
    df_ext['날짜'].astype(str), format='%Y%m%d').dt.weekday + 1
print(f"확장 기간: {len(df_ext):,}행")

# ── STEP 3: OBS 실제 날씨 병합 ───────────────────
df_ext['날짜_key'] = df_ext['날짜'].astype(int)
df_ext['시간_key'] = df_ext['시간'].astype(int)
df_ext = df_ext.merge(
    df_obs[['날짜_key','시간_key','solar_MJ',
            'asos_ta','asos_hm','asos_ws','asos_rn']],
    on=['날짜_key','시간_key'], how='left'
).rename(columns={
    'asos_ta':'기온','asos_hm':'습도',
    'asos_ws':'풍속','asos_rn':'강수량'
})
night2 = (df_ext['시간']<=5)|(df_ext['시간']>=19)
df_ext.loc[night2 & df_ext['solar_MJ'].isna(), 'solar_MJ'] = 0.0
df_ext['solar_MJ'] = (df_ext['solar_MJ']
    .interpolate().fillna(0).clip(lower=0))
for c in ['기온','습도','풍속','강수량']:
    df_ext[c] = (df_ext[c]
        .interpolate()
        .fillna(method='bfill')
        .fillna(method='ffill'))
df_ext = df_ext.drop(columns=['날짜_key','시간_key'])
print(f"OBS 날씨 병합 완료 | "
      f"기온: {df_ext['기온'].min():.1f}~{df_ext['기온'].max():.1f}°C")

# ── STEP 4: 추석·공휴일 정의 (9/15~12/31) ────────
holidays_ext = [
    20210920,  # 추석
    20210921,  # 추석
    20210922,  # 추석
    20211003,  # 개천절
    20211004,  # 대체공휴일
    20211009,  # 한글날
    20211225,  # 크리스마스
]

# ── STEP 5: Top6 규칙 기반 생산량 생성 ───────────
winter = df_okm[df_okm['m'].isin([1,2])].copy()
winter['wd'] = pd.to_datetime(
    winter['날짜'].astype(str)+
    winter['시간'].astype(str).str.zfill(2),
    format='%Y%m%d%H').dt.weekday

prod_table   = winter.groupby(['wd','시간'])['생산량'].mean().reset_index()
worker_table = winter.groupby(['wd','시간'])['공장인원'].mean().reset_index()
prod_table.columns   = ['wd','시간','avg_prod']
worker_table.columns = ['wd','시간','avg_worker']

df_ext['wd'] = df_ext['day'] - 1
df_ext = df_ext.merge(prod_table,   on=['wd','시간'], how='left')
df_ext = df_ext.merge(worker_table, on=['wd','시간'], how='left')
df_ext['avg_prod']   = df_ext['avg_prod'].fillna(0)
df_ext['avg_worker'] = df_ext['avg_worker'].fillna(0)

# 공휴일·일요일 완전 휴무
holiday_mask = df_ext['날짜'].isin(holidays_ext)
sunday_mask  = df_ext['wd'] == 6
df_ext.loc[holiday_mask | sunday_mask,
           ['avg_prod','avg_worker']] = 0

# 토요일 50% 특근
sat_idx = df_ext.index[df_ext['wd']==5]
sat_off = sat_idx[np.random.random(len(sat_idx)) < 0.5]
df_ext.loc[sat_off, ['avg_prod','avg_worker']] = 0

# 노이즈 추가
df_ext['생산량'] = (
    df_ext['avg_prod'] +
    np.random.normal(0, df_ext['avg_prod']*0.05+2, len(df_ext))
).clip(lower=0).round().astype(int)
df_ext['공장인원'] = (
    df_ext['avg_worker'] +
    np.random.normal(0, 0.3, len(df_ext))
).clip(lower=0).round(2)
df_ext['인건비'] = df_ext['시간'].apply(
    lambda h: 1.5 if 8<=h<=18 else 1.0)
df_ext = df_ext.drop(columns=['wd','avg_prod','avg_worker'])

# ── STEP 6: 생산량 평균·표준편차 검증 ─────────────
orig_mean = df_okm['생산량'].mean()
orig_std  = df_okm['생산량'].std()
ext_mean  = df_ext['생산량'].mean()
print(f"\n=== 생산량 통계 검증 ===")
print(f"원본(1~9월) 평균: {orig_mean:.1f} / 표준편차: {orig_std:.1f}")
print(f"증강(9/15~12월) 평균: {ext_mean:.1f}")

# ── STEP 7: 전기요금·피크 생성 ───────────────────
def tariff(m):
    return (109.8 if m in [1,2,11,12]
            else 191.6 if m in [6,7,8] else 167.2)
df_ext['전기요금(계절)'] = df_ext['m'].apply(tariff)

def peak(prod, worker, h):
    if prod > 0:
        return max(0, 25 + min(prod/500*60,120)
                   + worker*3 + np.random.normal(0,8))
    if 8<=h<=18 and np.random.random()<0.15:
        return max(0, np.random.normal(75,20))
    return max(0, np.random.normal(25,5))

df_ext['15분'] = df_ext.apply(
    lambda r: round(peak(r['생산량'],r['공장인원'],r['시간']),1),
    axis=1)
df_ext['30분'] = (df_ext['15분']*np.random.uniform(0.95,1.05,len(df_ext))).round(1)
df_ext['45분'] = (df_ext['15분']*np.random.uniform(0.95,1.05,len(df_ext))).round(1)
df_ext['60분'] = (df_ext['15분']*np.random.uniform(0.95,1.05,len(df_ext))).round(1)
df_ext['평균']  = ((df_ext['15분']+df_ext['30분']+
                   df_ext['45분']+df_ext['60분'])/4).round(1)

# ── STEP 8: 합치기 + 저장 ────────────────────────
okm_cols = list(df_okm.columns) + ['solar_MJ']
df_work  = pd.concat(
    [df_orig[okm_cols], df_ext[okm_cols]], ignore_index=True)
df_work  = df_work.sort_values(['날짜','시간']).reset_index(drop=True)

os.makedirs('./data', exist_ok=True)
df_work.to_csv('./data/okm_full_2021.csv', index=False, encoding='utf-8-sig')

print(f"\n=== 최종 요약 ===")
print(f"전체 행 수: {len(df_work):,}")
print(f"날짜 범위 : {df_work['날짜'].min()} ~ {df_work['날짜'].max()}")
print(f"컬럼 수   : {df_work.shape[1]}")
print(f"\n월별 평균 기온 (OBS 울산 실측):")
print(df_work.groupby('m')['기온'].mean().round(1).to_string())
print(f"\n월별 평균 생산량:")
print(df_work.groupby('m')['생산량'].mean().round(0).to_string())
print(f"\n전체 생산량 평균: {df_work['생산량'].mean():.1f}")
print(f"전체 생산량 표준편차: {df_work['생산량'].std():.1f}")
print(f"\n공휴일 반영 확인 (추석 9/20~22):")
for d in [20210920, 20210921, 20210922, 20211003, 20211009]:
    rows = df_work[df_work['날짜']==d]
    print(f"  {d}: 생산량 평균={rows['생산량'].mean():.0f} (0이면 정상)")
print(f"\n저장 완료: ./data/okm_full_2021.csv")
print("Step 27 완료")

# %%
import pandas as pd

# 로드
df = pd.read_csv('./data/okm_full_2021.csv')

# solar_MJ 제거
if 'solar_MJ' in df.columns:
    df = df.drop(columns=['solar_MJ'])

print(f"컬럼 수: {df.shape[1]}")
print(f"컬럼 목록: {df.columns.tolist()}")

# 새 파일명으로 먼저 저장
df.to_csv('./data/okm_full_2021_new.csv', index=False, encoding='utf-8-sig')
print("저장 완료: ./data/okm_full_2021_new.csv")

# %%
import pandas as pd
import os
import time

# 잠깐 대기 후 시도
time.sleep(1)

try:
    os.remove('./data/okm_full_2021.csv')
    os.rename('./data/okm_full_2021_new.csv',
              './data/okm_full_2021.csv')
    print("파일 교체 완료")

    df_check = pd.read_csv('./data/okm_full_2021.csv')
    print(f"행 수: {len(df_check):,}")
    print(f"컬럼: {df_check.columns.tolist()}")
    print(f"solar_MJ 제거 확인: {'solar_MJ' not in df_check.columns}")

except PermissionError:
    print("아직 파일이 열려있습니다.")
    print("아래 중 하나를 확인해주세요:")
    print("1. 엑셀에서 okm_full_2021.csv 닫기")
    print("2. 윈도우 탐색기 미리보기 창 닫기")
    print("3. Jupyter 다른 탭에서 같은 파일 read_csv 실행 중인지 확인")
    print("닫은 후 이 셀 다시 실행하세요.")

# %% [markdown]
# # 확인용

# %%
print(f"행 수    : {len(df_work):,}")
print(f"날짜 범위: {df_work['날짜'].min()} ~ {df_work['날짜'].max()}")
print(f"월별 행수:")
print(df_work['m'].value_counts().sort_index())

# %% [markdown]
# # Step 28: OBS 울산 기상 데이터 로드 및 df_work 준비

# %%
# ================================================
# Step 28: OBS 울산 기상 데이터 로드
# okm_full_2021.csv → df_work 로드
# ================================================
import pandas as pd
import numpy as np
import os

# ── OBS 울산 날씨 파일 로드 ───────────────────────
obs_path = r'C:\Users\Admin\hipython\ml\data\OBS_ASOS_TIM_20260319115729.csv'
df_obs = pd.read_csv(obs_path, encoding='cp949')

df_obs['일시']     = pd.to_datetime(df_obs['일시'])
df_obs['날짜_key'] = df_obs['일시'].dt.strftime('%Y%m%d').astype(int)
df_obs['시간_key'] = df_obs['일시'].dt.hour

df_obs = df_obs.rename(columns={
    '기온(°C)' : 'obs_ta',
    '풍속(m/s)': 'obs_ws',
    '습도(%)'  : 'obs_hm',
    '강수량(mm)': 'obs_rn',
})
df_obs['obs_rn'] = df_obs['obs_rn'].fillna(0)
df_obs['obs_ws'] = df_obs['obs_ws'].fillna(df_obs['obs_ws'].median())

print(f"OBS 로드 완료  : {len(df_obs):,}행")
print(f"OBS 날짜 범위  : {df_obs['날짜_key'].min()} ~ {df_obs['날짜_key'].max()}")
print(f"OBS 기온 범위  : {df_obs['obs_ta'].min():.1f} ~ {df_obs['obs_ta'].max():.1f}°C")

# ── okm_full_2021.csv → df_work 로드 ─────────────
df_work = pd.read_csv(r'C:\Users\Admin\hipython\ml\data\okm_full_2021.csv')

print(f"\ndf_work 로드 완료")
print(f"행 수  : {len(df_work):,}")
print(f"컬럼 수: {df_work.shape[1]}")
print(f"날짜 범위: {df_work['날짜'].min()} ~ {df_work['날짜'].max()}")
print(f"컬럼 목록: {df_work.columns.tolist()}")
print("\nStep 28 완료")

# %% [markdown]
# # Step 29: GMM 생산구분(0~3) 파생변수 추가 (GMM 노트북 흡수)

# %%
# ================================================
# Step 29: GMM 생산구분(0~3) 파생변수 추가
# 15번 노트북 핵심 로직 흡수
# 구분4(39건, 0.45%) → 구분3으로 통합
# ================================================
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

# ── 비가동 구간(구분0) 먼저 분리 ─────────────────
mask_zero = df_work['생산량'] <= 0
df_na     = df_work[mask_zero].copy()
df_na['GMM생산구분'] = 0

# ── 가동 구간 GMM 군집화 ──────────────────────────
df_target = df_work[~mask_zero].copy()

# 생산인력비율 계산 (제품 1000개당 투입 인원)
df_target['생산인력비율'] = (
    df_target['공장인원'] / (df_target['생산량'] / 1000)
).replace([np.inf, -np.inf], 0).fillna(0)

# GMM 입력 피처: 생산인력비율 + 평균전력
features   = df_target[['생산인력비율', '평균']].fillna(0)
scaler_gmm = StandardScaler()
X_scaled   = scaler_gmm.fit_transform(features)

# GMM 학습 (3개 군집)
gmm = GaussianMixture(n_components=3, random_state=42, n_init=5)
gmm.fit(X_scaled)
labels = gmm.predict(X_scaled)

# ── 라벨 → 생산구분 번호 매핑 ────────────────────
# 평균 전력 기준 내림차순: 1=고생산, 2=중생산, 3=저생산
label_power = {}
for lbl in set(labels):
    label_power[lbl] = df_target.loc[labels == lbl, '평균'].mean()

sorted_labels = sorted(
    label_power, key=lambda x: label_power[x], reverse=True)
final_map = {sorted_labels[i]: i+1 for i in range(len(sorted_labels))}
df_target['GMM생산구분'] = [final_map[l] for l in labels]

# ── 생산량 4,000 이상 → 구분1 세분화 ─────────────
df_target.loc[
    (df_target['GMM생산구분'] == 3) & (df_target['생산량'] > 4000),
    'GMM생산구분'] = 2

# ── 구분4 없음: 소량·야간(39건) → 구분3으로 통합 ──
# 근거: 39건(0.45%)으로 학습 최소 기준 100건 미달
#       구분3과 통합 시 피크평균 변화 0.6kW 이내 (영향 미미)

# ── 합치기 → df_work 반영 ────────────────────────
df_combined = pd.concat([df_na, df_target], ignore_index=False)
df_combined = df_combined.sort_index()
df_work['GMM생산구분'] = df_combined['GMM생산구분'].fillna(0).astype(int)

# ── 결과 확인 ─────────────────────────────────────
print("=== GMM 생산구분 분포 (0~3) ===")
print(df_work['GMM생산구분'].value_counts().sort_index().to_string())

print("\n=== 생산구분별 통계 ===")
stats = df_work.groupby('GMM생산구분').agg(
    건수=('15분','count'),
    피크평균=('15분','mean'),
    피크최대=('15분','max'),
    생산량평균=('생산량','mean'),
).round(1)
stats.index = ['0(비가동)','1(고생산)','2(중생산)','3(저생산)']
print(stats.to_string())

print(f"\ndf_work 컬럼 수: {df_work.shape[1]}")
print("Step 29 완료 — 구분 0~3 (구분4 구분3으로 통합)")

# %% [markdown]
# # Step 30: 달력 파생변수 생성 (공장 여름휴가 포함)

# %%
# ================================================
# Step 30: 달력 파생변수 생성
# 공장 여름휴가: 7/31 ~ 8/8 (9일) is_holiday=1
# ================================================

# ── 2021년 법정공휴일 ─────────────────────────────
national_holidays = [
    20210101,  # 신정
    20210211,  # 설날 연휴
    20210212,  # 설날
    20210301,  # 삼일절
    20210505,  # 어린이날
    20210519,  # 부처님오신날
    20210816,  # 광복절 대체
    20210920,  # 추석 연휴
    20210921,  # 추석
    20210922,  # 추석 연휴
    20211003,  # 개천절
    20211004,  # 개천절 대체
    20211009,  # 한글날
    20211225,  # 크리스마스
]

# ── 공장 여름휴가 (7/31 ~ 8/8) ───────────────────
summer_vacation = [
    20210731,  # 토
    20210801,  # 일
    20210802,  # 월
    20210803,  # 화
    20210804,  # 수
    20210805,  # 목
    20210806,  # 금
    20210807,  # 토
    20210808,  # 일
]

# ── 전체 휴일 = 법정공휴일 + 여름휴가 ─────────────
all_holidays = national_holidays + summer_vacation

# ── 달력 파생변수 생성 ────────────────────────────
df_work['weekday']    = pd.to_datetime(
    df_work['날짜'].astype(str), format='%Y%m%d'
).dt.weekday

df_work['is_weekend'] = (df_work['weekday'] >= 5).astype(int)

df_work['is_holiday'] = df_work['날짜'].isin(all_holidays).astype(int)

df_work['주간여부']    = (
    (df_work['시간'] >= 8) & (df_work['시간'] <= 18)
).astype(int)

# ── 결과 확인 ─────────────────────────────────────
print("=== 달력 파생변수 완료 ===")
print(f"is_holiday = 1: {df_work['is_holiday'].sum():,}건")
print(f"is_weekend = 1: {df_work['is_weekend'].sum():,}건")
print(f"주간여부   = 1: {df_work['주간여부'].sum():,}건")

print("\n=== 여름휴가 반영 확인 ===")
vac = df_work[df_work['날짜'].isin(summer_vacation)].groupby('날짜').agg(
    is_holiday=('is_holiday','first'),
    생산량평균=('생산량','mean'),
).reset_index()
print(vac.to_string(index=False))

print(f"법정공휴일: {len(national_holidays)}일")
print(f"여름휴가  : {len(summer_vacation)}일")
print(f"합계      : {len(all_holidays)}일")
print(f"is_holiday=1 행 수: {df_work['is_holiday'].sum():,}건")
print("Step 30 완료")




# %% [markdown]
# # Step 31: 가동여부 파생변수 (피처 중요도 1위, 상관계수 0.73)

# %%
# ================================================
# Step 31: 가동여부 파생
# 생산량 > 0 = 1 (가동)
# 생산량 = 0 = 0 (비가동)
# 상관계수 1위 (0.73) — 피크 예측 핵심 변수
# ================================================

df_work['가동여부'] = (df_work['생산량'] > 0).astype(int)

# ── 결과 확인 ─────────────────────────────────────
on  = df_work['가동여부'].sum()
off = len(df_work) - on

print("=== 가동여부 분포 ===")
print(f"가동  (1): {on:,}건 ({on/len(df_work)*100:.1f}%)")
print(f"비가동(0): {off:,}건 ({off/len(df_work)*100:.1f}%)")

print(f"\n=== 가동여부별 평균 전력 (15분) ===")
chk = df_work.groupby('가동여부')['15분'].agg(['mean','min','max']).round(1)
chk.index = ['비가동(0)','가동(1)']
print(chk.to_string())

diff = (df_work[df_work['가동여부']==1]['15분'].mean() -
        df_work[df_work['가동여부']==0]['15분'].mean())
ratio = (df_work[df_work['가동여부']==1]['15분'].mean() /
         df_work[df_work['가동여부']==0]['15분'].mean())
print(f"\n가동 vs 비가동 전력 차이: {diff:.1f} kW")
print(f"가동 시 전력이 비가동 대비: {ratio:.2f}배")

print(f"\ndf_work 컬럼 수: {df_work.shape[1]}")
print("Step 31 완료")

# %% [markdown]
# # Step 32: furnace_on 열처리로 역추론
# # 비가동 중 전력≥60kW → 열처리로 예열 상태

# %%
# ================================================
# Step 32: furnace_on 열처리로 역추론
# 생산량=0 이지만 전력≥60kW → 열처리로 가동 중
# 비가동 중 최대 192kW 설명 가능
# ================================================

# ── 1단계: 기본 역추론 ───────────────────────────
df_work['furnace_on'] = 0

# 생산 중 → 열처리로 당연히 가동
df_work.loc[df_work['가동여부'] == 1, 'furnace_on'] = 1

# 비가동이지만 전력 60kW 이상 → 열처리로 예열 중
df_work.loc[
    (df_work['가동여부'] == 0) &
    (df_work['15분'] >= 60),
    'furnace_on'] = 1

# ── 2단계: 불확실 구간 보간 (30≤전력<60) ─────────
# -1 로 표시 후 ffill → 직전 상태 유지
ambiguous = (
    (df_work['가동여부'] == 0) &
    (df_work['15분'] >= 30) &
    (df_work['15분'] < 60)
)
df_work.loc[ambiguous, 'furnace_on'] = -1
df_work['furnace_on'] = (
    df_work['furnace_on']
    .replace(-1, np.nan)
    .fillna(method='ffill')
    .fillna(0)
    .astype(int)
)

# ── 결과 확인 ─────────────────────────────────────
total  = len(df_work)
on_cnt = df_work['furnace_on'].sum()

print("=== furnace_on 분포 ===")
print(f"ON  (가동): {on_cnt:,}건 ({on_cnt/total*100:.1f}%)")
print(f"OFF (휴지): {total-on_cnt:,}건 ({(total-on_cnt)/total*100:.1f}%)")

print(f"\n=== furnace_on별 평균 전력 (15분) ===")
chk = df_work.groupby('furnace_on')['15분'].agg(['mean','min','max']).round(1)
chk.index = ['OFF(0)','ON(1)']
print(chk.to_string())

print(f"\n=== 비가동 중 열처리로 ON 구간 ===")
rest = df_work[df_work['가동여부'] == 0]
furnace_rest = rest['furnace_on'].sum()
print(f"비가동 전체      : {len(rest):,}건")
print(f"열처리로 ON 추정 : {furnace_rest:,}건 ({furnace_rest/len(rest)*100:.1f}%)")
print(f"최대 전력        : {rest[rest['furnace_on']==1]['15분'].max():.1f} kW")
print(f"평균 전력        : {rest[rest['furnace_on']==1]['15분'].mean():.1f} kW")

print(f"\ndf_work 컬럼 수: {df_work.shape[1]}")
print("Step 32 완료")

# %% [markdown]
# # Step 33: TOU 요금구간 / SMP / CO2 / 인건비 병합

# %%
# ================================================
# Step 33: TOU / SMP / CO2 / 인건비 병합
# TOU: 한전 산업용 갑 기준
# SMP: 2021년 월별 실측값 (EPSIS)
# CO2: 0.4153 tCO2eq/MWh (온실가스종합정보센터)
# ================================================

# ── TOU 구간 함수 ─────────────────────────────────
def get_tou(month, hour, is_holiday, is_weekend):
    if is_holiday or is_weekend:
        return 0, 95.7      # 경부하
    if month in [6, 7, 8]:  # 여름
        if hour in [10,11,12,13,14,15,16,17]:
            return 2, 155.0  # 최대부하
        if hour in [22,23,0,1,2,3,4,5]:
            return 0, 95.7
        return 1, 121.5
    elif month in [11, 12, 1, 2]:  # 겨울
        if hour in [9,10,17,18,19]:
            return 2, 155.0
        if hour in [22,23,0,1,2,3,4,5]:
            return 0, 95.7
        return 1, 121.5
    else:                           # 봄가을
        if hour in [10,11,12,13,14,15,16,17]:
            return 1, 121.5
        if hour in [22,23,0,1,2,3,4,5]:
            return 0, 95.7
        return 1, 121.5

tou_results = df_work.apply(
    lambda r: get_tou(r['m'], r['시간'], r['is_holiday'], r['is_weekend']),
    axis=1)
df_work['tou_bucket'] = [x[0] for x in tou_results]
df_work['tou_price']  = [x[1] for x in tou_results]

# ── SMP 2021년 월별 실측값 (EPSIS CSV) ──────────
smp_map = {
     1: 70.47,  2: 75.25,  3: 83.78,
     4: 75.97,  5: 78.93,  6: 82.72,
     7: 87.04,  8: 93.41,  9: 98.21,
    10:107.53, 11:126.83, 12:142.46
}
df_work['smp_land']  = df_work['m'].map(smp_map)
df_work['smp_total'] = (df_work['smp_land'] * 1.02).round(2)

# ── CO2 탄소배출계수 ──────────────────────────────
# 출처: 온실가스종합정보센터 2021년 국가 전력배출계수
EMISSION_FACTOR = 0.4153  # tCO2eq/MWh
df_work['co2_kg'] = (
    df_work['15분'] / 1000 * EMISSION_FACTOR * 1000
).round(2)

# ── 인건비 (주간=1.0 / 야간=1.5) ─────────────────
df_work['인건비'] = df_work['시간'].apply(
    lambda h: 1.0 if 8 <= h <= 18 else 1.5)

# ── 결과 확인 ─────────────────────────────────────
print("=== TOU 구간 분포 ===")
tou_check = df_work.groupby(['tou_bucket','tou_price'])['15분'].count()
for (bucket, price), cnt in tou_check.items():
    label = ['경부하','중간부하','최대부하'][bucket]
    print(f"  구간{bucket} {label:5s} ({price}원/kWh): {cnt:,}건")

print(f"\n=== SMP 범위 ===")
print(f"  smp_land : {df_work['smp_land'].min():.2f} ~ {df_work['smp_land'].max():.2f} 원/kWh")
print(f"  smp_total: {df_work['smp_total'].min():.2f} ~ {df_work['smp_total'].max():.2f} 원/kWh")

print(f"\n=== CO2 배출량 ===")
print(f"  배출계수 : {EMISSION_FACTOR} tCO2eq/MWh")
print(f"  co2_kg 평균: {df_work['co2_kg'].mean():.2f} kg/h")
print(f"  co2_kg 최대: {df_work['co2_kg'].max():.2f} kg/h")

print(f"\n=== 월별 탄소배출 요약 ===")
monthly_co2 = df_work.groupby('m').agg(
    월전력kWh=('15분','sum'),
    월탄소tCO2=('co2_kg', lambda x: round(x.sum()/1000, 2))
).reset_index()
print(monthly_co2.to_string(index=False))

print(f"\ndf_work 컬럼 수: {df_work.shape[1]}")
print("Step 33 완료")

# %% [markdown]
# # Step 33-1: log1p 변환 (우상향 분포 보정 — 14번 노트북 흡수)

# %%
# ================================================
# Step 33-1: log1p 변환
# 우상향 분포 변수를 정규분포에 가깝게 변환
# 대상: 생산량, 강수량, 공장인원, 풍속
# 14번 노트북에서 흡수
# ================================================

log_cols = ['생산량', '강수량', '공장인원', '풍속']

print("=== log1p 변환 전후 비교 ===")
for col in log_cols:
    before_mean = df_work[col].mean()
    before_std  = df_work[col].std()
    before_max  = df_work[col].max()
    after_vals  = np.log1p(df_work[col])
    after_mean  = after_vals.mean()
    after_std   = after_vals.std()
    after_max   = after_vals.max()
    print(f"\n  [{col}]")
    print(f"    변환 전: 평균={before_mean:.2f}, std={before_std:.2f}, max={before_max:.2f}")
    print(f"    변환 후: 평균={after_mean:.2f}, std={after_std:.2f}, max={after_max:.2f}")

# df_log = 원본 보존 + 변환 적용 사본
df_log = df_work.copy()
for col in log_cols:
    df_log[col] = np.log1p(df_work[col])

print(f"\n원본 df_work: {df_work.shape} (보존)")
print(f"변환 df_log : {df_log.shape} (모델 학습용)")
print("Step 33-1 완료")

# %% [markdown]
# # Step 33-2: okm_enriched_final.csv 저장

# %%
# ================================================
# Step 33-2: 최종 피처 데이터 저장
# df_log (log1p 변환 완료본) → okm_enriched_final.csv
# ================================================

import os

os.makedirs('./data', exist_ok=True)

# 결측치 최종 확인
missing = df_log.isnull().sum()
missing = missing[missing > 0]
if len(missing) == 0:
    print("결측치 없음 ✅")
else:
    print("결측치 있는 컬럼:")
    print(missing.to_string())

# 저장
save_path = './data/okm_enriched_final.csv'
df_log.to_csv(save_path, index=False, encoding='utf-8-sig')
size_kb = os.path.getsize(save_path) / 1024

print(f"\n=== 최종 데이터 요약 ===")
print(f"행 수      : {len(df_log):,}")
print(f"컬럼 수    : {df_log.shape[1]}")
print(f"날짜 범위  : {df_log['날짜'].min()} ~ {df_log['날짜'].max()}")
print(f"파일 크기  : {size_kb:.1f} KB")
print(f"저장 경로  : {save_path}")

print(f"\n=== 전체 컬럼 목록 ===")
for i, col in enumerate(df_log.columns, 1):
    print(f"  {i:2d}. {col}")

print("\nStep 33-2 완료")


# %% [markdown]
# # Step 34: Feature Set A / B / C / D 정의 + Train/Test 분할

# %%
# ================================================
# Step 34: Feature Set A / B / C 정의
# Set_A: 날짜·시간·달력만
# Set_B: Set_A + 날씨
# Set_C: Set_B + 생산·GMM·furnace_on·전기요금 전체
# co2_kg 제외 (타겟 직접 파생 — 데이터 누수)
# Train/Test: 랜덤 8:2, random_state=42
# ================================================
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

TARGET = '15분'

def safe_cols(cols):
    missing = [c for c in cols if c not in df_log.columns]
    if missing:
        print(f"  없는 컬럼 제외: {missing}")
    return [c for c in cols if c in df_log.columns]

FEATURE_SETS = {
    # Set_A: 날짜·시간·달력 파생만
    'Set_A': safe_cols([
        '시간', 'day', 'd', 'm',
        'weekday', 'is_weekend', 'is_holiday', '주간여부',
    ]),
    # Set_B: Set_A + 날씨
    'Set_B': safe_cols([
        '시간', 'day', 'd', 'm',
        'weekday', 'is_weekend', 'is_holiday', '주간여부',
        '기온', '습도', '풍속', '강수량',
    ]),
    # Set_C: Set_B + 생산정보 + GMM + furnace_on + 전기요금
    'Set_C': safe_cols([
        '시간', 'day', 'd', 'm',
        'weekday', 'is_weekend', 'is_holiday', '주간여부',
        '기온', '습도', '풍속', '강수량',
        '생산량', '가동여부', '공장인원',
        'GMM생산구분', 'furnace_on',
        '전기요금(계절)', 'tou_bucket', 'tou_price',
        'smp_land', '인건비',
    ]),
}

print("=== Feature Set 구성 ===")
for name, cols in FEATURE_SETS.items():
    print(f"  {name} ({len(cols):2d}개): {cols}")

# ── Train/Test 분할 (랜덤 8:2) ───────────────────
X_all = df_log[FEATURE_SETS['Set_C']]
y     = df_log[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X_all, y, test_size=0.2, random_state=42
)

# ── Set별 슬라이싱 ────────────────────────────────
splits = {}
for name, cols in FEATURE_SETS.items():
    splits[name] = {
        'X_train': X_train[cols],
        'X_test' : X_test[cols],
    }

# ── 스케일링 (DNN·Linear용) ───────────────────────
scalers = {}
for name, cols in FEATURE_SETS.items():
    sc = StandardScaler()
    splits[name]['X_train_sc'] = sc.fit_transform(splits[name]['X_train'])
    splits[name]['X_test_sc']  = sc.transform(splits[name]['X_test'])
    scalers[name] = sc

# ── 결과 확인 ─────────────────────────────────────
print(f"\n=== Train/Test 분할 결과 ===")
print(f"전체  : {len(df_log):,}행")
print(f"Train : {len(X_train):,}행 ({len(X_train)/len(df_log)*100:.1f}%)")
print(f"Test  : {len(X_test):,}행  ({len(X_test)/len(df_log)*100:.1f}%)")

print(f"\n=== y(타겟) 분포 비교 ===")
print(f"Train 평균: {y_train.mean():.1f} kW / 표준편차: {y_train.std():.1f}")
print(f"Test  평균: {y_test.mean():.1f} kW / 표준편차: {y_test.std():.1f}")

print(f"\n=== 피크 등급 분포 (Train vs Test) ===")
def grade_dist(s):
    return {
        '양호(<70)'   : (s<70).sum(),
        '주의(70~110)' : ((s>=70)&(s<110)).sum(),
        '위험(110~150)': ((s>=110)&(s<150)).sum(),
        '초과(>=150)'  : (s>=150).sum(),
    }
gd_train = grade_dist(y_train)
gd_test  = grade_dist(y_test)
for key in gd_train:
    tr_r = gd_train[key]/len(y_train)*100
    te_r = gd_test[key]/len(y_test)*100
    print(f"  {key}: Train={gd_train[key]:,}건({tr_r:.1f}%) "
          f"/ Test={gd_test[key]:,}건({te_r:.1f}%)")

print(f"\n=== Feature Set 요약 ===")
print(f"  Set_A ({len(FEATURE_SETS['Set_A'])}개): 날짜·시간·달력")
print(f"  Set_B ({len(FEATURE_SETS['Set_B'])}개): Set_A + 날씨 4종")
print(f"  Set_C ({len(FEATURE_SETS['Set_C'])}개): Set_B + 생산·GMM·furnace_on·전기요금")
print(f"  * co2_kg 제외 (타겟 직접 파생 변수)")
print("\nStep 34 완료")

# %% [markdown]
# # Feature Set 구성표 시각화

# %%
# ================================================
# Feature Set A / B / C 구성표 시각화
# ================================================
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

feature_info = [
    # (피처명, 카테고리, 출처, SetA, SetB, SetC, 설명)
    ('시간',          '시간/달력', 'OKM 원본',    True,  True,  True,  '0~23시'),
    ('day',          '시간/달력', 'OKM 원본',    True,  True,  True,  '요일 번호 1~7'),
    ('d',            '시간/달력', 'OKM 원본',    True,  True,  True,  '일(日) 1~31'),
    ('m',            '시간/달력', 'OKM 원본',    True,  True,  True,  '월(月) 1~12'),
    ('weekday',      '시간/달력', '원본 파생',   True,  True,  True,  '0=월~6=일'),
    ('is_weekend',   '시간/달력', '원본 파생',   True,  True,  True,  '주말=1 / 평일=0'),
    ('is_holiday',   '시간/달력', '원본 파생',   True,  True,  True,  '공휴일·여름휴가=1'),
    ('주간여부',       '시간/달력', '원본 파생',   True,  True,  True,  '8~18시=1'),
    ('기온',          '날씨',    'OKM+OBS',    False, True,  True,  '외기 온도(°C)'),
    ('습도',          '날씨',    'OKM 원본',    False, True,  True,  '상대습도(%)'),
    ('풍속',          '날씨',    'OKM 원본',    False, True,  True,  '풍속(m/s)'),
    ('강수량',         '날씨',    'OKM 원본',    False, True,  True,  '강수량(mm)'),
    ('생산량',         '생산',    'OKM 원본',    False, False, True,  '시간당 생산 수량(개)'),
    ('가동여부',        '생산',    '원본 파생',   False, False, True,  '생산량>0=1'),
    ('공장인원',        '생산',    'OKM 원본',    False, False, True,  '근무 인원 수(명)'),
    ('GMM생산구분',    '생산',    'GMM 파생',    False, False, True,  '공정패턴 0~3'),
    ('furnace_on',   '생산',    '전력 역추론',  False, False, True,  '열처리로 가동=1'),
    ('전기요금(계절)', '전기요금', 'OKM 원본',    False, False, True,  '계절별 단가(원/kWh)'),
    ('tou_bucket',   '전기요금', '한전 룰 파생', False, False, True,  '경=0/중=1/최대=2'),
    ('tou_price',    '전기요금', '한전 룰 파생', False, False, True,  '95.7/121.5/155원'),
    ('smp_land',     '전기요금', 'EPSIS CSV',   False, False, True,  '월별 SMP(원/kWh)'),
    ('인건비',         '생산',    'OKM 원본',    False, False, True,  '주간=1.0/야간=1.5'),
]

n = len(feature_info)

set_colors = {
    'A': '#2196F3',
    'B': '#4CAF50',
    'C': '#FF9800',
}
cat_colors = {
    '생산'    : '#E8A0A0',
    '시간/달력': '#A0C4E8',
    '날씨'    : '#A0E8B0',
    '전기요금' : '#F0D080',
}

fig, ax = plt.subplots(figsize=(14, 13))
ax.set_xlim(0, 10.5)
ax.set_ylim(-0.5, n - 0.5)
ax.axis('off')

col_x = {
    'num'   : 0.15,
    'feat'  : 0.65,
    'cat'   : 2.55,
    'source': 3.85,
    'setA'  : 5.3,
    'setB'  : 6.1,
    'setC'  : 6.9,
    'desc'  : 7.6,
}

# ── 헤더 ─────────────────────────────────────────
header_y = n - 0.2
for col, label, ha in [
    ('num',    '#',       'center'),
    ('feat',   '피처명',   'left'),
    ('cat',    '카테고리', 'center'),
    ('source', '출처',    'center'),
    ('setA',   'Set A',  'center'),
    ('setB',   'Set B',  'center'),
    ('setC',   'Set C',  'center'),
    ('desc',   '설명',    'left'),
]:
    ax.text(col_x[col], header_y, label, ha=ha, va='center',
            fontsize=9, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.3', fc='#37474F', ec='none'))

ax.axhline(n-0.5, color='#37474F', linewidth=1.5)

# ── 행 그리기 ─────────────────────────────────────
src_color_map = {
    'OKM 원본'   : '#BBDEFB',
    '원본 파생'   : '#E1BEE7',
    'OKM+OBS'   : '#B2EBF2',
    'GMM 파생'   : '#D1C4E9',
    '한전 룰 파생': '#FFF9C4',
    'EPSIS CSV' : '#FFE0B2',
    '전력 역추론' : '#F8BBD0',
}

for i, row in enumerate(feature_info):
    feat, cat, src, sa, sb, sc, desc = row
    y = n - 2 - i

    bg = '#FAFAFA' if i % 2 == 0 else '#F0F0F0'
    ax.barh(y, 10.5, left=0, height=0.85, color=bg, zorder=0)

    ax.text(col_x['num'],  y, str(i+1),
            ha='center', va='center', fontsize=8, color='#666')
    ax.text(col_x['feat'], y, feat,
            ha='left', va='center', fontsize=8.5, fontweight='bold')
    ax.text(col_x['cat'],  y, cat,
            ha='center', va='center', fontsize=7.5,
            bbox=dict(boxstyle='round,pad=0.25',
                      fc=cat_colors.get(cat,'#EEE'), ec='none'))
    ax.text(col_x['source'], y, src,
            ha='center', va='center', fontsize=7.5,
            bbox=dict(boxstyle='round,pad=0.25',
                      fc=src_color_map.get(src,'#EEE'), ec='none'))

    for flag, col_key, key in [
        (sa, 'setA', 'A'),
        (sb, 'setB', 'B'),
        (sc, 'setC', 'C'),
    ]:
        if flag:
            ax.text(col_x[col_key], y, 'O',
                    ha='center', va='center',
                    fontsize=11, fontweight='bold',
                    color=set_colors[key])
        else:
            ax.text(col_x[col_key], y, '-',
                    ha='center', va='center',
                    fontsize=10, color='#CCCCCC')

    ax.text(col_x['desc'], y, desc,
            ha='left', va='center', fontsize=7.5, color='#555')

# ── 구분선 ────────────────────────────────────────
# Set_A 끝 (8번째 피처 이후)
ax.axhline(n-2-7.5, color='#4CAF50',
           linewidth=1.2, linestyle='--', alpha=0.6)
# Set_B 끝 (12번째 피처 이후)
ax.axhline(n-2-11.5, color='#FF9800',
           linewidth=1.2, linestyle='--', alpha=0.6)

# ── 범례 ─────────────────────────────────────────
set_a_cnt = sum(r[3] for r in feature_info)
set_b_cnt = sum(r[4] for r in feature_info)
set_c_cnt = sum(r[5] for r in feature_info)
legend_patches = [
    mpatches.Patch(color=set_colors['A'],
                   label=f"Set A ({set_a_cnt}개)  날짜·시간·달력"),
    mpatches.Patch(color=set_colors['B'],
                   label=f"Set B ({set_b_cnt}개)  Set A + 날씨"),
    mpatches.Patch(color=set_colors['C'],
                   label=f"Set C ({set_c_cnt}개)  Set B + 생산·GMM·furnace_on·전기요금"),
]
ax.legend(handles=legend_patches, loc='lower right',
          fontsize=9, framealpha=0.9)

plt.title('Feature Set A / B / C 구성 피처 상세표',
          fontsize=13, fontweight='bold', pad=12)
plt.tight_layout()
plt.show()
print("Feature Set 구성표 완료")

# %% [markdown]
# # Step 35: LinearRegression

# %%
# ================================================
# Step 35: LinearRegression
# ================================================
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

results = []

def evaluate(model_name, model, X_tr, X_te, y_tr, y_te, set_name):
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    r2   = r2_score(y_te, pred)
    rmse = np.sqrt(mean_squared_error(y_te, pred))
    mae  = mean_absolute_error(y_te, pred)
    results.append({
        '모델': model_name, 'Set': set_name,
        'R²': round(r2,4), 'RMSE': round(rmse,2), 'MAE': round(mae,2),
    })
    print(f"  {model_name:20s} [{set_name:8s}] "
          f"R²={r2:.4f}  RMSE={rmse:.2f}  MAE={mae:.2f}")
    return model

print("=== Step 35: LinearRegression ===")
for fs_name in FEATURE_SETS:
    evaluate('LinearReg', LinearRegression(),
             splits[fs_name]['X_train_sc'],
             splits[fs_name]['X_test_sc'],
             y_train, y_test, fs_name)

print("Step 35 완료")

# %% [markdown]
# # Step 36: Ridge

# %%
# ================================================
# Step 36: Ridge
# ================================================
from sklearn.linear_model import Ridge

print("=== Step 36: Ridge ===")
for fs_name in FEATURE_SETS:
    evaluate('Ridge', Ridge(alpha=1.0),
             splits[fs_name]['X_train_sc'],
             splits[fs_name]['X_test_sc'],
             y_train, y_test, fs_name)

print("Step 36 완료")

# %% [markdown]
# # Step 37: DecisionTree

# %%
# ================================================
# Step 37: DecisionTree
# ================================================
from sklearn.tree import DecisionTreeRegressor

print("=== Step 37: DecisionTree ===")
for fs_name in FEATURE_SETS:
    evaluate('DecisionTree',
             DecisionTreeRegressor(random_state=42),
             splits[fs_name]['X_train'],
             splits[fs_name]['X_test'],
             y_train, y_test, fs_name)

print("Step 37 완료")

# %% [markdown]
# # Step 38: RandomForest

# %%
# ================================================
# Step 38: RandomForest
# n_jobs=1 필수 (Windows TerminatedWorkerError 방지)
# ================================================
from sklearn.ensemble import RandomForestRegressor

print("=== Step 38: RandomForest ===")
for fs_name in FEATURE_SETS:
    evaluate('RandomForest',
             RandomForestRegressor(
                 n_estimators=100,
                 random_state=42,
                 n_jobs=1),
             splits[fs_name]['X_train'],
             splits[fs_name]['X_test'],
             y_train, y_test, fs_name)

print("\n=== 중간 결과 요약 ===")
df_results = pd.DataFrame(results).sort_values(
    ['Set','R²'], ascending=[True,False])
print(df_results.to_string(index=False))

print("Step 38 완료")

# %% [markdown]
# # Step 39: XGBoost

# %%
# ================================================
# Step 39: XGBoost
# n_jobs=1 필수 (Windows TerminatedWorkerError 방지)
# ================================================
from xgboost import XGBRegressor

print("=== Step 39: XGBoost ===")
for fs_name in FEATURE_SETS:
    evaluate('XGBoost',
             XGBRegressor(
                 n_estimators=300,
                 random_state=42,
                 verbosity=0,
                 n_jobs=1),
             splits[fs_name]['X_train'],
             splits[fs_name]['X_test'],
             y_train, y_test, fs_name)

print("\n=== 현재까지 전체 결과 ===")
df_results = pd.DataFrame(results).sort_values(
    ['Set','R²'], ascending=[True,False])
print(df_results.to_string(index=False))

print("Step 39 완료")

# %% [markdown]
# # Step 40: DNN 3종 (Shallow / Medium / Deep)

# %%
# ================================================
# Step 40: DNN 3종 (Set_C 기준만 학습)
# ================================================
from sklearn.neural_network import MLPRegressor

print("=== Step 40: DNN 3종 (Set_C 기준) ===")

dnn_models = {
    'DNN-Shallow' : (64,),
    'DNN-Medium'  : (128, 64),
    'DNN-Deep'    : (128, 64, 32),
}

for model_name, layers in dnn_models.items():
    evaluate(model_name,
             MLPRegressor(
                 hidden_layer_sizes=layers,
                 max_iter=500,
                 random_state=42,
                 early_stopping=True),
             splits['Set_C']['X_train_sc'],
             splits['Set_C']['X_test_sc'],
             y_train, y_test, 'Set_C')

print("\n=== Set_C 기준 모델 순위 ===")
df_c = pd.DataFrame(results)
df_c = df_c[df_c['Set']=='Set_C'].sort_values('R²', ascending=False)
print(df_c.to_string(index=False))

print("\n=== 전체 결과 요약 ===")
df_all = pd.DataFrame(results).sort_values(
    ['Set','R²'], ascending=[True,False])
print(df_all.to_string(index=False))

print("Step 40 완료")

# %% [markdown]
# # Step 41: XGBoost 하이퍼파라미터 튜닝 (RandomizedSearchCV)

# %%
# ================================================
# Step 41: XGBoost 하이퍼파라미터 튜닝
# Set_C 기준 / RandomizedSearchCV
# n_jobs=1 필수 (Windows TerminatedWorkerError 방지)
# ================================================
from sklearn.model_selection import RandomizedSearchCV

X_tr_C = splits['Set_C']['X_train']
X_te_C = splits['Set_C']['X_test']

param_dist = {
    'n_estimators'    : [200, 300, 500],
    'max_depth'       : [4, 6, 8],
    'learning_rate'   : [0.05, 0.1, 0.2],
    'subsample'       : [0.7, 0.8, 1.0],
    'colsample_bytree': [0.7, 0.8, 1.0],
    'min_child_weight': [1, 3, 5],
}

xgb_search = RandomizedSearchCV(
    XGBRegressor(random_state=42, verbosity=0, n_jobs=1),
    param_distributions=param_dist,
    n_iter=10,
    cv=3,
    scoring='r2',
    random_state=42,
    n_jobs=1,
    verbose=1,
)

print("XGBoost 튜닝 중... (3~5분 소요)")
xgb_search.fit(X_tr_C, y_train)

# ── 최적 모델 평가 ────────────────────────────────
best_xgb  = xgb_search.best_estimator_
pred_tune = best_xgb.predict(X_te_C)
r2_tune   = r2_score(y_test, pred_tune)
rmse_tune = np.sqrt(mean_squared_error(y_test, pred_tune))
mae_tune  = mean_absolute_error(y_test, pred_tune)

xgb_before = [r['R²'] for r in results
               if r['모델']=='XGBoost' and r['Set']=='Set_C'][0]

print(f"\n=== XGBoost 튜닝 결과 ===")
print(f"최적 파라미터: {xgb_search.best_params_}")
print(f"튜닝 전 R²  : {xgb_before}")
print(f"튜닝 후 R²  : {r2_tune:.4f}")
print(f"튜닝 후 RMSE: {rmse_tune:.2f} kW")
print(f"튜닝 후 MAE : {mae_tune:.2f} kW")

# results에 추가
results.append({
    '모델': 'XGBoost-Tuned', 'Set': 'Set_C',
    'R²'  : round(r2_tune, 4),
    'RMSE': round(rmse_tune, 2),
    'MAE' : round(mae_tune, 2),
})

print("\n=== 전체 최종 결과 ===")
df_final = pd.DataFrame(results).sort_values('R²', ascending=False)
print(df_final.to_string(index=False))

print("Step 41 완료")

# %% [markdown]
# # Step 42: 피처 중요도 시각화 (XGBoost 튜닝 후)

# %%
# ================================================
# Step 42: 피처 중요도 Top 15 시각화
# XGBoost-Tuned (Set_C 기준)
# ================================================
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

importances = best_xgb.feature_importances_
feat_names  = FEATURE_SETS['Set_C']

feat_imp_df = pd.DataFrame({
    'Feature'   : feat_names,
    'Importance': importances
}).sort_values('Importance', ascending=False)

top15 = feat_imp_df.head(15)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# ── 좌: Top 15 막대 차트 ──────────────────────────
colors = ['#E74C3C' if i < 3 else
          '#F39C12' if i < 7 else
          '#3498DB' for i in range(len(top15))]

axes[0].barh(top15['Feature'][::-1],
             top15['Importance'][::-1],
             color=colors[::-1], edgecolor='white')
axes[0].set_xlabel('Feature Importance')
axes[0].set_title('XGBoost 피처 중요도 Top 15 (Set_C)',
                  fontweight='bold')
axes[0].axvline(top15['Importance'].mean(),
                color='gray', linestyle='--', linewidth=1.2,
                label=f"평균: {top15['Importance'].mean():.3f}")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3, axis='x')

# ── 우: 누적 기여도 ───────────────────────────────
feat_imp_df['cumsum'] = feat_imp_df['Importance'].cumsum()
feat_imp_df['rank']   = range(1, len(feat_imp_df)+1)

axes[1].plot(feat_imp_df['rank'],
             feat_imp_df['cumsum'],
             color='#2E86C1', linewidth=2,
             marker='o', markersize=4)
axes[1].axhline(0.8, color='#E74C3C', linestyle='--',
                linewidth=1.2, label='80% 기여도')
axes[1].axhline(0.9, color='#F39C12', linestyle='--',
                linewidth=1.2, label='90% 기여도')
axes[1].set_xlabel('피처 순위')
axes[1].set_ylabel('누적 중요도')
axes[1].set_title('피처 누적 기여도', fontweight='bold')
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)

plt.suptitle('XGBoost-Tuned 피처 중요도 분석 (Set_C)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.show()

# ── 결과 출력 ─────────────────────────────────────
print("=== 피처 중요도 Top 10 ===")
print(feat_imp_df.head(10)[['Feature','Importance']].to_string(index=False))

n_80 = (feat_imp_df['cumsum'] <= 0.8).sum() + 1
n_90 = (feat_imp_df['cumsum'] <= 0.9).sum() + 1
print(f"\n상위 {n_80}개 피처 → 전체 중요도의 80% 설명")
print(f"상위 {n_90}개 피처 → 전체 중요도의 90% 설명")

print("\nStep 42 완료")

# %% [markdown]
# # Step 43: 성능 비교 시각화 (R² 히트맵 + 막대 차트)

# %%
# ================================================
# Step 43: 성능 비교 시각화
# R² 히트맵 + Set_C 기준 막대 차트 + RMSE 비교
# ================================================
import seaborn as sns
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

df_res = pd.DataFrame(results)

# ── Feature Set 정의 출력 ─────────────────────────
print("=" * 60)
print("  Feature Set A / B / C 정의")
print("=" * 60)
print(f"  Set_A ({len(FEATURE_SETS['Set_A'])}개): 날짜·시간·달력")
print(f"  Set_B ({len(FEATURE_SETS['Set_B'])}개): Set_A + 날씨 4종")
print(f"  Set_C ({len(FEATURE_SETS['Set_C'])}개): Set_B + 생산·GMM·furnace_on·전기요금")
print("=" * 60)

# ── R² 히트맵 ─────────────────────────────────────
common_models = ['LinearReg','Ridge','DecisionTree',
                 'RandomForest','XGBoost']
df_heatmap = df_res[df_res['모델'].isin(common_models)]
pivot = df_heatmap.pivot_table(
    index='모델', columns='Set', values='R²').round(4)
col_order = [c for c in ['Set_A','Set_B','Set_C']
             if c in pivot.columns]
pivot = pivot[col_order]

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt='.4f', cmap='YlGn',
            linewidths=0.5, vmin=0.5, vmax=1.0, ax=ax,
            annot_kws={'size': 10})
ax.set_title('R² 히트맵 — Feature Set별 모델 성능 비교',
             fontsize=12, fontweight='bold')
ax.set_xlabel('Feature Set')
ax.set_ylabel('모델')
plt.tight_layout()
plt.show()

# ── Set_C 기준 R² 막대 차트 ──────────────────────
df_setC = df_res[df_res['Set'] == 'Set_C'].copy()
df_setC = df_setC.sort_values('R²', ascending=True)

colors = []
for m in df_setC['모델']:
    if 'Tuned'   in m: colors.append('#E74C3C')
    elif 'XGBoost' in m: colors.append('#F39C12')
    elif 'DNN'   in m: colors.append('#9B59B6')
    elif 'Forest' in m: colors.append('#2ECC71')
    else: colors.append('#3498DB')

fig2, ax2 = plt.subplots(figsize=(10, 6))
bars = ax2.barh(df_setC['모델'], df_setC['R²'],
                color=colors, edgecolor='white', alpha=0.88)
ax2.set_xlabel('R²')
ax2.set_title('Set_C 기준 전체 모델 성능 비교 (R²)',
              fontsize=12, fontweight='bold')
ax2.axvline(0.9,  color='gray', linestyle='--',
            linewidth=1.2, label='R²=0.9 기준선')
ax2.axvline(0.99, color='red',  linestyle='--',
            linewidth=1.2, label='R²=0.99 기준선')
ax2.legend(fontsize=9)
ax2.set_xlim(0, 1.05)
for bar, val in zip(bars, df_setC['R²']):
    ax2.text(val + 0.005, bar.get_y() + bar.get_height()/2,
             f'{val:.4f}', va='center', fontsize=9,
             fontweight='bold')
plt.tight_layout()
plt.show()

# ── Set_C 기준 RMSE 비교 ─────────────────────────
df_setC_rmse = df_setC.sort_values('RMSE', ascending=False)
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.barh(df_setC_rmse['모델'], df_setC_rmse['RMSE'],
         color='#5DADE2', edgecolor='white', alpha=0.85)
ax3.set_xlabel('RMSE (kW)')
ax3.set_title('Set_C 기준 RMSE 비교 (낮을수록 좋음)',
              fontsize=12, fontweight='bold')
for i, (_, row) in enumerate(df_setC_rmse.iterrows()):
    ax3.text(row['RMSE'] + 0.1, i,
             f"{row['RMSE']:.2f} kW", va='center', fontsize=9)
plt.tight_layout()
plt.show()

# ── 최종 순위 출력 ────────────────────────────────
print("\n=== Set_C 기준 최종 모델 순위 ===")
print(df_setC.sort_values('R²', ascending=False).to_string(index=False))

print("\nStep 43 완료")

# %% [markdown]
# # Step 44: 예측 결과 시각화 (실제값 vs 예측값)

# %%
# ================================================
# Step 44: 예측 결과 시각화
# 실제값 vs 예측값 — 선 그래프 / 산점도 / 잔차 / 등급별
# XGBoost-Tuned (Set_C 기준)
# ================================================
from matplotlib.patches import Patch

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 예측값 생성 ───────────────────────────────────
pred_tuned = best_xgb.predict(splits['Set_C']['X_test'])
y_true     = y_test.values
residuals  = y_true - pred_tuned
n_sample   = 200

# 시간 순서로 정렬
sort_idx  = np.argsort(y_test.index)[:n_sample]
y_true_s  = y_true[sort_idx]
y_pred_s  = pred_tuned[sort_idx]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# ── 1. 실제 vs 예측 선 그래프 ────────────────────
axes[0,0].plot(range(n_sample), y_true_s,
               color='#2E86C1', linewidth=1.5,
               label='실제값', alpha=0.8)
axes[0,0].plot(range(n_sample), y_pred_s,
               color='#E74C3C', linewidth=1.5,
               linestyle='--', label='예측값', alpha=0.8)
axes[0,0].fill_between(range(n_sample),
                        y_true_s, y_pred_s,
                        alpha=0.1, color='gray',
                        label='오차 구간')
axes[0,0].set_xlabel('샘플 순서')
axes[0,0].set_ylabel('피크 전력 (kW)')
axes[0,0].set_title(
    f'실제값 vs 예측값 (XGBoost-Tuned, 샘플 {n_sample}개)',
    fontweight='bold')
axes[0,0].legend(fontsize=9)
axes[0,0].grid(alpha=0.3)

# ── 2. 산점도 (등급별 색상) ───────────────────────
grade_colors = []
for v in y_true:
    if   v < 70:  grade_colors.append('#2ECC71')
    elif v < 110: grade_colors.append('#3498DB')
    elif v < 150: grade_colors.append('#F39C12')
    else:         grade_colors.append('#E74C3C')

axes[0,1].scatter(y_true, pred_tuned,
                  c=grade_colors, alpha=0.4, s=15)
max_val = max(y_true.max(), pred_tuned.max())
axes[0,1].plot([0, max_val], [0, max_val],
               'k--', linewidth=1.5, label='완벽한 예측선')
axes[0,1].set_xlabel('실제값 (kW)')
axes[0,1].set_ylabel('예측값 (kW)')
axes[0,1].set_title('실제값 vs 예측값 산점도 (등급별 색상)',
                     fontweight='bold')
axes[0,1].grid(alpha=0.3)
legend_els = [
    Patch(color='#2ECC71', label='양호 (<70kW)'),
    Patch(color='#3498DB', label='주의 (70~110kW)'),
    Patch(color='#F39C12', label='위험 (110~150kW)'),
    Patch(color='#E74C3C', label='초과 (>=150kW)'),
]
axes[0,1].legend(handles=legend_els, fontsize=8,
                 loc='upper left')

# ── 3. 잔차 분포 ──────────────────────────────────
axes[1,0].hist(residuals, bins=50,
               color='#5DADE2', edgecolor='white', alpha=0.85)
axes[1,0].axvline(0, color='red', linestyle='--',
                  linewidth=1.5, label='잔차=0')
axes[1,0].axvline(residuals.mean(), color='orange',
                  linestyle='--', linewidth=1.5,
                  label=f'평균={residuals.mean():.2f}')
axes[1,0].set_xlabel('잔차 (실제 - 예측)')
axes[1,0].set_ylabel('빈도')
axes[1,0].set_title('잔차 분포 (정규분포에 가까울수록 좋음)',
                     fontweight='bold')
axes[1,0].legend(fontsize=9)
axes[1,0].grid(alpha=0.3)

# ── 4. 등급별 예측 정확도 ─────────────────────────
grade_names  = ['양호\n(<70)', '주의\n(70~110)',
                '위험\n(110~150)', '초과\n(>=150)']
grade_ranges = [(0,70),(70,110),(110,150),(150,300)]
grade_r2s, grade_rmses, grade_cnts = [], [], []

for low, high in grade_ranges:
    mask = (y_true >= low) & (y_true < high)
    if mask.sum() > 0:
        g_r2   = r2_score(y_true[mask], pred_tuned[mask])
        g_rmse = np.sqrt(mean_squared_error(
            y_true[mask], pred_tuned[mask]))
        grade_r2s.append(round(g_r2, 4))
        grade_rmses.append(round(g_rmse, 2))
        grade_cnts.append(mask.sum())
    else:
        grade_r2s.append(0)
        grade_rmses.append(0)
        grade_cnts.append(0)

bar_colors = ['#2ECC71','#3498DB','#F39C12','#E74C3C']
bars = axes[1,1].bar(grade_names, grade_r2s,
                     color=bar_colors, edgecolor='white',
                     alpha=0.85)
axes[1,1].set_ylabel('R²')
axes[1,1].set_title('피크 위험 등급별 예측 정확도 (R²)',
                     fontweight='bold')
axes[1,1].set_ylim(0, 1.15)
axes[1,1].axhline(0.9, color='gray', linestyle='--',
                  linewidth=1.2, label='R²=0.9 기준')
axes[1,1].legend(fontsize=9)
for bar, r2, rmse, cnt in zip(
        bars, grade_r2s, grade_rmses, grade_cnts):
    axes[1,1].text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height() + 0.02,
        f'R²={r2:.3f}\nRMSE={rmse:.1f}\nn={cnt:,}',
        ha='center', fontsize=8, fontweight='bold')

plt.suptitle(
    'XGBoost-Tuned 최종 모델 예측 결과 분석 (Set_C)',
    fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

# ── 최종 요약 출력 ────────────────────────────────
print("=== 최종 모델 예측 성능 요약 ===")
print(f"모델      : XGBoost-Tuned")
print(f"피처      : Set_C ({len(FEATURE_SETS['Set_C'])}개)")
print(f"R²        : {r2_tune:.4f}")
print(f"RMSE      : {rmse_tune:.2f} kW")
print(f"MAE       : {mae_tune:.2f} kW")
print(f"잔차 평균  : {residuals.mean():.4f} kW")
print(f"잔차 표준편차: {residuals.std():.2f} kW")

print("\n=== 등급별 예측 정확도 ===")
for name, r2, rmse, cnt in zip(
        ['양호','주의','위험','초과'],
        grade_r2s, grade_rmses, grade_cnts):
    print(f"  {name:5s}: R²={r2:.4f}  "
          f"RMSE={rmse:.2f} kW  샘플={cnt:,}건")

print("\nStep 44 완료")

# %% [markdown]
# # Step 45: 최종 모델 저장

# %%
# ================================================
# Step 45: 최종 모델 저장
# XGBoost-Tuned (Set_C 기준)
# ================================================
import joblib
import os

os.makedirs('./models', exist_ok=True)

# ── 저장 딕셔너리 구성 ────────────────────────────
save_dict = {
    'model'       : best_xgb,
    'feature_cols': FEATURE_SETS['Set_C'],
    'feature_sets': FEATURE_SETS,
    'target'      : TARGET,
    'r2'          : r2_tune,
    'rmse'        : rmse_tune,
    'mae'         : mae_tune,
    'scaler'      : scalers['Set_C'],
    'params'      : xgb_search.best_params_,
}

save_path = './models/energy_pipeline_v2.pkl'
joblib.dump(save_dict, save_path)
size_mb = os.path.getsize(save_path) / 1024 / 1024

print(f"=== 모델 저장 완료 ===")
print(f"저장 경로 : {save_path}")
print(f"파일 크기 : {size_mb:.2f} MB")

# ── 로드 후 검증 ──────────────────────────────────
loaded       = joblib.load(save_path)
test_pred    = loaded['model'].predict(
    splits['Set_C']['X_test'][:3])
print(f"\n=== 로드 검증 ===")
print(f"예측값 3개: {test_pred.round(2)}")
print(f"실제값 3개: {y_test.values[:3].round(2)}")

print(f"\n=== 최종 모델 요약 ===")
print(f"모델      : XGBoost-Tuned")
print(f"피처 Set  : Set_C ({len(FEATURE_SETS['Set_C'])}개)")
print(f"R²        : {r2_tune:.4f}")
print(f"RMSE      : {rmse_tune:.2f} kW")
print(f"MAE       : {mae_tune:.2f} kW")
print(f"최적 파라미터: {xgb_search.best_params_}")

print(f"\n=== 피처 목록 ({len(FEATURE_SETS['Set_C'])}개) ===")
for i, col in enumerate(FEATURE_SETS['Set_C'], 1):
    print(f"  {i:2d}. {col}")

print("\nStep 45 완료 — 전체 모델 파이프라인 완성")

# %% [markdown]
# # Step 46: Streamlit app.py 업데이트 (Set_C 기준 최종)

# %%
# ================================================
# Step 46: Streamlit app.py 업데이트
# Set_C 기준 / GMM 0~3 / co2_kg 제거 / 여름휴가 반영
# ================================================
import os, shutil

os.makedirs('./energy_app', exist_ok=True)
os.makedirs('./energy_app/models', exist_ok=True)
os.makedirs('./energy_app/data', exist_ok=True)

shutil.copy('./models/energy_pipeline_v2.pkl',
            './energy_app/models/energy_pipeline_v2.pkl')

app_code = '''import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="에너지 피크 예측 시스템",
    page_icon="",
    layout="wide"
)

matplotlib.rcParams["font.family"]        = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

# ── 모델 로드 ─────────────────────────────────────
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "models", "energy_pipeline_v2.pkl")

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

loaded       = load_model()
model        = loaded["model"]
feature_cols = loaded["feature_cols"]

# ── 상수 정의 ─────────────────────────────────────
def get_tou(month, hour, is_holiday, is_weekend):
    if is_holiday or is_weekend:
        return 0, 95.7
    if month in [6,7,8]:
        if hour in [10,11,12,13,14,15,16,17]: return 2, 155.0
        if hour in [22,23,0,1,2,3,4,5]:       return 0, 95.7
        return 1, 121.5
    elif month in [11,12,1,2]:
        if hour in [9,10,17,18,19]:  return 2, 155.0
        if hour in [22,23,0,1,2,3,4,5]: return 0, 95.7
        return 1, 121.5
    else:
        if hour in [10,11,12,13,14,15,16,17]: return 1, 121.5
        if hour in [22,23,0,1,2,3,4,5]:       return 0, 95.7
        return 1, 121.5

TOU_LABEL   = {0:"경부하(95.7원)", 1:"중간부하(121.5원)", 2:"최대부하(155.0원)"}
EMISSION    = 0.4153
MONTH_NAMES = ["1월","2월","3월","4월","5월","6월",
               "7월","8월","9월","10월","11월","12월"]
DAY_MAP     = {"월":1,"화":2,"수":3,"목":4,"금":5,"토":6,"일":7}
SMP_2021    = {1:70.47,2:75.25,3:83.78,4:75.97,5:78.93,
               6:82.72,7:87.04,8:93.41,9:98.21,
               10:107.53,11:126.83,12:142.46}
NATIONAL_HOLIDAYS = [
    20210101,20210211,20210212,20210301,20210505,
    20210519,20210816,20210920,20210921,20210922,
    20211003,20211004,20211009,20211225,
]
SUMMER_VACATION = [
    20210731,20210801,20210802,20210803,20210804,
    20210805,20210806,20210807,20210808,
]
ALL_HOLIDAYS = NATIONAL_HOLIDAYS + SUMMER_VACATION

# GMM 생산구분 설명 (0~3)
GMM_LABEL = {
    0: "0 (비가동)",
    1: "1 (고생산)",
    2: "2 (중생산)",
    3: "3 (저생산)",
}

# ── 타이틀 ───────────────────────────────────────
st.title("제조 공장 피크 전력 예측 시스템")
st.caption("KAMP 자원 최적화 AI | 선박 부품 제조 공장 | 올라운더팀")
st.divider()

# ── 사이드바 ──────────────────────────────────────
st.sidebar.header("공정 파라미터 입력")
st.sidebar.divider()

st.sidebar.subheader("시간 / 날짜")
hour     = st.sidebar.slider("시간 (0~23시)", 0, 23, 10)
month    = st.sidebar.selectbox("월", MONTH_NAMES, index=5)
day_name = st.sidebar.selectbox("요일", list(DAY_MAP.keys()), index=0)
date_d   = st.sidebar.slider("일 (1~31)", 1, 31, 15)

st.sidebar.divider()
st.sidebar.subheader("생산 조건")
production = st.sidebar.slider("생산량 (개)", 0, 9830, 500, step=10)
workers    = st.sidebar.slider("공장 인원 (명)", 0.0, 48.0, 10.0, step=0.5)
gmm_class  = st.sidebar.selectbox(
    "GMM 생산구분", options=[0,1,2,3],
    format_func=lambda x: GMM_LABEL[x], index=1)
furnace    = st.sidebar.radio(
    "열처리로 상태", options=[0,1],
    format_func=lambda x: "OFF (휴지)" if x==0 else "ON (가동)")
labor      = st.sidebar.radio(
    "근무 유형", options=[1.0, 1.5],
    format_func=lambda x: "주간(1.0)" if x==1.0 else "야간(1.5)")

st.sidebar.divider()
st.sidebar.subheader("날씨 조건")
temperature = st.sidebar.slider("기온 (°C)", -20, 40, 20)
humidity    = st.sidebar.slider("습도 (%)", 0, 100, 60)
wind_speed  = st.sidebar.slider("풍속 (m/s)", 0.0, 10.0, 2.0, step=0.1)
rainfall    = st.sidebar.slider("강수량 (mm)", 0.0, 150.0, 0.0, step=0.5)

st.sidebar.divider()
st.sidebar.subheader("전기요금")
tariff_map = {
    "겨울 (109.8원/kWh)": 109.8,
    "봄가을 (167.2원/kWh)": 167.2,
    "여름 (191.6원/kWh)": 191.6,
}
season     = st.sidebar.selectbox("계절별 단가", list(tariff_map.keys()), index=1)
tariff     = tariff_map[season]

# ── 입력값 계산 ───────────────────────────────────
m_num      = MONTH_NAMES.index(month) + 1
wd_num     = DAY_MAP[day_name] - 1
is_weekend = 1 if wd_num >= 5 else 0
date_key   = int(f"2021{m_num:02d}{date_d:02d}")
is_holiday = 1 if date_key in ALL_HOLIDAYS else 0
is_work    = 1 if production > 0 else 0
is_day     = 1 if (8 <= hour <= 18) else 0
tou, tou_p = get_tou(m_num, hour, is_holiday, is_weekend)
smp        = SMP_2021.get(m_num, 87.0)

import math
prod_log    = math.log1p(production)
worker_log  = math.log1p(workers)
wind_log    = math.log1p(wind_speed)
rain_log    = math.log1p(rainfall)

input_dict = {
    "시간"        : hour,
    "day"        : DAY_MAP[day_name],
    "d"          : date_d,
    "m"          : m_num,
    "weekday"    : wd_num,
    "is_weekend" : is_weekend,
    "is_holiday" : is_holiday,
    "주간여부"    : is_day,
    "기온"        : temperature,
    "습도"        : humidity,
    "풍속"        : wind_log,
    "강수량"      : rain_log,
    "생산량"      : prod_log,
    "가동여부"    : is_work,
    "공장인원"    : worker_log,
    "GMM생산구분" : gmm_class,
    "furnace_on" : furnace,
    "전기요금(계절)": tariff,
    "tou_bucket" : tou,
    "tou_price"  : tou_p,
    "smp_land"   : smp,
    "인건비"      : labor,
}

input_df = pd.DataFrame([input_dict])[feature_cols]
pred_kw  = max(0, float(model.predict(input_df)[0]))
co2_val  = round(pred_kw / 1000 * EMISSION * 1000, 3)
saving_10 = int(pred_kw * 0.10 * 8320 / 730)
saving_20 = int(pred_kw * 0.20 * 8320 / 730)

# 위험 등급
if   pred_kw < 70:  grade, gcolor = "양호",  "green"
elif pred_kw < 110: grade, gcolor = "주의",  "blue"
elif pred_kw < 150: grade, gcolor = "위험",  "orange"
else:               grade, gcolor = "초과",  "red"

# ── 경보 배너 ────────────────────────────────────
if pred_kw >= 150:
    st.error(f"피크 초과 경보 — 즉각 조치 필요! 예측 피크: {pred_kw:.1f} kW")
elif pred_kw >= 110:
    st.warning(f"피크 위험 경보 — 생산 조정 권고. 예측 피크: {pred_kw:.1f} kW")
elif pred_kw >= 70:
    st.info(f"피크 주의 구간. 예측 피크: {pred_kw:.1f} kW")
else:
    st.success(f"양호 구간 — 현재 조건을 유지하세요. 예측 피크: {pred_kw:.1f} kW")

st.divider()

# ── KPI 카드 ─────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("예측 피크 전력", f"{pred_kw:.1f} kW",
              delta=f"{pred_kw-90:+.1f} kW vs 평균")
with c2:
    st.metric("피크 위험 등급", grade)
with c3:
    st.metric("TOU 요금 구간", TOU_LABEL[tou])
with c4:
    st.metric("탄소 배출량", f"{co2_val:.3f} kg CO2")

st.divider()

# ── 게이지 + 24h 시뮬레이션 ──────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("피크 위험 게이지")
    fig, ax = plt.subplots(figsize=(6, 3))
    zones   = [70, 110, 150, 210]
    zcolors = ["#2ecc71","#3498db","#f39c12","#e74c3c"]
    zlabels = ["양호","주의","위험","초과"]
    prev = 0
    for z, c, l in zip(zones, zcolors, zlabels):
        ax.barh(0, z-prev, left=prev, height=0.5,
                color=c, alpha=0.4, label=l)
        prev = z
    ax.axvline(pred_kw, color=gcolor,
               linewidth=4, label=f"예측 {pred_kw:.1f}kW")
    ax.axvline(90, color="gray", linewidth=1.5,
               linestyle="--", label="평균 90kW")
    ax.set_xlim(0, 220)
    ax.set_yticks([])
    ax.set_xlabel("피크 전력 (kW)")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title(f"현재: {pred_kw:.1f} kW [{grade}]")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_r:
    st.subheader("24시간 피크 시뮬레이션")
    hourly = []
    for h in range(24):
        row = input_dict.copy()
        tou_h, tou_p_h = get_tou(m_num, h, is_holiday, is_weekend)
        row["시간"]     = h
        row["주간여부"] = 1 if (8<=h<=18) else 0
        row["tou_bucket"] = tou_h
        row["tou_price"]  = tou_p_h
        row["인건비"]     = 1.0 if (8<=h<=18) else 1.5
        df_h = pd.DataFrame([row])[feature_cols]
        hourly.append(max(0, float(model.predict(df_h)[0])))

    fig2, ax2 = plt.subplots(figsize=(6, 3))
    bar_cols = [gcolor if h==hour else "steelblue"
                for h in range(24)]
    ax2.bar(range(24), hourly, color=bar_cols,
            alpha=0.8, edgecolor="white")
    ax2.axhline(150, color="#e74c3c", linestyle="--",
                lw=1.2, label="위험 150kW")
    ax2.axhline(110, color="#f39c12", linestyle="--",
                lw=1.2, label="주의 110kW")
    ax2.set_xlabel("시간 (시)")
    ax2.set_ylabel("예측 피크 (kW)")
    ax2.set_xticks(range(24))
    ax2.legend(fontsize=8)
    ax2.set_title("24시간 피크 예측")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

st.divider()

# ── 비용 절감 계산기 ─────────────────────────────
st.subheader("비용 절감 계산기")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("현재 시간 요금",
              f"{int(pred_kw * tou_p):,} 원")
with c2:
    st.metric("피크 10% 감축 시",
              f"{saving_10:,} 원 절감")
with c3:
    st.metric("피크 20% 감축 시",
              f"{saving_20:,} 원 절감")

st.divider()

# ── ESG 탄소 배출 ─────────────────────────────────
st.subheader("ESG 탄소 배출 현황")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("시간당 CO2", f"{co2_val:.3f} kg")
with c2:
    st.metric("일간 예상", f"{co2_val*24:.2f} kg")
with c3:
    st.metric("연간 추정", f"{co2_val*24*365/1000:.2f} tCO2")

# ── 입력값 확인 ───────────────────────────────────
with st.expander("현재 입력값 상세 보기"):
    display_df = pd.DataFrame({
        "항목": ["시간","월","일","요일","생산량","공장인원",
                 "GMM생산구분","열처리로","근무유형",
                 "기온","습도","풍속","강수량","계절요금",
                 "TOU 구간","SMP","공휴일","주말"],
        "입력값": [f"{hour}시", month, f"{date_d}일", day_name,
                  f"{production:,}개", f"{workers:.1f}명",
                  GMM_LABEL[gmm_class],
                  "ON" if furnace==1 else "OFF",
                  "주간" if labor==1.0 else "야간",
                  f"{temperature}°C", f"{humidity}%",
                  f"{wind_speed}m/s", f"{rainfall}mm",
                  f"{tariff}원/kWh",
                  TOU_LABEL[tou], f"{smp:.2f}원/kWh",
                  "예" if is_holiday else "아니오",
                  "예" if is_weekend else "아니오"],
    })
    st.dataframe(display_df, use_container_width=True,
                 hide_index=True)

st.caption("올라운더팀 | KAMP 자원 최적화 AI 프로젝트 2 | 2026")
'''

with open('./energy_app/app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("app.py 업데이트 완료")
print("변경 사항:")
print("  1. model 키 수정 (pipeline → model)")
print("  2. Set_C feature_cols 반영")
print("  3. co2_kg 입력 제거")
print("  4. GMM 생산구분 0~3 반영")
print("  5. log1p 변환 입력 반영 (생산량·인원·풍속·강수량)")
print("  6. 여름휴가(7/31~8/8) 공휴일 반영")
print("  7. Set A/B/C 명칭 통일")
print("\n실행 방법:")
print("  conda activate ml_edu")
print("  cd C:\\Users\\Admin\\hipython\\ml\\energy_app")
print("  streamlit run app.py")
print("\nStep 46 완료")

# %%


# %%


# %%



