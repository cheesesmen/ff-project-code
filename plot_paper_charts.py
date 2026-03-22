import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 设置学术图表风格与中文字体
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei'] # Windows请使用 SimHei，Mac请使用 Arial Unicode MS
plt.rcParams['axes.unicode_minus'] = False

game = "genshin" # 可改为 "delta" 画三角洲的图

# ==========================================
# 图 1：特征重要性条形图 (证明哪些特征对价格影响最大)
# ==========================================
def plot_feature_importance():
    df = pd.read_csv(f'paper_data_{game}_feature_importance.csv')
    df = df.head(10) # 只取前10个最重要的特征
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df, palette='viridis')
    plt.title(f'XGBoost 模型特征重要性分析 (Top 10) - {game.upper()}', fontsize=14)
    plt.xlabel('特征重要性 (F-score)', fontsize=12)
    plt.ylabel('特征名称', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'Fig1_{game}_Feature_Importance.png', dpi=300)
    print("✅ 已生成 图1: 特征重要性分析")

# ==========================================
# 图 2：真实价格 vs 预测价格 散点拟合图 (证明模型预测有多准)
# ==========================================
def plot_actual_vs_predicted():
    df = pd.read_csv(f'paper_data_{game}_test_results.csv')
    
    plt.figure(figsize=(8, 8))
    plt.scatter(df['Actual_Price'], df['Predicted_Price'], alpha=0.5, color='#2ca02c', edgecolor='k')
    
    # 画一条 y=x 的红色虚线基准线
    max_val = max(df['Actual_Price'].max(), df['Predicted_Price'].max())
    plt.plot([0, max_val], [0, max_val], 'r--', lw=2, label='完美预测基准线 (y=x)')
    
    plt.title(f'测试集预测分布：实际市场售价 vs AI预测估值 - {game.upper()}', fontsize=14)
    plt.xlabel('市场实际挂牌售价 (元)', fontsize=12)
    plt.ylabel('XGBoost 模型预测估值 (元)', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig2_{game}_Actual_vs_Predicted.png', dpi=300)
    print("✅ 已生成 图2: 实际vs预测散点图")

# ==========================================
# 图 3：模型训练 Loss 学习曲线 (证明模型没有过拟合)
# ==========================================
def plot_learning_curve():
    with open(f'paper_data_{game}_learning_curve.json', 'r') as f:
        data = json.load(f)
    
    # 提取训练集和测试集的均方根误差(rmse)
    train_loss = data['validation_0']['rmse']
    test_loss = data['validation_1']['rmse']
    epochs = range(len(train_loss))
    
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, train_loss, label='训练集 (Train Loss)', color='#1f77b4', lw=2)
    plt.plot(epochs, test_loss, label='验证集 (Validation Loss)', color='#ff7f0e', lw=2)
    
    plt.title(f'XGBoost 模型迭代学习曲线 - {game.upper()}', fontsize=14)
    plt.xlabel('迭代次数 (Boosting Rounds)', fontsize=12)
    plt.ylabel('均方根误差 RMSE', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Fig3_{game}_Learning_Curve.png', dpi=300)
    print("✅ 已生成 图3: Loss学习曲线图")

if __name__ == "__main__":
    plot_feature_importance()
    plot_actual_vs_predicted()
    plot_learning_curve()