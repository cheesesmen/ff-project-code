import requests
import time
import os
import re
import django
import json
from datetime import datetime

# ==================== Django 环境初始化 ====================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_system.settings')
django.setup()
from api.models import GenshinAccount, DeltaAccount

# ==================== 🔑 核心配置区 ====================
ACTIVE_COOKIE = "JSESSIONID=F3DD17843ADBAC33F70A7A4AD8B90622; gdp_user_id=gioenc-g29c9042%2C8615%2C558b%2Cc70c%2C318c81be7g5d; _c_WBKFRo=Ljz7mKSGIYjl28KpysBZGfQJbpzkuVWEvhyw9pm3; a6990010a0b40f79_gdp_user_key=; a6990010a0b40f79_gdp_gio_id=gioenc-041469482325898; a6990010a0b40f79_gdp_cs1=; __snaker__id=iLjLG54Nr8RSkuRb; Hm_lvt_6d8ffc7e04e74b3866a454a4477796ce=1773219015,1773684720; HMACCOUNT=1DBB69A5468E4E85; aliyungf_tc=4b53c9bb9033df8434123b7ca2681b62f732ede596164823ff2620ed8aff6051; Hm_lvt_9825d85599bde84eb4e38d1860196204=1773331747,1774014089; a6990010a0b40f79_gdp_session_id=2676de5a-a217-4ae8-92f1-c938c86e9a0a; a6990010a0b40f79_gdp_session_id_sent=2676de5a-a217-4ae8-92f1-c938c86e9a0a; deviceId=f38b8153-9704-449c-b61b-209b90cd6f4e; userId=; uuid=0608ddcfbe0f08aa5a3540278322f9db; Hm_lpvt_6d8ffc7e04e74b3866a454a4477796ce=1774019515; gdxidpyhxdE=zi%2BtvAEo0SbN2nJr4R2X0op24gcB%2F2D9C8zSj2yH79z3dpLkWUl7AZsfMrhgvid07Vz56baVjSN1LDyHM6HaWliM%2BHDZ%2FVql4Skrr7%2Br8DtnEXmgEyyIoNM6xI9T%5CXR2AShCYRm6lmUMr3c6rxG4m9CeQ2WMba%5Ce04TN2StjrZWa6c0o%3A1774022374554; acw_tc=0a065e9717740231489974207e0755b51a6c43d605cc90341728a28ac8d33b; acw_sc__v2=69bd71efb39cc6e16a96c84a525bf621391f01f8; acw_sc__v3=69bd768c70c8d7eaccffce9501f2f2751c0c84e7; Hm_lpvt_9825d85599bde84eb4e38d1860196204=1774024383; a6990010a0b40f79_gdp_sequence_ids={%22globalKey%22:2145}; ssxmod_itna=1-eqUxRDgQ0QD=eDKeYjx4Q9S8FnMP0dGMD3qiQGgDYq7=GFQDCOozD0Ka04_KYwIPD02G6PqDOT5D/KDAKiDnqD8UDQeDvDgfriYSjPEEuxQ=iixAGx62eCipfOsw0kY365X=1BLcHVtY=D4DHxi8DB94KD_xzxiiHx0rD0eDPxDYDG4Do1YDnr4DjxDdH9oAhIoDbxi3I4GCP_RfU4DFmCOmXtxD0oahHG_IiDDziCQe=7ww9B3DeaBLmChvdBlDqCoD9h4DscWyiCoXzqtepSjc7ufbr40kUq0Oh_kvHewIv33LGAAb344X7GGD_I0eweeenwP7qxciqne2Dx4jDK=GKlqeiDdGD1eiNSPDnn5Z_H80=D2Mm5ZQchUH8bu1mE1lR4tG=GiTjritw5yrN/hi07H3Y4iiqNiTFnrbGDD; ssxmod_itna2=1-eqUxRDgQ0QD=eDKeYjx4Q9S8FnMP0dGMD3qiQGgDYq7=GFQDCOozD0Ka04_KYwIPD02G6PqDOqeGIDxxWuvi1SlBUzVe90i0Ebp3D"

# 筛选配置（统一管理，便于修改）
FILTER_CONFIG = {
    "price_min": 500,
    "price_max": 15000,
    "genshin_yellow_min": 40,
    "genshin_yellow_max": 230,
    "required_keyword": "官方截图"
}

def get_data_via_api(game_type, target_count=300):
    """适配参考代码形式的核心抓取函数"""
    # 游戏ID映射
    game_id_map = {"genshin": "10026", "delta": "10371"}
    game_id = game_id_map.get(game_type, "10026")
    model_cls = GenshinAccount if game_type == "genshin" else DeltaAccount
    
    # 接口配置（参考代码的接口参数风格）
    url = "https://m1.pxb7.com/api/search/h5/product/selectSearchPageList"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://m1.pxb7.com",
        "Referer": "https://m1.pxb7.com/pages/buy/index",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36 Edg/145.0.0.0",
        "client_type": "2", 
        "px-authorization-user": "null",
        "Cookie": ACTIVE_COOKIE
    }

    # 初始化变量
    all_valid_items = []
    page_index = 1
    
    # 打印任务信息（参考代码风格）
    print(f"\n{'='*80}")
    print(f"📡 采集开始 | 游戏类型: {game_type} | 目标数量: {target_count}")
    filter_desc = f"📌 筛选条件: 必须含'{FILTER_CONFIG['required_keyword']}' | 价格 {FILTER_CONFIG['price_min']}-{FILTER_CONFIG['price_max']}"
    if game_type == "genshin":
        filter_desc += f" | 黄数 {FILTER_CONFIG['genshin_yellow_min']}-{FILTER_CONFIG['genshin_yellow_max']}"
    print(filter_desc)
    print(f"{'='*80}")

    # 翻页抓取（参考代码的while循环逻辑）
    while len(all_valid_items) < target_count:
        # 接口参数（参考代码的payload结构）
        payload = {
            "bizProd": "1",
            "couponIds": [],
            "pageIndex": page_index,
            "pageSize": 50,
            "gameId": game_id,
            "query": "",
            "type": "4",
            "mineFav": False,
            "filterDTOList": [],
            "combineFilterList": [],
            "posType": 1,
            "fromSubscribe": 0,
            "productTypeIds": [],
            "confirmSubscribe": 1
        }

        try:
            # 发送请求（参考代码的异常处理风格）
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ 第{page_index}页 - 状态码异常: {response.status_code}，停止采集")
                break
                
            try:
                res_json = response.json()
            except Exception as e:
                print(f"🧨 第{page_index}页 - 响应解析失败（Cookie可能过期）: {e}")
                break

            # 兼容解析数据（参考代码的多格式兼容）
            items = []
            if isinstance(res_json, dict):
                if 'data' in res_json and isinstance(res_json['data'], dict) and 'list' in res_json['data']:
                    items = res_json['data']['list']
                elif 'data' in res_json and isinstance(res_json['data'], list):
                    items = res_json['data']
                elif 'list' in res_json and isinstance(res_json['list'], list):
                    items = res_json['list']
            elif isinstance(res_json, list):
                items = res_json

            # 无数据则停止翻页
            if not items:
                print("🏁 接口没有更多数据了，停止翻页")
                break
            
            # 遍历当前页数据（参考代码的筛选逻辑）
            page_valid_count = 0
            for item in items:
                # 防止超过目标数量
                if len(all_valid_items) >= target_count:
                    break
                
                # 跳过非字典类型数据
                if not isinstance(item, dict):
                    continue
                
                # --- 1. 基础属性提取（参考代码的字段提取逻辑） ---
                product_id = item.get('productId') or item.get('id') or None
                show_title = str(item.get('showTitle', ''))
                product_name = str(item.get('productName', ''))
                price = float(item.get('price', 0)) / 100  # 分转元
                
                # 跳过无ID数据
                if not product_id:
                    continue

                # --- 2. 核心筛选条件 A: 必须包含官方截图（多字段校验） ---
                # 参考代码：同时校验showTitle和productName
                if FILTER_CONFIG['required_keyword'] not in show_title and FILTER_CONFIG['required_keyword'] not in product_name:
                    continue

                # --- 3. 核心筛选条件 B: 价格区间校验 ---
                if not (FILTER_CONFIG['price_min'] <= price <= FILTER_CONFIG['price_max']):
                    continue

                # --- 4. 核心筛选条件 C: 原神黄数专项校验（参考代码的正则逻辑） ---
                yellow_val = None
                if game_type == "genshin":
                    # 参考代码的精准正则匹配
                    yellow_match = re.search(r'黄数\s*[:：]?\s*(\d+)|(\d+)\s*黄', show_title)
                    if yellow_match:
                        # 提取第一个非空的数字组
                        yellow_val = int(yellow_match.group(1) or yellow_match.group(2))
                        # 黄数区间校验
                        if not (FILTER_CONFIG['genshin_yellow_min'] <= yellow_val <= FILTER_CONFIG['genshin_yellow_max']):
                            continue
                    else:
                        # 无黄数则跳过（参考代码逻辑）
                        continue

                # --- 5. 符合所有条件，记录数据 ---
                valid_item = {
                    'product_id': product_id,
                    'price': price,
                    'show_title': show_title,
                    'product_name': product_name,
                    'yellow_val': yellow_val,
                    'create_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 打印符合条件的数据（参考代码的输出风格）
                print(f"\n✅ 第{len(all_valid_items)+1}条有效数据 | 游戏: {game_type}")
                print(f"   ID: {product_id} | 价格: {price:.2f}元")
                print(f"   标题: {show_title[:60]}...")
                if yellow_val:
                    print(f"   黄数: {yellow_val}")
                
                all_valid_items.append(valid_item)
                page_valid_count += 1

            # 打印当前页进度（参考代码风格）
            print(f"\n📌 第 {page_index} 页扫描完成 | 本页有效: {page_valid_count} 条 | 累计有效: {len(all_valid_items)} / {target_count}")
            
            # 翻页控制
            page_index += 1
            if page_index > 500:  # 参考代码的500页上限
                print("⚠️ 已扫描500页，为保护IP自动停止")
                break
            
            # 防封控延迟（参考代码的1秒间隔）
            time.sleep(1.0)

        except Exception as e:
            print(f"🧨 第{page_index}页发生异常: {str(e)}，停止采集")
            break

    # --- 数据入库（保留Django原有逻辑） ---
    if all_valid_items:
        # 去重（参考代码的去重逻辑）
        unique_items = []
        seen_ids = set()
        for item in all_valid_items:
            if item['product_id'] not in seen_ids:
                seen_ids.add(item['product_id'])
                unique_items.append(item)
        
        # 转换为Django模型对象
        model_items = []
        for item in unique_items:
            model_obj = model_cls(
                product_id=item['product_id'],
                show_title=item['show_title'],
                price=item['price']
            )
            model_items.append(model_obj)
        
        # 清空旧数据并批量入库
        model_cls.objects.all().delete()
        model_cls.objects.bulk_create(model_items)
        
        # 最终汇总（参考代码风格）
        print(f"\n{'='*80}")
        print(f"🎉 {game_type} 采集完成！最终有效数据: {len(unique_items)} 条")
        print(f"📦 已同步至Django数据库: api_{game_type}account 表")
        print(f"{'='*80}")
    else:
        print(f"\n⚠️ {game_type} 采集完成！无符合条件的数据")

    return all_valid_items

def run_task():
    """任务入口（参考代码的run_task结构）"""
    # 配置要采集的游戏和目标数量
    tasks = [
        {"type": "genshin", "target": 300},
        {"type": "delta", "target": 300}
    ]
    
    # 依次执行采集任务
    for task in tasks:
        get_data_via_api(task["type"], task["target"])
        # 任务间隔
        time.sleep(3)

if __name__ == "__main__":
    # 启动采集任务
    run_task()