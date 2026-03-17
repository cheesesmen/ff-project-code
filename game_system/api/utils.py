import re
import pandas as pd

DELTA_SKINS = {
    "ops_red": ["赤影猎手", "毒液专家", "荒野猎手", "苍龙", "暗金教父", "星夜舞者", "战场先锋", "战地医师"],
    "ops_gold": ["丛林迷彩", "沙漠迷彩", "雪地迷彩", "城市迷彩", "工业迷彩", "霓虹迷彩"],
    "knife": ["暗夜猎手", "赤焰", "冰霜", "黄金", "黑曜石", "霓虹", "迷彩"],
    "gun_red_high": ["赤影", "苍龙", "暗金", "霓虹", "荒野", "冰霜", "暗金", "荒野"], 
    "gun_red_mid": ["毒液", "迷彩", "赤焰", "暗夜"], 
    "gun_red_low": ["黄金", "黑曜石", "赤焰", "暗夜"]  
}
DELTA_CORE = ["赛季手册满级", "典藏手册", "限定角色", "限定武器", "刀皮全套", "红皮全套", "金皮全套"]

def extract_features_from_db(acc, game_type):
    text = str(acc.show_title)
    f = {}
    
    if game_type == 'genshin':
        f['email_coeff'] = 1.0 if "未绑定" in text else (0.88 if "已实名" in text else 0.85)
        m_y = re.search(r'黄数\s*[:：]?\s*(\d+)', text)
        f['yellow_num'] = float(m_y.group(1)) if m_y else (float(re.search(r'(\d+)\s*黄(?!数)', text).group(1)) if re.search(r'(\d+)\s*黄(?!数)', text) else 0.0)
        m_s = re.search(r'(\d+)\s*套时装|时装数量\s*[:：]?\s*(\d+)', text)
        f['skin_cnt'] = float(m_s.group(1) or m_s.group(2)) if m_s else 0.0
        f['meta_score'] = f['yellow_num'] * 2.0 
        f['whale_factor'] = (f['meta_score'] ** 1.35) if f['meta_score'] > 200 else f['meta_score']
        f['c6_synergy_rate'] = 1.0
        f['t1_c6_cnt'] = float(len(re.findall(r'满命', text)))
        f['t2_c6_cnt'] = 0.0
        f['r5_weapon_cnt'] = float(len(re.findall(r'精5', text)))
        f['currency_val'] = 0.0
        
    elif game_type == 'delta':
        f['email_coeff'] = 0.8 if re.search(r'不可二次', text) else (1.0 if re.search(r'可二次', text) else 0.9)
        m_asset = re.search(r'总资产\s*[:：]?\s*([\d\.]+)', text)
        f['assets_m'] = float(m_asset.group(1)) if m_asset else (float(re.search(r'([\d\.]+)\s*[Mm姆]', text).group(1)) if re.search(r'([\d\.]+)\s*[Mm姆]', text) else 0.0)
        m_hafu = re.search(r'哈夫币\s*[:：]?\s*([\d\.]+)', text)
        f['hafu_w'] = float(m_hafu.group(1)) if m_hafu else (float(re.search(r'([\d\.]+)\s*[Ww万]', text).group(1)) if re.search(r'([\d\.]+)\s*[Ww万]', text) else 0.0)
        
        f['ops_red_cnt'] = float(sum(1 for s in set(DELTA_SKINS["ops_red"]) if s in text))
        f['ops_gold_cnt'] = float(sum(1 for s in set(DELTA_SKINS["ops_gold"]) if s in text))
        f['knife_cnt'] = float(sum(1 for s in set(DELTA_SKINS["knife"]) if s in text))
        f['gun_red_high'] = float(sum(1 for s in set(DELTA_SKINS["gun_red_high"]) if s in text))
        f['gun_red_mid'] = float(sum(1 for s in set(DELTA_SKINS["gun_red_mid"]) if s in text))
        f['gun_red_low'] = float(sum(1 for s in set(DELTA_SKINS["gun_red_low"]) if s in text))
        f['core_asset_flag'] = float(sum(1 for c in DELTA_CORE if c in text))

    return pd.Series(f)