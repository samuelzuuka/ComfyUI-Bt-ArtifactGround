import os
import json
import asyncio
import aiohttp
from aiohttp import web
from PIL import Image
import numpy as np
import folder_paths
import logging
import server
import uuid
# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

user_manager = server.PromptServer.instance.user_manager
user_settings = user_manager.settings


class FakeRequest:
    def __init__(self,headers=None):
        self.headers = {"comfy-user": "default"}
        if headers:
            self.headers = headers

class BtUploadImageNode:
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
            # 隐藏的内置参数
            "hidden": {
                # 提示词
                "prompt": "PROMPT", 
                # 额外信息
                "extra_pnginfo": "EXTRA_PNGINFO",
                # 节点id
                "unique_id": "UNIQUE_ID", 
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)  # 返回保存结果和保存地址
    RETURN_NAMES = ("result", "save_path",)
    FUNCTION = "upload_images"
    CATEGORY = "Bt-ArtifactGround"
    OUTPUT_NODE = True
    # CATEGORY = "image"

    @classmethod
    def IS_CHANGED(self, images, filename_prefix):
        # 返回一个随机字符串，永远不会被缓存
        return str(uuid.uuid4())

    def get_comfyui_user_setting(self,key,default=None):
        req = FakeRequest()
        all_settings = user_settings.get_settings(req)
        # logging.info(f"all_settings: {json.dumps(all_settings)}")
        return all_settings.get(key,default)
    
    async def upload_image(self, file_path, settings):
        """异步上传单个文件"""
        try:
            # 构建完整的文件路径
            full_path = os.path.join(self.output_dir, file_path)
            filename = os.path.basename(file_path)
            
            logging.info(f"开始上传文件: {filename},path={full_path}")
            logging.info(f"上传地址: {settings['url']}")
            
            # 读取文件内容到内存
            with open(full_path, 'rb') as f:
                file_data = f.read()
            
            # 准备上传的文件
            data = aiohttp.FormData()
            data.add_field('files',
                         file_data,
                         filename=filename,
                         content_type='image/png')

            # 设置请求头
            headers = {
                'token': settings['token']
            }
            logging.info(f"请求头: {json.dumps({k: v if k != 'token' else '***' for k, v in headers.items()})}")

            # 发送请求
            timeout = aiohttp.ClientTimeout(total=settings['timeout'] / 1000)  # 转换为秒
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(settings['retryCount'] + 1):
                    try:
                        logging.info(f"正在进行第 {attempt + 1} 次尝试上传...")
                        async with session.post(settings['url'], data=data, headers=headers) as response:
                            status = response.status
                            logging.info(f"响应状态码: {status}")
                            
                            if status == 200:
                                result = await response.json()
                                if result.get('success'):
                                    # 解析成功结果
                                    data = result.get('data', {})
                                    success_files = data.get('success_files', [])
                                    material_ids = data.get('material_ids', [])
                                    
                                    success_info = {
                                        'url': success_files[0] if success_files else None,
                                        'material_id': material_ids[0] if material_ids else None,
                                        'filename': success_files[0] if success_files else None
                                    }
                                    
                                    logging.info(f"上传成功 - 文件: {filename}")
                                    logging.info(f"文件URL: {success_info['url']}")
                                    logging.info(f"素材ID: {success_info['material_id']}")
                                    logging.info(f"服务器响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                                    return True, success_info
                                else:
                                    error_msg = result.get('msg', '未知错误')
                                    logging.error(f"上传失败 - 文件: {filename}")
                                    logging.error(f"错误信息: {error_msg}")
                                    if attempt == settings['retryCount']:
                                        return False, f"业务处理失败: {error_msg}"
                            else:
                                error_text = await response.text()
                                logging.error(f"上传失败 - 文件: {filename}")
                                logging.error(f"错误响应: {error_text}")
                                if attempt == settings['retryCount']:
                                    return False, f"HTTP错误: {status} - {error_text}"
                    except Exception as e:
                        logging.error(f"上传出错 - 文件: {filename}")
                        logging.error(f"错误信息: {str(e)}")
                        if attempt == settings['retryCount']:
                            return False, f"请求异常: {str(e)}"
                        logging.info(f"等待 1 秒后进行重试...")
                        await asyncio.sleep(1)  # 重试前等待1秒

        except Exception as e:
            logging.error(f"文件处理错误 - 文件: {filename}")
            logging.error(f"错误信息: {str(e)}")
            return False, f"文件处理错误: {str(e)}"

    async def do_upload_images(self, saved_paths, settings):
        """异步上传多个文件"""
        logging.info(f"开始批量上传 {len(saved_paths)} 个文件")
        logging.info(f"并发数: {settings['concurrent']}")
        
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
        
        logging.info(f"批量上传完成 - 成功: {success_count}, 失败: {failed_count}")
        
        # 构建返回消息
        success_files = []
        error_files = []
        
        for i, (success, result) in enumerate(results):
            if success:
                success_files.append({
                    'local_path': saved_paths[i],
                    'url': result['url'],
                    'material_id': result['material_id'],
                    'filename': result['filename']
                })
            else:
                error_files.append({
                    'local_path': saved_paths[i],
                    'error': result
                })
                logging.error(f"文件 {os.path.basename(saved_paths[i])} - {result}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "success_files": success_files,
            "error_files": error_files
        }

    def upload_images(self, images, filename_prefix,prompt:dict, extra_info:dict, id:str):
        try:
            logging.info(f"images: {type(images)}")
            settings = {
                "enabled": self.get_comfyui_user_setting("BtArtifactGround.server.enabled", True),
                "url": self.get_comfyui_user_setting("BtArtifactGround.server.url", ""),
                "token": self.get_comfyui_user_setting("BtArtifactGround.server.token", ""),
                "auto": self.get_comfyui_user_setting("BtArtifactGround.upload.auto", True),
                "timeout": self.get_comfyui_user_setting("BtArtifactGround.upload.timeout", 30000),
                "retryCount": self.get_comfyui_user_setting("BtArtifactGround.upload.retryCount", 3),
                "concurrent": self.get_comfyui_user_setting("BtArtifactGround.upload.concurrent", 3)
            }
        except Exception as e:
            print(f"读取设置出错: {str(e)}")
            return ("读取设置失败",)

        logging.info(f"settings: {json.dumps(settings)}")
        # 检查是否启用上传
        # if not settings["enabled"] or not settings["auto"]:
        #     return ("上传服务未启用",)

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
        # if not settings["auto"]:
        #     return (json.dumps({"message": "图片已保存但未上传", "paths": saved_paths}),)

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
            
            if upload_results['success_files']:
                result["success_files"] = upload_results['success_files']
            
            if upload_results['error_files']:
                result["error_files"] = upload_results['error_files']
            
            save_urls = []
            for success_file in upload_results['success_files']:
                save_urls.append(success_file['url'])
            
            return (json.dumps(result,ensure_ascii=False),"\n".join(save_urls))
            
        except Exception as e:
            return (json.dumps({
                "message": f"上传过程出错: {str(e)}",
                "paths": saved_paths
            },ensure_ascii=False),) 