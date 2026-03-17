import os
import glob
import pandas as pd
import django

# 1. 初始化 Django 环境 (根据你的项目名修改)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_system.settings')
django.setup()

from api.models import GenshinAccount

def run_import():
    # 自动获取最新的原神 CSV
    csv_files = glob.glob('raw_Genshin_10026_*.csv')
    if not csv_files:
        print("❌ 错误：未找到原神 CSV 文件，请确认文件在当前目录下。")
        return
    
    target_csv = csv_files[0]
    print(f"📂 正在读取文件: {target_csv}")
    
    df = pd.read_csv(target_csv)
    count = 0
    
    # 2. 批量写入数据库 (只取前 200 条演示)
    for _, row in df.head(200).iterrows():
        # get_or_create 防止重复导入
        obj, created = GenshinAccount.objects.get_or_create(
            product_id=str(row['productId']),
            defaults={
                'price': float(row['price']),
                'show_title': f"{row['showTitle']} {row['productName']}",
                'level': 60
            }
        )
        if created: count += 1
            
    print(f"✅ 导入成功！新增数据: {count} 条。")

if __name__ == "__main__":
    run_import()