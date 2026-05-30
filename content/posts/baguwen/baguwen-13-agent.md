## Agent的组成部分

<img src="file:///C:/Users/陈%20华%20宇/Pictures/Screenshots/屏幕截图%202026-04-30%20111341.png" title="" alt="" width="730">

## ReAct & Plan and Execute

任务步骤少、目标模糊、需要随机应变 → 用 ReAct​

任务步骤多、目标明确、需要全局把控 → 用 Plan and Execute​

系统复杂、两者都需要 → Plan and Execute 做外层框架，每个子任务内部跑 ReAct

## Agent  Vs  Workflow

Workflow（工作流） 是你提前写好所有步骤和分支逻辑的流程：先做 A，再做 B，如果 B 的结果是 X 就走流程 C，否则走流程 D。大模型只是其中某个步骤里被调用一次，整体流程是**硬编码**的。

**一个是实时的，一个是写死的**

## 一个简单的agent例子

```python
def run_agent(user_message):​
    messages = [​
        {"role": "system", "content": SYSTEM_PROMPT},​
        {"role": "user",   "content": user_message},​
    ]​
​
    while True:​
        # 1. 调用大模型，让它思考下一步​
        response = llm.call(messages)​
​
        # 2. 如果大模型说"我完成了"，退出循环​
        if response.is_final_answer:​
            return response.content​
​
        # 3. 否则，执行大模型指定的工具​
        tool_result = execute_tool(response.tool_name, response.tool_args)​
​
        # 4. 把工具结果追加到 messages，供下一轮参考​
        messages.append({"role": "tool", "content": tool_result})
```

## Skill

预定义的指令集，它告诉 AI 在遇到特定类型的任务时应该怎么做、遵循什么规范、输出什么格式。

具体来讲，一个 Skill 通常就是一个 SKILL.md 文件，里面包含了针对某类任务的最佳实践。

三层加载机制（只读元数据 -> 按需加载指令 -> 用到时才取资源）让 Skill 既能提供丰富的能力，又不会浪费宝贵的 context window 空间。

### 一个好的 skill 通常要有这些东西：

1. SKILL.md，必需  
   这是 skill 的核心文件。

2. YAML frontmatter，必需  
   至少要有：

`--- name: your-skill-name description: "什么时候使用这个 skill，以及它能做什么。" ---`

description 很关键，因为 Codex 是靠它判断什么时候触发 skill 的。触发条件应该写在这里，而不是只写在正文里。

3. Markdown 正文，必需  
   写清楚 Codex 使用这个 skill 时应该怎么做。最好是流程、规则、注意事项、工具选择，而不是写一堆泛泛背景知识。

4. scripts/，可选  
   放可执行脚本。适合那些重复、易错、需要稳定执行的任务，比如 PDF 旋转、图片处理、批量转换。

5. references/，可选  
   放详细文档、API 说明、公司规则、schema、长示例。SKILL.md 里只写什么时候读这些文件，避免一开始就塞太多上下文。

6. assets/，可选  
   放模板、图片、字体、图标、样例项目等输出时会用到的资源。

7. agents/openai.yaml，推荐  
   这是 UI 元数据，比如显示名、简短描述、默认提示。不是核心逻辑，但能让 skill 在界面里更好用。



### Prompt VS Skill

从关系上看：包含与被包含。 Prompt 是 Skill 的“灵魂核心”，但不是全部。一个完整的 Skill = Prompt（指令与流程） + 挂载的工具列表（MCP） + 触发条件 + 上下文状态 。

## Tool

一个能被llm调用的工具，需要写好说明书：

说明书四要素：

1. 函数本体，也就是干活的代码

2. name,给llm的识别标签

3. description，一个好的 description 应该包含三件事：​
   
   能做什么 ：这个工具的核心功能是什么​
   
   什么场景用 ：遇到哪类问题、哪种情况该选它​
   
   返回什么 ：调用完会得到哪些信息

4. parameters（参数定义），告诉大模型怎么「填参数」​

**工具写好了，下一个问题：大模型怎么知道我有哪些工具？​**

答案是： 你得主动告诉它。​

Agent 在每次对话开始前，会把所有可用工具的 name + description + parameters 打包成一个列表，通过 API 的 tools 参数传给大模型。这个列表就叫 工具清单 。

### RAG

在 Agent 里的位置 ：RAG 就是一个特殊的工具，「检索知识库」被封装成一次 Function Call，是 Agent 能力体系的重要组成部分。

## Fuction Call(llm与agent之间的协议)

**Function Calling 的本质，是一套大模型和 Agent 之间的标准化工具调用协议**

Tool 是「能力实体」，Function Call 是「调用机制」 ，大模型通过 Function Call 这个协议，去调用 Tool 这个具体的功能。

三个核心：工具定义，fuction call（一般是一个json）,工具返回结果

<img src="file:///C:/Users/陈%20华%20宇/Pictures/Screenshots/屏幕截图%202026-04-30%20124226.png" title="" alt="" width="467">

## MCP(AI届的USB)

**定义了AI 应用和工具服务之间如何标准化通信**

工具开发者只需要实现一套 MCP Server，把工具能力按 MCP 协议暴露出来，之后所有支持 MCP 的 AI 应用，都能直接接入，不需要任何额外适配。

#### MCP与Fuction call的区别

**第一步：确认 Function Calling 工作在哪个层面​**

Function Calling 解决的问题是：大模型做出「要调这个工具」的决策之后，怎么把这个决策用标准化 JSON 格式传给 Agent。这是 **大模型和 Agent 之间 的通信协议**，负责「大模型怎么开口下指令」这一段。​

**第二步：确认 MCP 工作在哪个层面​**

MCP 解决的问题是：工具怎么被统一注册、统一发现、统一调用。这是**Agent 和工具服务之间**的连接协议，负责「Agent 怎么找到并执行工具」这一段。

## Harness

Agent = harness+llm

<img src="file:///C:/Users/陈%20华%20宇/Pictures/Screenshots/屏幕截图%202026-04-30%20133030.png" title="" alt="" width="533">

输入：context & memory

动作：tool & 执行编排

评估：evaluate & 约束与恢复

## 如何用harness实现一个项目的无代码重构

harness 不是单纯写测试，而是建立一套让项目可以安全重构的工程环境。它的目标是让代码在改动前后都能被自动验证，保证重构不是凭感觉改，而是有反馈、有约束、有回归保障。
