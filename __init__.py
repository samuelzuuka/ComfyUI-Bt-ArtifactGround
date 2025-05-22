from .nodes.upload_node import UploadImageNode
from .btmiddleware import *

NODE_CLASS_MAPPINGS = {
    "UploadImage": UploadImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UploadImage": "上传图片到服务器",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"] 