# 律所智能问答 RAG 系统

法律垂直领域多 Agent 智能问答系统。基于 RAG（检索增强生成）技术，结合 LangGraph 多 Agent 协作架构和 Function Calling，为民商事诉讼、刑事辩护、行政诉讼三类案件提供专业法律咨询服务。支持 Word/PDF 文档智能分块、混合向量检索、精排重排序、会话记忆、检索参数动态调整。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 前端框架 | Vue 3 + Vite |
| 向量数据库 | Milvus 2.|
| 多 Agent 框架 | LangGraph + LangChain |
| 嵌入模型 | BGE-M3（稠密 + 稀疏双编码） |
| 重排序模型 | BGE Reranker v2-M3 |
| 大模型 | DeepSeek API |
| LLM 框架 | LangChain |


---

## 项目结构

```
RAG3.0/
├── test/                                  # 后端代码
│   ├── agent/                             # 多 Agent 模块
│   │   ├── legal_graph.py                 # LangGraph 工作流编排
│   │   ├── reception_agent.py             # 客户接待 Agent（信息收集/分类/追问）
│   │   ├── civil_lawyer_agent.py          # 民商事诉讼律师 Agent
│   │   ├── criminal_lawyer_agent.py       # 刑事辩护律师 Agent
│   │   ├── admin_lawyer_agent.py          # 行政诉讼律师 Agent
│   │   ├── FengKuaiAgent.py               # 语义分块 Agent 入口
│   │   ├── tools.py                       # Function Calling 工具定义
│   │   ├── prompt_loader.py               # Prompt 文件加载工具
│   │   └── prompts/                       # Prompt 模板
│   │       ├── legal_reception.txt        # 接待 Agent 提示词
│   │       ├── legal_civil_lawyer.txt     # 民商事律师提示词
│   │       ├── legal_criminal_lawyer.txt  # 刑事律师提示词
│   │       ├── legal_admin_lawyer.txt     # 行政律师提示词
│   │       ├── gray_zone_chunker.txt      # 灰色地带 LLM 判定提示词
│   │       └── smart_chunker.txt          # 智能分块提示词
│   ├── api/                               # FastAPI 路由层
│   │   ├── __init__.py                    # 应用工厂、CORS、生命周期
│   │   ├── router.py                      # 路由聚合
│   │   ├── chat.py                        # 法律咨询接口 
│   │   ├── collection.py                  # Milvus 集合管理接口
│   │   └── documents.py                   # 文档上传/删除接口
│   ├── database/
│   │   ├── milvus.py                      # Milvus 操作
│   │   └── registry.py                    # 文件注册表
│   ├── jiansuo/
│   │   └── qurey.py                       # 检索入口（编码 → 混合检索）
│   ├── qianru/
│   │   └── BGE.py                         # BGE-M3 稠密+稀疏向量编码
│   ├── chongpai/
│   │   └── reranker.py                    # BGE Reranker 精排
│   ├── load/
│   │   ├── smart_chunker.py               # 核心分块逻辑（BGE-M3 + 百分位 + LLM）
│   │   ├── load_word.py                   # Word 文档段落提取
│   │   └── load_pdf.py                    # PDF 文档文本块提取
│   ├── llmodel/
│   │   └── llm.py                         # LLM 实例初始化
│   ├── data/                              # 测试用法律文档
│   ├── config.py                          # 环境变量加载与配置
│   ├── main.py                            # 启动入口
│   ├── file_registry.json                 # 文件注册表
│   ├── .env.example                       # 环境变量模板
│   └── requirements.txt                   # Python 依赖
│
├── qianduan/                              # 前端代码
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── router/index.js
│   │   ├── api/entries.js                 # API 请求封装
│   │   └── views/
│   │       ├── ChatPage.vue               # 法律咨询
│   │       ├── CollectionsPage.vue        # 集合管理
│   │       ├── DocumentsPage.vue          # 文档上传与管理（.docx / .pdf）
│   │       └── ParamsPage.vue             # 检索参数调整
│   ├── index.html
│   ├── vite.config.js                     # Vite 配置（含 API 代理超时）
│   └── package.json
│
└── .gitignore
```

---

## 核心架构

### 1. LangGraph 多 Agent 工作流

```
                         ┌────────────┐
                         │  用户输入   │
                         └─────┬──────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │      客户接待 Agent            │
               │  · 分析对话历史 + 最新问题      │
               │  · 提取/更新三要素：            │
               │    案件类型 | 用户诉求 | 基本信息 │
               │  · 判断三要素是否全部收集完毕     │
               └───────────────┬───────────────┘
                               │
                     _route_after_reception()
                               │
               ┌───────┬───────┼───────┬───────┐
               │       │       │       │       │
               ▼       ▼       ▼       ▼       ▼
           incomplete 民商事   刑事    行政   其他案件
               │       │       │       │       │
               ▼       ▼       ▼       ▼       ▼
          ┌────────┐┌──────┐┌──────┐┌──────┐┌──────────┐
          │追问用户││民事  ││刑事  ││行政  ││本律所暂   │
          │ END   ││律师  ││律师  ││律师  ││无法受理   │
          └────────┘└──┬───┘└──┬───┘└──┬───┘└──────────┘
                       │       │       │
                       ▼       ▼       ▼
                     ┌──────────────────────┐
                     │   生成法律分析意见     │
                     │        END           │
                     └──────────────────────┘
```

**关键设计**：
- 接待 Agent 收齐「案件类型 + 用户诉求 + 案件基本信息」后才交接，不全则持续追问
- 传递单向：接待 → 律师，律师不反向回传
- 每个 Agent 独立维护对话历史，通过 LangGraph State 传递

### 2. RAG 混合检索流程（Function Calling 驱动）

```
律师Agent 接收: 案件类型 + 用户诉求 + 基本信息
    │
    ├─→ LLM 分析案情，提取关键法律要素
    │
    ├─→ Agent 自主决定调用 search_knowledge_base 检索
    │       ├── BGE-M3 稠密语义检索 top-K
    │       ├── BGE-M3 稀疏关键词检索 top-K
    │       └── RRF 融合排序（加权）
    │
    ├─→ Agent 查看检索结果，自主判断：
    │       ├── 不够全面 → 换检索词再次检索
    │       ├── 太多需筛选 → 调用 rerank_documents 精排
    │       └── 少数且相关 → 直接入分析
    │
    └─→ Agent 基于精排案例生成法律分析报告
```


### 3. 文档语义分块流程

```
Word / PDF 文档
    │
    ├─→ 提取所有文本段落
    │
    ├─→ BGE-M3 编码每个段落 → 稠密向量
    │
    ├─→ 计算相邻段落余弦相似度
    │
    ├─→ 动态百分位阈值判定：
    │       · < P25（下界）→ 明确分割
    │       · > P75（上界）→ 明确合并
    │       · P25 ~ P75     → 灰色地带
    │
    ├─→ 灰色地带分批（每批20个）交由 LLM 判断
    │
    └─→ 根据决策构建最终 chunks
```

**优势**：
- 阈值由当前文档相似度分布动态计算，不依赖固定值
- 灰色地带引入 LLM 语义判断，提升分块准确度
- Word 和 PDF 共享同一套分块逻辑（`smart_chunker.py`）



---

## 快速启动

### 环境要求

| 组件 | 版本 |
|------|------|
| Python | ≥ 3.10 |
| Node.js | ≥ 18 |
| Milvus | ≥ 2.6（需支持 SPARSE_FLOAT_VECTOR） |
| BGE-M3 模型 | 本地路径 |
| BGE Reranker v2-M3 模型 | 本地路径 |
| DeepSeek API Key | sk-xxx |

### 1. 安装 Python 依赖

```bash
cd test
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

`.env` 配置项：

| 变量 | 说明 |
|------|------|
| `BGE_MODEL_PATH` | BGE-M3 模型本地路径 |
| `RERANKER_MODEL_PATH` | BGE Reranker 模型本地路径 |
| `MILVUS_HOST` | Milvus 服务地址 |
| `MILVUS_PORT` | Milvus 服务端口 |
| `COLLECTION_NAME` | 默认集合名称 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 |
| `HF_HOME` | HuggingFace 缓存目录 |
| `HF_ENDPOINT` | HuggingFace 镜像地址 |

### 3. 启动后端

```bash
cd test
python main.py
```

后端启动后访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### 4. 启动前端

```bash
cd qianduan
npm install
npm run dev
```

前端启动后访问 `http://localhost:5173`。Vite 代理 `/api` 到 `localhost:8000`（超时 30 分钟）。

### 5. 创建 Milvus 集合

通过前端「集合管理」页或 API 创建三个集合：

| 集合名称 | 描述 | 用途 |
|----------|------|------|
| `minshi` | 民商事诉讼案例库 | 婚姻家庭/合同/侵权/劳动等 |
| `xingshi` | 刑事辩护案例库 | 各类刑事案件 |
| `xingzheng` | 行政诉讼案例库 | 行政处罚/许可/强制案件 |

### 6. 上传法律文档

通过前端「文档管理」页上传 `.docx` 或 `.pdf` 格式法律文档，选择目标集合，系统自动完成：
1. 语义分块（BGE-M3 + 百分位 + LLM）
2. BGE-M3 稠密+稀疏向量编码
3. 写入 Milvus
4. 注册文件记录（source_id 全局唯一）

### 7. 开始咨询

通过前端「法律咨询」页面输入问题，系统自动：
1. 接待 Agent 收集案情三要素
2. 路由到对应专业律师 Agent
3. 律师 Agent 自主检索 + 精排参考案例
4. 生成专业法律分析意见
