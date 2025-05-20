import os
import folder_paths
from ..database.manager import db_manager

class DeleteArtifactNode:
    """删除生成记录的节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "artifact_id": ("INT", {"default": 0, "min": 0}),
                "delete_file": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "delete_artifact"
    CATEGORY = "Bt-ArtifactGround"

    def delete_artifact(self, artifact_id, delete_file):
        # 获取记录信息
        artifact = db_manager.get_artifact_by_id(artifact_id)
        if not artifact:
            return ("记录不存在",)

        # 删除文件
        if delete_file:
            image_path = artifact[1]  # 获取图片路径
            full_path = os.path.join(folder_paths.get_output_directory(), image_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                return (f"删除文件失败: {str(e)}",)

        # 删除数据库记录
        if db_manager.delete_artifact(artifact_id):
            return ("删除成功",)
        else:
            return ("删除失败",) 