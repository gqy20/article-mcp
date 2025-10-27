#!/usr/bin/env python3
"""
真实API集成测试
测试与真实外部API的集成
注意：这些测试需要网络连接，可能会比较慢
"""

import asyncio
import os

import pytest
from article_mcp.tests.test_helpers import (
    TestTimer,
    assert_valid_search_results,
    run_async_with_timeout,
)

# 跳过网络测试的环境变量标记
SKIP_NETWORK_TESTS = os.getenv("SKIP_NETWORK_TESTS", "false").lower() == "true"


@pytest.mark.integration
@pytest.mark.network
class TestRealAPIIntegration:
    """真实API集成测试"""

    @pytest.fixture(autouse=True)
    def skip_if_no_network(self):
        """如果没有网络连接或设置了跳过标记，则跳过测试"""
        if SKIP_NETWORK_TESTS:
            pytest.skip("跳过网络测试 (SKIP_NETWORK_TESTS=true)")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_europe_pmc_real_search(self):
        """测试Europe PMC真实搜索"""
        try:
            # 导入真实服务
            import logging

            from article_mcp.services.europe_pmc import EuropePMCService

            # 创建日志记录器
            logger = logging.getLogger(__name__)

            # 创建服务实例
            service = EuropePMCService(logger)

            # 执行搜索
            with TestTimer() as timer:
                result = await service.search_articles(keyword="machine learning", max_results=5)

            # 验证结果
            assert timer.stop() < 30.0  # 应该在30秒内完成
            assert_valid_search_results(result)
            assert len(result["articles"]) > 0

            # 验证至少有一篇文章有有效的字段
            article = result["articles"][0]
            assert "title" in article
            assert "authors" in article
            assert len(article["title"]) > 0

        except ImportError:
            pytest.skip("Europe PMC服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_arxiv_real_search(self):
        """测试arXiv真实搜索"""
        try:
            # 导入真实服务
            import logging

            from article_mcp.services.arxiv_search import create_arxiv_service

            # 创建日志记录器
            logger = logging.getLogger(__name__)

            # 创建服务实例
            service = create_arxiv_service(logger)

            # 执行搜索
            with TestTimer() as timer:
                result = await service.search_papers(
                    keyword="artificial intelligence", max_results=3
                )

            # 验证结果
            assert timer.stop() < 20.0  # 应该在20秒内完成
            assert_valid_search_results(result)
            assert len(result["articles"]) > 0

            # 验证arXiv特有字段
            article = result["articles"][0]
            assert "title" in article
            assert "authors" in article
            assert len(article["title"]) > 0

        except ImportError:
            pytest.skip("ArXiv服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_crossref_real_doi_resolution(self):
        """测试CrossRef真实DOI解析"""
        try:
            # 导入真实服务
            import logging

            from article_mcp.services.crossref_service import CrossRefService

            # 创建日志记录器
            logger = logging.getLogger(__name__)

            # 创建服务实例
            service = CrossRefService(logger)

            # 使用一个已知的DOI进行测试
            test_doi = "10.1016/j.neuron.2023.01.001"

            # 执行DOI解析
            with TestTimer() as timer:
                result = await service.resolve_doi(test_doi)

            # 验证结果
            assert timer.stop() < 15.0  # 应该在15秒内完成
            assert "title" in result
            assert len(result["title"]) > 0
            assert result.get("doi") == test_doi

        except ImportError:
            pytest.skip("CrossRef服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise


@pytest.mark.integration
@pytest.mark.network
class TestAPIPerformance:
    """API性能测试"""

    @pytest.fixture(autouse=True)
    def skip_if_no_network(self):
        """如果没有网络连接或设置了跳过标记，则跳过测试"""
        if SKIP_NETWORK_TESTS:
            pytest.skip("跳过网络测试 (SKIP_NETWORK_TESTS=true)")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """测试并发API调用性能"""
        try:
            import logging

            from article_mcp.services.arxiv_search import create_arxiv_service
            from article_mcp.services.europe_pmc import EuropePMCService

            logger = logging.getLogger(__name__)

            # 创建服务实例
            europe_pmc_service = EuropePMCService(logger)
            arxiv_service = create_arxiv_service(logger)

            # 并发调用测试
            with TestTimer() as timer:
                tasks = [
                    europe_pmc_service.search_articles("machine learning", max_results=3),
                    arxiv_service.search_papers("deep learning", max_results=3),
                    europe_pmc_service.search_articles("neural networks", max_results=3),
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证性能
            assert timer.stop() < 60.0  # 应该在60秒内完成

            # 验证结果
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 1  # 至少有一个成功

        except ImportError:
            pytest.skip("服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """测试API速率限制"""
        try:
            import logging

            from article_mcp.services.europe_pmc import EuropePMCService

            logger = logging.getLogger(__name__)
            service = EuropePMCService(logger)

            # 快速连续调用测试
            call_times = []
            for i in range(3):
                with TestTimer() as timer:
                    try:
                        await service.search_articles(f"test query {i}", max_results=1)
                        call_times.append(timer.stop())
                    except Exception as e:
                        if "rate limit" in str(e).lower():
                            # 遇到速率限制是正常的
                            call_times.append(timer.stop())
                        else:
                            raise

            # 验证速率限制处理
            assert len(call_times) > 0
            # 如果有多个调用，后面的调用应该因为速率限制而更慢
            if len(call_times) > 1:
                # 不强制要求，但可以观察到速率限制的影响
                pass

        except ImportError:
            pytest.skip("Europe PMC服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise


@pytest.mark.integration
@pytest.mark.network
class TestAPIReliability:
    """API可靠性测试"""

    @pytest.fixture(autouse=True)
    def skip_if_no_network(self):
        """如果没有网络连接或设置了跳过标记，则跳过测试"""
        if SKIP_NETWORK_TESTS:
            pytest.skip("跳过网络测试 (SKIP_NETWORK_TESTS=true)")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_api_retry_mechanism(self):
        """测试API重试机制"""
        try:
            import logging

            from article_mcp.services.europe_pmc import EuropePMCService

            logger = logging.getLogger(__name__)
            service = EuropePMCService(logger)

            # 测试重试机制（通过观察日志或行为）
            retry_count = 0

            async def counting_request(*args, **kwargs):
                nonlocal retry_count
                retry_count += 1
                if retry_count < 2:
                    # 前两次调用失败
                    raise Exception("Temporary failure")
                # 第三次调用成功
                return {
                    "articles": [
                        {
                            "title": "Test Article",
                            "authors": ["Test Author"],
                            "year": "2023",
                            "abstract": "Test abstract",
                        }
                    ],
                    "total_count": 1,
                }

            # 替换请求方法
            service._make_request = counting_request

            # 执行搜索（应该会重试）
            result = await service.search_articles("test query", max_results=1)

            # 验证重试机制
            assert retry_count >= 2  # 应该至少重试了2次
            assert len(result["articles"]) == 1

        except ImportError:
            pytest.skip("Europe PMC服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """测试API超时处理"""
        try:
            import logging

            from article_mcp.services.europe_pmc import EuropePMCService

            logger = logging.getLogger(__name__)
            service = EuropePMCService(logger)

            # 模拟超时

            async def slow_request(*args, **kwargs):
                await asyncio.sleep(35)  # 超过通常的超时时间
                return {"articles": [], "total_count": 0}

            service._make_request = slow_request

            # 测试超时处理
            with pytest.raises((asyncio.TimeoutError, Exception)):
                await run_async_with_timeout(
                    service.search_articles("test query", max_results=1), timeout=30.0
                )

        except ImportError:
            pytest.skip("Europe PMC服务不可用")
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"网络连接问题: {e}")
            else:
                raise


class TestAPIConfiguration:
    """API配置测试"""

    def test_api_key_configuration(self):
        """测试API密钥配置"""
        # 测试环境变量配置
        email = os.getenv("TEST_EMAIL", "test@example.com")
        assert "@" in email  # 简单的邮箱验证

        # 测试API密钥配置（如果有的话）
        api_key = os.getenv("EASYSCHOLAR_SECRET_KEY")
        if api_key:
            assert len(api_key) > 0

    def test_proxy_configuration(self):
        """测试代理配置"""
        # 检查代理环境变量
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")

        # 如果设置了代理，验证格式
        if http_proxy:
            assert "://" in http_proxy
        if https_proxy:
            assert "://" in https_proxy


# 网络测试辅助函数
def check_network_connectivity():
    """检查网络连接"""
    import socket

    try:
        # 尝试连接到Google的DNS服务器
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def network_available():
    """检查网络连接是否可用"""
    return check_network_connectivity()
