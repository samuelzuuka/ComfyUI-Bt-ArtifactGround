# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

ComfyUI-Bt-ArtifactGround 是一个 ComfyUI 插件，为 ComfyUI 生成记录提供永久存储，防止队列清空时历史数据丢失。它具有基于 Web 的界面，用于查看生成历史、过滤记录以及将图片上传到外部存储服务。

## 架构设计

### 核心组件

**插件入口点 (`__init__.py`)**

- 注册 `BtUploadImageNode` 自定义节点
- 定义前端资源的 web 目录

**请求监控 (`btmiddleware.py`)**

- 中间件拦截 ComfyUI API 请求 `/api/prompt`
- 提交新提示词时自动保存生成记录到数据库
- 异步监控提示词状态直到完成
- 使用最终结果更新数据库（成功/错误状态、输出、元数据）

**数据库层 (`database/`)**

- SQLite 数据库存储生成记录
- `manager.py`：数据库管理器，包含 ArtifactDB 实例
- `models/artifact.py`：artifacts 表的数据模型
- 数据库结构包括：id, prompt_id, created_at, result_status, prompt, meta, outputs, status

**API 端点 (`api.py`)**

- `/bt/artifacts/list`：分页获取构建物列表的 GET/POST 端点，支持过滤
- `/bt/artifacts/delete`：删除记录的 DELETE 端点
- 返回标准化格式的 JSON 响应

**上传节点 (`nodes/upload_node.py`)**

- 用于上传生成图片的自定义 ComfyUI 节点
- 支持 HTTP 直接上传和阿里云 OSS
- 处理批量上传，可配置并发数
- 与 ComfyUI 设置系统集成进行配置

**前端 (`js/`)**

- `main.js`：入口点和对话框管理
- `artifact-list.js`：列表和管理构建物的组件
- `settings.js`：配置界面
- 使用 ComfyUI 的对话框系统和样式

## 开发命令

### Python 依赖

```bash
pip install -r requirements.txt
```

### 前端开发

```bash
cd temp
npm run dev  # 监控 Tailwind CSS 变化
```

### 数据库

- 数据库文件：`data/artifacts.db`
- 首次运行时自动初始化
- 无需迁移脚本

## 配置说明

插件使用 ComfyUI 用户设置系统，配置项前缀为 `BtArtifactGround.`：

**服务器设置：**

- `BtArtifactGround.server.url`：上传服务器端点
- `BtArtifactGround.server.token`：认证令牌
- `BtArtifactGround.server.tokenField`：令牌请求头字段名

**上传设置：**

- `BtArtifactGround.upload.method`："http" 或 "oss"
- `BtArtifactGround.upload.timeout`：请求超时时间（毫秒）
- `BtArtifactGround.upload.retryCount`：重试次数
- `BtArtifactGround.upload.concurrent`：并发上传限制

**OSS 设置（当 method="oss" 时）：**

- `BtArtifactGround.oss.accessKeyId`：阿里云访问密钥 ID
- `BtArtifactGround.oss.accessKeySecret`：阿里云访问密钥 Secret
- `BtArtifactGround.oss.endpoint`：OSS 端点 URL
- `BtArtifactGround.oss.regionEndpoint`：OSS 区域端点
- `BtArtifactGround.oss.bucket`：OSS 存储桶名称
- `BtArtifactGround.oss.directory`：上传目录路径

## 关键集成点

**ComfyUI 集成：**

- 接入 ComfyUI 的提示词执行流水线
- 使用 ComfyUI 的 folder_paths 进行输出目录管理
- 与 ComfyUI 用户设置系统集成
- 通过自定义对话框扩展 ComfyUI 的 Web 界面

**数据流：**

1. 用户提交提示词 → 中间件拦截 → 以 status=0 保存到数据库
2. 提示词执行 → 监控状态 → 以结果和 status=1/2 更新数据库
3. 用户查看历史 → 前端查询 API → 显示分页结果
4. 用户上传图片 → 上传节点处理 → 外部服务集成

## 文件结构说明

- `locales/`：国际化支持（中文/英文）
- `temp/`：Tailwind CSS 处理的构建产物
- `example_workflows/`：示例 ComfyUI 工作流文件
- `doc/`：文档资源，包括使用截图