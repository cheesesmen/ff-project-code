# game_system/api/apps.py
from django.apps import AppConfig
import joblib
import os
import numpy as np

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    # 静态字典挂载模型
    ml_models = {}

    def ready(self):
        # Django 启动时执行一次
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            self.ml_models['genshin'] = joblib.load(os.path.join(base_dir, 'valuer_genshin_pro.pkl'))
            self.ml_models['delta'] = joblib.load(os.path.join(base_dir, 'valuer_delta_pro.pkl'))
            print("🟢 AI 评估模型加载成功，已驻留内存。")
        except Exception as e:
            print(f"🟡 模型暂未就绪，请先运行 model_test.py: {e}")