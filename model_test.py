import pandas as pd
import numpy as np
import re
import glob
import joblib
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

warnings.filterwarnings("ignore")

# ==========================================
# 1. 专家知识库配置 (5 级精准梯度)
# ==========================================
GENSHIN_TIER = {
    1: ["兹白", "奈芙尔", "恰斯卡", "杜林", "玛薇卡", "芙宁娜", "丝柯克", "瓦雷莎", "菈乌玛", "伊涅芙", "茜特菈莉", "爱可菲", "菲林斯", "哥伦比娅"],
    2: ["千织", "阿蕾奇诺", "玛拉妮", "法尔伽", "基尼奇", "那维莱特", "希诺宁", "闲云"],
    3: ["艾梅莉埃", "林尼", "万叶", "雷电将军", "克洛琳德", "娜维娅"],
    4: ["希格雯", "妮露", "艾尔海森", "神里绫华", "纳西妲", "申鹤", "阿贝多", "胡桃", "夜兰", "魈", "温迪", "优菈", "甘雨", "八重神子", "钟离", "白术", "珊瑚宫心海", "荒泷一斗", "流浪者"],
    5: ["琴", "迪卢克", "可莉", "莫娜", "埃洛伊", "宵宫", "迪希雅", "神里绫人", "刻晴", "七七", "达达利亚", "提纳里", "赛诺", "梦见月瑞希"]
}

DELTA_SKINS = {
    "ops_red": ["赤影猎手", "毒液专家", "荒野猎手", "苍龙", "暗金教父", "星夜舞者", "战场先锋", "战地医师"],
    "ops_gold": ["丛林迷彩", "沙漠迷彩", "雪地迷彩", "城市迷彩", "工业迷彩", "霓虹迷彩"],
    "knife": ["暗夜猎手", "赤焰", "冰霜", "黄金", "黑曜石", "霓虹", "迷彩"],
    "gun_red_high": ["赤影", "苍龙", "暗金", "霓虹", "荒野", "冰霜", "暗金", "荒野"], 
    "gun_red_mid": ["毒液", "迷彩", "赤焰", "暗夜"], 
    "gun_red_low": ["黄金", "黑曜石", "赤焰", "暗夜"]  
}
DELTA_CORE = ["赛季手册满级", "典藏手册", "限定角色", "限定武器", "刀皮全套", "红皮全套", "金皮全套"]

# ==========================================
# 2. 泰斗级特征抽取：动态降权协同引擎
# ==========================================
def get_email_multiplier(text, game_type):
    if game_type == 'delta':
        if re.search(r'不可二次实名|不可二次|不能二次|死实名', text): return 0.8
        if re.search(r'可二次实名|可二次|包二次|支持二次', text): return 1.0
        return 0.9 
    else:
        if "未绑定" in text: return 1.0
        if "未实名" in text: return 0.94
        if "已实名" in text or "实名出售" in text: return 0.88
        if "不出售" in text or "死邮" in text: return 0.82
        return 0.85

def extract_features(row, game_type):
    text = str(row.get('showTitle', '')) + " " + str(row.get('productName', ''))
    f = {}
    f['email_coeff'] = get_email_multiplier(text, game_type)

    if game_type == 'genshin':
        t1t2_c6_score = 0.0      
        t1_c6_cnt = 0        
        t2_c6_cnt = 0
        
        t1t2_c2plus_score = 0.0  
        t1_c2plus_cnt = 0    
        t2_c2plus_cnt = 0
        
        t3_score = 0.0           
        t4_score = 0.0           
        t5_score = 0.0           
        base_score = 0.0         
        
        # 完美提取黄数
        m_yellow_explicit = re.search(r'黄数\s*[:：]?\s*(\d+)', text)
        if m_yellow_explicit:
            f['yellow_num'] = float(m_yellow_explicit.group(1))
        else:
            m_yellow_implicit = re.search(r'(\d+)\s*黄(?!数)', text)
            f['yellow_num'] = float(m_yellow_implicit.group(1)) if m_yellow_implicit else 0.0

        for tier, chars in GENSHIN_TIER.items():
            for char in chars:
                if char in text:
                    m = re.search(fr'(满命|[1-6]命)[\s,，、]*{char}|{char}[\s,，、]*(满命|[1-6]命)', text)
                    cons = 0
                    if m:
                        match_str = m.group(1) or m.group(2)
                        cons = 6 if '满' in match_str else int(match_str[0])
                    
                    if cons == 6:
                        if tier == 1:
                            t1t2_c6_score += 250
                            t1_c6_cnt += 1
                        elif tier == 2:
                            t1t2_c6_score += 120
                            t2_c6_cnt += 1
                        elif tier == 3: t3_score += 60   
                        elif tier == 4: t4_score += 30   
                        else: t5_score += 5    
                            
                    elif cons >= 2:
                        if tier == 1:
                            t1t2_c2plus_score += 60 + (cons * 20)
                            t1_c2plus_cnt += 1
                        elif tier == 2:
                            t1t2_c2plus_score += 30 + (cons * 15)
                            t2_c2plus_cnt += 1
                        elif tier == 3: t3_score += 15 + (cons * 7.5) 
                        elif tier == 4: t4_score += 7.5 + (cons * 3.5) 
                        else: t5_score += 2
                    else:
                        base_pts = {1: 15, 2: 10, 3: 5, 4: 2.5, 5: 1}[tier]
                        base_score += base_pts
        
        # T2 联动增幅削弱
        base_deduct_c6 = 0.35 if t1_c6_cnt > 0 else (0.15 if t2_c6_cnt > 0 else 0)
        c6_synergy = 1.0 + (t1_c6_cnt * 0.35) + (t2_c6_cnt * 0.15) - base_deduct_c6
        
        base_deduct_c2 = 0.20 if t1_c2plus_cnt > 0 else (0.10 if t2_c2plus_cnt > 0 else 0)
        c2_synergy = 1.0 + (t1_c2plus_cnt * 0.20) + (t2_c2plus_cnt * 0.10) - base_deduct_c2
        
        m_skin = re.search(r'(\d+)\s*套时装|时装数量\s*[:：]?\s*(\d+)', text)
        skin_cnt = float(m_skin.group(1) or m_skin.group(2)) if m_skin else 0.0
        f['skin_cnt'] = skin_cnt
        
        raw_meta_score = (t1t2_c6_score * c6_synergy) + (t1t2_c2plus_score * c2_synergy) + t3_score + t4_score + t5_score + base_score + (skin_cnt * 10)
        
        f['meta_score'] = raw_meta_score * f['email_coeff']
        f['whale_factor'] = (f['meta_score'] ** 1.35) if f['meta_score'] > 200 else f['meta_score']
        
        f['c6_synergy_rate'] = c6_synergy
        f['t1_c6_cnt'] = t1_c6_cnt
        f['t2_c6_cnt'] = t2_c6_cnt
        f['r5_weapon_cnt'] = len(re.findall(r'精5', text))
        
        def get_n(p): m = re.search(p, text); return float(m.group(1) or m.group(2)) if m else 0.0
        fates = get_n(r'纠缠之源\s*[:：]?\s*(\d+)|纠缠\s*(\d+)')
        primos = get_n(r'原石\s*[:：]?\s*(\d+)')
        f['currency_val'] = (fates + primos/160) * 1.5

    else:
        # 三角洲资产提取
        m_asset_explicit = re.search(r'总资产\s*[:：]?\s*([\d\.]+)', text)
        if m_asset_explicit: f['assets_m'] = float(m_asset_explicit.group(1))
        else:
            m_asset_implicit = re.search(r'([\d\.]+)\s*[Mm姆]', text)
            f['assets_m'] = float(m_asset_implicit.group(1)) if m_asset_implicit else 0.0

        m_hafu_explicit = re.search(r'哈夫币\s*[:：]?\s*([\d\.]+)', text)
        if m_hafu_explicit: f['hafu_w'] = float(m_hafu_explicit.group(1))
        else:
            m_hafu_implicit = re.search(r'([\d\.]+)\s*[Ww万]', text)
            f['hafu_w'] = float(m_hafu_implicit.group(1)) if m_hafu_implicit else 0.0
        
        f['ops_red_cnt'] = sum(1 for s in set(DELTA_SKINS["ops_red"]) if s in text)
        f['ops_gold_cnt'] = sum(1 for s in set(DELTA_SKINS["ops_gold"]) if s in text)
        f['knife_cnt'] = sum(1 for s in set(DELTA_SKINS["knife"]) if s in text)
        f['gun_red_high'] = sum(1 for s in set(DELTA_SKINS["gun_red_high"]) if s in text) 
        f['gun_red_mid'] = sum(1 for s in set(DELTA_SKINS["gun_red_mid"]) if s in text)   
        f['gun_red_low'] = sum(1 for s in set(DELTA_SKINS["gun_red_low"]) if s in text)   
        f['core_asset_flag'] = sum(1 for c in DELTA_CORE if c in text)

    return pd.Series(f)

# ==========================================
# 3. 训练与严苛过滤系统
# ==========================================
def train_expert_model(search_pattern, game_type):
    print(f"\n🚀 启动 {game_type.upper()} [极严过滤+前10诊断版] 模型...")
    all_files = glob.glob(search_pattern)
    if not all_files: return
    
    df = pd.concat([pd.read_csv(f) for f in all_files]).drop_duplicates(subset=['productId'])
    
    # === 🛡️ 核心改动：物理降噪 - 严格约束价格与截图条件 ===
    if game_type == 'genshin':
        # 提取标题和商品名，方便搜索
        text_series = df['showTitle'].astype(str) + df['productName'].astype(str)
        # 过滤价格 1000~15000，且必须包含“官方截图”
        mask_price_img = (df['price'] >= 1000) & (df['price'] <= 15000) & text_series.str.contains("官方截图", na=False)
        clean_df = df[mask_price_img].copy().reset_index(drop=True)
        print(f"🧹 [基础清洗] 仅保留价格 1000~15000 且含官方截图的账号，剩余 {len(clean_df)} 条。")
    else:
        clean_df = df[(df['price'] > 150) & (df['price'] < 30000)].copy().reset_index(drop=True)
    
    # 提取特征
    X = clean_df.apply(lambda r: extract_features(r, game_type), axis=1).fillna(0.0)
    
    # === 🛡️ 核心改动：物理降噪 - 剔除黄数异常值 ===
    if game_type == 'genshin':
        before_len = len(X)
        # 黄数必须在 40 到 240 之间
        valid_mask = (X['yellow_num'] >= 40) & (X['yellow_num'] <= 240)
        X = X[valid_mask]
        clean_df = clean_df[valid_mask] 
        print(f"🧹 [深度清洗] 已剔除黄数 <40 或 >240 的异常账号，共排除 {before_len - len(X)} 条。")

    y_real = clean_df['price'].astype(float)
    
    X_train, X_test, y_train_real, y_test_real = train_test_split(
        X, y_real, test_size=0.2, random_state=42
    )
    
    rf = RandomForestRegressor(n_estimators=500, max_depth=None, min_samples_split=2, random_state=42)
    rf.fit(X_train, y_train_real)
    
    y_pred_real = pd.Series(rf.predict(X_test), index=y_test_real.index)
    score = r2_score(y_test_real, y_pred_real)
    
    print(f"\n{'='*65}")
    print(f"🏆 {game_type.upper()} 训练完毕 | R²: {score:.4f}")
    print(f"{'='*65}")
    
    # === 核心改动：输出扩大至前 10 名 ===
    errors = abs(y_pred_real - y_test_real)
    bad_idx = errors.nlargest(10).index 
    
    print(f"\n🚨 {game_type.upper()} 误差前 10 名 [深度诊断白盒]:")
    for rank, idx in enumerate(bad_idx, 1):
        actual = y_test_real.loc[idx]
        pred = y_pred_real.loc[idx]
        
        raw_text = str(clean_df.loc[idx, 'showTitle']) + " " + str(clean_df.loc[idx, 'productName'])
        feat = X.loc[idx].to_dict()
        
        print(f"\n[{rank}] 差距: ￥{errors.loc[idx]:.0f} (实际: ￥{actual:.0f} | AI估算: ￥{pred:.0f})")
        
        if game_type == 'genshin':
            print(f"   [战力指数] 最终分:{feat.get('meta_score',0):.0f} | 破壁极值:{feat.get('whale_factor',0):.0f}")
            print(f"   [协同效应] 触发满命暴击倍率: {feat.get('c6_synergy_rate',1):.2f}x (T1满命:{feat.get('t1_c6_cnt',0):.0f}个, T2满命:{feat.get('t2_c6_cnt',0):.0f}个)")
            print(f"   [基础指标] 黄数: {feat.get('yellow_num',0):.0f} | 邮箱系数:{feat.get('email_coeff',1.0)}")
        else:
            print(f"   [资产概览] 资产:{feat.get('assets_m',0)}M | 核心满配:{feat.get('core_asset_flag',0)}个")
            print(f"   [高级皮肤] 刀皮:{feat.get('knife_cnt',0)} | 高级红枪:{feat.get('gun_red_high',0)} | 角色红皮:{feat.get('ops_red_cnt',0)}")
            print(f"   [安全体系] 实名系数:{feat.get('email_coeff',1.0)} (1.0=可二次, 0.8=不可二次)")

        print(f"   [原始文本] \n      {raw_text[:400]}...")

    joblib.dump(rf, f'valuer_{game_type}_pro.pkl')

if __name__ == "__main__":
    train_expert_model('*10026*.csv', 'genshin')
    train_expert_model('*10371*.csv', 'delta')