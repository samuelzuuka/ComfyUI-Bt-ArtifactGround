from .models import ArtifactDB

class DBManager:
    def __init__(self):
        self.artifact = ArtifactDB()
        self.artifact.init_db()

# 创建全局数据库管理器实例
db_manager = DBManager() 