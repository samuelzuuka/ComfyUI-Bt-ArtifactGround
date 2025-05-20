import aiohttp
from aiohttp import web
import server
import logging
import json
import asyncio
from datetime import datetime
from .database.manager import db_manager
from .api import routes

prompt_server = server.PromptServer.instance
app = prompt_server.app

# 记录队列请求、监听成功状态，并保存到数据库

def save_prompt_to_db(prompt_id: str):
    """将prompt信息保存到数据库"""
    try:
        db_manager.artifact.save_artifact(prompt_id,result_status='0')
        logging.info(f"保存prompt {prompt_id} 到数据库成功")
    except Exception as e:
        logging.error(f"保存prompt到数据库失败: {str(e)}")

async def monitor_prompt_status(prompt_id: str):
    """监控prompt状态直到完成"""
    try:
        while True:
            current_queue = prompt_server.prompt_queue.get_current_queue()
            queue_running = current_queue[0]  # [[id, prompt_id], ...]
            queue_pending = current_queue[1]  # [[id, prompt_id], ...]
            
            # 检查当前prompt_id是否在运行队列或等待队列中
            prompt_running = any(item[1] == prompt_id for item in queue_running)
            prompt_pending = any(item[1] == prompt_id for item in queue_pending)
            
            if prompt_running or prompt_pending:
                # 任务还在处理中，继续等待
                logging.info(f"Prompt {prompt_id} 仍在处理中，继续等待...")
                await asyncio.sleep(1)
                continue
                
            # 任务不在队列中，检查历史记录
            history = prompt_server.prompt_queue.get_history(prompt_id)
            if not history:
                logging.error(f"Prompt {prompt_id} 历史生成记录没有找到...")
                break
            
            # 获取该prompt_id的历史记录
            prompt_history = history.get(prompt_id, {})
            if not prompt_history:
                logging.error(f"Prompt {prompt_id} 历史记录为空")
                break

            # 提取需要的数据
            prompt_data = prompt_history.get('prompt')
            outputs_data = prompt_history.get('outputs')
            status_data = prompt_history.get('status')
            meta_data = prompt_history.get('meta')

            # 更新数据库
            try:
                # 准备更新的数据                
                # 获取执行状态
                execution_status = '1'
                # status_str : success, error
                if status_data.get('status_str') == 'error':
                    execution_status = '2'  
                
                # 更新数据库记录
                db_manager.artifact.update_artifact(
                    prompt_id=prompt_id,
                    meta=meta_data,
                    outputs=outputs_data,
                    status=status_data,
                    prompt=prompt_data,
                    result_status=execution_status
                )
                
                logging.info(f"Prompt {prompt_id} 数据更新成功，执行状态: {execution_status}")
                break
            except Exception as e:
                logging.error(f"更新数据库失败: {str(e)}")
                break
    except Exception as e:
        logging.error(f"监控prompt状态失败: {str(e)}")

async def handle_pre_request(request: web.Request):
    """处理请求前的逻辑"""
    try:
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.path,
        }
        logging.info(f"请求信息: {json.dumps(request_info, ensure_ascii=False)}")

        if request.path == '/api/prompt' and request.method == 'POST':
            data = await request.json()
            logging.info(f"请求参数: {json.dumps(data, ensure_ascii=False)}")

    except Exception as e:
        logging.error(f"请求前处理异常: {str(e)}")

async def handle_post_response(request: web.Request, response: web.Response):
    """处理响应后的逻辑"""
    try:
        if request.path == '/api/prompt' and request.method == 'POST':
            logging.info(f"响应信息: {str(response.body)}")
            body = json.loads(response.body)
            if body.__contains__('prompt_id'):
                prompt_id = body.get('prompt_id')
                save_prompt_to_db(prompt_id)
                # 异步启动状态监控
                asyncio.create_task(monitor_prompt_status(prompt_id))
            else:
                logging.error(f"生成任务失败...{json.dumps(body, ensure_ascii=False)}")

        if isinstance(response, web.Response):
            response_info = {
                "status": response.status,
            }
            logging.info(f"响应信息: {json.dumps(response_info, ensure_ascii=False, indent=2)}")
    except Exception as e:
        logging.error(f"响应后处理异常: {str(e)}")

async def process_request(request, handler):
    """Process the request by calling the handler and setting response headers."""
    response = await handler(request)
    if request.path == '/':  # Prevent caching the main page after logout
        response.headers.setdefault('Cache-Control', 'no-cache')
    return response

def query_prompt_history_byid(prompt_id):
    """查询prompt_id对应的prompt"""
    return prompt_server.prompt_queue.get_history(prompt_id=prompt_id)

@web.middleware
async def record_queue_req(request: web.Request, handler):
    try:
        # 请求前处理
        await handle_pre_request(request)
        
        # 处理请求
        response = await handler(request)
        
        # 响应后处理
        await handle_post_response(request, response)
        
        return response
    except Exception as e:
        logging.error(f"中间件处理异常: {str(e)}")
        raise

app.middlewares.append(record_queue_req)

# 注册API路由
app.add_routes(routes)

async def handle_artifacts_list(request: web.Request):
    """处理历史记录列表请求"""
    try:
        # 获取查询参数
        params = request.query
        date = params.get('date', '')
        status = params.get('status', '')
        limit = int(params.get('limit', 20))
        offset = int(params.get('offset', 0))
        
        # 获取数据库记录
        artifacts = db_manager.artifact.list_artifacts(
            limit=limit,
            offset=offset,
            date=date,
            status=status
        )
        
        return web.json_response(artifacts)
    except Exception as e:
        logging.error(f"获取历史记录失败: {str(e)}")
        return web.json_response({"error": str(e)}, status=500)

# 注册路由
app.router.add_get('/bt/artifacts/list', handle_artifacts_list)