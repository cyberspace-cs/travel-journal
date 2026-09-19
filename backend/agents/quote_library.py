"""
金句库：按分类匹配，不用每次调大模型
"""


# 按分类分的金句库
QUOTE_LIBRARY = {
    "travel": [
        "旅行的声音，我帮你留着。",
        "风过留声，雁过留痕。",
        "今天的风，我记下来了。",
        "走到哪里，都是好天气。",
        "路上的风，比计划更动人。",
        "把日子过成旅行，把旅行过成日子。",
        "风景不说话，但风记得。",
        "在路上，就是最好的时光。",
        "脚步到过的地方，都成了回忆。",
        "生活不止眼前的苟且，还有诗和远方的田野。",
    ],
    "daily": [
        "今天也是好好生活的一天。",
        "把普通的日子，过得浪漫一点。",
        "记录生活，就是热爱生活。",
        "日子慢慢过，慢慢也很好。",
        "平凡的日子，也有光。",
        "今天的小确幸，存起来。",
        "生活不在别处，就在当下。",
        "好好生活，慢慢相遇。",
        "把每一天，都过成值得回忆的一天。",
        "生活细碎，万物成诗。",
    ],
    "work": [
        "把复杂的事，做简单。",
        "一步一步，总有答案。",
        "今天的努力，明天的底气。",
        "认真工作，好好生活。",
        "把每一件小事，做好就是大事。",
        "慢慢来，比较快。",
        "工作是为了更好的生活。",
        "每一步都算数。",
        "专注当下，未来已来。",
        "把工作做成作品。",
    ],
    "food": [
        "人间烟火气，最抚凡人心。",
        "好吃的东西，要记下来。",
        "一碗人间烟火，半日闲情。",
        "吃好喝好，长生不老。",
        "美食是最好的旅行日记。",
    ],
    "emotion": [
        "情绪是彩色的，记下来就不会褪色。",
        "难过会过去，但感受是真的。",
        "开心要记下来，以后慢慢用。",
        "所有的情绪，都值得被记录。",
        "感受当下，就是对自己最好的温柔。",
    ],
}


def get_quote(category: str = "daily", keywords: list = None):
    """
    从金句库里随机选一个最相关的金句
    :param category: 分类：travel/daily/work/food/emotion
    :param keywords: 关键词列表，用来匹配
    :return: 金句
    """
    # 先找对应分类的金句
    quotes = QUOTE_LIBRARY.get(category, QUOTE_LIBRARY["daily"])

    # 如果有关键词，找最相关的
    if keywords:
        best_quote = quotes[0]
        best_score = 0
        for q in quotes:
            score = sum(1 for kw in keywords if kw in q)
            if score > best_score:
                best_score = score
                best_quote = q
        return best_quote

    # 没有关键词就随机选一个
    import random
    return random.choice(quotes)


if __name__ == "__main__":
    # 测试
    print("旅行金句示例:")
    for i in range(3):
        print(f"  {get_quote('travel')}")

    print("\n日常金句示例:")
    for i in range(3):
        print(f"  {get_quote('daily')}")

    print("\n工作金句示例:")
    for i in range(3):
        print(f"  {get_quote('work')}")
