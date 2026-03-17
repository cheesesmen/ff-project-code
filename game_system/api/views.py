import os
import joblib
import pandas as pd
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import GenshinAccount, DeltaAccount
from .utils import extract_features_from_db
from rest_framework.decorators import api_view

class ValuationAnalyticsView(APIView):
    def get(self, request):
        game = request.query_params.get('game', 'genshin')
        
        # 动态选择模型和数据库
        if game == 'genshin':
            model_file = 'valuer_genshin_pro.pkl'
            accounts = GenshinAccount.objects.all().order_by('-id')[:50]
        else:
            model_file = 'valuer_delta_pro.pkl'
            accounts = DeltaAccount.objects.all().order_by('-id')[:50]
            
        model_path = os.path.join(settings.BASE_DIR, model_file)
        
        if not os.path.exists(model_path):
            return Response({"error": f"找不到模型文件: {model_file}"}, status=404)
            
        try:
            model = joblib.load(model_path)
        except Exception as e:
            return Response({"error": f"模型加载失败: {str(e)}"}, status=500)
            
        chart_data = []
        for acc in accounts:
            try:
                # 传入 game 区分特征提取逻辑
                feat_series = extract_features_from_db(acc, game)
                pred_price = model.predict([feat_series])[0]
                
                chart_data.append({
                    "name": acc.show_title[:15] + "...",
                    "actual": float(acc.price),
                    "predict": round(float(pred_price), 2),
                    "ratio": round(float(pred_price / acc.price), 2) if acc.price > 0 else 0
                })
            except Exception as e:
                continue
                
        return Response(chart_data)
    # 在 views.py 文件的最后面加上这个
@api_view(['GET'])
def get_delta_list(request):
    try:
        from .models import DeltaAccount
        data = DeltaAccount.objects.all().order_by('-id').values()[:50]
        return Response(list(data))
    except Exception as e:
        return Response({"error": str(e)}, status=500)