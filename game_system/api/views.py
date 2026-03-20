# api/views.py 完整修正版
import subprocess
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .apps import ApiConfig
from .utils import extract_features_from_db
from .models import GenshinAccount, DeltaAccount

class ValuationAnalyticsView(APIView):
    def get(self, request):
        game = request.query_params.get('game', 'genshin')
        model = ApiConfig.ml_models.get(game)
        
        if not model:
            return Response({"error": "模型尚未就绪，请先确认 .pkl 文件存在"}, status=500)

        # 获取最新在售账号（取最新60条）
        if game == 'genshin':
            accounts = GenshinAccount.objects.all().order_by('-id')[:60]
        else:
            accounts = DeltaAccount.objects.all().order_by('-id')[:60]

        results = []
        for acc in accounts:
            try:
                # 1. 提取特征
                feat_series = extract_features_from_db(acc, game)
                
                # 2. 推理预测
                pred_log = model.predict([feat_series])[0]
                pred_val = np.expm1(pred_log)
                
                # 3. 价格补偿 (原神抽数价值)
                predict_price = round(float(pred_val + (feat_series.get('pulls_cash_value', 0) if game == 'genshin' else 0)), 2)
                actual_price = float(acc.price)
                margin = predict_price - actual_price

                results.append({
                    "id": acc.product_id,
                    "name": acc.show_title,
                    "actual_price": actual_price,
                    "predict_price": predict_price,
                    "margin": round(margin, 2),
                    "is_recommended": margin > (actual_price * 0.15),
                    "features": feat_series.to_dict() # 这一行很重要，对应详情弹窗的数据
                })
            except Exception as e:
                continue
        
        return Response(sorted(results, key=lambda x: x['margin'], reverse=True))

# 🌟 重点：必须添加这个函数，urls.py 才能找到它！
@api_view(['POST'])
def trigger_sync(request):
    """
    接收前端按钮指令，运行爬虫脚本同步最新市场数据
    """
    try:
        # 在 Django 环境下运行外部 Python 脚本
        # 确保 sync_live_market.py 就在 manage.py 同级目录下
        subprocess.run(['python', 'sync_live_market.py'], check=True)
        return Response({"message": "市场数据同步成功！"})
    except subprocess.CalledProcessError as e:
        return Response({"error": f"同步脚本运行失败: {str(e)}"}, status=500)
    except Exception as e:
        return Response({"error": f"发生未知错误: {str(e)}"}, status=500)