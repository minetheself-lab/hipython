# ⚡ 에너지 사용량 예측 및 DR(수요반응) 시뮬레이션

본 프로젝트는 중소기업의 에너지 비용 절감을 위해 **15분 단위 피크 전력 사용량을 예측**하고, 이를 기반으로 **DR(Demand Response) 참여 시 수익성을 시뮬레이션**하는 통합 솔루션을 제공합니다.

## 📌 1. 프로젝트 개요
* **목적**: AI 모델을 활용한 전력 피크 관리 및 DR 참여를 통한 추가 수익 창출 분석.
* **데이터 출처**: 
    * KAMP(Korea AI Manufacturing Platform) 소성가공 자원최적화 데이터셋.
    * 기상청(OBS) ASOS 실측 기상 데이터.

## 🛠 2. 주요 기능
* **AI 예측**: XGBoost 기반의 15분 단위 최대수요전력(kW) 예측 모델.
* **데이터 증강**: 기상 실측 데이터와 결합하여 1년치 데이터셋 구축.
* **CBL 시뮬레이션**: '평일 상위 4일 평균(Max 4/5)' 방식을 적용한 표준 CBL 산출.
* **수익성 분석**: 감축량에 따른 예상 정산금 및 전기료 절감액 실시간 계산.

## 📂 3. 파일 구조
* `12_에너지사용량_예측_Final.ipynb`: 모델링 전체 파이프라인.
* `DR_app.py`: Streamlit 기반 대시보드 웹 앱.
* `energy_pipeline_v2.pkl`: 학습 완료된 최적 AI 모델 파일.

## 🚀 4. 시작하기
```bash
# 관련 라이브러리 설치
pip install pandas xgboost scikit-learn streamlit plotly

# 대시보드 실행
streamlit run DR_app.py