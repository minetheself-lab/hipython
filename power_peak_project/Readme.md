⚡ 에너지 사용량 예측 및 DR 시뮬레이션 AI 프로젝트
본 프로젝트는 중소기업의 에너지 비용 절감을 목표로, 15분 단위 피크 전력 사용량을 예측하고 이를 기반으로 DR(수요반응) 참여 시뮬레이션을 수행하는 통합 솔루션을 제공합니다.

📌 프로젝트 개요
목적: AI 모델을 통한 전력 피크 예측으로 연간 기본 전기료를 절감하고, DR 참여를 통한 추가 수익 창출 가능성을 분석합니다.

데이터셋: KAMP(Korea AI Manufacturing Platform) 자원 최적화 AI 데이터셋 (okm_augumented_2021.csv) 및 기상청(OBS) 실측 데이터.

핵심 목표: 15분 단위 최대수요전력(kW) 예측.

🛠 주요 기능
데이터 전처리 및 증강:

결측치 및 이상치 처리와 상관관계 분석(Heatmap) 수행.

기상청 실측 날씨 데이터를 결합하여 데이터셋을 1년치(8,760행)로 증강 및 보정.

머신러닝 모델링:

XGBoost, RandomForest, Ridge, DNN 등 다양한 모델 비교 학습.

GridSearchCV를 이용한 하이퍼파라미터 튜닝 및 최종 모델(pipeline.pkl) 저장.

Streamlit 기반 대시보드:

예측 모델을 활용한 실시간 전력 사용량 모니터링 시뮬레이션.

CBL(Customer Baseline, 고객기준부하) 자동 계산을 통한 DR 참여 수익 시뮬레이션 기능 제공.

📂 파일 구성
12_에너지사용량_예측_Final.ipynb: 데이터 분석부터 모델 선정, 저장까지의 전체 파이프라인.

12_에너지사용량_예측_v3_PE기반.ipynb: 기상 실측 데이터를 반영한 고도화된 데이터 증강 과정.

DR_app.py / dr_app2.py: Streamlit 기반의 DR 시뮬레이션 웹 애플리케이션 소스.

13_전력사용량.ipynb: 구간별 부하율 검증 및 컬럼별 데이터 특성 분석.

🚀 시작하기
필요 라이브러리 설치
프로젝트 실행을 위해 다음 패키지들이 필요합니다:

Bash
pip install xgboost scikit-learn pandas numpy matplotlib seaborn joblib streamlit plotly
실행 방법
모델 생성: Jupyter Notebook(Final.ipynb)을 실행하여 학습된 모델 파일을 생성합니다.

앱 실행: 터미널에서 다음 명령어를 입력하여 대시보드를 구동합니다.

Bash
streamlit run DR_app.py
📊 모델링 프로세스 요약
Data Load: 데이터 로드 및 기본 통계 확인.

EDA: 분포 시각화 및 생산량-전력 관계 분석.

Feature Engineering: Feature Set A/B/C 설계 및 스케일링.

Training: 다양한 알고리즘 학습 및 종합 평가.

Deployment: 최적 모델 저장 및 Streamlit 연동.

Note: 본 프로젝트는 올라운더팀의 KAMP 자원 최적화 AI 프로젝트의 일환으로 제작되었습니다.