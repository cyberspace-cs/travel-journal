"""
RAG Agent：从知识库召回相关攻略
"""
import chromadb
from backend.config import CHROMA_DIR
from backend.traces import trace_agent

# 初始化 Chroma
client = chromadb.PersistentClient(path=str(CHROMA_DIR))


@trace_agent("rag", "chroma")
def retrieve_context(query: str, city: str = None, top_k: int = 3):
    """
    根据查询，从知识库召回相关的旅行攻略片段
    :param query: 用户说的话，或提到的地名
    :param city: 限定城市（可选）
    :param top_k: 返回几条
    :return: 召回的片段列表
    """
    try:
        collection = client.get_or_create_collection("travel_guides")

        # 如果知识库是空的，返回 mock 数据
        if collection.count() == 0:
            return {
                "contexts": [
                    "大理古城的人民路最有生活气息，傍晚去最好",
                    "洱海环湖建议骑电动车，随时停下来看风景",
                    "喜洲古镇的粑粑一定要尝，现烤的最好吃",
                ],
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }

        # 真实查询
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"city": city} if city else None,
        )

        contexts = results["documents"][0] if results["documents"] else []
        return {
            "contexts": contexts,
            "usage": {"input_tokens": len(query), "output_tokens": sum(len(c) for c in contexts)},
        }

    except Exception as e:
        # 出错就返回空，不影响主流程
        return {
            "contexts": [],
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "error": str(e),
        }


def init_knowledge_base():
    """初始化知识库：插入一些 Demo 用的攻略片段"""
    collection = client.get_or_create_collection("travel_guides")

    if collection.count() > 0:
        print(f"知识库已有 {collection.count()} 条，跳过初始化")
        return

    # 插入一些示例攻略
    sample_data = [
        {"content": "大理古城的人民路最有生活气息，傍晚去最好，有很多街头艺人", "city": "大理", "category": "景点"},
        {"content": "洱海环湖建议骑电动车，随时停下来看风景，不要坐大巴", "city": "大理", "category": "交通"},
        {"content": "喜洲古镇的粑粑一定要尝，现烤的最好吃，甜咸都有", "city": "大理", "category": "美食"},
        {"content": "玉龙雪山海拔 4680 米，记得带氧气罐，高反别硬撑", "city": "丽江", "category": "贴士"},
        {"content": "丽江古城晚上酒吧街很吵，想安静住的话选五一街附近", "city": "丽江", "category": "住宿"},
        {"content": "沙溪古镇比大理古城安静多了，玉津桥日落超美", "city": "大理", "category": "景点"},
    ]

    collection.add(
        documents=[d["content"] for d in sample_data],
        metadatas=[{"city": d["city"], "category": d["category"]} for d in sample_data],
        ids=[f"guide_{i}" for i in range(len(sample_data))],
    )

    print(f"✅ 知识库初始化完成，插入了 {len(sample_data)} 条攻略")


if __name__ == "__main__":
    init_knowledge_base()
