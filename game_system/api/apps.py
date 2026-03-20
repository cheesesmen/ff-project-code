from django.apps import AppConfig
import joblib
import os
from django.conf import settings

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    # 这是一个全局字典，用来在内存中保存你的AI模型
    ml_models = {}

    def ready(self):
        # 这个方法会在 Django 启动时自动运行（也就是 python manage.py runserver 时）
        base_dir = settings.BASE_DIR
        # 定位到你项目目录下的 pkl 文件
        genshin_model_path = os.path.join(base_dir, 'valuer_genshin_pro.pkl')
        delta_model_path = os.path.join(base_dir, 'valuer_delta_pro.pkl')

        try:
            if os.path.exists(genshin_model_path):
                self.ml_models['genshin'] = joblib.load(genshin_model_path)
                print("✅ 原神 AI 估价模型加载成功！")
            
            if os.path.exists(delta_model_path):
                self.ml_models['delta'] = joblib.load(delta_model_path)
                print("✅ 三角洲 AI 估价模型加载成功！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")