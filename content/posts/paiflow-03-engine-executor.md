---
title: PaiFlow 学习笔记 03：Engine 与节点执行器
slug: paiflow-03-engine-executor
category: tech
date: 2026-04-20
summary: 拆解工作流 Engine 的总体架构、策略模式与模板方法模式，以及 executeNode 和执行器模板方法的核心逻辑。
collection: paiflow
collectionTitle: Paiflow
seriesOrder: 3
---

# Engine详解

## 总体架构

![Image #3](https://cdn.paicoding.com/paicoding/df6f51434c35219bda64987c0e22eb33.png)

## 策略模式，模版方法模式(执行器)

**为了未来的节点扩展预留足够的扩展空间**。无论是新增 LLM 节点、插件节点，还是引入更复杂的控制节点（如条件分支、并行节点），都不应该影响现有的执行逻辑。因此，节点执行机制必须以**接口和抽象类为核心**，确保新节点只关注自身业务实现，而无需侵入执行引擎本身。

### 模板方法模式的作用

![](C:\Users\陈%20华%20宇\Pictures\Screenshots\屏幕截图%202026-04-19%20211329.png)

### 策略模式的作用

![](C:\Users\陈%20华%20宇\Pictures\Screenshots\屏幕截图%202026-04-19%20211455.png)

## Engine执行节点核心逻辑

MARK 的核心作用 ：处理条件分支场景，**标记"可能不执行"的节点**，在执行时再判断是否真正需要执行。

Engine只关心节点执行的调度，执行顺序逻辑，不关心节点本身的执行逻辑，而是将其 交给执行器去实现

![](https://cdn.paicoding.com/paicoding/88fe6ad866795595aee36369e0c57edc.png)

```java
private void executeNode(Node node, VariablePool pool, WorkflowMsgCallback callback) throws Exception {
 // 1. 已执行检查
 if (node.getStatus().executed()) {
 return;
 }
// 2. 确保前置节点执行完毕
for (Node preNode : node.getPreNodes()) {
    if (!preNode.getStatus().executed()) {
        executeNode(preNode, pool, callback);
    }
}

// 3. MARK 节点判断（条件分支）
if (node.getStatus() == NodeStatusEnum.MARK) {
    if (!canExecuteInBranch(node)) {
        node.setStatus(NodeStatusEnum.SKIP);
        return;
    }
}

// 4. 执行当前节点
NodeExecutor executor = nodeExecutors.get(node.getNodeType());
node.setStatus(NodeStatusEnum.RUNNING);

NodeRunResult result = executor.execute(new NodeState(node, pool, callback));
NodeExecStatusEnum status = result.getStatus();

// 5. 根据结果执行后续分支
switch (status) {
    case ERR_INTERUPT -> {
        node.setStatus(NodeStatusEnum.ERROR);
        throw new NodeCustomException(ErrorCode.INTERRUPTED_ERROR);
    }
    case ERR_FAIL_CONDITION -> {
        node.setStatus(NodeStatusEnum.ERROR);
        executeFailedCondition(node, pool, callback);  // 走失败分支
    }
    case ERR_CODE_MSG -> {
        node.setStatus(NodeStatusEnum.ERROR);
        executeNormalCondition(node, pool, callback);  // 走正常分支
    }
    default -> {
        node.setStatus(NodeStatusEnum.SUCCESS);
        executeNormalCondition(node, pool, callback);  // 走正常分支
    }
}
}
```

## 执行器模版方法

```java
execute(nodeState)
 ↓
[1] 记录执行次数
 executeTime = node.getExecutedCount().addAndGet(1)
 ↓
[2] 检查重试配置
 ├─ 无配置 → doExecute()
 ├─ 不重试 → doExecuteWithTimeout()
 └─ 支持重试 → while(true) 循环
 ↓
[3] doExecute() 执行
 ├─ callback.onNodeStart() ← 发送开始事件
 ├─ resolveInputs() ← 解析输入参数 输入来源可能是开始节点也有可能是别的节点 开始节点直接从variablePool里面拿 其他则需要解析inputItem(分为引用和不是引用的情况,
                        引用的情况下需要去variablePool里面根据node_id,name取)                                  
 ├─ executeNode() ← 调用子类实现（抽象方法）
 ├─ storeOutputs() ← 存储输出到变量池
 └─ callback.onNodeEnd() ← 发送结束事件
 ↓
[4] 重试判断
 ├─ 成功 → 返回结果
 └─ 失败 → handleRetryWait() → 继续循环`
```

resolveInputs 方法会遍历节点定义的所有 InputItem，并逐一进行解析：

- 如果输入值是字面量，则直接作为参数注入；

- 如果输入值是引用表达式，则从 VariablePool 中解析对应节点、对应字段的数据；

- 如果引用指向的是复杂对象或数组中的嵌套字段，则按照路径规则进行逐层解析。
