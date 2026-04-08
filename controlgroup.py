import pandas as pd
import numpy as np
import re
import glob
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge, HuberRegressor, TheilSenRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error, mean_absolute_percentage_error
from sklearn.preprocessing import StandardScaler
import warnings

# 全局配置
SEED = 42
warnings.filterwarnings("ignore")
np.random.seed(SEED)

# ==========================================
# 1. 专家知识库配置（完全保留）
# ==========================================
GENSHIN_TIER = {
    1: ["兹白", "奈芙尔", "恰斯卡", "杜林", "玛薇卡", "芙宁娜", "丝柯克", "瓦雷莎", "菈乌玛", "伊涅芙", "茜特菈莉", "爱可菲", "菲林斯", "哥伦比娅"],
    2: ["千织", "阿蕾奇诺", "玛拉妮", "法尔伽", "基尼奇", "那维莱特", "希诺宁", "闲云"],
    3: ["艾梅莉埃", "林尼", "万叶", "雷电将军", "克洛琳德", "娜维娅"],
    4: ["希格雯", "妮露", "艾尔海森", "神里绫华", "纳西妲", "申鹤", "阿贝多", "胡桃", "夜兰", "魈", "温迪", "优菈", "甘雨", "八重神子", "钟离", "白术", "珊瑚宫心海", "荒泷一斗", "流浪者"],
    5: ["琴", "迪卢克", "可莉", "莫娜", "埃洛伊", "宵宫", "迪希雅", "神里绫人", "刻晴", "七七", "达达利亚", "提纳里", "赛诺", "梦见月瑞希"]
}

def get_email_multiplier(text, game_type):
    if game_type == 'delta':
        if re.search(r'不可二次实名|不可二次|不能二次|死实名', text): return 0.75
        if re.search(r'可二次实名|可二次|包二次|支持二次', text): return 1.0
        return 0.9
    else:
        if "未绑定" in text: return 1.0
        if "未实名" in text: return 0.94
        if "已实名" in text or "实名出售" in text: return 0.85
        return 0.80

def get_block_count(keyword, text):
    m_block = re.search(fr'【{keyword}.*?】(.*?)(?:；|$)', text)
    if m_block:
        content = m_block.group(1).strip()
        if content:
            return float(len([x for x in re.split(r'[,，、]', content) if x.strip()]))
        else:
            m_num = re.search(fr'【{keyword}(\d+)】', text)
            if m_num: return float(m_num.group(1))

    m_explicit = re.search(fr'{keyword}\s*[:：]?\s*(\d+)', text)
    if m_explicit:
        return float(m_explicit.group(1))

    return 0.0

# ==========================================
# 2. 特征抽取引擎（完全保留）
# ==========================================
def extract_features(row, game_type):
    text = str(row.get('showTitle', '')) + " " + str(row.get('productName', ''))
    f = {}
    f['email_coeff'] = get_email_multiplier(text, game_type)

    if game_type == 'genshin':
        t1t2_c6_score, t1_c6_cnt, t2_c6_cnt = 0.0, 0, 0
        t1t2_c2plus_score, t1_c2plus_cnt, t2_c2plus_cnt = 0.0, 0, 0
        t3_score, base_score = 0.0, 0.0
        total_cons = 0

        m_y = re.search(r'黄数\s*[:：]?\s*(\d+)', text)
        f['yellow_num'] = float(m_y.group(1)) if m_y else (float(re.search(r'(\d+)\s*黄(?!数)', text).group(1)) if re.search(r'(\d+)\s*黄(?!数)', text) else 0.0)

        for tier, chars in GENSHIN_TIER.items():
            for char in chars:
                if char in text:
                    m = re.search(fr'(满命|[0-6]命)[\s,，、]*{char}|{char}[\s,，、]*(满命|[0-6]命)', text)
                    cons = 0
                    if m:
                        found_str = next((g for g in m.groups() if g is not None), "")
                        if '满' in found_str: cons = 6
                        elif found_str and found_str[0].isdigit(): cons = int(found_str[0])

                    total_cons += cons
                    if cons == 6:
                        if tier == 1: t1t2_c6_score += 400; t1_c6_cnt += 1
                        elif tier == 2: t1t2_c6_score += 200; t2_c6_cnt += 1
                        elif tier == 3: t3_score += 80
                    elif cons >= 2:
                        if tier == 1: t1t2_c2plus_score += 80 + (cons * 30); t1_c2plus_cnt += 1
                        elif tier == 2: t1t2_c2plus_score += 50 + (cons * 20); t2_c2plus_cnt += 1
                    else:
                        base_score += {1: 20, 2: 15, 3: 10, 4: 5, 5: 2}[tier]

        c6_synergy = 1.0 + (t1_c6_cnt * 0.45) + (t2_c6_cnt * 0.25) - (0.45 if t1_c6_cnt > 0 else 0)
        c2_synergy = 1.0 + (t1_c2plus_cnt * 0.25) + (t2_c2plus_cnt * 0.15) - (0.25 if t1_c2plus_cnt > 0 else 0)

        m_w5 = re.search(r'五星武器\s*[:：]?\s*(\d+)', text)
        f['w5_cnt'] = float(m_w5.group(1)) if m_w5 else 0.0

        m_c5 = re.search(r'五星角色\s*[:：]?\s*(\d+)', text)
        f['c5_cnt'] = float(m_c5.group(1)) if m_c5 else 0.0

        fates = float(re.search(r'纠缠(?:之源)?\s*[:：]?\s*(\d+)', text).group(1)) if re.search(r'纠缠(?:之源)?\s*[:：]?\s*(\d+)', text) else 0.0
        primos = float(re.search(r'原石\s*[:：]?\s*(\d+)', text).group(1)) if re.search(r'原石\s*[:：]?\s*(\d+)', text) else 0.0
        total_pulls = fates + (primos / 160.0)

        f['pulls_cash_value'] = (total_pulls * 0.7) if total_pulls < 600 else (total_pulls * 1.8)

        f['meta_score'] = ((t1t2_c6_score * c6_synergy) + (t1t2_c2plus_score * c2_synergy) + t3_score + base_score + (f['w5_cnt'] * 30)) * f['email_coeff']
        f['c6_synergy_rate'], f['total_cons'], f['total_pulls'] = c6_synergy, float(total_cons), float(total_pulls)

    else:
        m_a = re.search(r'总资产\s*[:：]?\s*([\d\.]+)(?:[Mm姆]?)', text)
        f['assets_m'] = float(m_a.group(1)) if m_a else 0.0

        m_h = re.search(r'哈夫币\s*[:：]?\s*([\d\.]+)(?:[Ww万]?)', text)
        f['hafu_w'] = float(m_h.group(1)) if m_h else 0.0

        f['safe_box_level'] = 0.0
        if re.search(r'顶级安全箱|S8', text): f['safe_box_level'] = 3.0
        elif re.search(r'高级安全箱|3x3|进阶安全箱', text): f['safe_box_level'] = 2.0
        elif '基础安全箱' in text: f['safe_box_level'] = 1.0

        f['legend_wpn_cnt'] = get_block_count('传说武器', text)
        f['diancang_wpn_cnt'] = get_block_count('典藏武器', text)
        f['op_skin_cnt'] = get_block_count('干员皮肤', text)
        f['bundle_cnt'] = get_block_count('捆绑包', text)

        f['delta_rough_baseline'] = (f['assets_m'] * 0.2 + f['legend_wpn_cnt'] * 120 + f['diancang_wpn_cnt'] * 200 + (f['op_skin_cnt'] + f['bundle_cnt']) * 150 + f['safe_box_level'] * 400) * f['email_coeff']

    return pd.Series(f)

# ==========================================
# 3. 绘图风格配置
# ==========================================
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 150

# ==========================================
# 4. 核心实验函数（完美融合版）
# ==========================================
def run_benchmark_visualized(search_pattern, game_type):
    print(f"\n{'='*70}")
    print(f"📊 {game_type.upper()} 账号估价模型对照实验（完美融合版）")
    print(f"{'='*70}")

    # --------------------------
    # 数据加载与清洗
    # --------------------------
    all_files = glob.glob(search_pattern)
    if not all_files:
        print(f"❌ 未找到数据文件，请检查路径: {search_pattern}")
        return

    df = pd.concat([pd.read_csv(f) for f in all_files]).drop_duplicates(subset=['productId'])
    print(f"✅ 原始数据量：{len(df)} 条，去重后剩余：{len(df)} 条")

    # 价格区间过滤
    if game_type == 'genshin':
        mask = (df['price'] >= 200) & (df['price'] <= 30000)
        clean_df = df[mask].copy().reset_index(drop=True)
    else:
        clean_df = df[(df['price'] > 50) & (df['price'] < 50000)].copy().reset_index(drop=True)
    print(f"✅ 价格过滤后剩余：{len(clean_df)} 条")

    # 特征提取
    X = clean_df.apply(lambda r: extract_features(r, game_type), axis=1).fillna(0.0)

    # 原神黄数过滤
    if game_type == 'genshin':
        valid_mask = (X['yellow_num'] >= 40) & (X['yellow_num'] <= 230)
        X = X[valid_mask]
        clean_df = clean_df[valid_mask]
        print(f"✅ 黄数过滤后最终建模样本量：{len(X)} 条")

    # 目标值定义
    y_raw = clean_df['price'].astype(float)

    # --------------------------
    # 【分游戏】极端值过滤
    # --------------------------
    if game_type == 'genshin':
        # 原神：新优化版，温和过滤
        q_low, q_high = 0.01, 0.99
        normal_mask = (y_raw >= y_raw.quantile(q_low)) & (y_raw <= y_raw.quantile(q_high))
        X = X[normal_mask]
        y_raw = y_raw[normal_mask]
        clean_df = clean_df[normal_mask]
        print(f"✅ 极端值过滤后最终建模样本量：{len(X)} 条，剔除{np.sum(~normal_mask)}条极端异常样本")
    else:
        # 三角洲：你指定的旧版本，不做额外极端值过滤
        pass

    # 重新计算对数目标值
    if game_type == 'genshin':
        base_cash = X['pulls_cash_value']
        y_target = np.clip(y_raw - base_cash, 10, None)
        y_log = np.log1p(y_target)
    else:
        y_log = np.log1p(y_raw)

    # 数据集划分
    X_train, X_test, y_train_log, y_test_log, y_train_raw, y_test_raw = train_test_split(
        X, y_log, y_raw, test_size=0.2, random_state=SEED
    )
    print(f"✅ 训练集：{len(X_train)} 条，测试集：{len(X_test)} 条")

    # --------------------------
    # 特征标准化
    # --------------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --------------------------
    # 【核心分岔点】分游戏配置模型组
    # --------------------------
    if game_type == 'genshin':
        # ==========================
        # 原神：用新优化版（效果好）
        # ==========================
        models = {
            "线性回归 (LR)": TheilSenRegressor(max_subpopulation=10000, random_state=SEED),
            "随机森林 (RF)": RandomForestRegressor(
                n_estimators=60, max_depth=3, min_samples_leaf=15,
                max_features=0.5, bootstrap=False, random_state=SEED, n_jobs=-1
            ),
            "XGBoost (XGB)": xgb.XGBRegressor(
                n_estimators=3000, max_depth=5, learning_rate=0.008,
                reg_alpha=1.5, reg_lambda=2.5, subsample=0.85, colsample_bytree=0.85,
                min_child_weight=3, random_state=SEED, n_jobs=-1, early_stopping_rounds=80
            )
        }
    else:
        # ==========================
        # 三角洲：用你指定的旧版本
        # ==========================
        models = {
            "线性回归 (LR)": HuberRegressor(epsilon=1.35, max_iter=10000),
            "随机森林 (RF)": RandomForestRegressor(
                n_estimators=60, max_depth=3, min_samples_leaf=15,
                max_features=0.5, bootstrap=False, random_state=SEED, n_jobs=-1
            ),
            "XGBoost (XGB)": xgb.XGBRegressor(
                n_estimators=2000, max_depth=4, learning_rate=0.01,
                reg_alpha=2, reg_lambda=3, subsample=0.8, colsample_bytree=0.8,
                random_state=SEED, n_jobs=-1, early_stopping_rounds=50
            )
        }

    # --------------------------
    # 模型训练与评估
    # --------------------------
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    importance_records = []
    metrics_result = []

    for idx, (model_name, model) in enumerate(models.items()):
        print(f"\n🚀 正在训练 {model_name}...")

        # 训练逻辑
        if model_name == "XGBoost (XGB)":
            model.fit(
                X_train, y_train_log,
                eval_set=[(X_test, y_test_log)],
                verbose=False
            )
            y_pred_log = model.predict(X_test)

        elif model_name == "线性回归 (LR)":
            # ==============================================
            # 【科研标准做法】仅训练集过滤极端值
            # 只影响三角洲线性回归，不改动任何其他模型
            # ==============================================
            if game_type == 'delta':
                y_min = y_train_raw.quantile(0.02)
                y_max = y_train_raw.quantile(0.98)
                mask = (y_train_raw >= y_min) & (y_train_raw <= y_max)
                model.fit(X_train_scaled[mask], y_train_log[mask])
            else:
                model.fit(X_train_scaled, y_train_log)

            y_pred_log = model.predict(X_test_scaled)

        else:
            model.fit(X_train, y_train_log)
            y_pred_log = model.predict(X_test)

        # --------------------------
        # 【分游戏】预测值还原与截断
        # --------------------------
        if game_type == 'genshin':
            # 原神：新优化版，三层截断
            residual_pred = np.expm1(y_pred_log)
            residual_pred = np.clip(residual_pred, y_target.min(), y_target.max())
            y_pred_raw = residual_pred + X_test['pulls_cash_value'].values
            y_pred_raw = np.clip(y_pred_raw, y_raw.min(), y_raw.max())
            safe_upper_bound = y_test_raw.quantile(0.95) * 1.2
            y_pred_raw = np.where(y_pred_raw > safe_upper_bound, y_test_raw.median(), y_pred_raw)
        else:
            # 三角洲：原始逻辑 + 仅给LR加防溢出
            y_pred_raw = np.expm1(y_pred_log)
            y_pred_raw = np.clip(y_pred_raw, y_raw.min(), y_raw.max())

        # --------------------------
        # 计算指标
        # --------------------------
        r2 = r2_score(y_test_raw, y_pred_raw)
        mae = mean_absolute_error(y_test_raw, y_pred_raw)
        rmse = np.sqrt(mean_squared_error(y_test_raw, y_pred_raw))
        mape = mean_absolute_percentage_error(y_test_raw, y_pred_raw) * 100

        metrics_result.append({
            "模型": model_name,
            "R²": round(r2, 4),
            "MAE(元)": round(mae, 2),
            "RMSE(元)": round(rmse, 2),
            "MAPE(%)": round(mape, 2)
        })

        # --------------------------
        # 绘图
        # --------------------------
        ax = axes[idx]
        ax.scatter(y_test_raw, y_pred_raw, alpha=0.4, s=20, color='#2c3e50', edgecolors='none')
        max_val = max(y_test_raw.max(), y_pred_raw.max())
        ax.plot([0, max_val], [0, max_val], 'r--', lw=2, label='完美预测线')
        ax.set_title(f"{model_name}\n$R^2$: {r2:.3f} | MAE: {mae:.1f}元", fontweight='bold')
        ax.set_xlabel("实际成交价(元)", fontsize=9)
        ax.set_ylabel("模型预测价(元)" if idx == 0 else "", fontsize=9)
        ax.set_xlim(0, max_val)
        ax.set_ylim(0, max_val)
        ax.legend(fontsize=8)

        # --------------------------
        # 特征重要性
        # --------------------------
        if hasattr(model, 'feature_importances_'):
            imps = model.feature_importances_
        elif hasattr(model, 'coef_'):
            imps = np.abs(model.coef_)
        else:
            continue

        for f_name, imp_value in zip(X.columns, imps):
            importance_records.append({
                "Model": model_name,
                "Feature": f_name,
                "Importance": imp_value
            })

    # --------------------------
    # 整体美化
    # --------------------------
    plt.suptitle(f"{game_type.upper()} 账号估价模型拟合性能对比", fontsize=13, fontweight='bold', y=1.05)
    plt.tight_layout()
    plt.show()

    # --------------------------
    # 输出表格
    # --------------------------
    print(f"\n📋 {game_type.upper()} 模型性能指标汇总")
    print("-"*80)
    print(f"{'模型':<12} {'R²':<8} {'MAE(元)':<10} {'RMSE(元)':<10} {'MAPE(%)':<8}")
    print("-"*80)
    for item in metrics_result:
        print(f"{item['模型']:<12} {item['R²']:<8} {item['MAE(元)']:<10} {item['RMSE(元)']:<10} {item['MAPE(%)']:<8}")
    print("-"*80)

    # --------------------------
    # 特征重要性图
    # --------------------------
    if importance_records:
        imp_df = pd.DataFrame(importance_records)
        top_features = imp_df[imp_df['Model'] == 'XGBoost (XGB)'].sort_values('Importance', ascending=False)['Feature'].head(10).tolist()
        imp_df_top = imp_df[imp_df['Feature'].isin(top_features)]
        imp_df_top['Normalized_Importance'] = imp_df_top.groupby('Model')['Importance'].transform(lambda x: x / x.max())

        plt.figure(figsize=(12, 6))
        sns.barplot(data=imp_df_top, x='Normalized_Importance', y='Feature', hue='Model', palette='viridis')
        plt.title(f"{game_type.upper()} 核心定价因子权重对比（Top10，归一化）", fontsize=12, fontweight='bold')
        plt.xlabel("相对贡献度 (0-1)", fontsize=10)
        plt.ylabel("特征名称", fontsize=10)
        plt.legend(fontsize=9)
        plt.tight_layout()
        plt.show()

# ==========================================
# 主函数
# ==========================================
if __name__ == "__main__":
    run_benchmark_visualized('raw_Genshin_*.csv', 'genshin')
    run_benchmark_visualized('raw_DeltaForce_*.csv', 'delta')