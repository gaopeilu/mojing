# 墨镜 (MoJing) API 接口文档

**版本**: v1.0  
**基础路径**: `/api/v1`  
**简介**: 墨镜是一个基于 LangGraph 和 RAG 技术的智能写作助手，旨在通过风格迁移技术实现“去 AI 化”的个性化内容生成。

---

## 1. 认证模块 (Auth)
*   **前缀**: `/auth`

### 1.1 用户注册
*   **接口**: `POST /register`
*   **描述**: 创建新用户账号。
*   **请求体 (JSON)**:
    ```json
    {
      "username": "string",
      "password": "string",
      "email": "string (可选)"
    }
    ```

### 1.2 用户登录
*   **接口**: `POST /login`
*   **描述**: 获取访问令牌 (JWT)。
*   **请求体 (Form Data)**:
    *   `username`: 用户名
    *   `password`: 密码
*   **响应示例**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer"
    }
    ```

---

## 2. 知识库模块 (Knowledge Base)
*   **前缀**: `/upload`

### 2.1 上传私有文档
*   **接口**: `POST /upload`
*   **描述**: 上传私有文档并存入 ChromaDB 向量库，作为写作的参考资料。
*   **请求体 (Form Data)**:
    *   `file`: 文档文件 (.txt, .pdf, .docx)

### 2.2 获取知识库列表
*   **接口**: `GET /list`
*   **描述**: 获取当前用户已上传的所有文档列表。
*   **响应示例**:
    ```json
    [
      {
        "id": 1,
        "filename": "report.pdf",
        "file_path": "uploads/...",
        "uploaded_at": "2024-05-17 10:00:00"
      }
    ]
    ```

### 2.3 删除知识库文档
*   **接口**: `DELETE /delete/{kb_id}`
*   **描述**: 删除指定的文档及其在向量库中的索引。

---

## 3. 风格管理模块 (Style)
*   **前缀**: `/style`

### 3.1 上传风格样本
*   **接口**: `POST /upload`
*   **描述**: 上传范文，后台将异步分析其写作风格（笔迹克隆）。
*   **请求体 (Form Data)**:
    *   `file`: 文本文件 (.txt, .pdf, .docx)

### 3.2 获取风格列表
*   **接口**: `GET /list`
*   **描述**: 获取当前用户的风格样本及分析状态。
*   **响应示例**:
    ```json
    [
      {
        "id": 1,
        "title": "sample.txt",
        "word_count": 1200,
        "style_description": "用词严谨、多用排比句..."
      }
    ]
    ```

### 3.3 手动触发风格分析
*   **接口**: `POST /analyze/{style_id}`
*   **描述**: 如果后台异步分析失败，可手动调用此接口重新分析。

### 3.4 删除风格样本
*   **接口**: `DELETE /delete/{style_id}`
*   **描述**: 删除指定的风格样本。

---

## 4. 智能写作模块 (Writing)
*   **前缀**: `/write`
*   **注意**: 以下接口均需在 Header 中携带 `Authorization: Bearer <token>`。

### 4.1 生成初稿大纲
*   **接口**: `POST /outline`
*   **描述**: 根据主题和 RAG 检索结果生成文章大纲。
*   **请求体 (JSON)**:
    ```json
    {
      "query": "写作主题或指令",
      "user_id": 1
    }
    ```

### 4.2 重修大纲
*   **接口**: `POST /refine`
*   **描述**: 根据用户反馈对已有大纲进行优化。
*   **请求体 (JSON)**:
    ```json
    {
      "query": "写作主题",
      "outline": "上一版大纲内容",
      "feedback": "修改意见",
      "user_id": 1
    }
    ```

### 4.3 生成正文 (含风格注入)
*   **接口**: `POST /generate`
*   **描述**: 确认大纲后，注入风格指纹并生成最终正文。
*   **请求体 (JSON)**:
    ```json
    {
      "query": "写作主题",
      "outline": "最终确认的大纲",
      "style_id": 5, 
      "user_id": 1
    }
    ```

---

## 5. 历史记录模块 (History)
*   **前缀**: `/history`

### 5.1 获取写作历史列表
*   **接口**: `GET /list`
*   **描述**: 分页获取用户的写作成品记录。
*   **查询参数**:
    *   `page`: 页码 (默认 1)
    *   `limit`: 每页数量 (默认 10)

### 5.2 获取历史详情
*   **接口**: `GET /detail/{history_id}`
*   **描述**: 查看某篇历史文章的完整内容和元数据。

### 5.3 删除历史记录
*   **接口**: `DELETE /delete/{history_id}`
*   **描述**: 删除指定的写作历史。

---

## 💡 核心技术亮点说明

1.  **异步风格分析**: 采用 `FastAPI BackgroundTasks` 处理耗时的 LLM 风格提取，确保上传接口秒级响应。
2.  **动态风格注入**: 在写作节点实时检索 `style_description`，实现 Few-shot Learning（少样本学习）级别的风格模仿。
3.  **RAG 增强**: 结合 ChromaDB 实现用户级数据隔离的私有知识检索，提升内容的专业度。
4.  **自我反思机制**: 内置 `reflect_node`，自动对生成内容进行语言精炼和逻辑校验。
5.  **多阶段工作流**: 采用 LangGraph 构建“大纲-重修-正文-反思”的链式 Agent 流程，解决长文本生成难题。
