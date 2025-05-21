from aiohttp import web
import logging
from datetime import datetime
from .database.manager import db_manager

routes = web.RouteTableDef()

@routes.post('/bt/artifacts/list')
async def handle_artifacts_list(request: web.Request):
    """处理历史记录列表请求"""
    try:
        # 获取请求参数
        data = await request.json()
        date = data.get('date', '')
        status = data.get('status', '')
        limit = int(data.get('limit', 20))
        offset = int(data.get('offset', 0))
        
        # 获取数据库记录
        artifacts = db_manager.artifact.list_artifacts(
            limit=limit,
            offset=offset,
            date=date,
            status=status
        )
        
        # 获取总数
        total = db_manager.artifact.count_artifacts(date=date, status=status)
        
        return web.json_response({
            'code': 0,
            'msg': 'success',
            'data': {
                'list': artifacts,
                'total': total,
                'page': offset // limit + 1,
                'pageSize': limit
            }
        })
    except Exception as e:
        logging.error(f"获取历史记录失败: {str(e)}")
        return web.json_response({
            'code': 500,
            'msg': str(e),
            'data': None
        })

# @routes.get('/bt/artifacts/{id}')
# async def handle_artifact_detail(request: web.Request):
#     """处理单条记录详情请求"""
#     try:
#         artifact_id = request.match_info['id']
#         artifact = db_manager.artifact.get_artifact(artifact_id)
        
#         if not artifact:
#             return web.json_response({
#                 'code': 404,
#                 'msg': '记录不存在',
#                 'data': None
#             })
            
#         return web.json_response({
#             'code': 0,
#             'msg': 'success',
#             'data': artifact
#         })
#     except Exception as e:
#         logging.error(f"获取记录详情失败: {str(e)}")
#         return web.json_response({
#             'code': 500,
#             'msg': str(e),
#             'data': None
#         }) 