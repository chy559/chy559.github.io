# Memory架构

- 门面模式：MemoryManager 是总入口，统一管短期记忆、长期记忆、检索、压缩和 token 预算。MemoryManager用于集成到agent中
- ConversationMemory 是会话内短期记忆，存用户消息、助手回复、工具结果。ConversationMemory.java (line 14)
- LongTermMemory 是跨会话持久化记忆，落盘到 ~/.paicli/memory/long_term_memory.json，默认只存“稳定事实”。LongTermMemory.java (line 25)
- 真正发给模型的消息历史 conversationHistory 还有自己单独的一层压缩器 ConversationHistoryCompactor，这是这个项目里最关键也最容易忽略的一点。ConversationHistoryCompactor.java (line 32)

ConversationMemory 很朴素：内部是 LinkedHashMap，按进入顺序存；超过预算会先淘汰最旧条目，并把淘汰内容记到 compressedSummaries。FIFO

### 上下文压缩

短期记忆满了，旧消息得淘汰，但关键信息不能丢。怎么办？压缩成摘要，再注入回去。

压缩策略用的是 **Map-Reduce**，跟处理大文档的思路一样

`retainRecentRounds` 这个参数很关键——最近几轮消息不参与压缩，原样保留。

## 具体链路

用户输入
  -> 写入短期 memory
  -> 用用户输入检索长期 memory
  -> 拼 system prompt
  -> 创建 conversationHistory
  -> 调用 LLM

  ->并行追加短期记忆和history
  -> 如果有 tool call，追加工具结果再继续调用 LLM
  -> 如果没有 tool call，返回最终回答

## 什么情况下会变成长期记忆

1.用户手动/save

2.Agent调用save_memory工具

短期记忆压缩时不会自动写长期记忆。ContextCompressor.compress(...) 只会把 ConversationMemory 里的旧条目压成一条 SUMMARY，再放回短期记忆里。

## 项目中的压缩策略

<img src="file:///C:/Users/陈%20华%20宇/Pictures/Screenshots/屏幕截图%202026-05-27%20153813.png" title="" alt="" width="682">

conversationHistory 压缩是 PaiCLI 的“请求前最后一道保险”：它在 LLM 调用前按 90% 上下文窗口触发，把早期完整消息摘要化，同时完整保留最近 3 个 user turn，并且只在 user message 边界切割，避免破坏 tool call 协议。

短期记忆的压缩是paicli内部的 防止无限扩张

## 重点：压缩策略

这个项目有两道压缩：**短期记忆压缩负责管理 PaiCLI 内部的 shortTermMemory**，当记忆占用接近预算时，把较早的用户消息、助手回复和工具结果摘要化，同时保留最近几轮完整内容，保证记忆池长期可检索、可注入、不会被大日志撑爆；

上下文压缩负责管理真正发给 LLM 的 conversationHistory，在每次调用模型前按**上下文窗口约 90%触发**(maxWindowSize*0.9)，把早期对话压成摘要，并从最近几个 user turn 开始完整保留尾部消息，避免切断 tool call/tool result 协议。这样做的好处是：既能防止真实请求爆上下文窗口，又能让内部记忆保持轻量、高密度、可持续复用，长任务跑久了也能继续接上目标、进展和未完成事项。(**system 之后、splitIdx 之前的旧消息 -> 送给 LLM 摘要
splitIdx 到末尾的消息 -> 原样完整保留)关键约束：分割点必然落在 user message 边界，避免切断 tool_call / tool_result 的成对协议。**

## 长期记忆检索策略

检索后会作用于System Prompt中

MemoryEntry记分策略如下：1.完全包含直接为满分 

2.分词后看关键词命中多少   分1 = 命中个数/总个数，关键词的分词使用jieba 

3.计算时间的权重，24小时内从1.0衰落到0.5 然后权重和命中的分数相乘

**关键词匹配**——把查询分词后逐词匹配，命中越多分数越高；

**时间衰减**——24 小时内从 1.0 线性衰减到 0.5，三天前的旧事权重自然就低了 加权

## 短期记忆的作用(可以简单的理解为对话的历史)

- **记录当前会话的用户、助手、工具结果**  
  位置在 MemoryManager.java (line 67)、MemoryManager.java (line 82)、MemoryManager.java (line 100)。

- **用于状态展示**  
  /context 这类状态会通过 memoryManager.getSystemStatus() 展示短期记忆条数、token、预算、压缩数量，见 Agent.java (line 423)。

- **用于短期记忆压缩测试和管理**  
  短期记忆超过预算会压成 SUMMARY 类型条目，见 MemoryManager.java (line 160) 和 ContextCompressor.java (line 101)。

- **提供一个“可检索短期+长期”的 API，但主流程现在没用它**  
  这里确实同时搜短期和长期记忆。但 ReAct/Plan 注入 prompt 用的是 buildContextForQuery()，它只搜长期。

## 外部记忆

RAG ——> agent:

首先明确一点CLI的rag适用的对象是**代码库**而不是平常场景下的知识库文件等

## 混合检索

**第一件，语义检索打底**。 把查询向量化，跟库里所有向量算余弦相似度，先把语义最近的一批捞出来。

**第二件，关键词加权**。 用 jieba 把查询切词，挑出“Agent”“run”“ReAct”这类代码关键词，再用 LIKE 去库里扫一遍。

命中的结果按命中位置给不同分——类名/方法名命中 +0.3，文件路径命中 +0.1，内容命中 +0.1。命中的位置越关键，分数越重，跟 ES 那一套 BM25 加权思路差不多，只是更轻量级。

**第三件，类型加分。** method 块 +0.15，class 块 +0.1，file 块不加。理由很简单，用户问“怎么实现”的时候，给方法体比给整个文件有用得多。

## 集成到Agent中

在ToolRegister中注册search_code的工具即可

/index：建索引    /search:混合检索

日常用法基本就是：先 `/index` 一次建索引，平时有问题就 `/search` 自然语言搜一下，想看架构就 `/graph` 查关系。Agent 模式更省事，问题直接抛给它，背后自动调 search_code，连 `/search` 都不用手动敲。

## 总的架构：短期记忆 长期记忆 外部知识库的协调

PaiCLI 不是用一个单独的 MemoryManager 管所有上下文，而是由 Agent 主循环协调。

每轮开始时，Agent 把用户输入写入短期记忆，同时用 MemoryManager 从长期记忆中检索相关事实，并通过 PromptAssembler 注入 system prompt。当前会话的真实上下文由 conversationHistory 维护，用户消息、助手消息和工具结果都直接追加到这里。

**外部代码库知识不常驻 prompt，而是暴露为 search_code 工具**；模型需要代码上下文时调用该工具，ToolRegistry 执行 CodeRetriever.hybridSearch，从预建索引里做语义检索和关键词检索，结果再作为 tool message 回灌到 conversationHistory。这样长期记忆负责稳定事实，短期记忆负责运行期状态，RAG 负责按需代码检索，Agent 主循环负责把它们接到模型调用链上。

## RAG核心1:分片向量化落库  (index,chunker,vectorStore)

/index
 -> CodeIndex.index()// 建索引
 -> collectFiles()
 -> CodeChunker.chunkFile()// 文件的分片
 -> CodeChunk.toEmbeddingText()// 分片向量化
 -> EmbeddingClient.embed()
 -> VectorStore.insertChunks()// 存入sqlite文件

**分片策略**：非 Java 文件走 CodeChunker.java (line 50) 的 chunkLargeText()。单块上限是 2000

Java 文件走 CodeChunker.java (line 80) 的 chunkJavaFile()。这里用 JavaParser，语言级别是 Java 17解析失败会回退到普通文本分段

每个类会生成一个 class chunk，类内容取类起始处最多 5 行 包含字段和签名

**向量化调用**远程或本地的ollama轻量模型:细节是用OKhttp调用，json和java对象的转换用的是jackson包

**落库**：通过jdbc中到的 `PreparedStatement + batch + 手动事务` 批量插入 `CodeChunkEntry`，成功则统一 `commit`，失败则 `rollback`，保证批量插入的原子性。

## RAG核心2：检索(/search或者agent调用工具使用  retriver)

code_search
 -> query embedding
 -> 向量余弦相似度召回候选
 -> query 分词
 -> 在索引表中 LIKE 匹配 name/content
 -> 语义结果和关键词结果合并去重
 -> 双重命中 +0.1
 -> method +0.15 / class +0.10
 -> 按 similarity 降序
 -> 同文件最多 2 条
 -> 返回 topK
 -> 格式化成 tool result
 -> 回灌 conversationHistory

1.语义检索把query向量化之后计算余弦相似度取topK

2.关键词检索：jieba提取query关键词后 在sql中做一个like的查询 命中加0.3

3.合并结果 双重命中奖励0.1分

4.类型加权：method>class>default   

sort之后同一文件最多保留 maxPerFile 个结果，总数不超过 topK

5.格式化为tool result        摘要加结果
