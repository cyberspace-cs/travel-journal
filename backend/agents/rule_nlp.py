"""
规则化 NLP 模块：不依赖大模型，本地规则跑
用来做标签、打分、情绪识别，省成本省时间
"""
import re


# ========== 关键词 → 标签映射表 ==========

TAG_KEYWORDS = {
    "美食": ["吃", "喝", "味道", "好吃", "米线", "面", "饭", "咖啡", "奶茶", "小吃", "餐厅", "老板", "厨师", "香", "甜", "辣", "咸"],
    "景点": ["风景", "好看", "拍照", "打卡", "景点", "景区", "公园", "山", "水", "湖", "海", "古城", "古镇", "寺庙", "塔"],
    "感受": ["感觉", "觉得", "心情", "开心", "难过", "感动", "治愈", "舒服", "累", "放松", "享受", "喜欢", "讨厌", "惊讶", "意外"],
    "交通": ["车", "地铁", "公交", "打车", "走路", "骑", "飞机", "火车", " delay", "堵车", "司机", "导航", "路", "走"],
    "住宿": ["酒店", "民宿", "房间", "床", "干净", "脏", "前台", "入住", "退房", "阳台", "窗"],
    "购物": ["买", "逛", "店", "商店", "超市", "特产", "纪念品", "砍价", "便宜", "贵"],
    "人文": ["历史", "文化", "当地人", "传统", "习俗", "故事", "老人", "小孩", "街头", "集市"],
    "日落/日出": ["日落", "日出", "夕阳", "朝阳", "黄昏", "清晨"],
    "美食/本地特色": ["本地", "特色", "传统", "老字号", "三十年", "老", "正宗"],
}

# ========== 情绪关键词表 ==========

EMOTION_KEYWORDS = {
    "开心": ["开心", "快乐", "高兴", "棒", "好", "喜欢", "爱", "爽", "哈哈", "笑", "满意", "治愈", "舒服"],
    "感动": ["感动", "泪目", "温暖", "温柔", "难忘", "纪念", "回忆", "珍贵", "美好"],
    "疲惫": ["累", "疲惫", "困", "乏", "脚痛", "腰酸", "走不动", "躺平", "休息"],
    "惊喜": ["惊喜", "没想到", "意外", "哇", "居然", "竟然", "震撼", "壮观", "太美了"],
    "平静": ["平静", "安静", "悠闲", "慢", "放松", "发呆", "放空", "舒服"],
}

# ========== 地点关键词表 ==========

CITY_KEYWORDS = [
    "大理", "丽江", "昆明", "成都", "重庆", "西安", "北京", "上海", "杭州",
    "苏州", "厦门", "三亚", "桂林", "张家界", "黄山", "拉萨", "新疆", "西藏",
    "古城", "古镇", "洱海", "玉龙雪山", "双廊", "喜洲", "束河", "虎跳峡",
]


def rule_based_tag(text: str):
    """
    规则化打标签：不调大模型，用关键词匹配
    """
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                tags.append(tag)
                break  # 每个标签只加一次

    # 去重
    tags = list(set(tags))
    return tags[:5]  # 最多 5 个标签


def rule_based_score(text: str, tags: list):
    """
    规则化打分：根据关键词数量、情绪词数量来打分
    """
    score = 0.5  # 基础分

    # 有具体内容加分
    if len(text) > 20:
        score += 0.1
    if len(text) > 50:
        score += 0.1

    # 有情绪词加分
    has_emotion = False
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                has_emotion = True
                break
    if has_emotion:
        score += 0.15

    # 有具体地点/事物加分
    if any(kw in text for kw in CITY_KEYWORDS):
        score += 0.1

    # 标签越多分越高
    score += min(len(tags) * 0.05, 0.15)

    # 封顶
    return min(score, 0.95)


def rule_based_emotion(text: str):
    """
    规则化情绪识别
    """
    emotion_counts = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        count = 0
        for kw in keywords:
            if kw in text:
                count += 1
        emotion_counts[emotion] = count

    # 取最多的
    if max(emotion_counts.values()) == 0:
        return "平静"

    return max(emotion_counts, key=emotion_counts.get)


def rule_based_location(text: str):
    """
    规则化地点识别
    """
    for city in CITY_KEYWORDS:
        if city in text:
            return city
    return "未知"


def rule_based_classify(text: str):
    """
    一站式规则化分类：打标签 + 打分 + 情绪 + 地点
    不用调大模型，本地秒出结果
    """
    tags = rule_based_tag(text)
    score = rule_based_score(text, tags)
    emotion = rule_based_emotion(text)
    location = rule_based_location(text)

    return {
        "tags": tags,
        "score": score,
        "location": location,
        "emotion": emotion,
    }


if __name__ == "__main__":
    # 测试
    test_texts = [
        "今天在大理古城逛了逛，人好多啊，但是很有感觉。",
        "吃了一家很好吃的米线，老板是本地人，说他们做了三十年了。",
        "下午去了洱海，风吹过来特别舒服，看到好多人在拍照。",
        "晚上去了双廊，看了日落，太治愈了。",
    ]

    for t in test_texts:
        result = rule_based_classify(t)
        print(f"原文: {t}")
        print(f"标签: {result['tags']}")
        print(f"打分: {result['score']:.2f}")
        print(f"情绪: {result['emotion']}")
        print(f"地点: {result['location']}")
        print("---")
