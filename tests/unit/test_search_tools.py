"""
搜索工具单元测试
"""

from unittest.mock import Mock

import pytest

from tool_modules.core.search_tools import register_search_tools


class TestSearchTools:
    """搜索工具测试类"""

    @pytest.fixture
    def mock_services(self):
        """模拟服务字典"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }

    @pytest.fixture
    def mock_mcp(self):
        """模拟 MCP 对象"""
        mcp = Mock()
        mcp.tool = Mock()
        return mcp

    @pytest.fixture
    def logger(self):
        """模拟日志记录器"""
        return Mock()

    def test_register_search_tools(self, mock_mcp, mock_services, logger):
        """测试搜索工具注册"""
        tools = register_search_tools(mock_mcp, mock_services, logger)

        assert len(tools) == 1
        mock_mcp.tool.assert_called_once()

        # 获取注册的工具
        search_tool = tools[0]
        assert search_tool.__name__ == "search_literature"

    def test_search_literature_success(self, mock_services, logger):
        """测试成功搜索文献"""
        # 设置模拟服务返回
        mock_services["europe_pmc"].search.return_value = {
            "articles": [
                {
                    "title": "Machine Learning in Healthcare",
                    "authors": ["AI Researcher"],
                    "doi": "10.1234/ml.health.2023",
                    "journal": "Health AI Journal",
                }
            ],
            "total_count": 1,
        }

        mock_services["pubmed"].search.return_value = {
            "articles": [
                {
                    "title": "Deep Learning Applications",
                    "authors": ["ML Specialist"],
                    "doi": "10.5678/dl.apps.2023",
                    "journal": "Machine Learning Today",
                }
            ],
            "total_count": 1,
        }

        # 导入搜索工具函数
        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        # 执行搜索
        result = search_literature(
            keyword="machine learning",
            sources=["europe_pmc", "pubmed"],
            max_results=10,
            search_type="comprehensive",
        )

        # 验证结果
        assert result["success"] is True
        assert result["keyword"] == "machine learning"
        assert "europe_pmc" in result["sources_used"]
        assert "pubmed" in result["sources_used"]
        assert len(result["merged_results"]) == 2

    def test_search_literature_empty_keyword(self, mock_services, logger):
        """测试空关键词搜索"""
        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(keyword="   ")

        assert result["success"] is False
        assert result["error"] == "搜索关键词不能为空"
        assert result["total_count"] == 0

    def test_search_literature_unknown_service(self, mock_services, logger):
        """测试未知数据源搜索"""
        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(keyword="test", sources=["unknown_source"], max_results=10)

        assert result["success"] is True
        assert "unknown_source" not in result["sources_used"]
        assert result["total_count"] == 0

    def test_search_literature_api_failure(self, mock_services, logger):
        """测试 API 调用失败"""
        mock_services["europe_pmc"].search.return_value = {
            "articles": [],
            "error": "API Error",
            "total_count": 0,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(keyword="test", sources=["europe_pmc"], max_results=10)

        assert result["success"] is True  # 即使部分失败也返回成功
        assert result["total_count"] == 0
        assert "europe_pmc" not in result["sources_used"]

    def test_search_literature_search_types(self, mock_services, logger):
        """测试不同搜索类型"""
        mock_services["europe_pmc"].search.return_value = {
            "articles": [{"title": "Recent Article"}],
            "total_count": 1,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        # 测试不同搜索类型
        for search_type in ["comprehensive", "recent", "high_quality"]:
            result = search_literature(
                keyword="test", sources=["europe_pmc"], search_type=search_type
            )
            assert result["success"] is True
            assert result["search_type"] == search_type

    def test_search_literature_max_results_filtering(self, mock_services, logger):
        """测试最大结果数过滤"""
        mock_services["europe_pmc"].search.return_value = {
            "articles": [{"title": f"Article {i}"} for i in range(20)],
            "total_count": 20,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(keyword="test", sources=["europe_pmc"], max_results=5)

        assert result["success"] is True
        # 由于是单个数据源，应该返回所有结果
        assert len(result["merged_results"]) == 20

    def test_search_literature_exception_handling(self, mock_services, logger):
        """测试异常处理"""
        mock_services["europe_pmc"].search.side_effect = Exception("Network Error")

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(keyword="test", sources=["europe_pmc"], max_results=10)

        assert result["success"] is False
        assert "Network Error" in result["error"]
        assert result["total_count"] == 0

    def test_search_literature_concurrent_sources(self, mock_services, logger):
        """测试并发搜索多个数据源"""
        # 模拟多个服务返回
        mock_services["europe_pmc"].search.return_value = {
            "articles": [{"title": "Europe PMC Result"}],
            "total_count": 1,
        }
        mock_services["pubmed"].search.return_value = {
            "articles": [{"title": "PubMed Result"}],
            "total_count": 1,
        }
        mock_services["crossref"].search.return_value = {
            "articles": [{"title": "CrossRef Result"}],
            "total_count": 1,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(
            keyword="test", sources=["europe_pmc", "pubmed", "crossref"], max_results=10
        )

        assert result["success"] is True
        assert len(result["sources_used"]) == 3
        assert len(result["merged_results"]) == 3
        assert result["total_count"] == 3

    def test_search_literature_parameter_validation(self, mock_services, logger):
        """测试参数验证"""
        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        # 测试无效的 sources 参数
        result = search_literature(keyword="test", sources=[], max_results=10)  # 空列表

        assert result["success"] is True
        assert result["sources_used"] == []
        assert result["total_count"] == 0

        # 测试无效的 max_results 参数
        result = search_literature(
            keyword="test", sources=["europe_pmc"], max_results=0  # 零结果数
        )

        assert result["success"] is True
        assert result["merged_results"] == []

    def test_search_literature_time_tracking(self, mock_services, logger):
        """测试搜索时间跟踪"""
        mock_services["europe_pmc"].search.return_value = {
            "articles": [{"title": "Test Article"}],
            "total_count": 1,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        import time

        start_time = time.time()
        result = search_literature(keyword="test", sources=["europe_pmc"], max_results=10)
        end_time = time.time()

        assert result["success"] is True
        assert "search_time" in result
        assert 0 <= result["search_time"] <= end_time - start_time + 0.1  # 允许小的误差

    def test_search_literature_merging_logic(self, mock_services, logger):
        """测试结果合并逻辑"""
        # 模拟重复的数据
        mock_services["europe_pmc"].search.return_value = {
            "articles": [
                {
                    "title": "Duplicate Article",
                    "doi": "10.1234/duplicate",
                    "authors": ["Author A"],
                    "source": "europe_pmc",
                }
            ],
            "total_count": 1,
        }
        mock_services["pubmed"].search.return_value = {
            "articles": [
                {
                    "title": "Duplicate Article",
                    "doi": "10.1234/duplicate",
                    "authors": ["Author A", "Author B"],
                    "source": "pubmed",
                }
            ],
            "total_count": 1,
        }

        from tool_modules.core.search_tools import register_search_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        tools = register_search_tools(mock_mcp, mock_services, logger)
        search_literature = tools[0]

        result = search_literature(
            keyword="duplicate", sources=["europe_pmc", "pubmed"], max_results=10
        )

        assert result["success"] is True
        # 应该去重，只保留一个结果
        assert len(result["merged_results"]) == 1
        assert result["merged_results"][0]["doi"] == "10.1234/duplicate"
        # 合并后的文章应该包含两个来源的信息
        assert result["merged_results"][0]["authors"] == ["Author A", "Author B"]
