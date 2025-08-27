#!/usr/bin/env python3
"""
数据库设置脚本
帮助用户配置数据库连接
"""

import os
import sys
from pathlib import Path

def setup_database_config():
    """设置数据库配置"""
    print("🔧 RedFire 数据库配置向导")
    print("=" * 50)
    
    # 获取用户输入
    print("请输入MySQL数据库连接信息：")
    
    db_host = input("数据库主机 (默认: localhost): ").strip() or "localhost"
    db_port = input("数据库端口 (默认: 3306): ").strip() or "3306"
    db_user = input("数据库用户名 (默认: root): ").strip() or "root"
    db_password = input("数据库密码: ").strip()
    db_name = input("数据库名称 (默认: vnpy): ").strip() or "vnpy"
    
    # 构建数据库URL
    if db_password:
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    else:
        database_url = f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    
    print(f"\n📋 数据库连接信息:")
    print(f"主机: {db_host}")
    print(f"端口: {db_port}")
    print(f"用户: {db_user}")
    print(f"数据库: {db_name}")
    print(f"连接URL: {database_url}")
    
    # 测试连接
    print(f"\n🔍 测试数据库连接...")
    
    try:
        import pymysql
        if db_password:
            connection = pymysql.connect(
                host=db_host,
                port=int(db_port),
                user=db_user,
                password=db_password,
                database=db_name,
                charset='utf8mb4'
            )
        else:
            connection = pymysql.connect(
                host=db_host,
                port=int(db_port),
                user=db_user,
                database=db_name,
                charset='utf8mb4'
            )
        
        print("✅ 数据库连接成功！")
        
        # 检查表是否存在
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'web_users' in tables:
                print("✅ web_users表已存在")
                
                # 检查表结构
                cursor.execute("DESCRIBE web_users")
                columns = cursor.fetchall()
                print("📝 web_users表结构:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                    
                # 检查数据
                cursor.execute("SELECT COUNT(*) FROM web_users")
                count = cursor.fetchone()[0]
                print(f"👥 web_users表中有 {count} 条记录")
                
            else:
                print("⚠️ web_users表不存在，将创建表结构")
                
        connection.close()
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查MySQL服务是否启动")
        print("2. 检查用户名和密码是否正确")
        print("3. 检查数据库是否存在")
        print("4. 检查防火墙设置")
        return False
    
    # 创建环境配置文件
    env_content = f"""# RedFire 后端环境配置

# 数据库配置
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}

# 或者直接设置完整的数据库URL
DATABASE_URL={database_url}

# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
"""
    
    env_file = Path(".env")
    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"\n✅ 环境配置文件已保存到: {env_file.absolute()}")
    except Exception as e:
        print(f"❌ 保存配置文件失败: {e}")
        return False
    
    print("\n🎉 数据库配置完成！")
    print("现在可以启动后端服务了:")
    print("python main.py")
    
    return True

def main():
    """主函数"""
    try:
        success = setup_database_config()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ 配置已取消")
        sys.exit(1)

if __name__ == "__main__":
    main()
