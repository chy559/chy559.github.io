# 框架与分层

- **CLI壳层**：cli,render,tui(负责用户怎么跟agent交互)

- **Agent执行路径层**：agent,plan(默认 **ReAct**：  
  Agent.java  
  普通用户输入走这里。它是经典循环：组 prompt -> 调模型 -> 如果有工具调用就执行 -> 把工具结果回灌 -> 再调模型，直到输出最终答案。
  
  **Plan-and-Execute：**  
  PlanExecuteAgent.java  
  /plan 走这里。它先让 Planner 生成任务 DAG，经过用户审阅，再按依赖关系执行。
  
  **Multi-Agent**：  
  AgentOrchestrator.java、SubAgent.java  
  /team 走这里。它把任务拆给不同角色，比如 planner / worker / reviewer，适合更复杂的协作任务。)

- **LLM模型层**：策略模式+模版方法模式：接口加通用模版 负责与大模型进行交互
  
  ```java
  ChatResponse chat(List<Message> messages, List<Tool> tools) throws IOException;
  ChatResponse chat(List<Message> messages, List<Tool> tools, StreamListener listener) throws IOException;
  ```

- **Tool层**：人工审批+工具注册

- **Prompt,Memory,Context层**：上下文，提示词构建，memory 分两类：短期上下文压缩和长期记忆。长期记忆只通过 /save 或用户明确要求保存，不自动乱记

- **Rag层**：Search_code工具最终会落到这一层

- **MCP层**：MCP 工具会动态注册成 mcp__server__tool 形式，然后也走 HITL、审计和工具执行链路。Chrome DevTools MCP、resources、prompts 都在这套机制上扩展

- **Web / Browser**
  
  核心目录：
  
  - web
  - browser
  
  web 是轻量联网能力：搜索、抓网页、HTML 提取、网络安全策略。
  
  browser 是浏览器会话管理和安全策略，配合 Chrome DevTools MCP 使用。公开网页优先 web_fetch，SPA/登录态/复杂交互再走浏览器。

- **Skill系统**

**PaiCLI 的核心骨架是 Main 搭好运行环境，Agent/PlanExecuteAgent/AgentOrchestrator 负责思考循环，LlmClient 负责模型，ToolRegistry + HITL + policy 负责行动，Renderer 负责呈现，周边的 RAG/MCP/Memory/Skill/Browser/Snapshot 把它从简单 Agent CLI 扩成了一个比较完整的 agentic coding runtime。**

## 重要的中间件

### 消息格式

GLM-5.1 的 API 兼容 OpenAI 格式，消息有三种角色：

- `system`：系统提示，定义 Agent 的身份和能力
- `user`：用户输入
- `assistant`：助手回复，可以包含文本或工具调用
- `tool`：工具执行结果

### 工具定义格式

要让 LLM 知道有哪些工具可用，需要按照特定格式定义工具：

```java
public record Tool(String name, String description, JsonNode parameters) {}
```

## LLM Client层

实现了chat接口，利用OkHttp与服务器进行交互，使用OKio的BufferedSource接收内容并实现了sse的流式接收，通过StreamListener接口渲染到上层

## 值得写进简历的点：

___

## PaiCLI 怎么处理死循环的？

PaiCLI 源码里有四层防护：

第一层是 **Token 预算**。`AgentBudget` 根据当前模型的 `maxContextWindow()` 动态计算预算（默认取窗口的 80%），对话历史接近预算就触发摘要压缩或强制终止。

第二层是 **工具执行超时**。execute_command 有 60 秒超时，超时直接返回超时结果给 LLM，不会卡在那里。

第三层是**用户取消**。运行中按 ESC 或输入 /cancel 可以请求取消当前 Agent run。ReAct、Plan、Team 三条路径在边界处都会检查取消信号。

第四层是 **摘要压缩兜底**。ContextCompressor 在对话历史膨胀到临界点时介入，把早期对话压缩成

**每次 user / assistant / tool result 写入短期记忆后都会检查；当短期记忆 token 占用达到约 90% 预算，且旧条目足够多时，就会触发摘要压缩。**

## 短期记忆什么时候压缩

**短期记忆压缩的 token 预算主要靠本地粗估：窗口大小来自模型，短期记忆预算是窗口的 45%，压缩阈值是预算的 90%；每条记忆中文按 1.5 字/token、英文按 4 字符/token 粗略估算。**

## plan-execute模式

失败处理的策略也在 PlanExecuteAgent 里：

失败的任务标记为 FAILED
所有直接或间接依赖它的下游任务自动标记为 SKIPPED——不执行，因为前置条件不满足
和它没有依赖关系的其他任务不受影响，继续执行
这个设计是参考了**CI/CD 流水线**的做法——GitHub Actions 里一个 job 失败，依赖它的后续 job 会跳过，但其他并行 job 不受影响。

面试官可能追问“有没有重试机制”。

PaiCLI 的 Plan-and-Execute 当前没有任务级重试，但 Multi-Agent 模式下 Reviewer 审查不通过时有重做机制（最多 2 次）。这是有意的设计选择——**Plan 模式强调可预测性**，自动重试会让执行过程变得不可控。

## Multi模式

`AgentOrchestrator.java` 是总调度，协调三个角色的交互。每个角色都是一个 `SubAgent` 实例，有独立的 system prompt 和角色定义，但共享同一套 `ToolRegistry` 和 `MemoryManager`。

## 并行执行的性能提升有多大

I/O 密集型操作提升最明显。3 个文件读取各 100ms，串行 300ms，并行约 100ms。对于 `execute_command` 这种可能要几秒的操作，多个并行更有意义。

## 能否自己选择agent模式

可以。

但我不会把这个判断完全交给大模型自由发挥，而是做一个**模式路由层**。

用户输入进来后，先判断任务特征：是不是简单问答、是否需要工具调用、是否涉及多文件修改、是否有明显步骤依赖、是否适合并行拆分、风险是不是比较高。简单任务走 ReAct；有明确步骤和依赖的走 Plan-and-Execute；能拆成多个相对独立子任务的，再升级到 Multi-Agent。
