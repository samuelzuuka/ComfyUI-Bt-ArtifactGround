from aiohttp import web
import server
import logging
import json

prompt_server = server.PromptServer.instance
app = prompt_server.app


def command_ui_toast(message:str,title:str,type:str="info",timeout_millis=3000):
    """
    发送消息让前端显示UI提示
    """
    prompt_server.send_sync('bt_toast',{
        "severity": type,
        "summary": title,
        "detail": message,
        "life": timeout_millis
    })

def command_ui_alert(message:str):
    """
    发送消息让前端错误提示
    """
    prompt_server.send_sync('bt_alert',{
        "detail": message,
    })