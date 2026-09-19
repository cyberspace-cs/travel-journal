"""
Self-Evolving Agent 自进化模块
- 自我评估：给生成的手帐打分
- 反馈收集：用户满意/不满意，记下来
- Prompt 优化：根据历史反馈自动优化 Prompt
- 风格库：存用户喜欢的手帐，当 Few-shot 例子
"""
import json
import uuid
from datetime import datetime
import dashscope
from dashscope import Generation
from backend.config import DASHSCOPE_API_KEY, QWEN_LITE_MODEL
from backend.database import db
from backend.traces import trace_agent

dashscope.api_key = DASHSCOPE_API_KEY


# ========== 自我评估 ==========

@trace_agent("self_evaluator", QWEN_LITE_MODEL)
def evaluate_journal(content: str, title: str, clips: list):
    """
    自我评估：给刚生成的手帐打分
    从 5 个维度评：
    1. 温度感：有没有回忆感，会不会让人感动
    2. 真实感：像不像用户自己写的，还是太 AI 了
    3. 结构感：像不像手帐，有没有节奏
    4. 信息完整度：有没有把重要片段都包含进去
    5. 文风匹配：是不是用户想要的风格
    """

    prompt = f"""
    你是一个旅行手帐编辑，请给下面这篇手帐打分。

    手帐标题：{title}

    手帐内容：
    {content}

    原始声音片段：
    {json.dumps([c.get('transcript', '') for c in clips], ensure_ascii=False)}

    请从 5 个维度打分（每项 0-10 分）：
    1. 温度感：有没有回忆感，能不能唤起旅行的情绪
    2. 真实感：像不像用户自己写的日记，还是太像 AI 写的
    3. 结构感：像不像一本手帐，有没有翻页的节奏
    4. 信息完整度：有没有把重要的片段都写进去
    5. 自然度：读起来顺不顺，有没有生硬的地方

    返回 JSON 格式：
    {{
        "warmth_score": 0-10,
        "authenticity_score": 0-10,
        "structure_score": 0-10,
        "completeness_score": 0-10,
        "naturalness_score": 0-10,
        "overall_score": 0-10,
        "improvement_suggestion": "一句话说哪里可以改进"
    }}
    """

    response = Generation.call(
        model=QWEN_LITE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        result_format="message",
    )

    if response.status_code == 200:
        text = response.output.choices[0].message.content
        try:
            # 提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            data = json.loads(text[start:end])
            data["usage"] = {
                "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            }
            return data
        except:
            return {
                "overall_score": 7,
                "improvement_suggestion": "解析失败",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }
    else:
        return {
            "overall_score": 7,
            "improvement_suggestion": "评估调用失败",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


# ========== 反馈收集 ==========

def save_feedback(journal_id: str, user_rating: int, user_comment: str = ""):
    """
    保存用户反馈
    :param user_rating: 1-5 分
    :param user_comment: 用户的评价
    """
    db["journal_feedback"].insert({
        "id": f"feedback_{uuid.uuid4().hex[:12]}",
        "journal_id": journal_id,
        "user_rating": user_rating,
        "user_comment": user_comment,
        "created_at": datetime.now().isoformat(),
    })
    return {"status": "ok"}


# ========== 风格库 ==========

def get_style_examples(limit: int = 3):
    """
    从风格库拿用户喜欢的手帐当 Few-shot 例子
    """
    rows = db.execute(
        "SELECT * FROM style_examples ORDER BY rating DESC LIMIT ?",
        [limit]
    )
    return [
        {
            "title": r["title"],
            "content": r["content"],
            "rating": r["rating"],
            "comment": r.get("comment", ""),
        }
        for r in rows
    ]


def add_style_example(title: str, content: str, rating: int, comment: str = ""):
    """
    把用户喜欢的手帐加到风格库
    """
    db["style_examples"].insert({
        "id": f"style_{uuid.uuid4().hex[:12]}",
        "title": title,
        "content": content,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now().isoformat(),
    })


# ========== Prompt 优化器 ==========

@trace_agent("prompt_optimizer", QWEN_LITE_MODEL)
def optimize_prompt(current_prompt: str, feedbacks: list):
    """
    根据历史用户反馈，自动优化写作 Prompt
    """

    feedback_text = "\n".join([
        f"- 评分 {f['user_rating']}：{f['user_comment']}"
        for f in feedbacks[-10:]  # 最近 10 条反馈
    ])

    prompt = f"""
    这是当前的手帐写作 Prompt：
    ---
    {current_prompt}
    ---

    以下是最近用户的反馈：
    ---
    {feedback_text}
    ---

    请根据用户反馈，优化上面的 Prompt，让生成的手帐更符合用户的口味。
    只输出优化后的 Prompt 内容，不要解释。
    """

    response = Generation.call(
        model=QWEN_LITE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        result_format="message",
    )

    if response.status_code == 200:
        new_prompt = response.output.choices[0].message.content
        return {
            "optimized_prompt": new_prompt,
            "usage": {
                "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            },
        }
    else:
        return {
            "optimized_prompt": current_prompt,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


# ========== 初始化自进化相关表 ==========

def init_evolution_tables():
    """初始化自进化相关的数据库表"""

    # 手帐反馈表
    if "journal_feedback" not in db.table_names():
        db["journal_feedback"].create({
            "id": str,
            "journal_id": str,
            "user_rating": int,
            "user_comment": str,
            "created_at": str,
        }, pk="id")

    # 风格示例库
    if "style_examples" not in db.table_names():
        db["style_examples"].create({
            "id": str,
            "title": str,
            "content": str,
            "rating": int,
            "comment": str,
            "created_at": str,
        }, pk="id")

    print("✅ 自进化模块数据库表初始化完成")


if __name__ == "__main__":
    init_evolution_tables()
