---
title: 微服务实战 01：PmHub 总览与 Docker 快速启动
slug: pmhub-01-overview-docker
category: tech
date: 2026-06-16
summary: 整理 PmHub 的 Spring Cloud 微服务组成、Docker Compose 快速启动、需求分析、技术选型和系统分层。
collection: pmhub
collectionTitle: 微服务实战
seriesOrder: 1
---

<img title="" src="file:///C:/Users/陈%20华%20宇/Pictures/Screenshots/屏幕截图%202026-06-07%20191703.png" alt="" width="726">

Spring Cloud:注册中心，请求调用，熔断，网关

## docker快速启动

docker compose up -d pmhub-mysql pmhub-redis pmhub-nacos pmhub-seata
docker compose up -d pmhub-auth pmhub-gateway pmhub-system pmhub-project pmhub-workflow

.\start-pmhub-dev.ps1

.\stop-pmhub-dev.ps1

##### 编写 Docker Compose 与 PowerShell 自动化脚本，实现 PmHub 前后端及 MySQL、Redis、Nacos 等依赖服务一键启动，解决容器化部署中的配置兼容与中文编码问题。

## 需求分析

1. **项目协作管理**

包括项目创建、项目列表、项目详情、项目成员、项目阶段、项目进度、项目文件、项目日志等。目标是让团队能集中管理项目状态，而不是靠 Excel、聊天记录、文档零散维护。

2. **任务管理**

包括任务创建、任务分配、任务状态流转、子任务、任务工时、任务负责人、任务提醒等。它解决的是“谁负责什么、做到哪一步、是否延期、是否完成”的协作问题。

3. **流程审批**

项目里集成了 Flowable 工作流，用来做流程模型、表单设计、流程部署、流程实例、待办任务等。它解决的是企业里常见的“项目发布、任务变更、审批流转”不能只靠简单状态字段的问题。

4. **系统权限管理**

包括用户、角色、菜单、部门、岗位、字典、参数配置、登录日志、操作日志等。它解决的是后台系统必须有的权限控制和组织架构管理问题。

5. **统一认证与访问入口**

通过认证服务和网关服务，把登录、Token、接口鉴权、白名单、路由转发统一起来。这样前端只访问网关，后端服务可以隐藏在网关后面。

6. **微服务拆分与服务治理**

项目拆成 auth、gateway、system、project、workflow、job、gen 等服务，并用 Nacos 做注册发现和配置中心，用 Feign 做服务间调用。这解决的是单体系统变大后难维护、难扩展的问题。

7. **缓存、限流、事务、监控等基础能力**

它接入 Redis、Sentinel、Seata、Spring Boot Admin、Actuator、Docker Compose 等组件，解决缓存加速、接口限流、跨服务事务一致性、服务状态监控和本地/服务器部署的问题。

## 技术选型

服务注册与发现:Nacos

配置中心:Nacos

api网关:spring Gateway

熔断限流:sentinel

链路追踪：SkyWalking

服务调用:openFeign    用openFeign注解动态代理实现远程的调用 类似于mybatis-plus

分布式数据库:Seata

<img title="" src="https://cdn.nlark.com/yuque/0/2024/png/29495295/1720751962092-18914a92-752e-4849-b792-1eed70e9763b.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_26%2Ctext_UG1IdWI%3D%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10" alt="" width="688">

### 重点学什么：限流 降级 分布式数据一致性 分布式锁

___

## 分层

网关层  业务层   基础服务层（中间件） 存储层(mysql redis)

![](C:\Users\陈%20华%20宇\Pictures\Screenshots\屏幕截图%202026-06-10%20135250.png)

token存：login_tokens:{uuid} -> LoginUser
