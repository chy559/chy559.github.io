---
title: 微服务实战 02：Nacos、网关、Sentinel 与 Seata
slug: pmhub-02-nacos-gateway-sentinel
category: tech
date: 2026-06-16
summary: 整理 PmHub 中 Nacos 注册配置中心、Gateway 鉴权路由、Sentinel 限流熔断、OpenFeign 调用和 Seata 分布式事务。
collection: pmhub
collectionTitle: 微服务实战
seriesOrder: 2
---

# 1：注册中心

## Nacos1:服务注册中心

**这个项目里的 Nacos 既是服务通讯录，也是配置仓库。服务启动时把 spring.application.name + ip + port 注册进去；网关和 Feign 调用服务时，再用服务名从 Nacos 查真实地址。**

1.引入springcloud alibaba

2.在需要放进nacos的微服务中引入nacos-discovery

3.各个微服务在bootstrap中添加nacos作为注册中心的配置

## Nacos2:配置中心

配置变更后立即生效 基于nacos的实时推送机制

1.添加nacos-config依赖

2.bootstrap添加nacos的配置

动态配置:

Nacos Client 长轮询监听 dataId
-> 配置变化后拉取新内容
-> 更新 Spring Environment
-> @RefreshScope Bean 重新创建
-> @ConfigurationProperties 重新绑定

## Nacos持久化

这里使用的是mysql

## Nacos的作用总结

Nacos 在项目中同时承担**服务注册发现和配置中心**职责。服务注册发现用于支撑 Gateway 路由和 OpenFeign 服务间调用，避免硬编码服务地址；配置中心用于统一管理各微服务配置，支持部分配置动态刷新，降低多服务环境下配置修改和发布成本。

____

# 2：网关

主要作用:1.统一入口    2.路由   3.服务发现(通过nacos）   4.**统一鉴权**  

1. **白名单放行**  
   登录、注册、Swagger、静态资源等接口可以配置白名单，不走 token 校验。

2. **验证码处理**  
   网关提供 /code 生成验证码，也可以在登录/注册前通过 ValidateCodeFilter 校验验证码。

3. **请求体缓存**  
   CacheRequestFilter 解决网关过滤器中请求体只能读一次的问题，方便验证码等过滤器读取 body。

4. **安全过滤**  
   包括 XSS 过滤、黑名单 URL 过滤等。

5. **限流熔断**  
   集成 Sentinel，可以对网关路由做流控，比如限制 pmhub-auth、pmhub-system 的访问流量。

6. **统一日志**  
   AuthFilter 中记录接口访问路径、参数、耗时等信息。

## 三大法宝

路由，断言，过滤(分为 全局过滤器和路由过滤器)

## 路由动态uri

lb://服务名   通过nacos实现动态的uri

## 接口访问耗时

```java
return chain.filter(exchange).then(Mono.fromRunnable(() -> {

            try {

                // 记录接口访问日志

                Long beginVisitTime = exchange.getAttribute(BEGIN_VISIT_TIME);

                if (beginVisitTime != null) {

                    URI uri = exchange.getRequest().getURI();

                    Map<String, Object> logData = new HashMap<>();

                    logData.put("host", uri.getHost());

                    logData.put("port", uri.getPort());

                    logData.put("path", uri.getPath());

                    logData.put("query", uri.getRawQuery());

                    logData.put("duration", (System.currentTimeMillis() - beginVisitTime) + "ms");

                    log.info("访问接口信息: {}", logData);

                    log.info("我是美丽分割线: ###################################################");

                }

            } catch (Exception e) {

                log.error("记录日志时发生异常: ", e);

            }

        }));
```

过滤器里面的Mono.FormRunnable 的 then逻辑来实现

# 3.熔断降级限流(Sentinel)网关级别的限流

1.1配合Gateway实现限流：pom引入依赖 yml写sentinel配置 nacos动态配置 

```
超过阈值抛出 BlockException
-> SentinelFallbackHandler 捕获异常并返回“请求超过最大数，请稍候再试”
```

1.2.配合openFeign实现熔断降级

第一步，使用 @FeignClient 注解上添加自定义的 fallbackFactory。

第二步，创建 UserFeginFallbackFactory 进行自定义的降级处理。

feign.sentinel.enabled=true

+ @EnablePmFeignClients 扫描 Feign 接口
+ @FeignClient(fallbackFactory=xxx)
+ FallbackFactory 返回兜底实现
  = 远程调用失败时返回 R.fail(...)，避免异常直接击穿业务 

sentinel根据慢调用比例，异常比例，异常数来进行熔断

2.redis固定窗口配合注解进行限流 

**两者的区别：** Redis 限流超了，默认是业务拒绝，不是 OpenFeign 熔断；

除非这个业务拒绝最终被 Feign 识别成异常，否则不会走 fallback。Sentinel 熔断/降级要看 Sentinel 自己的规则信号，比如慢调用比例、异常比例、异常数等。

# 4.服务间的调用-------OpenFeign

特点:声明式调用 只用写接口 类似于mapper 底层是基于jdk的动态代理调用http服务

配合nacos实现动态配置调用

作用：

1. 用于微服务间的http调用，声明式接口简化代码

2. 用于熔断降级自定义实现fallbackFactory 支持sentinel和fallback

# 5.分布式事务解决方案------Seata

常见解决手段：

1. 2PC:两阶段提交，优点是一致性强缺点是性能差，阻塞严重，协调者压力大

2. TCC:   Try：预留资源
   
              Confirm：确认执行
              Cancel：取消回滚

3. SAGA方案：是长事务方案，把一个大事务拆成多个小事务，每一步都有补偿操作

4. MQ实现最终的一致性

Seata模式

1. AT模式：业务代码正常写 SQL，Seata 在底层帮你记录回滚日志 `undo_log`，如果全局事务失败，就根据 `undo_log` 自动补偿回滚。

2. TCC SAGA
