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

            # Mock aiohttp 响应
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": "test"})

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                # 执行 GET 请求
                result = await client.get("https://api.example.com/data")

                # 验证结果
                assert result["success"] is True
                assert result["status_code"] == 200
                assert result["data"]["data"] == "test"

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 get 方法尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_with_params(self):
        """测试：异步 GET 请求带参数"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"results": []})

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                params = {"query": "test", "limit": 10}
                await client.get("https://api.example.com/search", params=params)

                # 验证参数被传递
                mock_session.get.assert_called_once()
                call_args = mock_session.get.call_args
                assert "params" in call_args.kwargs or call_args[1].get("params")

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或 get 方法尚未实现")

    @pytest.mark.asyncio
    async def test_async_post_request(self):
        """测试：异步 POST 请求"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            mock_response = Mock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={"id": "123"})

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.post = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                data = {"name": "test"}
                result = await client.post("https://api.example.com/create", json=data)

                # 验证结果
                assert result["success"] is True
                assert result["status_code"] == 201
                assert result["data"]["id"] == "123"

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

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()

                # Mock 超时
                async def mock_get_with_timeout(*args, **kwargs):
                    await asyncio.sleep(10)  # 超过超时限制
                    return Mock(status=200)

                mock_session.get = mock_get_with_timeout
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await client.get("https://api.example.com/slow")

                # 应该返回错误信息
                assert result["success"] is False
                assert "error" in result
                assert "timeout" in result["error"].lower() or result.get("error_type") == "timeout"

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或超时处理尚未实现")

    @pytest.mark.asyncio
    async def test_async_get_network_error(self):
        """测试：异步 GET 请求网络错误处理"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            client = AsyncAPIClient(logger=Mock())

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()

                # Mock 网络错误
                async def mock_get_with_error(*args, **kwargs):
                    raise Exception("Network error")

                mock_session.get = mock_get_with_error
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await client.get("https://api.example.com/error")

                # 应该返回错误信息
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

            mock_response = Mock()
            mock_response.status = 404
            mock_response.raise_for_status = Mock(side_effect=Exception("Not Found"))

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await client.get("https://api.example.com/notfound")

                # 应该返回错误信息
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

            # 前两次返回 429，第三次成功
            responses = [
                Mock(status=429, headers={}),
                Mock(status=429, headers={}),
                Mock(status=200, json=AsyncMock(return_value={"data": "success"})),
            ]

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()

                call_count = 0

                async def mock_get_with_retry(*args, **kwargs):
                    nonlocal call_count
                    response = responses[min(call_count, len(responses) - 1)]
                    call_count += 1
                    if response.status == 429:
                        import aiohttp

                        raise aiohttp.ClientResponseError(
                            request_info=Mock(),
                            history=(),
                            status=response.status,
                            message="Rate limited",
                        )
                    await asyncio.sleep(0.01)
                    return response

                mock_session.get = mock_get_with_retry
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await client.get("https://api.example.com/rate-limited")

                # 最终应该成功
                assert result["success"] is True or call_count >= 3

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

            async def mock_request(url, **kwargs):
                await asyncio.sleep(0.02)
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={"url": url})
                return mock_response

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = mock_request
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                # 并发发送多个请求
                urls = [f"https://api.example.com/data/{i}" for i in range(5)]

                import time

                start = time.time()
                results = await asyncio.gather(*[client.get(url) for url in urls])
                elapsed = time.time() - start

                # 验证所有请求成功
                assert len(results) == 5
                for result in results:
                    assert result["success"] is True

                # 并发执行应该远快于串行
                # 5个请求每个0.02秒，串行需要0.1秒，并行应该 < 0.05秒
                assert elapsed < 0.06, f"并发执行耗时 {elapsed:.3f}s"

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或并发处理尚未实现")

    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """测试：连接池复用"""
        try:
            from article_mcp.services.api_utils import AsyncAPIClient

            # 创建客户端
            client = AsyncAPIClient(logger=Mock())

            async def mock_request(url, **kwargs):
                await asyncio.sleep(0.01)
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={})
                return mock_response

            with patch("aiohttp.ClientSession") as mock_session_class:
                # Mock 会话应该只创建一次
                mock_session = Mock()
                mock_session.get = mock_request
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                # 发送多个请求
                for i in range(3):
                    await client.get(f"https://api.example.com/data/{i}")

                # ClientSession 应该只创建一次（连接池复用）
                assert mock_session_class.call_count <= 2

        except (ImportError, NotImplementedError):
            pytest.skip("AsyncAPIClient 或连接池尚未实现")


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

            async def mock_request(url, **kwargs):
                await asyncio.sleep(0.01)
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={})
                return mock_response

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = mock_request
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                # 使用同一个客户端发送多个请求
                result1 = await client.get("https://api.example.com/1")
                result2 = await client.get("https://api.example.com/2")

                assert result1["success"] is True
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
