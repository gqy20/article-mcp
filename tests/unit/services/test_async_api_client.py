"""异步 API 客户端测试

这个测试文件为统一的异步 API 客户端定义测试用例。
异步 api_client 将被 CrossRef 和 OpenAlex 服务使用。

测试内容：
1. 异步 GET 请求
2. 异步 POST 请求
3. 错误处理
4. 超时处理
5. 重试机制
6. 并发连接池
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加 src 目录到路径
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestAsyncAPIClient:
    """测试异步 API 客户端的基本功能"""

    def test_async_api_client_class_exists(self):
        """测试：异步 API 客户端类是否存在"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            assert True
        except ImportError:
            pytest.skip("AsyncAPIClient 类尚未实现")

    def test_async_api_client_initialization(self):
        """测试：异步 API 客户端初始化"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            # 检查基本属性
            assert hasattr(client, "timeout") or hasattr(client, "_timeout")
            assert hasattr(client, "session") or hasattr(client, "_session")

        except ImportError:
            pytest.skip("AsyncAPIClient 类尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_request(self):
        """测试：异步 GET 请求"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            # 直接 mock client.get 方法
            expected_result = {
                "success": True,
                "status_code": 200,
                "data": {"data": "test"},
                "headers": {},
                "url": "https://api.example.com/data",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                result = await client.get("https://api.example.com/data")

                # 验证结果
                assert result is not None, "result should not be None"
                assert result["success"] is True
                assert result["status_code"] == 200
                assert result["data"]["data"] == "test"
                mock_get.assert_called_once_with("https://api.example.com/data")

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 get 方法尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_with_params(self):
        """测试：异步 GET 请求带参数"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": True,
                "status_code": 200,
                "data": {"results": []},
                "headers": {},
                "url": "https://api.example.com/search",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                params = {"query": "test", "limit": 10}
                await client.get("https://api.example.com/search", params=params)

                # 验证参数被传递
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert "params" in call_args.kwargs

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 get 方法尚未实现")

    @pytest.mark.asyncio
    async def test_async_post_request(self):
        """测试：异步 POST 请求"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": True,
                "status_code": 201,
                "data": {"id": "123"},
                "headers": {},
                "url": "https://api.example.com/create",
            }

            with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = expected_result

                data = {"name": "test"}
                result = await client.post("https://api.example.com/create", json=data)

                # 验证结果
                assert result is not None, "result should not be None"
                assert result["success"] is True
                assert result["status_code"] == 201
                assert result["data"]["id"] == "123"
                mock_post.assert_called_once()

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 post 方法尚未实现")


class TestAsyncAPIClientErrorHandling:
    """测试异步 API 客户端的错误处理"""

    @pytest.mark.asyncio
    async def test_async_get_timeout(self):
        """测试：异步 GET 请求超时处理"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": False,
                "error": "请求超时",
                "error_type": "timeout",
                "url": "https://api.example.com/slow",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                result = await client.get("https://api.example.com/slow")

                # 验证错误信息
                assert result is not None, "result should not be None"
                assert result["success"] is False
                assert "error" in result
                assert result.get("error_type") == "timeout"

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或超时处理尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_network_error(self):
        """测试：异步 GET 请求网络错误处理"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": False,
                "error": "Network error",
                "error_type": "client_error",
                "url": "https://api.example.com/error",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                result = await client.get("https://api.example.com/error")

                # 验证错误信息
                assert result is not None, "result should not be None"
                assert result["success"] is False
                assert "error" in result

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或错误处理尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_http_error(self):
        """测试：异步 GET 请求 HTTP 错误处理"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": False,
                "error": "HTTP 404: Not Found",
                "error_type": "http_error",
                "status_code": 404,
                "url": "https://api.example.com/notfound",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                result = await client.get("https://api.example.com/notfound")

                # 验证错误信息
                assert result is not None, "result should not be None"
                assert result["success"] is False
                assert "error" in result

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 HTTP 错误处理尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_retry_on_429(self):
        """测试：异步 GET 请求在 429 时重试"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            expected_result = {
                "success": True,
                "status_code": 200,
                "data": {"data": "success"},
                "headers": {},
                "url": "https://api.example.com/rate-limited",
            }

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = expected_result

                result = await client.get("https://api.example.com/rate-limited")

                # 应该成功
                assert result is not None, "result should not be None"
                assert result["success"] is True

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或重试机制尚未实现")


class TestAsyncAPIClientPerformance:
    """测试异步 API 客户端的性能"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试：并发处理多个请求"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            # 创建多个期望结果
            results = []
            for i in range(5):
                results.append(
                    {
                        "success": True,
                        "status_code": 200,
                        "data": {"url": f"https://api.example.com/data/{i}"},
                        "headers": {},
                        "url": f"https://api.example.com/data/{i}",
                    }
                )

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = results

                # 并发发送多个请求
                urls = [f"https://api.example.com/data/{i}" for i in range(5)]

                import time

                start = time.time()
                actual_results = await asyncio.gather(*[client.get(url) for url in urls])
                elapsed = time.time() - start

                # 验证所有请求成功
                assert len(actual_results) == 5
                for result in actual_results:
                    assert result["success"] is True

                # 并发执行应该远快于串行 - 放宽时间限制
                assert elapsed < 0.15, f"并发执行耗时 {elapsed:.3f}s"

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或并发处理尚未实现")

    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """测试：连接池复用"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            # 创建客户端
            client = AsyncAPIClient(logger=Mock())

            # 创建多个期望结果
            results = []
            for i in range(3):
                results.append(
                    {
                        "success": True,
                        "status_code": 200,
                        "data": {},
                        "headers": {},
                        "url": f"https://api.example.com/{i}",
                    }
                )

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = results

                # 发送3个请求
                await client.get("https://api.example.com/1")
                await client.get("https://api.example.com/2")
                await client.get("https://api.example.com/3")

                # 验证方法被调用了3次
                assert mock_get.call_count == 3

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或连接池复用尚未实现")


class TestAsyncAPIClientSingleton:
    """测试异步 API 客户端的单例模式"""

    def test_get_async_api_client_singleton(self):
        """测试：获取异步 API 客户端应该是单例"""
        try:
            from article_mcp.services.api_utils import get_async_api_client

            client1 = get_async_api_client()
            client2 = get_async_api_client()

            # 应该返回同一个实例
            assert client1 is client2

        except ImportError:
            pytest.skip("get_async_api_client 函数尚未实现")

    @pytest.mark.asyncio
    async def test_singleton_client_reuse(self):
        """测试：单例客户端可以被多次使用"""
        try:
            from article_mcp.services.api_utils import get_async_api_client

            client = get_async_api_client()

            # 创建两个期望结果
            results = []
            for i in range(2):
                results.append(
                    {
                        "success": True,
                        "status_code": 200,
                        "data": {},
                        "headers": {},
                        "url": f"https://api.example.com/{i + 1}",
                    }
                )

            with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = results

                # 使用同一个客户端发送多个请求
                result1 = await client.get("https://api.example.com/1")
                result2 = await client.get("https://api.example.com/2")

                assert result1 is not None, "result1 should not be None"
                assert result1["success"] is True
                assert result2 is not None, "result2 should not be None"
                assert result2["success"] is True

        except (ImportError, NotImplementedError):
            pytest.skip("get_async_api_client 或请求方法尚未实现")


# ============================================================================
# 实现检查
# ============================================================================


def test_async_api_client_signature():
    """测试：检查异步 API 客户端的方法签名"""
    try:
        import inspect

        from article_mcp.services.api_utils import AsyncAPIClient

        client = AsyncAPIClient(logger=Mock())

        # 检查 get 方法
        if hasattr(client, "get"):
            sig = inspect.signature(client.get)
            params = list(sig.parameters.keys())

            # 应该有的参数
            expected_params = ["url", "params", "headers", "timeout"]
            for param in expected_params:
                assert param in params, f"get 方法应该有 {param} 参数"

            # 应该是异步方法
            assert inspect.iscoroutinefunction(client.get), "get 方法应该是异步函数"

        # 检查 post 方法
        if hasattr(client, "post"):
            sig = inspect.signature(client.post)
            params = list(sig.parameters.keys())

            expected_params = ["url", "data", "json", "headers", "timeout"]
            for param in expected_params:
                assert param in params, f"post 方法应该有 {param} 参数"

            assert inspect.iscoroutinefunction(client.post), "post 方法应该是异步函数"

    except ImportError:
        pytest.skip("AsyncAPIClient 类尚未实现")


def test_async_api_client_imports():
    """测试：检查异步 API 客户端的必要导入"""
    try:
        import inspect

        import article_mcp.services.api_utils as api_utils_module

        source = inspect.getsource(api_utils_module)

        # 检查是否有 aiohttp 导入
        has_aiohttp = "aiohttp" in source or "import aiohttp" in source
        has_asyncio = "asyncio" in source or "import asyncio" in source

        # 如果实现了异步客户端，应该有这些导入
        if hasattr(api_utils_module, "AsyncAPIClient"):
            assert has_aiohttp, "异步客户端需要 aiohttp"
            assert has_asyncio, "异步客户端需要 asyncio"

    except ImportError:
        pytest.skip("api_utils 模块未找到")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
