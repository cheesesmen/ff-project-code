import re
import pandas as pd

# ==========================================
# 1. 专家知识库配置 (与 model_test.py 完全同步)
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
# 2. 特征抽取引擎 (对接 Django 数据库对象)
# ==========================================
def extract_features_from_db(acc, game_type):
    """
    将 Django 的 Account 对象转换为模型可识别的特征格式
    """
    # 获取标题信息
    text = str(acc.show_title)
    
    # 如果你的数据库模型有 productName 字段，可以取消下面两行的注释把它加上
    # if hasattr(acc, 'product_name') and acc.product_name:
    #     text += " " + str(acc.product_name)

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
        
        m_fates = re.search(r'纠缠(?:之源)?\s*[:：]?\s*(\d+)', text)
        fates = float(m_fates.group(1)) if m_fates else 0.0
        m_primos = re.search(r'原石\s*[:：]?\s*(\d+)', text)
        primos = float(m_primos.group(1)) if m_primos else 0.0
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

    # 返回 Pandas Series 格式，这与之前 views.py 里的预测调用保持一致
    return pd.Series(f)