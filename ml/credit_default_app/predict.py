import joblib
import pandas as pd
import os

class DefaultPredictor:
    def __init__(self, model_path=None):
        # 모델 경로 설정 (기본값 설정)
        if model_path is None:
            self.model_path = r'C:\Users\Admin\hipython\ml\credit_default_app\model\credit_default_pipeline.pkl'
        else:
            self.model_path = model_path
        
        self.model = self._load_model()

    def _load_model(self):
        """저장된 피클 파일을 로드합니다."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
        return joblib.load(self.model_path)

    def predict(self, input_data):
        """
        입력 데이터를 바탕으로 예측을 수행합니다.
        input_data: dict 또는 pd.DataFrame
        """
        # 딕셔너리 입력일 경우 데이터프레임으로 변환
        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        else:
            input_df = input_data

        # 예측 및 확률 계산
        prediction = self.model.predict(input_df)[0]
        probability = self.model.predict_proba(input_df)[0]
        
        return {
            "is_default": int(prediction),
            "probability_normal": float(probability[0]),
            "probability_default": float(probability[1])
        }

# --- 단독 실행 테스트용 ---
if __name__ == "__main__":
    # 테스트용 가상 데이터
    sample_user = {
        'LIMIT_BAL': 200000, 'SEX': 1, 'EDUCATION': 2, 'MARRIAGE': 1, 'AGE': 35,
        'PAY_0': 0, 'PAY_2': 0, 'PAY_3': 0, 'PAY_4': 0, 'PAY_5': 0, 'PAY_6': 0,
        'BILL_AMT1': 50000, 'BILL_AMT2': 45000, 'BILL_AMT3': 40000, 
        'BILL_AMT4': 35000, 'BILL_AMT5': 30000, 'BILL_AMT6': 25000,
        'PAY_AMT1': 2000, 'PAY_AMT2': 2000, 'PAY_AMT3': 2000, 
        'PAY_AMT4': 2000, 'PAY_AMT5': 2000, 'PAY_AMT6': 2000
    }

    try:
        predictor = DefaultPredictor()
        result = predictor.predict(sample_user)
        
        print("\n=== 예측 결과 보고서 ===")
        print(f"상태: {'채무불이행 위험' if result['is_default'] == 1 else '정상'}")
        print(f"연체 확률: {result['probability_default']:.2%}")
        print(f"정상 확률: {result['probability_normal']:.2%}")
        
    except Exception as e:
        print(f"에러 발생: {e}")