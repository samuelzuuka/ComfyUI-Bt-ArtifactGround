# ComfyUI 节点注册清单

本清单汇总 `ComfyUI-Bt-ArtifactGround` 插件在当前仓库中注册的 ComfyUI 自定义节点。

- 注册入口：`__init__.py` 中的 `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS`
- 节点所在目录：`nodes/`
- 统一分类（菜单目录）：`Bt-ArtifactGround`
- 前端扩展目录：`WEB_DIRECTORY = "./js"`

> 所有节点运行时所需的密钥 / 服务器地址 / OSS 配置等，均从 ComfyUI 用户设置（`BtArtifactGround.*`）中读取，节点本身不暴露这些敏感参数。

---

## 节点总览

| 内部类（NODE_CLASS_MAPPINGS 键） | 显示名 | 源码文件 | 功能 |
|---|---|---|---|
| `BtUploadImageNode` | 上传图片到服务器 | `nodes/upload_node.py` | 将生成图片保存并上传到远程服务器 |
| `BtJimengT2IV31Node` | 即梦文生图3.1 | `nodes/jimeng_t2i_v31_node.py` | 调用火山引擎即梦文生图 3.1 |
| `BtJimengT2IV30Node` | 即梦文生图3.0 | `nodes/jimeng_t2i_v31_node.py` | 调用火山引擎即梦文生图 3.0 |
| `BtJimengT2IV40Node` | 即梦文生图4.0 | `nodes/jimeng_t2i_v31_node.py` | 调用火山引擎即梦文生图 4.0 |

> 3 个即梦节点共用基类 `BtJimengT2IBaseNode`，仅 `REQ_KEY`（算法名称）不同：`jimeng_t2i_v31` / `jimeng_t2i_v30` / `jimeng_t2i_v40`。接口、输入、输出完全一致。

---

## 1. BtUploadImageNode（上传图片到服务器）

- **源码**：`nodes/upload_node.py`
- **执行函数**：`upload_images`
- **分类**：`Bt-ArtifactGround`
- **`OUTPUT_NODE = True`**（无图像输出，纯结果节点）
- **返回类型**：`RETURN_TYPES = ("STRING", "STRING")`，`RETURN_NAMES = ("result", "save_path")`

### 作用
将上游传入的 ComfyUI 图像批保存到本地 `output/Bt-ArtifactGround/uploads/` 目录，并按配置（HTTP 直传或阿里云 OSS）上传到远程服务器（构建物广场），返回上传结果与图片地址。

### 输入（INPUT_TYPES）

**required（必填）**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `images` | `IMAGE` | — | ComfyUI 图像张量（可批量，shape 为 `[B, H, W, 3]`） |
| `filename_prefix` | `STRING` | `"upload"` | 保存文件名前缀，实际文件名形如 `{prefix}_{序号:05d}.png` |
| `material_category` | `STRING` | `"默认分类"` | 上传到服务器时使用的素材分类名称 |

**hidden（ComfyUI 自动注入，不暴露在界面）**

| 参数 | 值 | 说明 |
|---|---|---|
| `prompt` | `"PROMPT"` | 当前工作流 prompt |
| `extra_pnginfo` | `"EXTRA_PNGINFO"` | 附加 PNG 元数据 |
| `unique_id` | `"UNIQUE_ID"` | 节点唯一 ID |

### 输出

| 名称 | 类型 | 说明 |
|---|---|---|
| `result` | `STRING` | JSON 字符串，包含 `message`、成功/失败数量、成功文件（url / material_id / filename）与失败文件信息 |
| `save_path` | `STRING` | 成功上传文件的 URL 列表，以换行符 `\n` 拼接 |

### 依赖的运行配置（从用户设置读取，键名前缀 `BtArtifactGround.`）
- `server.url` / `server.tokenField` / `server.token`：上传服务器地址与鉴权
- `upload.method`（默认 `http`，可选 `oss`）、`upload.timeout`、`upload.retryCount`、`upload.concurrent`
- `oss.*`：阿里云 OSS 的 accessKeyId / accessKeySecret / endpoint / regionEndpoint / region / bucket / directory（仅 OSS 模式需要）

### 其他行为
- `IS_CHANGED` 每次都返回随机 UUID，因此**不会被缓存**，每次执行都会重新保存并上传。
- OSS 模式需要额外安装 `oss2` 模块，未安装时会通过 `command_ui_alert` 提示。

---

## 2. BtJimengT2IV31Node / BtJimengT2IV30Node / BtJimengT2IV40Node（即梦文生图）

- **源码**：`nodes/jimeng_t2i_v31_node.py`
- **基类**：`BtJimengT2IBaseNode`（三个子类仅 `REQ_KEY` 不同）
- **执行函数**：`generate`
- **分类**：`Bt-ArtifactGround`
- **返回类型**：`RETURN_TYPES = ("IMAGE", "STRING")`，`RETURN_NAMES = ("images", "result")`

### 作用
调用火山引擎视觉智能（visual.volcengineapi.com）的即梦文生图异步接口：先提交生成任务（`CVSync2AsyncSubmitTask`），再轮询查询结果（`CVSync2AsyncGetResult`），最后把返回的图片（base64 或 URL）解码为 ComfyUI 图像张量输出。三个节点分别对应算法 `jimeng_t2i_v31` / `jimeng_t2i_v30` / `jimeng_t2i_v40`。

### 输入（INPUT_TYPES，三个节点共享）

**required（必填）**

| 参数 | 类型 | 默认值 / 范围 | 说明 |
|---|---|---|---|
| `prompt` | `STRING`（多行） | — | 生成提示词，中英文均可；建议 ≤120 字符，最长 ≤800 |
| `width` | `INT` | 默认 1328，范围 512–3024，步长 8 | 生成宽度；需与 `height` 同时传才生效 |
| `height` | `INT` | 默认 1328，范围 512–3024，步长 8 | 生成高度 |
| `seed` | `INT` | 默认 -1，范围 -1–2147483647 | 随机种子；-1 表示随机 |
| `use_pre_llm` | `BOOLEAN` | 默认 `True` | 是否开启文本扩写（对短 prompt 建议开启） |
| `poll_interval_ms` | `INT` | 默认 1000，范围 200–10000，步长 100 | 轮询查询间隔（毫秒） |
| `poll_timeout_ms` | `INT` | 默认 120000，范围 1000–600000，步长 1000 | 轮询总超时（毫秒） |
| `return_url` | `BOOLEAN` | 默认 `False` | 是否以图片链接形式返回（而非 base64） |

**optional（可选）**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `req_json` | `STRING`（多行） | `""` | 透传给即梦接口的 `req_json`，可配置水印（`logo_info`）、隐式标识（`aigc_meta`）等；若 `return_url=True` 且此项为空时，节点会自动填充 `{"return_url": true}` |

### 输出

| 名称 | 类型 | 说明 |
|---|---|---|
| `images` | `IMAGE` | 生成的图片张量（批量，shape `[B, H, W, 3]`）；失败时返回 1×64×64×3 的占位张量 |
| `result` | `STRING` | JSON 字符串，包含 `task_id`、`status`、`image_count`、`image_urls`；出错时返回错误描述字符串 |

### 依赖的运行配置（从用户设置读取，键名前缀 `BtArtifactGround.volc.`）
- `volc.accessKeyId` / `volc.secretAccessKey`：火山引擎 AK/SK（必填，缺失时节点直接返回错误）
- `volc.region`（默认 `cn-north-1`）、`volc.service`（默认 `cv`）
- `volc.endpoint`（默认 `https://visual.volcengineapi.com`）
- `volc.timeout`（默认 30000，单位毫秒）

### 其他行为
- 使用 HMAC-SHA256 签名（火山引擎 V4 签名），在节点内部 `_build_auth_headers` 构造 `Authorization` 头。
- 任务状态为 `done` 时收集图片；状态 `not_found` / `expired` 或轮询超时则报错返回占位图。
- 接口协议详情见 `doc/jimeng-3.1.md`（即梦文生图 3.1 官方接口说明）。
