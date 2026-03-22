import pandas as pd
import numpy as np
import re
import glob
import joblib
import warnings
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import json

warnings.filterwarnings("ignore")

# ==========================================
# 1. 专家知识库配置
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

# 🌟 智能分词计数器：专治三角洲的无数字文本
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
# 2. 特征抽取引擎
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
# 3. 训练与严苛过滤系统 (残差分离技术)
# ==========================================
def train_expert_model(search_pattern, game_type):
    print(f"\n{'#'*65}")
    print(f"🚀 启动 {game_type.upper()} [XGBoost 残差破壁版] 模型训练")
    print(f"{'#'*65}")
    
    all_files = glob.glob(search_pattern)
    if not all_files:
        print(f"❌ 未找到数据文件: {search_pattern}")
        return
    
    df = pd.concat([pd.read_csv(f) for f in all_files]).drop_duplicates(subset=['productId'])
    
    if game_type == 'genshin':
        mask = (df['price'] >= 200) & (df['price'] <= 30000)
        clean_df = df[mask].copy().reset_index(drop=True)
    else:
        clean_df = df[(df['price'] > 50) & (df['price'] < 50000)].copy().reset_index(drop=True)
    
    X = clean_df.apply(lambda r: extract_features(r, game_type), axis=1).fillna(0.0)
    
    if game_type == 'genshin':
        valid_mask = (X['yellow_num'] >= 40) & (X['yellow_num'] <= 230)
        X = X[valid_mask]
        clean_df = clean_df[valid_mask]
        
    y_raw = clean_df['price'].astype(float)
    
    if game_type == 'genshin':
        base_cash = X['pulls_cash_value']
        y_target = np.clip(y_raw - base_cash, 10, None)
        y_log = np.log1p(y_target)
    else:
        y_log = np.log1p(y_raw)
    
    X_train, X_test, y_train_log, y_test_log, y_train_raw, y_test_raw = train_test_split(
        X, y_log, y_raw, test_size=0.2, random_state=42
    )
    
    model = xgb.XGBRegressor(
        n_estimators=1000,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    # 修改点：同时传入训练集和测试集，以便记录双向 Loss 用于画学习曲线
    model.fit(
        X_train, y_train_log, 
        eval_set=[(X_train, y_train_log), (X_test, y_test_log)], 
        verbose=False
    )
    
    y_pred_log = model.predict(X_test)
    
    if game_type == 'genshin':
        y_pred_raw = np.expm1(y_pred_log) + X_test['pulls_cash_value'].values
    else:
        y_pred_raw = np.expm1(y_pred_log)
        
    y_pred_series = pd.Series(y_pred_raw, index=y_test_raw.index)
    
    mae = mean_absolute_error(y_test_raw, y_pred_raw)
    r2 = r2_score(y_test_raw, y_pred_raw)
    
    # 修改点：增加学术常用指标 RMSE 和 MAPE
    rmse = np.sqrt(mean_squared_error(y_test_raw, y_pred_raw))
    mape = np.mean(np.abs((y_test_raw - y_pred_raw) / y_test_raw)) * 100
    
    print(f"\n🏆 {game_type.upper()} 训练报告:")
    print(f"   > R² 拟合优度: {r2:.4f}")
    print(f"   > MAE 平均绝对误差: ￥{mae:.2f}")
    print(f"   > RMSE 均方根误差: ￥{rmse:.2f}")
    print(f"   > MAPE 平均绝对百分比误差: {mape:.2f}%")
    print(f"   > 训练/测试样本数: {len(X_train)} / {len(X_test)}")

    errors = abs(y_pred_series - y_test_raw)
    bad_idx = errors.nlargest(6).index 
    
    print(f"\n🚨 {game_type.upper()} 误差最大的 6 个案例:")
    for i, idx in enumerate(bad_idx, 1):
        actual = y_test_raw.loc[idx]
        pred = y_pred_series.loc[idx]
        feat = X.loc[idx].to_dict()
        raw_text = str(clean_df.loc[idx, 'showTitle']) + " " + str(clean_df.loc[idx, 'productName'])
        print(f"   [{i}] 差距: ￥{errors.loc[idx]:.0f} (实际: ￥{actual:.0f} vs AI估: ￥{pred:.0f}) | 内容: {raw_text[:60]}...")

    # ==========================================
    # 🌟 修改点：论文可视化数据导出模块
    # ==========================================
    # 1. 导出特征重要性 (Feature Importance)
    feature_importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    feature_importances.to_csv(f'paper_data_{game_type}_feature_importance.csv', index=False)
    
    # 2. 导出测试集预测对比结果 (实际价格 vs 预测价格)
    results_df = pd.DataFrame({
        'Actual_Price': y_test_raw,
        'Predicted_Price': y_pred_raw,
        'Error': y_pred_raw - y_test_raw
    })
    results_df = pd.concat([results_df, X_test], axis=1) # 拼入特征方便论文做聚类分析
    results_df.to_csv(f'paper_data_{game_type}_test_results.csv', index=False)
    
    # 3. 导出模型训练的 Loss 学习曲线 (Learning Curve)
    evals_result = model.evals_result()
    with open(f'paper_data_{game_type}_learning_curve.json', 'w') as f:
        json.dump(evals_result, f)
        
    print(f"\n📊 论文图表所需数据已导出: paper_data_{game_type}_*.csv/json")

    joblib.dump(model, f'valuer_{game_type}_pro.pkl')
    print(f"✅ 模型已保存为: valuer_{game_type}_pro.pkl\n")

if __name__ == "__main__":
    train_expert_model('raw_Genshin_*.csv', 'genshin')
    train_expert_model('raw_DeltaForce_*.csv', 'delta')