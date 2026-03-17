import numpy as np
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from .apps import ApiConfig
from .utils import extract_features_from_db # 确保 utils.py 已更新
from .models import GenshinAccount, DeltaAccount

class ValuationAnalyticsView(APIView):
    def get(self, request):
        game = request.query_params.get('game', 'genshin')
        model = ApiConfig.ml_models.get(game)
        
        if not model:
            return Response({"error": f"{game} 模型未加载，请先运行训练脚本"}, status=500)

        # 获取展示数据
        if game == 'genshin':
            accounts = GenshinAccount.objects.all().order_by('-id')[:60]
        else:
            accounts = DeltaAccount.objects.all().order_by('-id')[:60]

        results = []
        for acc in accounts:
            try:
                # 1. 提取特征（返回 pd.Series）
                feat_series = extract_features_from_db(acc, game)
                
                # 2. 转换为 DataFrame 喂给 XGBoost (防止格式报错)
                input_df = pd.DataFrame([feat_series])
                
                # 3. 推理预测（得到对数空间的溢价/价格）
                pred_log = model.predict(input_df)[0]
                pred_val = np.expm1(pred_log) # 还原对数
                
                # 4. 🌟 补偿逻辑（对齐 model_test 的残差架构）
                if game == 'genshin':
                    # 原神：最终估价 = AI预测溢价 + 抽数现金保底
                    cash_guard = feat_series.get('pulls_cash_value', 0)
                    final_predict = pred_val + cash_guard
                else:
                    # 三角洲：直接预测价格
                    final_predict = pred_val

                results.append({
                    "name": acc.show_title[:20] + "...",
                    "actual": float(acc.price),
                    "predict": round(float(final_predict), 2),
                    "ratio": round(float(final_predict / acc.price), 2) if acc.price > 0 else 0
                })
            except Exception as e:
                print(f"预测单条数据失败: {e}")
                continue
        
        return Response(results)