import os
import json
import asyncio
import aiohttp
from PIL import Image
import numpy as np
import folder_paths

class UploadImageNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "upload"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)  # 返回保存结果和保存地址
    RETURN_NAMES = ("result", "save_path",)
    FUNCTION = "upload_images"
    CATEGORY = "Bt-ArtifactGround"
    OUTPUT_NODE = True
    CATEGORY = "image"
    
    async def upload_image(self, file_path, settings):
        """异步上传单个文件"""
        try:
            # 构建完整的文件路径
            full_path = os.path.join(self.output_dir, file_path)
            
            # 准备上传的文件
            with open(full_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file',
                             f,
                             filename=os.path.basename(file_path),
                             content_type='image/png')

            # 设置请求头
            headers = {
                'token': settings['token']
            }

            # 发送请求
            timeout = aiohttp.ClientTimeout(total=settings['timeout'] / 1000)  # 转换为秒
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(settings['retryCount'] + 1):
                    try:
                        async with session.post(settings['url'], data=data, headers=headers) as response:
                            if response.status == 200:
                                result = await response.json()
                                return True, result
                            else:
                                error_text = await response.text()
                                if attempt == settings['retryCount']:
                                    return False, f"上传失败: HTTP {response.status} - {error_text}"
                    except Exception as e:
                        if attempt == settings['retryCount']:
                            return False, f"上传出错: {str(e)}"
                        await asyncio.sleep(1)  # 重试前等待1秒

        except Exception as e:
            return False, f"文件处理错误: {str(e)}"

    async def do_upload_images(self, saved_paths, settings):
        """异步上传多个文件"""
        # 创建信号量来限制并发数
        semaphore = asyncio.Semaphore(settings['concurrent'])
        
        async def upload_with_semaphore(path):
            async with semaphore:
                return await self.upload_image(path, settings)
        
        # 并发上传所有文件
        tasks = [upload_with_semaphore(path) for path in saved_paths]
        results = await asyncio.gather(*tasks)
        
        # 处理上传结果
        success_count = sum(1 for success, _ in results if success)
        failed_count = len(results) - success_count
        
        # 构建返回消息
        messages = []
        for i, (success, result) in enumerate(results):
            if not success:
                messages.append(f"文件 {os.path.basename(saved_paths[i])} - {result}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "messages": messages
        }

    def upload_images(self, images, filename_prefix):
        try:
            import server
            settings = {
                "enabled": server.PromptServer.instance.client_settings.get("BtArtifactGround.server.enabled", True),
                "url": server.PromptServer.instance.client_settings.get("BtArtifactGround.server.url", ""),
                "token": server.PromptServer.instance.client_settings.get("BtArtifactGround.server.token", ""),
                "auto": server.PromptServer.instance.client_settings.get("BtArtifactGround.upload.auto", True),
                "timeout": server.PromptServer.instance.client_settings.get("BtArtifactGround.upload.timeout", 30000),
                "retryCount": server.PromptServer.instance.client_settings.get("BtArtifactGround.upload.retryCount", 3),
                "concurrent": server.PromptServer.instance.client_settings.get("BtArtifactGround.upload.concurrent", 3)
            }
        except Exception as e:
            print(f"读取设置出错: {str(e)}")
            return ("读取设置失败",)

        # 检查是否启用上传
        if not settings["enabled"] or not settings["auto"]:
            return ("上传服务未启用",)

        # 检查服务器配置
        if not settings["url"]:
            return ("未配置上传服务器地址",)

        # 创建保存目录
        output_dir = folder_paths.get_output_directory()
        full_output_dir = os.path.join(output_dir, "Bt-ArtifactGround", "uploads")
        os.makedirs(full_output_dir, exist_ok=True)
        
        saved_paths = []
        
        # 处理每张图片
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        for idx in range(batch_size):
            # 生成文件名
            counter = 1
            while True:
                filename = f"{filename_prefix}_{counter:05d}.png"
                full_path = os.path.join(full_output_dir, filename)
                if not os.path.exists(full_path):
                    break
                counter += 1

            # 获取当前图片
            if len(images.shape) == 4:
                image = images[idx]
            else:
                image = images
                
            # 将图片数据转换为PIL Image并保存
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            img.save(full_path)
            
            # 记录相对路径
            relative_path = os.path.join("Bt-ArtifactGround", "uploads", filename)
            saved_paths.append(relative_path)

        # 如果没有启用自动上传，直接返回
        if not settings["auto"]:
            return (json.dumps({"message": "图片已保存但未上传", "paths": saved_paths}),)

        # 执行异步上传
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            upload_results = loop.run_until_complete(self.do_upload_images(saved_paths, settings))
            
            # 构建返回消息
            result = {
                "message": f"上传完成: 成功{upload_results['success']}个, 失败{upload_results['failed']}个",
                "success": upload_results['success'],
                "failed": upload_results['failed'],
                "paths": saved_paths
            }
            
            if upload_results['messages']:
                result["errors"] = upload_results['messages']
            
            return (json.dumps(result),)
            
        except Exception as e:
            return (json.dumps({
                "message": f"上传过程出错: {str(e)}",
                "paths": saved_paths
            }),) 