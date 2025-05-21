import json
from typing import Optional, List, Dict, Any
from ..base import BaseDB

class ArtifactDB(BaseDB):
    def init_db(self) -> None:
        """初始化数据库，创建必要的表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 创建新表结构（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comfyui_bt_artifact (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id TEXT UNIQUE NOT NULL,  -- 唯一的提示词ID
                    meta TEXT,           -- 存储元数据，JSON格式
                    outputs TEXT,        -- 存储输出数据，JSON格式
                    status TEXT,         -- 存储状态信息，JSON格式
                    prompt TEXT,         -- 存储提示词数据，JSON格式
                    result_status TEXT DEFAULT '0',  -- 结果状态：0-处理中 1-已完成 2-错误
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 创建prompt_id索引
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_id ON comfyui_bt_artifact(prompt_id)')
            conn.commit()

    def save_artifact(self, prompt_id: str, meta: dict = None, outputs: dict = None, 
                     status: dict = None, prompt: dict = None, result_status: str = '0') -> int:
        """保存生成记录到数据库
        
        Args:
            prompt_id: 唯一的提示词ID
            meta: 元数据字典
            outputs: 输出数据字典
            status: 状态信息字典
            prompt: 提示词数据字典
            result_status: 结果状态，0-处理中 1-已完成
            
        Returns:
            int: 插入记录的ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comfyui_bt_artifact (prompt_id, meta, outputs, status, prompt, result_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                prompt_id,
                json.dumps(meta or {}),
                json.dumps(outputs or {}),
                json.dumps(status or {}),
                json.dumps(prompt or {}),
                result_status
            ))
            conn.commit()
            return cursor.lastrowid

    def update_result_status(self, prompt_id: str, result_status: str) -> bool:
        """更新结果状态
        
        Args:
            prompt_id: 提示词ID
            result_status: 新的状态值
            
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE comfyui_bt_artifact 
                SET result_status = ? 
                WHERE prompt_id = ?
            ''', (result_status, prompt_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_artifact(self, prompt_id: str, meta: dict = None, outputs: dict = None,
                      status: dict = None, prompt: dict = None, result_status: str = None) -> bool:
        """更新记录
        
        Args:
            prompt_id: 提示词ID
            meta: 元数据字典
            outputs: 输出数据字典
            status: 状态信息字典
            prompt: 提示词数据字典
            result_status: 结果状态 0-处理中 1-已完成 2-错误
            
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            params = []
            
            if meta is not None:
                update_fields.append("meta = ?")
                params.append(json.dumps(meta))
            if outputs is not None:
                update_fields.append("outputs = ?")
                params.append(json.dumps(outputs))
            if status is not None:
                update_fields.append("status = ?")
                params.append(json.dumps(status))
            if prompt is not None:
                update_fields.append("prompt = ?")
                params.append(json.dumps(prompt))
            if result_status is not None:
                update_fields.append("result_status = ?")
                params.append(result_status)
                
            if not update_fields:
                return False
                
            # 添加WHERE条件参数
            params.append(prompt_id)
            
            # 构建并执行更新语句
            sql = f'''
                UPDATE comfyui_bt_artifact 
                SET {", ".join(update_fields)}
                WHERE prompt_id = ?
            '''
            cursor.execute(sql, params)
            conn.commit()
            
            return cursor.rowcount > 0

    def get_artifact(self, artifact_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, prompt_id, meta, outputs, status, prompt, result_status, created_at
                FROM comfyui_bt_artifact WHERE id = ?
            ''', (artifact_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'prompt_id': row[1],
                    'meta': json.loads(row[2]) if row[2] else {},
                    'outputs': json.loads(row[3]) if row[3] else {},
                    'status': json.loads(row[4]) if row[4] else {},
                    'prompt': json.loads(row[5]) if row[5] else {},
                    'result_status': row[6],
                    'created_at': row[7]
                }
            return None

    def get_artifact_by_prompt_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """根据prompt_id获取记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, prompt_id, meta, outputs, status, prompt, result_status, created_at
                FROM comfyui_bt_artifact WHERE prompt_id = ?
            ''', (prompt_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'prompt_id': row[1],
                    'meta': json.loads(row[2]) if row[2] else {},
                    'outputs': json.loads(row[3]) if row[3] else {},
                    'status': json.loads(row[4]) if row[4] else {},
                    'prompt': json.loads(row[5]) if row[5] else {},
                    'result_status': row[6],
                    'created_at': row[7]
                }
            return None

    def list_artifacts(self, limit: int = 100, offset: int = 0, date: str = '', status: str = '') -> List[Dict[str, Any]]:
        """获取记录列表
        
        Args:
            limit: 限制返回记录数
            offset: 起始偏移量
            date: 日期过滤（YYYY-MM-DD）
            status: 状态过滤（0,1,2）
            
        Returns:
            list: 记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if date:
                conditions.append("DATE(created_at) = DATE(?)")
                params.append(date)
            if status:
                conditions.append("result_status = ?")
                params.append(status)
                
            # 构建SQL语句
            sql = '''
                SELECT id, prompt_id, meta, outputs, status, prompt, result_status, created_at
                FROM comfyui_bt_artifact
            '''
            
            if conditions:
                sql += f" WHERE {' AND '.join(conditions)}"
            
            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            
            return [{
                'id': row[0],
                'prompt_id': row[1],
                'meta': json.loads(row[2]) if row[2] else {},
                'outputs': json.loads(row[3]) if row[3] else {},
                'status': json.loads(row[4]) if row[4] else {},
                'prompt': json.loads(row[5]) if row[5] else {},
                'result_status': row[6],
                'created_at': row[7]
            } for row in cursor.fetchall()]

    def delete_artifact(self, artifact_id: int) -> bool:
        """删除指定的生成记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comfyui_bt_artifact WHERE id = ?", (artifact_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_artifacts(self, date: str = '', status: str = '') -> int:
        """统计记录总数
        
        Args:
            date: 日期过滤，格式为YYYY-MM-DD
            status: 状态过滤
            
        Returns:
            记录总数
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if date:
            conditions.append("date(created_at) = ?")
            params.append(date)
            
        if status:
            conditions.append("status = ?") 
            params.append(status)
            
        # 拼接SQL
        sql = "SELECT COUNT(*) FROM comfyui_bt_artifact"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        # 执行查询    
        cursor.execute(sql, params)
        count = cursor.fetchone()[0]
        
        conn.close()
        return count 