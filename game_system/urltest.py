from playwright.sync_api import sync_playwright
import json
import re
import time

def crawl_genshin_impact_playwright():
    """原神爬虫（Playwright模拟浏览器，绕过反爬，含黄数筛选）"""
    # 配置项
    url = "https://m1.pxb7.com/api/search/h5/product/selectSearchPageList"
    payload = {
        "bizProd": 1,
        "couponIds": [],
        "pageIndex": 1,
        "pageSize": 16,
        "gameId": "10026",
        "query": "",
        "type": 4,
        "mineFav": False,
        "filterDTOList": [],
        "combineFilterList": [],
        "posType": 1,
        "fromSubscribe": 0,
        "productTypeIds": [],
        "confirmSubscribe": 1
    }

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # 模拟手机端上下文
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36 Edg/145.0.0.0",
            viewport={"width": 375, "height": 812},
            extra_http_headers={
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-HK;q=0.6,en-GB;q=0.5",
                "Content-Type": "application/json",
                "Origin": "https://m1.pxb7.com",
                "Referer": "https://m1.pxb7.com/pages/buy/index",
                "client_type": "2",
                "px-authorization-user": "null"
            }
        )

        page = context.new_page()
        try:
            # 访问主页获取Cookie
            page.goto("https://m1.pxb7.com/pages/buy/index", timeout=30000)
            time.sleep(2)

            # 发送API请求
            response = page.request.post(
                url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=30000
            )

            if response.ok:
                res_json = response.json()
                items = res_json.get('data', {}).get('list', [])
                
                # 筛选有效商品（含黄数）
                valid_items = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    title = str(item.get('title', item.get('showTitle', '')))
                    raw_price = float(item.get('price', 0))
                    price = raw_price / 100 if raw_price > 50000 else raw_price
                    
                    # 基础筛选
                    if "官方截图" in title and 500 <= price <= 15000:
                        # 黄数筛选
                        y_match = re.search(r'黄数\s*[:：]?\s*(\d+)|(\d+)\s*黄', title)
                        if y_match:
                            yellow_num = int(y_match.group(1) or y_match.group(2))
                            if 40 <= yellow_num <= 230:
                                valid_items.append({
                                    "product_id": item.get('id') or item.get('productId'),
                                    "title": title,
                                    "price": price,
                                    "yellow_number": yellow_num,
                                    "game_id": item.get('gameId')
                                })
                
                # 输出结果
                print(f"✅ 原神爬取成功")
                print(f"   - 原始商品数: {len(items)}")
                print(f"   - 有效商品数: {len(valid_items)}")
                
                if valid_items:
                    print(f"\\n📌 示例商品:")
                    print(f"   ID: {valid_items[0]['product_id']}")
                    print(f"   标题: {valid_items[0]['title'][:50]}...")
                    print(f"   价格: {valid_items[0]['price']} 元")
                    print(f"   黄数: {valid_items[0]['yellow_number']}")
                
                return valid_items
            else:
                print(f"❌ 请求失败，状态码: {response.status}")
                print(f"   响应内容: {response.text()[:500]}")

        except Exception as e:
            print(f"❌ 爬取出错: {str(e)}")
        finally:
            browser.close()
    
    return []

# 测试调用
if __name__ == "__main__":
    crawl_genshin_impact_playwright()