from .nodes.upload_node import BtUploadImageNode
from .btmiddleware import *

# 检查并安装依赖
# def ensure_dependencies():
#     requirements_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")
#     if os.path.exists(requirements_file):
#         logging.info("正在安装 ComfyUI-Bt-ArtifactGround 依赖...")
#         subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
#         logging.info("ComfyUI-Bt-ArtifactGround 依赖安装完成")

# # 在插件加载时自动安装依赖
# ensure_dependencies()

NODE_CLASS_MAPPINGS = {
    "BtUploadImageNode": BtUploadImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BtUploadImageNode": "上传图片到服务器",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"] 