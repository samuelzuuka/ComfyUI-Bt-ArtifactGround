from ..database.manager import db_manager

class QueryArtifactsNode:
    """查询生成记录的节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page": ("INT", {"default": 1, "min": 1}),
                "page_size": ("INT", {"default": 50, "min": 1, "max": 100}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "query_artifacts"
    CATEGORY = "Bt-ArtifactGround"

    def query_artifacts(self, page, page_size):
        offset = (page - 1) * page_size
        artifacts = db_manager.get_artifacts(limit=page_size, offset=offset)
        
        # 格式化输出结果
        result = []
        for artifact in artifacts:
            id, image_path, workflow, parameters, created_at = artifact
            result.append(f"ID: {id}")
            result.append(f"图片路径: {image_path}")
            result.append(f"创建时间: {created_at}")
            result.append("-" * 50)
        
        return ("\n".join(result),) 