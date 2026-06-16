# MCP 接入

**工具的开发者和 Agent 的开发者可以完全解耦**,双方只要遵循 MCP 协议，就能无缝对接。

底层基于JSON rpc

### 1.传输层mcpTransport

策略模式：1.send发消息 2.onReceive接收消息 注册监听者->用stdio或者Streamable Http来实现

1. stdio实现:本地建一个server的子进程，通过 stdin/stdout 一行一个 JSON-RPC 消息通信   **业务线程通过 stdin 向 MCP 子进程发送 JSON-RPC 请求，并在 `CompletableFuture` 上等待；stdout 后台线程持续监听子进程响应，收到消息后通过 id 找到 pending 中的 future 并完成它，从而唤醒等待的业务线程。** 超时是通过 **scheduler 定时任务 + CompletableFuture** 来判断的：定时任务到时间还没收到响应，就把对应 future 异常完成，从而唤醒阻塞的 request() 调用。

2. StreamableHttp: 基于OKHttp实现 发post请求，可能用sse传输的情况 服务端发sessionid,client以后可以带sessionid，这样服务端就能继续

### 2.协议层 JsonRpcClient

基于json rpc发送请求   主要负责包装请求，用ConcurrentMap<id,future>来监听id上的任务是否完成

### 3.client层

主要用于包装传输层和协议层，向server发请求

## Skill系统

1.建立skill索引：三级skill ,用户 项目 全局  建立索引一般是name +description的一部分 塞进system prompt中

2.llm根据skill的描述来看是否需要调用load skill的工具

主要是建索引让llm调用

## load skill干了什么

1. 接收一个 name，比如 java-code-reviewer
2. 去 SkillRegistry 里查这个 Skill 是否存在且已启用
3. 取出该 Skill 的 SKILL.md 正文 body
4. 如果正文超过 5KB，截断
5. 把正文放进 SkillContextBuffer
6. 返回提示：这个 Skill 会在下一轮上下文中以 ## 已加载 Skill：xxx 注入

load skill对 LLM 生效的方式：**不是作为 system prompt，也不是作为 tool result，而是作为下一轮 user message 的前置上下文**。

## 改进

不足:load skill要在下一轮对话才能加载skill进行操作

改进:新增skillinject类在同一个循环中就可以将buffer中的内容注入user message
