# 旅行手帐 AI

> 白天你玩你的，晚上手帐自己长出来

安克首届黑客松 · 智能录音赛道参赛项目

## 项目简介

旅行的时候用录音豆随手录下声音，晚上 AI 自动把它变成一篇有温度的旅行手帐。
不需要你打字，不需要你整理，睡觉的时候 AI 就帮你写好了。

## 技术栈

- **后端**：Python + FastAPI
- **数据库**：SQLite + Chroma 向量库
- **AI 模型**：阿里千问（ASR + LLM）
- **前端**：HTML + CSS + 原生 JS（Demo 阶段）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export DASHSCOPE_API_KEY="your-qwen-api-key"

# 3. 初始化数据库
python -m backend.database

# 4. 启动服务器
python -m backend.main
```

打开 http://localhost:8000 就能看到 Demo 页面。

## 项目结构

```
travel-journal/
├── backend/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置
│   ├── database.py      # 数据库
│   ├── traces.py        # Agent Trace 可观测性
│   ├── agents/          # 各个 Agent
│   │   ├── asr.py       # 语音转写
│   │   ├── writer.py    # 写手帐
│   │   ├── rag.py       # 知识库 RAG
│   │   └── router.py    # 路由层
│   └── pipelines/       # 流水线
│       └── simple_pipeline.py
├── frontend/
│   └── index.html       # Demo 页面
└── data/
    ├── audio/           # 音频文件
    ├── chroma_db/       # 向量库
    └── app.db           # SQLite
```

## 核心功能

- [x] 上传音频 → 自动转写 → 打标签 → 写手帐
- [x] 快速模式 / 深度模式 双路径
- [x] RAG 知识库召回
- [x] Agent Trace 记录（耗时/token/成本）
- [ ] 录音豆 SDK 对接
- [ ] 地图页
- [ ] 分享卡片生成

## 产品设计

详细 PRD 和代码实现方案见飞书文档：
- 旅行版 PRD：https://my.feishu.cn/docx/Mxx6dEU6NoBCPyxiwKBcJqbRnWe
- 代码实现方案：https://my.feishu.cn/docx/KuuGdgSWUosnajx3sJmca8BsnNf
