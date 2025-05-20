import os
import json
import folder_paths
import numpy as np
from PIL import Image
from ..database.manager import db_manager

class SaveArtifactNode:
    """保存生成结果到数据库的节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "artifact"}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "save_artifact"
    CATEGORY = "Bt-ArtifactGround"

    def save_artifact(self, images, filename_prefix, prompt=None, extra_pnginfo=None):
        # 获取工作流和参数信息
        workflow = {}
        parameters = {}
        
        if prompt is not None:
            workflow = prompt.copy()
        if extra_pnginfo is not None:
            parameters = extra_pnginfo.copy()

        # 保存图片
        output_dir = folder_paths.get_output_directory()
        full_output_dir = os.path.join(output_dir, "Bt-ArtifactGround")
        os.makedirs(full_output_dir, exist_ok=True)
        
        # 生成文件名
        counter = 1
        while True:
            filename = f"{filename_prefix}_{counter:05d}.png"
            full_path = os.path.join(full_output_dir, filename)
            if not os.path.exists(full_path):
                break
            counter += 1

        # 保存图片 - 处理第一张图片
        if len(images.shape) == 4:
            image = images[0]
        else:
            image = images
            
        # 将图片数据转换为PIL Image并保存
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        img.save(full_path)

        # 保存到数据库
        relative_path = os.path.join("Bt-ArtifactGround", filename)
        db_manager.save_artifact(relative_path, workflow, parameters)

        return (images,) 