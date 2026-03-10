# LeetCode AI Knowledge Base — Project Plan

## 项目定位

本地 AI 知识库工具，用于管理刷题笔记和八股文，支持自然语言查询。开源，支持自定义 LLM 配置。

---

## 两个 GitHub Repo

| Repo                  | 内容                             |
| --------------------- | -------------------------------- |
| `leetcode-kb`         | 主工具（Electron + FastAPI）     |
| `leetcode-kb-content` | 社区内容（Markdown 题解/八股文） |

---

## 最终技术栈

```
Electron (React + TypeScript)
      ↓
FastAPI (Python, sidecar 进程)
      ↓
LangChain
  ├── Document Loader (Markdown, PDF, txt)
  ├── RecursiveCharacterTextSplitter
  ├── BGE-m3 Embedding (本地免费，中英混合)
  └── Retriever
      ↓
Chroma (本地向量数据库)
      ↓
LLM (可配置，见下方)
      ↓
Langfuse (tracing) + RAGAs (evaluation)
```

---

## LLM 配置选项

| Provider           | 特点                       |
| ------------------ | -------------------------- |
| Ollama（默认）     | 完全本地，免费，需用户安装 |
| OpenAI GPT-4o      | 效果最好，需 API key       |
| Claude (Anthropic) | 效果好，需 API key         |
| DeepSeek           | 便宜，国内友好             |
| 智谱AI             | 国内用户备选               |

---

## 核心功能模块

### 1. Ingest 模块

```
用户上传文件 / 输入内容
      ↓
判断文件类型
  ├── .py/.js → 按函数切
  ├── 含表格 PDF → 表格解析
  └── 其他（md/txt/pdf）→ RecursiveCharacterTextSplitter
      ↓
BGE-m3 Embedding
      ↓
存入本地 Chroma
```

- 支持动态 ingest（用户添加时实时更新向量库）
- 自动去重（同一道题不重复存）
- 支持更新题解后重新 embedding
- 社区内容一键导入（从 `leetcode-kb-content` repo 拉取）

### 2. Query 模块

```
用户提问
      ↓
BGE-m3 Embedding
      ↓
Chroma 向量检索 top-k
      ↓
Rerank（可选）
      ↓
塞进 prompt → LLM
      ↓
Streaming 返回答案
```

### 3. 管理模块

- 添加 / 编辑 / 删除题目
- 按标签 / 难度 / 题型筛选
- 导出知识库（markdown 文件夹）
- 复习提醒（间隔重复，类似 Anki）

---

## 数据格式（Markdown 标准模板）

````markdown
# 1. Two Sum

难度：Easy
标签：Array, Hash Table

## 题目

...

## 思路

...

## 解法

```python
# code here
```
````

## 复杂度

Time: O(n) | Space: O(n)

## 错误记录

...

````

---

## 配置文件 config.yaml

```yaml
llm: ollama              # ollama / openai / claude / deepseek / zhipuai
llm_model: llama3        # 具体模型名
embedding: bge-m3        # bge-m3 / openai / cohere
vectorstore: chroma      # 默认本地

# API Keys（按需填写）
openai_api_key: ""
anthropic_api_key: ""
deepseek_api_key: ""
zhipuai_api_key: ""
ollama_base_url: "http://localhost:11434"
````

---

## 数据存储路径

```
Mac:     ~/Library/Application Support/leetcode-kb/
Windows: %APPDATA%/leetcode-kb/
  ├── chroma/        # 向量数据库
  ├── config.yaml    # 用户配置
  └── exports/       # 导出文件
```

---

## 社区内容 Repo 结构

```
leetcode-kb-content/
  ├── leetcode/
  │   ├── easy/
  │   │   └── 0001-two-sum.md
  │   ├── medium/
  │   └── hard/
  ├── backend/
  │   ├── redis.md
  │   └── system-design.md
  ├── frontend/
  └── README.md
```

PR 流程：fork → 添加内容 → PR → 审核 → merge
GitHub Actions 自动检查 Markdown 格式规范

---

## 打包方案（需 POC 验证）

| 方式               | 方案                                                              |
| ------------------ | ----------------------------------------------------------------- |
| git clone          | 用户自装 Python + `pip install` + `npm install`                   |
| 安装包 (.dmg/.exe) | 内嵌独立 Python 环境（python-build-standalone）+ Electron Builder |

**打包工具**：PyInstaller（Python）+ Electron Builder（整体）

**第一次启动**：自动下载 BGE-m3 模型（带进度条，避免用户以为卡死）

---

## Telegram / Discord / Slack / 飞书 集成

- Bot 作为第二入口，和 Desktop 共享同一个本地 Chroma
- FastAPI 本地跑，电脑开着即可接收消息
- 配置入口在 Settings，用户自己填 Bot Token

---

## 开发顺序

```
Phase 1：POC 验证（优先）
  └── Electron + FastAPI sidecar 打包验证
      在无 Python 环境的机器上跑通 hello world

Phase 2：核心 RAG 功能
  ├── FastAPI + LangChain + Chroma 跑通
  ├── 基础 ingest（markdown/txt）
  ├── 基础 query（向量检索 + LLM 回答）
  └── Electron UI 基础界面

Phase 3：完整功能
  ├── 动态 ingest（实时更新向量库）
  ├── 多文件类型支持（PDF、代码文件）
  ├── LLM 配置切换（config.yaml）
  ├── 管理功能（增删改查、标签筛选）
  └── RAGAs 评估 + Langfuse tracing

Phase 4：体验优化
  ├── 模型首次下载进度条
  ├── 社区内容一键导入
  ├── 数据导出功能
  └── 复习提醒（间隔重复）

Phase 5：发布
  ├── 打包 .dmg / .exe
  ├── 开源发布（两个 repo）
  ├── Telegram / Discord bot 集成
  └── README + 文档
```

---

## 首次启动引导流程

```
Step 1：欢迎页
  └── 简单介绍工具功能

Step 2：选择 LLM 方式
  ○ 使用 Ollama（本地免费，需下载约 4GB）
  ○ 我有 API Key（OpenAI / DeepSeek / Claude / 其他）
  [继续]

Step 3a（选了 Ollama）：
  └── 检测是否已安装 Ollama
      ├── 已安装 → 直接选模型（llama3 / qwen 等）
      └── 未安装 → 提示引导用户去 ollama.ai 下载安装
          安装完成后回来点"我已安装"继续

Step 3b（选了 API Key）：
  └── 下拉选择 Provider → 填入 API Key → 验证可用

Step 4：完成，进入主界面
```

**原则：未经用户同意不自动安装任何软件**

---

## 注意事项

- **Chroma 数据存系统用户目录**，不能存在应用目录，防止卸载丢数据
- **打包是最大风险**，Phase 1 必须先验证
- **BGE-m3 模型较大**，首次启动需要下载提示
- **Electron + FastAPI 通信**需要健康检查，确认 FastAPI ready 再渲染 UI
- **LangChain 抽象层**保证所有 LLM / Embedding / VectorStore 切换不影响业务逻辑
