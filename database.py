import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_path='website_analyzer.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, url, analysis_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO analyses (url, analysis_data) VALUES (?, ?)',
            (url, json.dumps(analysis_data))
        )
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def get_analysis(self, analysis_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM analyses WHERE id = ?',
            (analysis_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'url': result[1],
                'analysis_data': json.loads(result[2]),
                'created_at': result[3]
            }
        return None
    
    def get_recent_analyses(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, url, created_at FROM analyses ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'url': r[1], 'created_at': r[2]} for r in results]