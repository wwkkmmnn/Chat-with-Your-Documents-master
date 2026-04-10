# Multi Tool AI Assistant

基于原始 `Chat-with-Your-Documents` 仓库重构的多工具智能助手原型。当前版本按照《基于 Chat-with-Your-Documents 的二次开发方案》完成了后端分层、Skill 注册表、SSE 流式聊天、会话持久化、文档检索与网页搜索等核心能力。

![App Screenshot](images/app.png)

## 本次重构完成的能力

- 文档上传与索引：支持 `PDF / TXT / DOCX`，MVP 重点仍然是 PDF。
- 文档问答：按文件维度建立 FAISS 索引，避免把所有文件混进同一个全局向量库。
- 网页搜索：内置轻量级 `web_search` Skill，用于“搜索 / 查一下 / 最新”等问题。
- 混合路由：支持 `direct_answer / doc_search / web_search / hybrid` 四类模式。
- 流式返回：后端通过 `SSE` 返回 `route / tool_start / tool_result / token / done` 事件。
- 会话持久化：本地 JSON 保存会话和消息，支持新建、切换、回看历史。
- Skill 抽象：统一的 `BaseSkill + registry` 结构，便于继续扩展 `summarize`、更多工具或 MCP 验证。
- MCP 基础验证：如果本地安装了 `fastapi-mcp`，应用会自动尝试挂载 `/mcp`。

## 新目录结构

```text
backend/
├── app/
├── routes/
├── services/
├── skills/
├── utils/
└── data/

front-chatdoc/
└── src/
    ├── api/
    ├── components/
    └── pages/
```

## 后端接口

- `GET /api/health`：健康检查
- `POST /api/upload`：上传文档并返回 `fileId`
- `GET /api/files`：获取已上传文档列表
- `GET /api/sessions`：获取会话列表
- `POST /api/sessions`：创建会话
- `GET /api/sessions/{id}/messages`：获取会话历史消息
- `POST /api/chat/stream`：SSE 流式聊天接口

### `/api/chat/stream` 请求体

```json
{
  "sessionId": "session_xxx",
  "message": "先搜索 MCP，再结合文档写一段简历描述",
  "fileIds": ["file_xxx"]
}
```

### SSE 事件

- `route`：后端判定本轮路由模式
- `tool_start`：工具开始执行
- `tool_result`：工具返回摘要与结果概览
- `token`：模型逐步输出内容
- `done`：本轮结束

## 启动方式

### 1. 安装 Python 依赖

```powershell
pip install -r requirements.txt
```

如果你还没有安装前置依赖，也可以使用下面这条手动安装命令：

```powershell
pip install fastapi "uvicorn[standard]" python-dotenv openai langchain langchain-community langchain-huggingface langchain-text-splitters sentence-transformers pypdf python-multipart faiss-cpu python-docx fastapi-mcp
```

### 2. 配置环境变量

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

可选配置：

```env
CHATDOC_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CHATDOC_CHUNK_SIZE=1000
CHATDOC_CHUNK_OVERLAP=120
CHATDOC_MAX_SEARCH_RESULTS=4
```

### 3. 启动后端

```powershell
uvicorn backend_chatdoc:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端

```powershell
cd front-chatdoc
npm install
npm run dev
```

默认前端地址：`http://localhost:5173`

## 开发说明

### 路由策略

- `direct_answer`：普通解释或闲聊问题，直接走 LLM。
- `doc_search`：优先从已选文档中检索，再回答。
- `web_search`：问题包含“搜索 / 查一下 / 最新”等明显联网意图。
- `hybrid`：同时需要网页搜索与文档检索，再经 `summarize` 归并上下文。

### 本地数据位置

- 上传文件：`backend/data/uploads/`
- 解析文本：`backend/data/parsed/`
- 向量索引：`backend/data/indexes/`
- 文件元数据：`backend/data/metadata/files.json`
- 会话数据：`backend/data/sessions/sessions.json`

## 已完成验证

- 前端 `npm run build` 已通过。
- 后端源码已完成 Python 级语法编译检查。

## 当前注意事项

- 本地如果还没安装 `FastAPI` 等依赖，后端运行前需要先执行 `pip install -r requirements.txt`。
- `web_search` 依赖运行环境能访问外部网络；若网络受限，会返回“未获取到网页搜索结果”的降级提示。
- DeepSeek API 未配置时，应用仍会返回工具摘要，但不会得到完整的模型生成结果。

## 后续可继续增强

- 为 `doc_search` 增加更细的引用片段展示
- 增加 `requirements-lock` 或 `environment.yml`
- 增强 `hybrid` 提示词与来源引用格式
- 继续把 Skill 暴露为更完整的 MCP 工具能力
