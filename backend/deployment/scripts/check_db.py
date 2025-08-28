#!/usr/bin/env python3
"""
数据库检查脚本
用于检查数据库中的用户数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models.database_models import WebUser, WebTradingAccount, WebOrder, WebTrade, WebPosition, WebStrategy

def check_database():
    """检查数据库中的数据"""
    try:
        db = next(get_db())
        
        print("🔍 检查数据库中的数据...")
        print("=" * 50)
        
        # 检查用户数据
        users = db.query(WebUser).all()
        print(f"👥 用户数量: {len(users)}")
        if users:
            print("用户列表:")
            for user in users:  # 显示所有用户
                print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}")
        else:
            print("  ❌ 没有找到用户数据")
        
        print()
        
        # 检查交易账户
        accounts = db.query(WebTradingAccount).all()
        print(f"💼 交易账户数量: {len(accounts)}")
        if accounts:
            print("交易账户列表:")
            for account in accounts[:5]:
                print(f"  - ID: {account.id}, 用户ID: {account.user_id}, 账户名: {account.account_name}")
        else:
            print("  ❌ 没有找到交易账户数据")
        
        print()
        
        # 检查订单
        orders = db.query(WebOrder).all()
        print(f"📋 订单数量: {len(orders)}")
        
        # 检查交易记录
        trades = db.query(WebTrade).all()
        print(f"💰 交易记录数量: {len(trades)}")
        
        # 检查持仓
        positions = db.query(WebPosition).all()
        print(f"📊 持仓数量: {len(positions)}")
        
        # 检查策略
        strategies = db.query(WebStrategy).all()
        print(f"🤖 策略数量: {len(strategies)}")
        
        print("=" * 50)
        
        if not users:
            print("⚠️  警告: 数据库中没有用户数据!")
            print("建议运行初始化脚本来创建演示数据")
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
