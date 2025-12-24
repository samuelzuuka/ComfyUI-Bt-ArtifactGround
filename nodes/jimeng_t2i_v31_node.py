import asyncio
import base64
import datetime
import hashlib
import hmac
import io
import json
import logging
import time
import urllib.parse

import aiohttp
from PIL import Image
import numpy as np
import torch
import server


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

user_manager = server.PromptServer.instance.user_manager
user_settings = user_manager.settings


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = {"comfy-user": "default"}
        if headers:
            self.headers = headers


class BtJimengT2IV31Node:
    def __init__(self):
        self.base_url = "https://visual.volcengineapi.com"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "width": ("INT", {"default": 1328, "min": 512, "max": 3024, "step": 8}),
                "height": ("INT", {"default": 1328, "min": 512, "max": 3024, "step": 8}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "use_pre_llm": ("BOOLEAN", {"default": True}),
                "poll_interval_ms": ("INT", {"default": 1000, "min": 200, "max": 10000, "step": 100}),
                "poll_timeout_ms": ("INT", {"default": 120000, "min": 1000, "max": 600000, "step": 1000}),
                "return_url": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "req_json": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "result")
    FUNCTION = "generate"
    CATEGORY = "Bt-ArtifactGround"

    def get_comfyui_user_setting(self, key, default=None):
        req = FakeRequest()
        all_settings = user_settings.get_settings(req)
        return all_settings.get(key, default)

    def _build_settings(self):
        return {
            "access_key": self.get_comfyui_user_setting("BtArtifactGround.volc.accessKeyId", ""),
            "secret_key": self.get_comfyui_user_setting("BtArtifactGround.volc.secretAccessKey", ""),
            "region": self.get_comfyui_user_setting("BtArtifactGround.volc.region", "cn-north-1"),
            "service": self.get_comfyui_user_setting("BtArtifactGround.volc.service", "cv"),
            "endpoint": self.get_comfyui_user_setting("BtArtifactGround.volc.endpoint", self.base_url),
            "timeout_ms": self.get_comfyui_user_setting("BtArtifactGround.volc.timeout", 30000),
        }

    def _sha256_hex(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _hmac_sha256(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _quote(self, value: str) -> str:
        return urllib.parse.quote(value, safe="-_.~")

    def _canonical_query(self, params: dict) -> str:
        items = []
        for key in sorted(params.keys()):
            value = params[key]
            if value is None:
                continue
            items.append(f"{self._quote(str(key))}={self._quote(str(value))}")
        return "&".join(items)

    def _build_auth_headers(self, method: str, path: str, query: dict, body: bytes, settings: dict):
        now = datetime.datetime.utcnow()
        x_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        host = urllib.parse.urlparse(settings["endpoint"]).netloc
        content_type = "application/json"
        payload_hash = self._sha256_hex(body)

        canonical_query = self._canonical_query(query)
        canonical_headers = "\n".join(
            [
                f"content-type:{content_type}",
                f"host:{host}",
                f"x-content-sha256:{payload_hash}",
                f"x-date:{x_date}",
            ]
        ) + "\n"
        signed_headers = "content-type;host;x-content-sha256;x-date"
        canonical_request = "\n".join(
            [
                method,
                path,
                canonical_query,
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )

        credential_scope = f"{date_stamp}/{settings['region']}/{settings['service']}/request"
        string_to_sign = "\n".join(
            [
                "HMAC-SHA256",
                x_date,
                credential_scope,
                self._sha256_hex(canonical_request.encode("utf-8")),
            ]
        )

        k_date = self._hmac_sha256(settings["secret_key"].encode("utf-8"), date_stamp)
        k_region = hmac.new(k_date, settings["region"].encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, settings["service"].encode("utf-8"), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"HMAC-SHA256 Credential={settings['access_key']}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Content-Type": content_type,
            "Host": host,
            "X-Date": x_date,
            "X-Content-Sha256": payload_hash,
            "Authorization": authorization,
        }
        return headers

    async def _post(self, action: str, body: dict, settings: dict):
        query = {"Action": action, "Version": "2022-08-31"}
        body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = self._build_auth_headers("POST", "/", query, body_bytes, settings)

        url = f"{settings['endpoint'].rstrip('/')}/?{self._canonical_query(query)}"
        timeout = aiohttp.ClientTimeout(total=settings["timeout_ms"] / 1000)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=body_bytes, headers=headers) as response:
                text = await response.text()
                if response.status != 200:
                    return None, f"HTTP错误: {response.status} - {text}"
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    return None, f"响应解析失败: {text}"
                return data, None

    async def _submit_task(self, prompt, width, height, seed, use_pre_llm, settings):
        body = {
            "req_key": "jimeng_t2i_v31",
            "prompt": prompt,
            "seed": seed,
        }
        if width and height:
            body["width"] = width
            body["height"] = height
        if use_pre_llm is not None:
            body["use_pre_llm"] = use_pre_llm

        data, error = await self._post("CVSync2AsyncSubmitTask", body, settings)
        if error:
            return None, error
        if data.get("code") != 10000:
            return None, f"提交任务失败: {data.get('message', '未知错误')}"
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return None, "未获取到task_id"
        return task_id, None

    async def _query_task(self, task_id, settings, req_json=None):
        body = {
            "req_key": "jimeng_t2i_v31",
            "task_id": task_id,
        }
        if req_json:
            body["req_json"] = req_json

        data, error = await self._post("CVSync2AsyncGetResult", body, settings)
        if error:
            return None, error
        if data.get("code") != 10000:
            return None, f"查询任务失败: {data.get('message', '未知错误')}"
        return data.get("data", {}), None

    async def _fetch_image_bytes(self, session: aiohttp.ClientSession, url: str):
        async with session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"图片下载失败: {response.status}")
            return await response.read()

    async def _collect_images(self, result_data):
        images = []
        if result_data.get("binary_data_base64"):
            for item in result_data["binary_data_base64"]:
                data = base64.b64decode(item)
                img = Image.open(io.BytesIO(data)).convert("RGB")
                images.append(img)
        elif result_data.get("image_urls"):
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for url in result_data["image_urls"]:
                    data = await self._fetch_image_bytes(session, url)
                    img = Image.open(io.BytesIO(data)).convert("RGB")
                    images.append(img)
        return images

    def _pil_to_tensor(self, image: Image.Image):
        array = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(array)[None, ...]

    def _run_async(self, coro):
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_in_new_loop, coro)
                return future.result()
        except RuntimeError:
            return self._run_in_new_loop(coro)

    def _run_in_new_loop(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def generate(
        self,
        prompt,
        width,
        height,
        seed,
        use_pre_llm,
        poll_interval_ms,
        poll_timeout_ms,
        return_url,
        req_json="",
    ):
        settings = self._build_settings()
        if not settings["access_key"] or not settings["secret_key"]:
            return (torch.zeros((1, 64, 64, 3)), "未配置火山引擎AccessKeyId/SecretAccessKey")

        if return_url and not req_json:
            req_json = json.dumps({"return_url": True}, ensure_ascii=False)

        task_id, error = self._run_async(
            self._submit_task(prompt, width, height, seed, use_pre_llm, settings)
        )
        if error:
            return (torch.zeros((1, 64, 64, 3)), error)

        deadline = time.monotonic() + poll_timeout_ms / 1000.0

        while True:
            result_data, query_error = self._run_async(self._query_task(task_id, settings, req_json))
            if query_error:
                return (torch.zeros((1, 64, 64, 3)), query_error)

            status = result_data.get("status")
            if status == "done":
                images = self._run_async(self._collect_images(result_data))
                if not images:
                    return (torch.zeros((1, 64, 64, 3)), "未返回图片数据")
                tensors = [self._pil_to_tensor(img) for img in images]
                batch = torch.cat(tensors, dim=0)
                result = {
                    "task_id": task_id,
                    "status": status,
                    "image_count": len(images),
                    "image_urls": result_data.get("image_urls"),
                }
                return (batch, json.dumps(result, ensure_ascii=False))

            if status in {"not_found", "expired"}:
                return (torch.zeros((1, 64, 64, 3)), f"任务状态异常: {status}")

            if time.monotonic() > deadline:
                return (torch.zeros((1, 64, 64, 3)), "任务超时未完成")

            time.sleep(poll_interval_ms / 1000.0)
