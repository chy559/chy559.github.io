---
title: PaiFlow 学习笔记 04：SSE 回传与实时通信
slug: paiflow-04-sse-callback
category: tech
date: 2026-04-23
summary: 记录 WorkflowMsgCallback、ChatCallbacks、streamQueue 与 SseEmitter 如何协作完成工作流状态实时推送。
collection: paiflow
collectionTitle: Paiflow
seriesOrder: 4
---

# SSE实现消息回传和实时通信

WorkflowMsgCallback 负责把引擎内部发生的 onWorkflowStart、onNodeStart、onNodeProcess、onNodeEnd 这些事件统一转换成可传输的消息对象，并丢进队列。与此同时，引擎会启动一个异步线程去消费 streamQueue，这样生产者和消费者就彻底解耦了。

![Image #2](https://cdn.paicoding.com/paicoding/e5e5af17cbd5099687e8167d4df9c548.png)

## 策略模式的应用

StreamCallback接口定义行为规范 callback

SSeStreamCallback具体用SseEmitter来实现这个接口

当 WorkflowMsgCallback 的异步任务从队列里拿到一个事件对象（如 LLMGenerate ）后，它会调用 `clientCallback.callback("stream", eventObject)` 方法。这个根据具体实现的不同来用不同的策略

比如我想用websocket来实现 只用另外实现这个接口就可以了 并不用改变其他的东西，解耦

### WorkflowMsgCallback

WorkflowMsgCallback 是工作流事件的**异步消息总线，它通过后台线程持续监听队列**，将工作流和节点的生命周期事件（开始、执行中、结束）实时推送到前端，同时桥接业务层（ChatCallBacks）和传输层（SseStreamCallback）。

### ChatCallbacks

事件的生产者工厂：负责监听工作流和节点的生命周期事件，将**事件转换为标准的 LLMGenerate 对象**，放入 **streamQueue 队列**；管理节点执行时间统计和 Token 消耗统计等。

其中节点处理中是流式响应

### LLMGenerate

```java
LLMGenerate
├── code: int // 状态码
├── message: String // 状态消息
├── id: String // 会话ID
├── created: long // 时间戳
├── workflow_step: WorkflowStep // 工作流步骤
│ ├── seq: int // 序号
│ ├── progress: double // 进度 (0.0 ~ 1.0)
│ └── node: NodeInfo // 节点信息
│     ├── id: String // 节点ID (如 "llm:1", "end:1")
│     ├── alias_name: String // 节点别名
│     ├── finish_reason: String // 完成原因
│     ├── inputs: Map // 输入参数
│     ├── outputs: Map // 输出结果
│     ├── error_outputs: Map // 错误输出
│     ├── executed_time: double // 执行时间(秒)
│     ├── ext: Map // 扩展信息
│     └── usage: GenerateUsage // Token统计
├── choices: List<Choice> // OpenAI格式内容
│ └── Choice
│     ├── index: int // 索引
│     ├── finish_reason: String // 完成原因
│     └── delta: Delta // 增量内容
│         ├── role: String // 角色
│         ├── content: String // 主要内容
│         └── reasoning_content: String // 推理过程
├── usage: GenerateUsage // 总Token统计
│ ├── prompt_tokens: int
│ ├── completion_tokens: int
│ └── total_tokens: int
└── event_data: InterruptData // 中断事件
 ├── event_id: String
 ├── event_type: String
 ├── need_reply: boolean
 └── value: Map
```

## 分工

ChatCallBacks 事件处理器，接收事件并构建响应 生产者 

LLMGenerate 响应数据结构，承载具体内容 产品 

streamQueue 消息队列，解耦生产与消费 传送带

WorkflowMsgCallback 异步消费者 以及管理生命周期内对象的创建 负责调度

![](https://cdn.paicoding.com/paicoding/be9e43d7e2934baf3d9fd6249dae9b5a.png)

## 生命周期

<img src="https://cdn.paicoding.com/paicoding/b50fc04bc3e2e552b4e819ee092eb098.png" title="" alt="Image #19" width="873">

## 解耦的作用

将消息的“生产”和“消费”解耦：引擎侧只负责把消息丢进队列，SSE 推送线程只关心从队列中取数据并发送。

同时，streamQueue 还承担了缓冲的角色。在高并发场景或者网络抖动时，消息生成速度往往会快于消费速度，如果直接同步发送，很容易出现阻塞甚至丢消息的情况。通过队列作为中间缓冲，可以把短时间内堆积的消息暂存下来，再逐条推送。

另外，队列天然具备 FIFO 的特性。节点的执行状态、日志、流式 token 都是有时间顺序语义的，只有按照产生顺序推送，前端才能正确还原执行过程。

## 超时控制，异常处理

#### SimpleTimeLimiter来实现执行，超时则抛出异常

一句话作用：给任意方法强制设置执行超时，超时立刻中断任务、抛超时异常，防止接口 / 远程调用 / IO 卡死拖垮服务

当调用**callWithTimeLimit**时， SimpleTimeLimiter 会接收一个 Callable 对象，并将其提交到它在初始化时绑定的 executorService 线程池中执行。这个提交动作会立即返回一个 Future 对象。

这三种策略提供了 灵活的异常处理能力 ：

1. 中断流程 ：适用于关键失败，立即停止
2. 错误码 ：适用于优雅降级，返回兜底内容
3. 错误条件 ：适用于条件分支，走不同执行路径
