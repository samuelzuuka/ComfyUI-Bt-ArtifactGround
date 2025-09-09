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
from ..tool import command_ui_alert
import datetime
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
                "material_category": ("STRING", {"default": "默认分类"}),
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
    def IS_CHANGED(self, images, filename_prefix, material_category):
        # 返回一个随机字符串，永远不会被缓存
        return str(uuid.uuid4())

    def get_comfyui_user_setting(self,key,default=None):
        req = FakeRequest()
        all_settings = user_settings.get_settings(req)
        return all_settings.get(key,default)
    
    def _run_async_upload(self, saved_paths, settings, material_category):
        """安全地运行异步上传任务"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
            # 如果已经有运行中的事件循环，使用 asyncio.create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_in_new_loop, saved_paths, settings, material_category)
                return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            return self._run_in_new_loop(saved_paths, settings, material_category)
    
    def _run_in_new_loop(self, saved_paths, settings, material_category):
        """在新的事件循环中运行异步任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.do_upload_images(saved_paths, settings, material_category))
        finally:
            loop.close()
    
    async def upload_image(self, file_path, settings, material_category="默认分类"):
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
            data.add_field('material_category', material_category)

            # 设置请求头
            headers = {
                settings['tokenField']: settings['token']
            }
            logging.info(f"请求头: {json.dumps({k: v if k != settings['tokenField'] else '***' for k, v in headers.items()})}")

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

    async def do_upload_images(self, saved_paths, settings, material_category="默认分类"):
        """异步上传多个文件"""
        logging.info(f"开始批量上传 {len(saved_paths)} 个文件")
        logging.info(f"并发数: {settings['concurrent']}")
        logging.info(f"上传方式: {settings['method']}")
        
        # 创建信号量来限制并发数
        semaphore = asyncio.Semaphore(settings['concurrent'])
        
        async def upload_with_semaphore(path):
            async with semaphore:
                if settings['method'] == 'oss':
                    # OSS 上传流程
                    success, result = await self.upload_to_oss(path, settings)
                    if not success:
                        return False, result
                    
                    # 提交 OSS URL 到后台
                    return await self.submit_oss_url(result, os.path.basename(path), settings, material_category)
                else:
                    # HTTP 直接上传
                    return await self.upload_image(path, settings, material_category)
        
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

    def upload_images(self, images, filename_prefix, material_category, prompt:dict, extra_pnginfo:dict, unique_id:str):
        try:
            logging.info(f"images: {type(images)}")
            # 获取所有配置
            settings = {
                # 服务器设置
                "url": self.get_comfyui_user_setting("BtArtifactGround.server.url", ""),
                "tokenField": self.get_comfyui_user_setting("BtArtifactGround.server.tokenField", "token"),
                "token": self.get_comfyui_user_setting("BtArtifactGround.server.token", ""),
                
                # 上传设置
                "method": self.get_comfyui_user_setting("BtArtifactGround.upload.method", "http"),
                "timeout": self.get_comfyui_user_setting("BtArtifactGround.upload.timeout", 30000),
                "retryCount": self.get_comfyui_user_setting("BtArtifactGround.upload.retryCount", 3),
                "concurrent": self.get_comfyui_user_setting("BtArtifactGround.upload.concurrent", 3),
                
                # OSS配置
                "oss": {
                    "accessKeyId": self.get_comfyui_user_setting("BtArtifactGround.oss.accessKeyId", ""),
                    "accessKeySecret": self.get_comfyui_user_setting("BtArtifactGround.oss.accessKeySecret", ""),
                    "endpoint": self.get_comfyui_user_setting("BtArtifactGround.oss.endpoint", ""),
                    "regionEndpoint": self.get_comfyui_user_setting("BtArtifactGround.oss.regionEndpoint", ""),
                    "region": self.get_comfyui_user_setting("BtArtifactGround.oss.region", ""),
                    "bucket": self.get_comfyui_user_setting("BtArtifactGround.oss.bucket", ""),
                    "directory": self.get_comfyui_user_setting("BtArtifactGround.oss.directory", "comfyui")
                }
            }
        except Exception as e:
            print(f"读取设置出错: {str(e)}")
            return ("读取设置失败", "")

        logging.info(f"settings: {json.dumps({**settings, 'oss': {'accessKeyId': '***', 'accessKeySecret': '***', **{k:v for k,v in settings['oss'].items() if k not in ['accessKeyId', 'accessKeySecret']}}})}")
        
        # 检查服务器配置
        if not settings["url"]:
            return ("未配置上传服务器地址", "")
            
        # 如果是 OSS 上传，检查 OSS 配置
        if settings["method"] == "oss":
            if not all([settings["oss"]["accessKeyId"], 
                       settings["oss"]["accessKeySecret"],
                       settings["oss"]["endpoint"],
                       settings["oss"]["bucket"]]):
                command_ui_alert("OSS 配置不完整，请先进行系统配置")
                return ("OSS 配置不完整", "")
            try:
                import oss2
            except ImportError:
                logging.error("未安装 oss2 模块，无法使用 OSS 上传")
                command_ui_alert("请先安装 oss2 模块以使用 OSS 上传功能")
                return ("请先安装 oss2 模块以使用 OSS 上传功能", "")

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

        # 根据上传方式选择上传方法
        if settings["method"] == "oss":
            # 执行阿里云OSS上传
            try:
                # 执行上传
                upload_results = self._run_async_upload(saved_paths, settings, material_category)
                
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
                
                return (json.dumps(result, ensure_ascii=False), "\n".join(save_urls))
                    
            except ImportError:
                logging.error("未安装 oss2 模块，无法使用OSS上传")
                return ("请先安装 oss2 模块以使用OSS上传功能", "")
        else:
            # 执行HTTP上传
            try:
                upload_results = self._run_async_upload(saved_paths, settings, material_category)
                
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
                
                return (json.dumps(result, ensure_ascii=False), "\n".join(save_urls))
                
            except Exception as e:
                return (json.dumps({
                    "message": f"上传过程出错: {str(e)}",
                    "paths": saved_paths
                }, ensure_ascii=False), "") 

    async def upload_to_oss(self, file_path, settings):
        """上传文件到 OSS 并返回 URL"""
        try:
            import oss2
            
            full_path = os.path.join(self.output_dir, file_path)
            filename = os.path.basename(file_path)
            
            logging.info(f"开始 OSS 上传文件: {filename}, path={full_path}")
            
            # 创建 Auth 对象
            auth = oss2.Auth(settings["oss"]["accessKeyId"], settings["oss"]["accessKeySecret"])
            
            # 创建 Bucket 对象
            endpoint = settings["oss"]["endpoint"]
            region_endpoint = settings["oss"]["regionEndpoint"]
            bucket_name = settings["oss"]["bucket"]
            logging.info(f"upload_endpoint: {region_endpoint}, bucket_name: {bucket_name}")
            bucket = oss2.Bucket(auth, region_endpoint, bucket_name, connect_timeout=30)
            
            # 生成 OSS 对象名称（使用当前时间和随机数）
            import time
            import random
            timestamp = time.strftime("%Y%m/%Y%m%d%H%M%S")
            random_num = random.randint(100000, 999999)
            # 使用配置的默认目录
            object_name = f"{settings['oss']['directory']}/{timestamp}{random_num}{os.path.splitext(filename)[1]}"
            
            logging.info(f"OSS 对象名称: {object_name}")
            
            max_retries = 3
            retry_delay = 1  # 初始重试延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    # 上传文件到 OSS
                    with open(full_path, 'rb') as f:
                        file_content = f.read()
                        headers = {
                            'Content-Type': 'image/png',
                            # 'x-oss-storage-class': 'Standard'
                        }
                        result = bucket.put_object(
                            object_name, 
                            file_content,
                            headers=headers
                        )
                    
                    logging.info(f"OSS 上传结果 - 请求ID: {result.request_id}")
                    logging.info(f"OSS 上传结果 - ETag: {result.etag}")
                    
                    # 根据配置决定URL生成方式
                    if settings['oss'].get('endpoint'):
                        url = f"http://{endpoint}/{object_name}"
                        logging.info(f"使用自定义域名 - URL: {url}")
                    else:
                        # 生成签名URL
                        url = bucket.sign_url('GET', object_name, 60 * 60 * 24 * 365 * 100)  # 100年有效期
                        logging.info(f"使用签名URL - URL: {url}")
                    
                    return True, url
                    
                except oss2.exceptions.ServerError as e:
                    import traceback
                    logging.error(f"OSS 服务器错误(第{attempt + 1}次尝试): {str(e)}")
                    logging.error(f"错误码: {e.code}")
                    logging.error(f"错误信息: {e.message}")
                    logging.error(f"请求ID: {e.request_id}")
                    logging.error(f"堆栈跟踪:\n{traceback.format_exc()}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
                        continue
                    raise
                    
                except oss2.exceptions.OssError as e:
                    logging.error(f"OSS 上传操作失败: {str(e)}")
                    logging.error(f"错误码: {e.code}")
                    logging.error(f"错误信息: {e.message}")
                    logging.error(f"请求ID: {e.request_id}")
                    raise
                
        except Exception as e:
            logging.error(f"OSS 上传失败: {str(e)}")
            command_ui_alert(f"OSS 上传失败: 文件={file_path}")
            return False, str(e)

    async def submit_oss_url(self, url, filename, settings, material_category="默认分类"):
        """将 OSS URL 提交到后台"""
        try:
            # 准备请求数据
            data = aiohttp.FormData()
            data.add_field('oss_url', url)
            data.add_field('filename', filename)
            data.add_field('material_category', material_category)
            
            # 设置请求头
            headers = {
                settings['tokenField']: settings['token']
            }
            
            # 发送请求
            timeout = aiohttp.ClientTimeout(total=settings['timeout'] / 1000)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(settings['retryCount'] + 1):
                    try:
                        async with session.post(settings['url'], data=data, headers=headers) as response:
                            status = response.status
                            if status == 200:
                                result = await response.json()
                                if result.get('success'):
                                    data = result.get('data', {})
                                    success_files = data.get('success_files', [])
                                    material_ids = data.get('material_ids', [])
                                    
                                    success_info = {
                                        'url': url,  # 使用 OSS URL
                                        'material_id': material_ids[0] if material_ids else None,
                                        'filename': filename
                                    }
                                    return True, success_info
                            return False, f"提交 OSS URL 失败: {await response.text()}"
                    except Exception as e:
                        if attempt == settings['retryCount']:
                            return False, f"提交 OSS URL 异常: {str(e)}"
                        await asyncio.sleep(1)
            return False, "提交 OSS URL 失败: 超过重试次数"
        except Exception as e:
            return False, f"提交 OSS URL 处理错误: {str(e)}" 