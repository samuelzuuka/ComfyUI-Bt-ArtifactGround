from .nodes.upload_node import BtUploadImageNode
from .btmiddleware import *

NODE_CLASS_MAPPINGS = {
    "BtUploadImageNode": BtUploadImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BtUploadImageNode": "上传图片到服务器",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"] 