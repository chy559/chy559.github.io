# 模块四：聊天助手

流程如下：

![](https://cdn.tobebetterjavaer.com/paicoding/30087641043a016aff8b6f8c435658e6.png)

## WebSocket接口：

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-17-18-22-09-image.png)

1.建立websocket连接，保存session到map中，断开连接则清理session和引用映射

2.处理业务逻辑在ChatHandler中：具体如下：

1. 获取会话id并且写入redis中，获取响应构建器和future跟踪完成状态

2. redis中获取对话历史，调用searchService检索搜索到的结果

3. 用检索到的结果构建上下文context记录sessionId->map{referenceId,fiileMd5},上下文内容如下;
   
   ![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-17-19-24-33-image.png)

4. 调用llm dpi流式响应，另起一个线程判断响应是否完成，完成则更新redis会话历史

Deepseek构建prompt访问接口：

1.通过上下文和Prompt的规则来构建prompt；

2.调用webclient访问api，并制定chunk的上传规则  

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-18-13-16-35-image.png)

## 终止回答

onChunk向前端推流中会检查stopflag

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-18-13-35-15-image.png)
