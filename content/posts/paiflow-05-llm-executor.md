---
title: PaiFlow 学习笔记 05：LLM 节点执行器
slug: paiflow-05-llm-executor
category: tech
date: 2026-04-24
summary: 梳理 LLM 节点如何构建请求、维护对话历史缓存、调用模型服务并处理流式响应。
collection: paiflow
collectionTitle: Paiflow
seriesOrder: 5
---

# LLM执行器

#### LLM 节点最终要做的事其实很简单，把 LlmReqBo 里的信息转换成一次真实的模型调用，然后把流式过程里的每一段内容及时回传，最后再拼出一个完整的结果返回给工作流引擎。

主要是要实现父类未实现的executeNode方法

![Image #1](https://cdn.paicoding.com/paicoding/45f1b04f8cc2e4cf0059e53f0148ac26.png)

## 完整逻辑

获取提示词和对话的历史(历史由本地的缓存构建，chatid在TTL中保存) **构建llm请求** 包括url,apikey,prompt，温度等信息;

记录对话的历史并且调用llm 并且进行流式响应 最后完善对话历史

格式化输出Map 一般是 "outputs":  ....   "reason": ....  最后通过格式化的输出来构建NodeRunResult

## 对话历史缓存

LoadingCache<String, ConcurrentLinkedQueue<ChatItem>>
     │              │
     │              └── 值：对话历史队列
     │
     └── 键："{chatId}:{nodeId}"

 LoadingCache 的核心作用是：

1. 缓存对话历史 ：按 chatId:nodeId 存储多轮对话
2. 自动过期清理 ：30 分钟后自动删除，防止内存泄漏
3. 容量限制 ：最多 10000 个会话，使用 LRU 淘汰
4. 懒加载 ：首次访问时自动创建队列
5. 线程安全 ：支持高并发场景

历史无限增长把内存吃爆，这里做了两道保险。

**第一道是队列固定长度，**MAX_HISTORY_LENGTH 设成 10。createChatHistoryQueue 返回的队列**重写了 add 方法**，往里塞新数据之前会先检查长度，超过就把最老的那条踢掉。

**第二道是缓存本身的上限和过期策略**maximumSize 设成 10000，意思是最多缓存一万个会话的队列，再多就让 Guava 做淘汰。expireAfterWrite 设成 30 分钟，意味着这段时间里没再写入这个会话，它就会自动过期回收。

## 关键组件：ModelServiceClient

![Image #10](https://cdn.paicoding.com/paicoding/e8284972c87aec5a4ac5edeae2d90043.png)

## 调用llm api的过程

```java
@Data
public class LlmReqBo {
 private String nodeId; // 节点ID
 private String modelId; // 模型ID
 private String userMsg; // 用户消息
 private String systemMsg; // 系统提示词
 private String model; // 模型名称（如 deepseek-chat）
 private String url; // API 地址
 private String apiKey; // API 密钥
 private String apiSecret; // API 密钥
 private Integer topK; // Top-K 采样
 private Integer maxTokens; // 最大 Token 数
 private Boolean isThink; // 是否启用思考模式
 private Map<String, Object> extraParams; // 额外参数
 private List<LlmChatHistory.ChatItem> history; // 对话历史
}

public record LlmResVo(
 Usage usage, // Token 使用统计
 String content, // LLM 响应内容
 String thinkContent // 思考过程（DeepSeek 等）
) {}
```

1. 从发来的llmReq中提取出参数(包括温度等)构建ChatOptions和用户prompt以及系统prompt,用户prompt和历史对话构造出**Prompt对象**

2. 用url和apikey初始化API客户端，构建ChatOptions并和api客户端一起初始化ChatModel

3. 流式调用 chatModel.stream(prompt)用fulx<Message>接收，flux流式逻辑处理，拼接加返回内容给前端
