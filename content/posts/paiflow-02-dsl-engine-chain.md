---
title: PaiFlow 学习笔记 02：DSL 结构与执行链路构建
slug: paiflow-02-dsl-engine-chain
category: tech
date: 2026-04-23
summary: 梳理 DSL 图结构、节点状态机、前后端调试流程，以及 WorkflowEngine 从校验到递归执行的主流程。
collection: paiflow
collectionTitle: Paiflow
seriesOrder: 2
---

# DSL图的结构，WorkEngine对执行链路的构建,总体流程

## DSL结构

上层的dsl只关系结构长啥样 不关心是怎么执行的 具体的执行交给engine实现

data是灵魂

## 节点状态机：

需要特别注意的两个标签

**MARK 就像“待定标签”**，表示这个节点当前不确定是否会被执行——也许这个分支现在没走它，但将来其他路径可能还会走到这里。

**SKIP 是最终确认的“不会执行”状态**，它的判断逻辑是这样的：

- 首先这个节点必须已经处于 MARK 状态。

- 然后检查它所有的前置节点是否都执行完了。

- 如果所有前置节点都没走向这个节点，就可以断定这个节点没有任何可能会被执行，于是标记为 SKIP。

## node type:有llm ,start ,end ,plugin等

Mapper 配合 Wrapper 可以**动态拼接查询条件**，无需手写 XML 与原生 SQL，

支持单条、列表、分页、统计、条件修改、条件删除，

Lambda 写法避免字段硬编码错误，维护更安全。

## 前后端总流程

用户点击"调试"按钮
    ↓
[1] 前端调用 POST /workflow/build(主要功能是验证dsl合规)
    ↓ Hub 微服务
    ├─ saveLocal() → Hub 本地数据库落库
    ├─ saveRemote() → 同步到工作流引擎
    └─ 调用引擎 /protocol/build/{flow_id} → 引擎 flow 表落库
    ↓
[2] build 成功后，前端调用 POST /workflow/chat
    ↓ Hub 微服务转发
    ↓
[3] 引擎接收请求 /workflow/v1/debug/chat/completions
    ├─ workflowService.getWorkflowDSL(flowId) → 从数据库读取刚保存的 DSL，创建新的dsl实例
    └─ workflowEngine.execute() → 执行工作流，SSE 流式返回结果
    ↓
[4] 前端通过 SSE 接收流式消息，实时更新 UI

update的调用时机：前端随意修改画面就会调用request->修改flow的数据库

## engine执行流程：execute

![Image #4](https://cdn.paicoding.com/paicoding/65b9f27f1f309b84cea32d875e51ceec.png)

[1] execute() 入口
    ↓
[2] verifyWorkflow() → 校验 DSL
    ├─ 节点/边非空
    ├─ 执行器存在
    └─ 环路检测
    ↓
[3] variablePool.clear() → 清空变量(ConcurrentMap实现) cMap<nodeid,concurrentMap<s，obj>> obj可能有三种情况 map ,list<Map> obj
    ↓
[4] 创建 WorkflowMsgCallback → SSE 管理器
    ↓
[5] EngineContextHolder.initContext() → 初始化上下文
    ↓
[6] workflowCallback.onWorkflowStart() → 发送开始事件
    ↓
[7] buildNodeExecuteChain() → 构建执行链路(完善node中的结构 比如preNodes,failNodes)
    ↓
[8] initializeStartNodeInputs() → 注入用户输入(pool的注入用户输入的map)
    ↓
[9] executeNode() → 递归执行所有节点
    ├─ node-start::001
    ├─ spark-llm::002
    └─ node-end::003
    ↓
[10] workflowCallback.onWorkflowEnd() → 发送完成事件
    ↓
[11] finally 清理资源
    ↓
[12] 前端收到完整结果

## 构建执行链路

1.构建节点映射表，map<nodeId,node>

2.根据edge和map获取节点,建立起preNodes，根据edge的handler分别放入nextNodes或者failNodes
