import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 绘图样式设置
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 自动生成 原神 + 三角洲 所有图表
game_list = ["genshin", "delta"]
game_name_map = {
    "genshin": "原神",
    "delta": "三角洲行动"
}

# ==========================================
# 图1：特征重要性
# ==========================================
def plot_feature_importance(game):
    df = pd.read_csv(f'paper_data_{game}_feature_importance.csv')
    df = df.head(10)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df, palette='viridis', hue='Feature', legend=False)
    plt.title(f'XGBoost 模型特征重要性分析 (Top 10) - {game_name_map[game]}', fontsize=14)
    plt.xlabel('特征重要性 (F-score)', fontsize=12)
    plt.ylabel('特征名称', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'Fig1_{game}_Feature_Importance.png', dpi=300)
    plt.close()
    print(f"✅ {game_name_map[game]} 图1 生成完成")

# ==========================================
# 图2：真实价格 vs 预测价格
# ==========================================
def plot_actual_vs_predicted(game):
    df = pd.read_csv(f'paper_data_{game}_test_results.csv')
    plt.figure(figsize=(8, 8))
    plt.scatter(df['Actual_Price'], df['Predicted_Price'], alpha=0.5, color='#2ca02c', edgecolor='k')
    max_val = max(df['Actual_Price'].max(), df['Predicted_Price'].max())
    plt.plot([0, max_val], [0, max_val], 'r--', lw=2, label='完美预测基准线 (y=x)')
    plt.title(f'测试集预测分布：实际售价 vs AI预测 - {game_name_map[game]}', fontsize=14)
    plt.xlabel('市场实际挂牌售价 (元)', fontsize=12)
    plt.ylabel('XGBoost 模型预测估值 (元)', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig2_{game}_Actual_vs_Predicted.png', dpi=300)
    plt.close()
    print(f"✅ {game_name_map[game]} 图2 生成完成")

# ==========================================
# 图3：学习曲线
# ==========================================
def plot_learning_curve(game):
    with open(f'paper_data_{game}_learning_curve.json', 'r') as f:
        data = json.load(f)
    train_loss = data['validation_0']['rmse']
    test_loss = data['validation_1']['rmse']
    epochs = range(len(train_loss))
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, train_loss, label='训练集 Loss', color='#1f77b4', lw=2)
    plt.plot(epochs, test_loss, label='验证集 Loss', color='#ff7f0e', lw=2)
    plt.title(f'XGBoost 模型迭代学习曲线 - {game_name_map[game]}', fontsize=14)
    plt.xlabel('迭代次数', fontsize=12)
    plt.ylabel('RMSE', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig3_{game}_Learning_Curve.png', dpi=300)
    plt.close()
    print(f"✅ {game_name_map[game]} 图3 生成完成")

# ==========================================
# 主函数：一次生成全部图表
# ==========================================
if __name__ == "__main__":
    print("🚀 开始自动生成【原神 + 三角洲】全部论文图表...\n")

    for game in game_list:
        print(f"\n🎮 正在生成：{game_name_map[game]}")
        plot_feature_importance(game)
        plot_actual_vs_predicted(game)
        plot_learning_curve(game)

    print("\n🎉🎉🎉 全部 6 张论文图表生成完成！")
    print("✅ 原神 3 张")
    print("✅ 三角洲 3 张")