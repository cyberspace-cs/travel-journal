"""
内容分类 Agent：判断音频内容是不是旅行相关的
避免把工作/会议/日常内容硬编成旅行手帐
"""
import re


# 旅行相关关键词
TRAVEL_KEYWORDS = [
    "旅行", "旅游", "度假", "景点", "景区", "打卡", "拍照",
    "酒店", "民宿", "机票", "高铁", "火车", "飞机", "打车", "公交",
    "古城", "古镇", "风景", "日出", "日落", "云海", "雪山",
    "洱海", "苍山", "丽江", "大理", "成都", "重庆", "西安",
    "小吃", "美食", "米线", "火锅", "烧烤", "咖啡",
    "背包", "行李箱", "攻略", "自由行", "跟团",
]

# 工作/会议相关关键词
WORK_KEYWORDS = [
    "工作", "会议", "项目", "KPI", "汇报", "PPT", "邮件",
    "基层治理", "政策", "部门", "协同", "考核", "指标",
    "同事", "老板", "领导", "客户", "需求", "产品",
    "代码", "bug", "上线", "测试", "开发",
]


def classify_content(text: str):
    """
    分类音频内容是不是旅行相关的
    :return: {
        "is_travel": bool,
        "travel_score": float (0-1),
        "content_type": "travel" / "work" / "daily" / "other",
        "message": str
    }
    """
    travel_count = sum(1 for kw in TRAVEL_KEYWORDS if kw in text)
    work_count = sum(1 for kw in WORK_KEYWORDS if kw in text)

    # 旅行相关得分
    travel_score = min(travel_count / 5.0, 1.0)  # 5个关键词就满分

    # 判断类型
    if travel_count >= 2 and travel_count > work_count:
        return {
            "is_travel": True,
            "travel_score": travel_score,
            "content_type": "travel",
            "message": "检测到旅行内容，可以生成旅行手帐 ✨",
        }
    elif work_count >= 2 and work_count > travel_count:
        return {
            "is_travel": False,
            "travel_score": travel_score,
            "content_type": "work",
            "message": "检测到工作/会议内容，这不是旅行相关的哦～我们是旅行手帐 AI，帮你把旅行声音变成有温度的图文手帐。如果你想记录工作内容，我可以帮你做个会议纪要总结 😊",
        }
    elif travel_count >= 1:
        return {
            "is_travel": True,
            "travel_score": travel_score,
            "content_type": "travel",
            "message": "检测到旅行相关内容，开始生成手帐...",
        }
    else:
        return {
            "is_travel": False,
            "travel_score": travel_score,
            "content_type": "other",
            "message": "这个音频内容和旅行关系不大哦～我们是旅行手帐 AI，专门帮你把旅途中的声音、见闻、感受变成有温度的图文手帐。下次旅行的时候再用它吧！🎒",
        }


if __name__ == "__main__":
    # 测试
    test_cases = [
        ("今天在大理古城逛了逛，吃了米线，下午去洱海吹风", "旅行"),
        ("基层治理涉及多个层级多个领域，各主体各置其位，信息梗阻", "工作"),
        ("早上起来做了个早饭，然后去上班，开了三个会", "日常"),
        ("爬玉龙雪山，高反了但是看到雪山那一刻值了", "旅行"),
    ]

    for text, expected in test_cases:
        result = classify_content(text)
        print(f"预期: {expected}, 实际: {result['content_type']}")
        print(f"  得分: {result['travel_score']:.2f}")
        print(f"  消息: {result['message'][:50]}...")
        print()
