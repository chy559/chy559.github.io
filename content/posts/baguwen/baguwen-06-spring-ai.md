# spring ai常用的类

## 1. ChatModel（最核心）

这是最顶层接口。

```
public interface ChatModel {    ChatResponse call(Prompt prompt);}
```

作用：

> 调用大模型聊天

# 2. Prompt

Prompt 是：

> 发给模型的完整请求

类似 HTTP Request。

包含：

- system prompt
- user prompt
- 参数
- temperature
- tools

示例：

```
Prompt prompt = new Prompt(    "你是谁？");
```

高级写法：

```
Prompt prompt = new Prompt(    List.of(        new SystemMessage("你是Java专家"),        new UserMessage("解释Spring AI")    ));
```

---

# 3. Message

聊天消息抽象。

父类：

```
Message
```

常见子类：

| 类                   | 作用     |
| ------------------- | ------ |
| UserMessage         | 用户消息   |
| SystemMessage       | 系统提示   |
| AssistantMessage    | AI 回复  |
| ToolResponseMessage | 工具调用结果 |

类似 OpenAI 的：

```
[  {"role":"system"},  {"role":"user"}]
```

# 4. ChatResponse

模型返回结果。

结构：

```
ChatResponse └── Generation      └── AssistantMessage
```

最常见：

```
String content =    response.getResult()            .getOutput()            .getContent();
```

- `OverAllState` 是 **Spring AI Agent 多步推理的全局状态类**。
- 用途：
  - 记录每一步动作和结果
  - 保存全局上下文
  - 提供调试和回溯能力
- 它让 Agent 能够做到 **复杂流程管理、多工具调用、跨步上下文共享**。

# 5.Agent
