import os
import sqlite3

class BaseDB:
    def __init__(self):
        # 获取插件目录路径
        plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # 在插件目录下创建data目录
        data_dir = os.path.join(plugin_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        # 设置数据库文件路径
        self.db_path = os.path.join(data_dir, "artifacts.db")
        
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path) 