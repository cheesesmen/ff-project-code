import requests
import pandas as pd
import time
import os
import re
from datetime import datetime
# 数据库相关导入
import pymysql
from sqlalchemy import create_engine, text

# ==================== 数据库配置 ====================
MYSQL_PASSWORD = "123456"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": MYSQL_PASSWORD,
    "database": "game_db",
    "charset": "utf8mb4"
}

def get_data_via_api(game_id, target_count=300):
    url = "https://www.pxb7.com/api/search/product/selectSelledList"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.pxb7.com/dealYesterday"
    }

    all_items = []
    page_index = 1 
    
    print(f"📡 采集开始 | 游戏 ID: {game_id} | 目标数量: {target_count}")
    print(f"📌 条件: 必须含'官方截图' | 价格 500-15000" + (" | 原神黄数 40-230" if str(game_id) == "10026" else ""))

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
                
                if not items:
                    print("🏁 接口没有更多数据了。")
                    break
                
                for item in items:
                    if not isinstance(item, dict): continue
                    
                    # --- 1. 基础属性提取 ---
                    title = str(item.get('showTitle', ''))
                    name = str(item.get('productName', ''))
                    price = float(item.get('price', 0)) / 100
                    
                    # --- 2. 硬筛选条件 A: 官方截图 & 价格区间 ---
                    if "官方截图" not in title and "官方截图" not in name:
                        continue
                    
                    if not (500 <= price <= 15000):
                        continue

                    # --- 3. 硬筛选条件 B: 原神黄数专项 (40-230) ---
                    if str(game_id) == "10026":
                        # 使用正则表达式精准匹配标题中的"黄数"或"XX黄"
                        yellow_match = re.search(r'黄数\s*[:：]?\s*(\d+)|(\d+)\s*黄', title)
                        if yellow_match:
                            # 提取匹配到的第一个非空数字组
                            y_val = int(yellow_match.group(1) or yellow_match.group(2))
                            if not (40 <= y_val <= 230):
                                continue
                        else:
                            # 如果标题完全没写黄数，根据你的要求（精准评估），建议也剔除
                            continue

                    # --- 4. 记录符合条件的数据 ---
                    all_items.append({
                        'productId': item.get('productId'),
                        'price': price,
                        'productName': name,
                        'showTitle': title,
                        'gameName': item.get('gameName'),
                        'createTime': item.get('createTime')
                    })
                
                print(f"✅ 第 {page_index} 页扫描完成 | 当前符合条件累计: {len(all_items)} 条")
                page_index += 1
                
                # 防止数据源不足导致无限翻页
                if page_index > 500: break
                time.sleep(1.0) 
            else:
                break
        except Exception as e:
            print(f"🧨 发生异常: {e}")
            break

    return all_items[:target_count]

def import_csv_to_db(csv_file, table_name):
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        if 'createTime' in df.columns:
            df.rename(columns={'createTime': 'create_time'}, inplace=True)
        if 'productId' in df.columns:
            df.rename(columns={'productId': 'product_id'}, inplace=True)
        
        df = df[['product_id', 'price', 'create_time']]
        df['create_time'] = df['create_time'].fillna(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        engine = create_engine(
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}",
            connect_args={"charset": "utf8mb4"}
        )
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                insert_count, ignore_count = 0, 0
                for _, row in df.iterrows():
                    sql = text(f"INSERT IGNORE INTO {table_name} (product_id, price, create_time) VALUES (:product_id, :price, :create_time)")
                    result = conn.execute(sql, {'product_id': row['product_id'], 'price': row['price'], 'create_time': row['create_time']})
                    if result.rowcount > 0: insert_count += 1
                    else: ignore_count += 1
                trans.commit()
                print(f"✅ 数据库同步: 新增 {insert_count} 条，重复跳过 {ignore_count} 条")
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        print(f"❌ 导入失败：{str(e)}")

def run_task():
    games = {
        "10026": {"name": "Genshin", "table": "api_genshinaccount"},
        "10371": {"name": "DeltaForce", "table": "api_deltaaccount"}
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for gid, game_info in games.items():
        data = get_data_via_api(gid, target_count=300)
        if data:
            df = pd.DataFrame(data)
            df = df.drop_duplicates(subset=['productId'])
            filename = f'raw_{game_info["name"]}_{gid}_{timestamp}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print("-" * 30)
            print(f"📦 {game_info['name']} 过滤完成！最终合格记录: {len(df)} 条")
            import_csv_to_db(filename, game_info["table"])

if __name__ == "__main__":
    run_task()