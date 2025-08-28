"""
pytest配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_user_data():
    """示例用户数据夹具"""
    return {
        "user_id": "user_123",
        "username": "testuser",
        "email": "test@example.com",
        "phone": "13800138000"
    }


@pytest.fixture
def invalid_user_data():
    """无效用户数据夹具"""
    return {
        "empty_username": "",
        "short_username": "ab",
        "long_username": "a" * 21,
        "invalid_username": "user@123",
        "invalid_email": "invalid-email",
        "invalid_phone": "12800138000"
    }


class AsyncMock:
    """异步Mock辅助类"""
    
    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect
        self.call_count = 0
        self.call_args_list = []
        
    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args_list.append((args, kwargs))
        
        if self.side_effect:
            if callable(self.side_effect):
                return await self.side_effect(*args, **kwargs)
            else:
                raise self.side_effect
                
        return self.return_value
        
    def assert_called_once(self):
        assert self.call_count == 1
        
    def assert_called_once_with(self, *args, **kwargs):
        self.assert_called_once()
        assert self.call_args_list[0] == (args, kwargs)
        
    def assert_not_called(self):
        assert self.call_count == 0


@pytest.fixture
def async_mock():
    """异步Mock夹具"""
    return AsyncMock
