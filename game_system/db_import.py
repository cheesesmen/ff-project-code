import pandas as pd
from sqlalchemy import create_engine, inspect
import os

# 1. 连接数据库
engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/game_db')

def import_data():
    inspector = inspect(engine)
    all_files = os.listdir('.')
    
    # 定义 CSV 和 数据库字段的映射关系
    mapping = {
        'productId': 'product_id',
        'price': 'price',
        'level': 'level',
        'assetsScore': 'assets_score',
        'showTitle': 'show_title',
        'createTime': 'create_time'
    }

    for f in all_files:
        if f.startswith('raw_Genshin') or f.startswith('raw_DeltaForce'):
            target_table = 'api_genshinaccount' if 'Genshin' in f else 'api_deltaaccount'
            print(f"正在处理: {f} ...")
            
            # 读取 CSV
            df = pd.read_csv(f)
            
            # 获取数据库表里真实的列名
            db_cols = [c['name'] for c in inspector.get_columns(target_table)]
            
            # 找出当前 CSV 中存在的、且在 mapping 里的列
            present_mapping = {k: v for k, v in mapping.items() if k in df.columns}
            
            # 过滤并重命名
            import_df = df[list(present_mapping.keys())].rename(columns=present_mapping)
            
            # 再次确保这些列在数据库里确实存在
            final_cols = [c for c in import_df.columns if c in db_cols]
            import_df = import_df[final_cols]
            
            # 执行灌库
            import_df.to_sql(target_table, con=engine, if_exists='append', index=False)
            print(f"✅ 成功入库 {len(import_df)} 条数据到 {target_table}")

if __name__ == '__main__':
    try:
        import_data()
        print("\n🚀 数据库已填满！")
    except Exception as e:
        print(f"\n❌ 出错了：{e}")