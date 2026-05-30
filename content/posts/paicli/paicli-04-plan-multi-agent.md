# Plan和DAG

为什么需要任务建模：

React方式的问题：
第一，**上下文膨胀**。复杂任务需要很多轮对话，随着历史消息越来越长，Token 的消耗剧增。

第二，**状态不清晰**。对话历史里混杂了思考过程、工具调用、执行结果，很难一眼看出任务执行到哪一步。

### 任务的生命周期

一个任务从创建到完成，完整的生命周期如下所示：

```objectivec
PENDING → RUNNING → COMPLETED/FAILED/SKIPPED
```

用DAG来表示依赖关系

依旧拓扑排序

其中plan和task类都有对应的状态管理

## Planner规划器的实现(用于planAgent中)

关键方法

```java
public ExecutionPlan createPlan(String goal) throws IOException 
        // 构建规划请求
        // 调用LLM生成计划
        // 解析JSON计划
    }
```

因为要解析Json计划 所以一定要规范输出的格式

解析时把依赖关系搞好之后 调用plan的拓扑排序方法 保证方法是合规的

# multi agent:主从模式

三角色分工：规划者+干活者+检查者

主从模式：编排器+子agent

## 为什么用主从模式

主从模式把协调逻辑集中到编排器，子 Agent 之间不直接对话，所有消息都经过编排器路由。结构清晰，调试方便。

编排器中的子agent有：

    private final SubAgent planner;

    private final List<SubAgent> workers;

    private final SubAgent reviewer;

## 编排器具体逻辑：

1. planner子agent制作计划

2. 解析计划：包括计划的步骤 依赖关系等

3. 按顺序执行节点，worker执行后交给reviewer检查

4. 全部结束后作总结返回

执行节点的并行细节：

- 用固定线程池并行
- 用 BlockingQueue<SubAgent> 做 worker 池，确保同一个 worker 不会同时被两个步骤占用
- 每个并行步骤单独拿一个 ByteArrayOutputStream + PrintStream
- 所有步骤跑完以后，再按 step 顺序 flush 到终端

这个项目中的并行实现方法：线程池+future.get阻塞，可以用invokeall接受所有任务 也可以遍历submmit

## 上下文传递机制

子agent每次执行都会清除对话历史只保留系统提示词

上下文传递的工作由编排器来实现

上下文构建：遍历所有节点 是依赖节点的加入context的构建

非java文件：按照文本的大小分

java文件：走AST分块

类级 chunk 只取类声明附近几行，方法级 chunk 取整个方法体

# 多并发的应用

并行的切入点：

**真正使用线程池/异步执行的地方**

1. ToolRegistry.executeTools()  
   这是最核心的一处。单轮里如果 LLM 一次返回多个 tool_calls，这里会开固定线程池并行执行，默认最多 4 个并发，最后按原顺序收集结果。  
   相关：invokeAll(...)、Future、shutdownNow() 在 ToolRegistry.java (line 884)

2. PlanExecuteAgent 的 DAG 批次并行执行  
   当一个执行计划里有多个“当前可执行且互不依赖”的任务时，会用固定线程池并行跑这一批任务，线程名 paicli-plan-executor。

3. AgentOrchestrator 的 Multi-Agent 批次并行  
   /team 模式里，同一依赖批次的多个 step 会并行执行。它用固定线程池 + LinkedBlockingQueue 做 worker 池，确保同一 worker 不会被重复占用。  
   位置：AgentOrchestrator.java (line 411)  
   worker 池在 AgentOrchestrator.java (line 416)
