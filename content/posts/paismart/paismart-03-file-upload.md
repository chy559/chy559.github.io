# 模块二：文件上传

___

![文件上传](https://cdn.tobebetterjavaer.com/paicoding/0c6c2d3d1b6b96924d664da51d3835fa.jpeg)

完整的业务流程如下：

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-15-18-26-38-image.png)

___

## 分片上传(全在一个接口中)

redis bitMap记录chunk的上传状态

1.从前端获取分片的信息，先获取文件类型和主组织，调用service,如果数据库中没有这个文件则先存入数据库；

2.从**redis中**检查该文件是否已经上传过，并且检查该chunk是否已经存入chunkinfo的表中

3.分片在redis中标记为上传但是数据库中没有则需要检查minIo中是否有分片，**没有则需要重新上传**，将chunkUploaded设置为false

4.未上传或需要重新上传的文件上传至minIO,使用putObjectArgs设置bucket名，路径，文件IO流和文件媒体类型，**重新上传至minIo**(putObject)，并且setbit key(用MD5和用户id区分) chunkindex 1,**在redis中标记为已上传**

5.如果chunkInfo没有存相关信息，不管是否上传都要存入数据库

6.准备返回给前端的数据：通过**redis中的bitmapdata**获取到所有已经上传的chunkindex和总分片数(filesize/chunksize),计算上传的百分比，将已上传的chunk和百分比返回给前端

___

## 文件合并

### 接口1：查询文件上传的状态(/status)

1.从数据库中获取文件信息，从redis中获取上传chunkindex,获取总分片数，计算上传的百分比；类似于分片上传接口中的最后部分

### 接口2：合并文件(merge)

1.前端上传完所有文件后调用该接口，首先校验文件的存在与否和用户的权限是否可以操作文件；

2.校验是否上传完所有的文件chunk,操作细节如**分片上传的步骤6**，随后则可以开始合并文件，调用service中的方法；

3.校验chunkinfo中的分片数是否和总分片数一致，保证数据的一致性，然后获取minIO中存储chunk的路径，校验minIo中数据是否都存在(数据一致性)；

4.mergePath = "merged/<md5>"，文件合并minIO示例代码,将各个chunk的path 存入list<ComposeSource>中，再调用composeObject方法,statob检查是否合并成功

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-16-15-04-04-image.png)

5.合并成功后则可以开始删除分片文件：首先调用removeObject删除minIo中的分片信息，然后删除redis中的记录分片的key，随后更新fileload数据库中的status,并记录merge的时间，返回预签名url；初始化FileProcessingTask，通过url

6.将文件处理任务发送到fileprocesstopic中，将文件处理的结果返回给前端（url)

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-16-16-35-05-image.png)

___

## 文件处理

consumer:异常处理在config中定义，设置了死信队列转发器和错误的处理器

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-16-16-54-39-image.png)

消费者定义：

1.通过url下载文件获取文件的inputstream，然后调用解析文件和向量化的service；

2.解析文件（使用**tika中的parser驱动整个流式处理的过程**）：流式处理文件(tika)，设置自定义的handle,维护一个**缓冲区**，Tika解析器会调用characters方法，当累积的文本达到"父块"大小时,就触发processParentChunk方法，进行"子切片"的生成和入库。

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-16-18-52-18-image.png) 其中流式文件的handle逻辑需要自己实现,将**父块按段落，标点，句子长短等规则划分**成更有语义的子块，并将子块**存入数据库**中

reason:embedding 模型本身有输入长度限制，分块是向量化的前提；语义集中的 chunk 在混合检索时也会更容易被精准召回

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-16-19-21-36-image.png)

3.向量化文件：首先从数据库中取出vectors并还原为更简单的TestChunk(id+string),提取文本内容后// 调用外部模型生成向量embedding模型
**List<float[]> vectors = embeddingClient.embed(texts);**  调用配置好的embeddingclient实现向量化 ,存入es中 调用es service,TODO es使用

____

## 删除文件

检查权限：需要同时删除minIO,数据库两个表和es中信息

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-17-13-11-34-image.png)

___

## 获取用户的有效org

先去redis缓存中找(List),没有则递归调用在数据库中获取所有的标签，和他们的父标签，然后加载进入redis 
