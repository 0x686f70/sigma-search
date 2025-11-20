import sqlite3
import os
import threading
from datetime import datetime

class DeploymentManager:
    def __init__(self, db_path="sigma_deployments.db"):
        """
        Quản lý trạng thái triển khai Sigma rules với SQLite database
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database và bảng deployments"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS deployments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_file_path TEXT UNIQUE NOT NULL,
                        rule_title TEXT,
                        is_deployed BOOLEAN DEFAULT FALSE,
                        deployed_at TIMESTAMP,
                        deployment_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tạo index để tăng hiệu suất tìm kiếm
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_rule_file_path 
                    ON deployments(rule_file_path)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_is_deployed 
                    ON deployments(is_deployed)
                """)
                
                conn.commit()
    
    def get_deployment_status(self, rule_file_path):
        """
        Lấy trạng thái triển khai của một rule
        
        Args:
            rule_file_path (str): Đường dẫn file rule
            
        Returns:
            dict: Thông tin triển khai hoặc None nếu chưa có
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM deployments 
                    WHERE rule_file_path = ?
                """, (rule_file_path,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
    
    def update_deployment_status(self, rule_file_path, rule_title, is_deployed, notes=""):
        """
        Cập nhật trạng thái triển khai của một rule
        
        Args:
            rule_file_path (str): Đường dẫn file rule
            rule_title (str): Tiêu đề rule
            is_deployed (bool): Trạng thái triển khai
            notes (str): Ghi chú thêm
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                deployed_at = datetime.now().isoformat() if is_deployed else None
                
                # Sử dụng INSERT OR REPLACE để update hoặc insert
                conn.execute("""
                    INSERT OR REPLACE INTO deployments 
                    (rule_file_path, rule_title, is_deployed, deployed_at, deployment_notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (rule_file_path, rule_title, is_deployed, deployed_at, notes, datetime.now().isoformat()))
                
                conn.commit()
    
    def get_all_deployments(self):
        """
        Lấy tất cả trạng thái triển khai
        
        Returns:
            list: Danh sách các deployment
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM deployments 
                    ORDER BY updated_at DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
    
    def get_deployed_rules(self):
        """
        Lấy danh sách các rule đã triển khai
        
        Returns:
            list: Danh sách file_path của các rule đã deploy
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT rule_file_path FROM deployments 
                    WHERE is_deployed = TRUE
                """)
                return [row[0] for row in cursor.fetchall()]
    
    def get_deployment_stats(self):
        """
        Lấy thống kê triển khai
        
        Returns:
            dict: Thống kê số lượng deployed/total
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_deployed = TRUE THEN 1 ELSE 0 END) as deployed
                    FROM deployments
                """)
                row = cursor.fetchone()
                return {
                    'total': row[0] if row[0] else 0,
                    'deployed': row[1] if row[1] else 0
                }
    
    def clean_old_entries(self, existing_file_paths):
        """
        Xóa các entry của các rule file không còn tồn tại
        
        Args:
            existing_file_paths (list): Danh sách file_path hiện tại
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                if existing_file_paths:
                    placeholders = ','.join(['?' for _ in existing_file_paths])
                    conn.execute(f"""
                        DELETE FROM deployments 
                        WHERE rule_file_path NOT IN ({placeholders})
                    """, existing_file_paths)
                else:
                    # Nếu không có rule nào, xóa tất cả
                    conn.execute("DELETE FROM deployments")
                
                conn.commit() 