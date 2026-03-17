import os
import django
import requests
import re
import time

# 初始化 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_system.settings')
django.setup()
from api.models import GenshinAccount, DeltaAccount

def extract_yellow_num(text):
    """提取原神黄数"""
    m = re.search(r'黄数\s*[:：]?\s*(\d+)', text)
    if m: return float(m.group(1))
    m_i = re.search(r'(\d+)\s*黄(?!数)', text)
    return float(m_i.group(1)) if m_i else 0.0

def sync_game_data():
    configs = {
        'genshin': {
            'url': "https://www.pxb7.com/api/search/product/selectSearchPageList",
            'params': {"gameId": "10026", "bizProd": "1", "size": "50", "page": "1"},
            'headers': {"Referer": "https://www.pxb7.com/buy/10026", "User-Agent": "Mozilla/5.0"},
            'model': GenshinAccount
        },
        'delta': {
            'url': "https://www.pxb7.com/api/search/product/selectSearchPageList",
            'params': {"gameId": "10371", "bizProd": "1", "size": "50", "page": "1"},
            'headers': {"Referer": "https://www.pxb7.com/buy/10371", "User-Agent": "Mozilla/5.0"},
            'model': DeltaAccount
        }
    }

    for game_type, cfg in configs.items():
        print(f"\n📡 正在抓取 {game_type.upper()} 实时在售数据...")
        try:
            res = requests.get(cfg['url'], params=cfg['params'], headers=cfg['headers'], timeout=10).json()
            if not res.get("success"):
                print(f"❌ 请求失败: {res.get('errorMessage')}")
                continue

            new_count = 0
            for item in res.get("data", []):
                price = float(item.get('price', 0)) / 100
                title = item.get('showTitle', '') or ''
                
                # ==========================================
                # 🛡️ 严格应用模型训练时的物理过滤门槛
                # ==========================================
                if game_type == 'genshin':
                    # 1. 价格 1000~15000
                    if not (1000 <= price <= 15000): continue
                    # 2. 官方截图
                    if "官方截图" not in title: continue
                    # 3. 黄数 40~240
                    y_num = extract_yellow_num(title)
                    if not (40 <= y_num <= 240): continue
                
                elif game_type == 'delta':
                    # 三角洲价格门槛：150~30000
                    if not (150 <= price <= 30000): continue
                # ==========================================

                obj, created = cfg['model'].objects.get_or_create(
                    product_id=str(item.get('productId')),
                    defaults={'price': price, 'show_title': title}
                )
                if created: new_count += 1
                
            print(f"✅ {game_type.upper()} 同步完成！经过严格过滤，新增 {new_count} 条优质数据。")
            time.sleep(1) # 防封停缓冲
            
        except Exception as e:
            print(f"🚨 {game_type.upper()} 发生异常: {str(e)}")

if __name__ == "__main__":
    sync_game_data()