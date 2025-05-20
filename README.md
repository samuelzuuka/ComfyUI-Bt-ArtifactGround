# ComfyUI-Bt-ArtifactGround

一个用于保存和管理ComfyUI生成记录的插件。

## 功能特点

- 自动保存生成的图片和相关参数
- 提供界面查看历史生成记录
- 支持查看详细的生成参数
- 支持删除不需要的记录
- 分页浏览大量记录
- 左侧菜单快速访问

## 安装方法

1. 进入ComfyUI的custom_nodes目录
```bash
cd custom_nodes
```

2. 克隆本仓库
```bash
git clone https://github.com/your-username/ComfyUI-Bt-ArtifactGround.git
```

3. 安装依赖
```bash
pip install -r ComfyUI-Bt-ArtifactGround/requirements.txt
```

## 使用方法

1. 在工作流中添加"保存生成记录"节点
2. 将图片输出连接到该节点
3. 运行工作流，生成的图片和参数会自动保存
4. 点击左侧菜单的"生成记录"按钮查看历史记录

## 数据存储

- 图片文件保存在ComfyUI的output目录
- 生成记录保存在插件目录下的SQLite数据库中
- 数据库文件：artifacts.db

## 开发说明

### 项目结构
```
ComfyUI-Bt-ArtifactGround/
├── __init__.py          # 插件入口
├── nodes.py            # 节点实现
├── web/                # 前端文件
│   ├── js/
│   │   └── main.js    # 前端逻辑
│   └── css/
│       └── style.css  # 样式文件
├── requirements.txt    # 依赖列表
└── README.md          # 说明文档
```

### API接口

- GET /artifact_ground/artifacts - 获取生成记录列表
- DELETE /artifact_ground/artifacts/{id} - 删除指定记录

## 更新日志

### v1.0.0 (2024-03-21)
- 初始版本发布
- 基本功能实现

## 许可证

MIT License 