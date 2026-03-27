import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# ==========================================
# 1. 环境配置
# ==========================================
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei'] # Windows
plt.rcParams['axes.unicode_minus'] = False

# 自动处理的游戏列表
games = ["genshin", "delta"]

def run_visual_pipeline(game_name):
    print(f"\n📊 正在为 [{game_name.upper()}] 生成论文图表...")
    
    # 文件路径检查
    feat_file = f'paper_data_{game_name}_feature_importance.csv'
    res_file = f'paper_data_{game_name}_test_results.csv'
    loss_file = f'paper_data_{game_name}_learning_curve.json'

    if not os.path.exists(feat_file):
        print(f"⚠️ 找不到 {feat_file}，跳过该游戏。请先运行 model_test.py")
        return

    # --- 图 1：特征重要性 ---
    df_feat = pd.read_csv(feat_file).sort_values(by='Importance', ascending=False).head(10)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df_feat, palette='viridis')
    plt.title(f'特征重要性分析 - {game_name.upper()}', fontsize=14)
    plt.xlabel('重要性权重', fontsize=12)
    plt.ylabel('核心特征', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'Fig1_{game_name}_Feature_Importance.png', dpi=300)
    plt.close()

    # --- 图 2：拟合散点图 ---
    df_res = pd.read_csv(res_file)
    plt.figure(figsize=(8, 8))
    plt.scatter(df_res['Actual_Price'], df_res['Predicted_Price'], alpha=0.4, color='#2ca02c')
    max_val = max(df_res['Actual_Price'].max(), df_res['Predicted_Price'].max())
    plt.plot([0, max_val], [0, max_val], 'r--', label='理想预测线')
    plt.title(f'拟合效果分析图 - {game_name.upper()}', fontsize=14)
    plt.xlabel('真实市场价格', fontsize=12)
    plt.ylabel('模型预测价格', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig2_{game_name}_Actual_vs_Predicted.png', dpi=300)
    plt.close()

    # --- 图 3：学习曲线 ---
    with open(loss_file, 'r') as f:
        loss_data = json.load(f)
    train_loss = loss_data['validation_0']['rmse']
    test_loss = loss_data['validation_1']['rmse']
    plt.figure(figsize=(10, 6))
    plt.plot(train_loss, label='训练集误差', lw=2)
    plt.plot(test_loss, label='验证集误差', lw=2)
    plt.title(f'模型收敛学习曲线 - {game_name.upper()}', fontsize=14)
    plt.xlabel('迭代轮次 (Epochs)', fontsize=12)
    plt.ylabel('RMSE 误差', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig3_{game_name}_Learning_Curve.png', dpi=300)
    plt.close()
    
    print(f"✅ {game_name.upper()} 的 3 张图表已保存至根目录。")

if __name__ == "__main__":
    for g in games:
        run_visual_pipeline(g)
    print("\n✨ 所有图表处理完毕！请在文件夹中查看 Fig1_... 到 Fig3_... 的图片。")