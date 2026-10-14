\% NK HistoryGuide Codex开发边界与实施路线文档

# 一、项目最终目标

项目名称：

NK HistoryGuide

定位：

面向真实校史馆参观场景的上下文感知 AI 智能讲解与参观 Agent。

核心目标：

不是开发普通校史问答机器人，而是开发能够理解参观者身份、当前展品、参观历史、用户兴趣和剩余时间，并提供个性化讲解、连续交流和参观建议的智能体系统。

# 二、Codex开发边界

## Codex负责

-   后端工程开发
-   FastAPI接口
-   数据模型设计
-   用户状态管理
-   展品数据库
-   GeniOS接口协作
-   测试代码
-   部署文档

## Codex不负责

-   训练大模型
-   替代GeniOS Agent
-   数字人开发
-   AR/VR开发
-   大型小程序开发

# 三、总体技术架构

用户

↓

Web/H5交互

↓

FastAPI后端

↓

Visitor State状态管理

↓

GeniOS Agent

↓

知识库RAG

↓

个性化讲解输出

# 四、技术选型

后端：

Python + FastAPI

数据库：

第一阶段 SQLite

后续 PostgreSQL

数据：

JSON + 数据库

# 五、MVP目标

第一阶段完成：

## GeniOS

-   创建对话型Agent
-   配置Prompt
-   建立校史知识库
-   完成RAG问答

## 后端

完成：

### 展品管理API

功能：

查询展品信息、历史背景、关键词。

### 用户状态API

功能：

保存：

-   用户身份
-   当前展品
-   已访问历史
-   兴趣信息

### 推荐接口

根据：

-   用户身份
-   剩余时间
-   兴趣

生成推荐展品。

# 六、开发阶段

## 阶段1：环境检查

检查：

-   Python
-   FastAPI
-   项目目录
-   Git

输出：

README。

## 阶段2：后端基础

建立：

historyguide-backend

目录：

-   main.py
-   api
-   models
-   services
-   database
-   tests

要求：

-   可以启动
-   有健康检查
-   有日志

## 阶段3：展品数据库

建立Exhibit模型：

字段：

-   id
-   name
-   description
-   period
-   keywords
-   importance

## 阶段4：Visitor State

管理：

-   visitor_type
-   current_exhibit
-   visited_history
-   interest
-   remaining_time

## 阶段5：GeniOS协作

GeniOS：

负责：

-   对话
-   RAG
-   知识检索
-   内容生成

后端：

负责：

-   提供上下文
-   提供展品信息
-   提供用户状态

## 阶段6：增强Agent

增加：

-   展品级RAG
-   新生/校友/游客个性化讲解
-   用户记忆

# 七、长期增强

V2：

-   二维码入口
-   Web页面
-   TTS语音

V3：

-   动态路线规划
-   参观总结

V4：

-   多Agent
-   高级Workflow

# 八、开发原则

1.  不偏离项目定位。
2.  不做普通聊天机器人。
3.  历史内容必须有知识依据。
4.  优先完成MVP。
5.  每个模块必须测试。
6.  每次开发更新README。
7.  保持模块化。

# 九、最终目标

打造：

理解游客。

理解展品。

理解参观过程。

形成完整校史馆AI参观体验。
