## 项目部署全流程总结

### 一、前端安全优化

1. 移除登录页管理员凭据显示
   
   - 修改 pwd-login.vue ，删除默认填充的 admin 账号密码
   - 删除快速登录按钮，防止任何人直接登录管理员账号

2. 修复侧边栏布局切换消失 Bug
   
   - 修改 global-header/index.vue ，恢复 GLOBAL_HEADER_MENU_ID 容器
   
   - 确保切换布局模式时侧边栏正常显示
     
     ### 二、Docker 容器化打包

3. 创建 Dockerfile
   
   - 前端 Dockerfile ：Node.js 构建 + Nginx 运行的多阶段构建
   - 后端 Dockerfile ：Maven 编译 + OpenJDK 运行的多阶段构建

4. 创建 .dockerignore
   
   - 后端 .dockerignore ：排除 node_modules、.git、IDE 配置等
   - 前端 .dockerignore ：排除 dist、.git、IDE 配置等

5. 编写自动化构建推送脚本
   
   - build-push.ps1 ：一键构建前后端镜像并推送到阿里云容器镜像服务
     
     ### 三、Docker Compose 编排

6. 编写 docker-compose.yaml ，包含 6 个服务：
   
   服务 镜像 端口 说明 mysql mysql:8 3306 数据库，配置了健康检查 redis redis:latest 6379 缓存 es elasticsearch:8.10.4 9200 搜索引擎，配置了单节点模式 kafka bitnamilegacy/kafka:latest 9092/9093 消息队列，KRaft 模式 minio minio:RELEASE.2025-04-22 19000(控制台)/19001(API) 对象存储 backend 阿里云私有镜像 8081 Spring Boot 后端

7. 关键配置优化 ：
   
   - 创建 pai-net 桥接网络，确保容器间通过服务名互通
   
   - 配置 depends_on + 健康检查，保证启动顺序
   
   - 设置内存限制（后端 768m、ES 1g、Kafka 768m 等）
   
   - Kafka ADVERTISED_LISTENERS 设为 kafka:9092 （而非 localhost）
     
     ### 四、环境配置适配

8. 编写 application-docker.yml
   
   - 数据库连接： mysql:3306 （容器服务名）
   - Redis： redis:6379
   - Kafka： kafka:9092
   - Elasticsearch： es:9200
   - MinIO API： minio:19001 ，公网访问： 8.148.76.22:19000
   - 补全 DeepSeek API Key 和通义千问 Embedding Key

9. 编写 nginx.conf
   
   - 前端静态文件托管
   
   - /api/ 反向代理到后端 8081
   
   - /proxy-ws WebSocket 代理
     
     ### 五、Bug 修复

10. 修复 ES 索引初始化 FileNotFoundException
    
    - EsIndexInitializer.java ： resource.getFile() → resource.getInputStream()
    - 原因：JAR 包内无法用 getFile() 读取资源文件

11. 修复 MinIO 端口配置
    
    - docker-compose 中 --console-address 和 --address 端口写反
    
    - application-docker.yml 中 endpoint 端口从 19000 改为 19001
      
      ### 六、服务器部署与网络配置

12. 阿里云 ECS 部署 （3.5GB 内存服务器）
    
    - 添加 swap 分区缓解内存不足
    - 停止服务器自带 MySQL 避免端口冲突
    - 清除 Kafka 数据卷解决 broker 注册冲突

13. Nginx 配置
    
    - 将 pai-smart.conf 放到宝塔面板的 /www/server/panel/vhost/nginx/ 目录
    - 监听 8080 端口，配置前端静态文件和后端 API 代理

14. 防火墙与安全组
    
    - UFW 开放 8080 端口
    - 阿里云安全组入方向规则放行 8080/TCP

15. MinIO 桶创建
    
    - 在容器内部通过 mc 命令创建 uploads 桶
