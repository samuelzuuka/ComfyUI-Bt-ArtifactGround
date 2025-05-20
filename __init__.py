from .nodes.save_node import SaveArtifactNode
from .nodes.query_node import QueryArtifactsNode
from .nodes.delete_node import DeleteArtifactNode
from .btmiddleware import *

NODE_CLASS_MAPPINGS = {
    "SaveArtifact": SaveArtifactNode,
    "QueryArtifacts": QueryArtifactsNode,
    "DeleteArtifact": DeleteArtifactNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveArtifact": "保存生成记录",
    "QueryArtifacts": "查询生成记录",
    "DeleteArtifact": "删除生成记录",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"] 