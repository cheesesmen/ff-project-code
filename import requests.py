import requests
import pandas as pd
import time
import os
from datetime import datetime

def get_data_via_api(game_id, target_count=300):
    url = "https://www.pxb7.com/api/search/product/selectSelledList"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.pxb7.com/dealYesterday"
    }

    all_items = []
    page_index = 1 
    
    print(f"📡 正在精准采集游戏 ID: {game_id}...")

    while len(all_items) < target_count:
        payload = {
            "bizProd": "1",
            "gameId": str(game_id),
            "pageIndex": page_index,
            "pageSize": 20, 
            "sort": "2"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                res_json = response.json()
                items = res_json.get('data', [])
                
                if not items or len(items) == 0:
                    print("🏁 接口没有更多数据了。")
                    break
                
                for item in items:
                    if isinstance(item, dict):
                        all_items.append({
                            'productId': item.get('productId'),
                            'price': float(item.get('price', 0)) / 100,
                            'productName': item.get('productName'), # ✨ 已补全此字段
                            'showTitle': item.get('showTitle'),
                            'gameName': item.get('gameName'),
                            'createTime': item.get('createTime')
                        })
                
                print(f"✅ 第 {page_index} 页 OK，当前累计: {len(all_items)} 条")
                page_index += 1
                time.sleep(1.2) 
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                break
        except Exception as e:
            print(f"🧨 发生异常: {e}")
            break

    return all_items[:target_count]

def run_task():
    # 10026: 原神, 10371: 三角洲行动
    games = {"10026": "Genshin", "10371": "DeltaForce"}
    
    # ✨ 生成精确的时间戳：格式为 年月日_时分秒
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for gid, gname in games.items():
        data = get_data_via_api(gid, target_count=300)
        if data:
            df = pd.DataFrame(data)
            df = df.drop_duplicates(subset=['productId'])
            
            # ✨ 优化后的文件名，带有游戏名和时间戳
            filename = f'raw_{gname}_{gid}_{timestamp}.csv'
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print("-" * 30)
            print(f"📦 {gname} 数据保存成功！")
            print(f"📁 文件名: {filename}")
            print(f"📊 最终获取: {len(df)} 条记录")
            print("-" * 30)

if __name__ == "__main__":
    run_task()