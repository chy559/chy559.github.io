# 人工审批层(HITL)和Tool Call

让hitltoolregister继承toolregister,创建Agent时传入hitl,利用java的多态，这就是 HITL 能截获所有 tool call 的原因。Agent 代码看起来只是调用 ToolRegistry，但运行时多态会进入 HitlToolRegistry.executeToolOutput()。@Override做了覆写

## tool的链路

1. agent收集LLM发过来的所有toolcalls并封装成一个List<ToolInvocation> 

2. 发给toolregister并行处理这些工具调用 executeOutputTool->doExecute,根据具体的对象调用hitl的executeToolOutput

## 后续的审批闸门怎么工作

1. HITL 没启用，或工具不在危险集合里：直接走 super.doExecuteTool(...)。
2. 如果是 Chrome DevTools MCP 工具，先做一次 checkBrowserTool(..., previewOnly=true)。
3. 敏感页面上的浏览器改写操作，强制单次审批，不吃 approve-all。
4. 如果当前工具或 MCP server 已经 approve-all，本次直接执行。
5. 否则构造 ApprovalRequest，调用 hitlHandler.requestApproval(request)

<img title="" src="https://cdn.paicoding.com/paicoding/dff1ec61873798992e1283f4bcf4a8ac.jpg" alt="" width="794">
