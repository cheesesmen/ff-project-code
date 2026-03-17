import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from .apps import ApiConfig
from .utils import extract_features_from_db  # 确保你的 utils 逻辑与 model_test 同步
from rest_framework.decorators import api_view

class ValuationAnalyticsView(APIView):
    def get(self, request):
        game = request.query_params.get('game', 'genshin')
        model = ApiConfig.ml_models.get(game)
        
        if not model:
            return Response({"error": "模型尚未就绪，请先运行训练脚本"}, status=500)

        # 获取最新入库的账号进行演示
        from .models import GenshinAccount, DeltaAccount
        accounts = GenshinAccount.objects.all().order_by('-id')[:60] if game == 'genshin' else \
                   DeltaAccount.objects.all().order_by('-id')[:60]

        results = []
        for acc in accounts:
            try:
                # 1. 提取特征
                feat_series = extract_features_from_db(acc, game)
                
                # 2. 推理预测
                pred_log = model.predict([feat_series])[0]
                pred_val = np.expm1(pred_log)
                
                # 🌟 关键：原神需要补偿回剥离的现金保底
                if game == 'genshin':
                    cash_guard = feat_series.get('pulls_cash_value', 0)
                    final_predict = pred_val + cash_guard
                else:
                    final_predict = pred_val

                results.append({
                    "name": acc.show_title[:18] + "...",
                    "actual": float(acc.price),
                    "predict": round(float(final_predict), 2),
                    "ratio": round(float(final_predict / acc.price), 2) if acc.price > 0 else 0
                })
            except Exception as e:
                continue
        
        return Response(results)
    
@api_view(['GET'])
def get_delta_list(request):
    from .models import DeltaAccount
    # 返回最近的 50 条原始数据
    data = DeltaAccount.objects.all().order_by('-id').values()[:50]
    return Response(list(data))