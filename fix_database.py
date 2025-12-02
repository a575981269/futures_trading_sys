"""
修复数据库索引冲突
"""
import os
import sqlite3
from pathlib import Path

def fix_database():
    """修复数据库索引冲突"""
    # 数据库路径
    db_path = Path('data/futures.db')
    
    if not db_path.exists():
        print("数据库文件不存在，无需修复")
        return True
    
    print(f"正在修复数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"发现 {len(indexes)} 个索引")
        
        # 删除可能冲突的旧索引
        old_indexes = ['idx_datetime', 'idx_symbol_datetime', 'idx_symbol_interval_datetime']
        deleted = []
        
        for idx_name in old_indexes:
            if idx_name in indexes:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
                    deleted.append(idx_name)
                    print(f"  ✓ 删除旧索引: {idx_name}")
                except Exception as e:
                    print(f"  ✗ 删除索引失败 {idx_name}: {e}")
        
        conn.commit()
        conn.close()
        
        if deleted:
            print(f"\n✅ 已删除 {len(deleted)} 个旧索引")
            print("请重新运行测试，系统会自动创建新的索引")
        else:
            print("\n✅ 未发现需要删除的旧索引")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复数据库失败: {e}")
        print("\n建议：删除 data/futures.db 文件后重新运行")
        return False

def delete_database():
    """删除数据库文件（重新开始）"""
    db_path = Path('data/futures.db')
    
    if db_path.exists():
        try:
            db_path.unlink()
            print(f"✅ 已删除数据库文件: {db_path}")
            return True
        except Exception as e:
            print(f"❌ 删除数据库文件失败: {e}")
            return False
    else:
        print("数据库文件不存在")
        return True

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("数据库修复工具")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        # 删除数据库
        print("\n⚠️  警告：将删除整个数据库文件！")
        confirm = input("确认删除？(yes/no): ")
        if confirm.lower() == "yes":
            delete_database()
        else:
            print("已取消")
    else:
        # 修复索引
        fix_database()
    
    print("\n" + "=" * 60)

