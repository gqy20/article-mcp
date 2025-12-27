"""CrossRef 服务单元测试 (异步版本)"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.services.crossref_service import CrossRefService


@pytest.mark.asyncio
class TestCrossRefService:
    """CrossRef 服务测试类 - 异步版本"""

    @pytest.fixture
    def service(self, logger):
        """创建 CrossRef 服务实例"""
        return CrossRefService(logger)

    def test_init(self, service):
        """测试服务初始化"""
        assert service.base_url == "https://api.crossref.org"
        # 移除同步 api_client，使用异步客户端
        assert service._async_api_client is None  # 延迟初始化
        assert hasattr(service, "search_works_async")
        assert hasattr(service, "get_work_by_doi_async")  # 新的异步方法
        assert hasattr(service, "get_references_async")  # 新的异步方法

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_search_works_async_success(self, mock_get_client, service):
        """测试异步搜索成功"""
        # 模拟异步 API 客户端
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {
                "message": {
                    "items": [
                        {
                            "title": ["Test Article"],
                            "author": [{"name": "Test Author"}],
                            "DOI": "10.1234/test",
                        }
                    ],
                    "total-results": 1,
                }
            },
        }
        mock_get_client.return_value = mock_client

        # 重新创建服务以使用 mock
        service = CrossRefService(None)
        service._async_api_client = mock_client

        result = await service.search_works_async("test query", max_results=10)

        assert result["success"] is True
        assert len(result["articles"]) == 1
        assert result["total_count"] == 1
        assert result["source"] == "crossref"

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_search_works_async_api_failure(self, mock_get_client, service):
        """测试异步 API 调用失败"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": False, "error": "API Error"}
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)
        service._async_api_client = mock_client

        result = await service.search_works_async("test query", max_results=10)

        assert result["success"] is False
        assert result["error"] == "API Error"
        assert len(result["articles"]) == 0
        assert result["source"] == "crossref"

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_search_works_async_exception(self, mock_get_client, service):
        """测试异步搜索过程中的异常"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network Error")
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)
        service._async_api_client = mock_client

        result = await service.search_works_async("test query", max_results=10)

        assert result["success"] is False
        assert "Network Error" in result["error"]
        assert len(result["articles"]) == 0

    def test_format_single_article_complete(self, service):
        """测试格式化完整文章数据"""
        item = {
            "title": ["Test Article Title"],
            "author": [{"given": "John", "family": "Doe"}, {"name": "Jane Smith"}],
            "DOI": "10.1234/test.2023",
            "short-container-title": ["Test Journal"],
            "created": {"date-time": "2023-01-15T10:30:00Z"},
        }

        result = service._format_single_article(item)

        assert result["title"] == "Test Article Title"
        assert result["authors"] == ["John Doe", "Jane Smith"]
        assert result["doi"] == "10.1234/test.2023"
        assert result["journal"] == "Test Journal"
        assert result["publication_date"] == "2023-01-15T10:30:00Z"
        assert result["source"] == "crossref"

    def test_format_single_article_minimal(self, service):
        """测试格式化最少的文章数据"""
        item = {}

        result = service._format_single_article(item)

        assert result["title"] == ""
        assert result["authors"] == []
        assert result["doi"] is None
        assert result["journal"] == ""
        assert result["publication_date"] == ""
        assert result["source"] == "crossref"

    def test_format_single_article_with_none_values(self, service):
        """测试格式化包含 None 值的文章数据"""
        item = {
            "title": None,
            "author": None,
            "DOI": None,
            "short-container-title": None,
            "created": None,
        }

        result = service._format_single_article(item)

        assert result["title"] == ""
        assert result["authors"] == []
        assert result["doi"] is None
        assert result["journal"] == ""
        assert result["publication_date"] == ""
        assert result["source"] == "crossref"

    def test_format_single_article_with_none_author(self, service):
        """测试格式化包含 None 作者的文章数据"""
        item = {
            "title": ["Test Article"],
            "author": [{"given": "John", "family": "Doe"}, None, {"name": "Jane Smith"}],
            "DOI": "10.1234/test",
        }

        result = service._format_single_article(item)

        assert result["title"] == "Test Article"
        assert result["authors"] == ["John Doe", "Jane Smith"]
        assert result["doi"] == "10.1234/test"

    def test_extract_title(self, service):
        """测试标题提取"""
        # 正常情况
        assert service._extract_title(["Title 1", "Title 2"]) == "Title 1"

        # 空列表
        assert service._extract_title([]) == ""

        # None 值（通过 .get('title') or [] 处理）
        assert service._extract_title(None) == ""

    def test_extract_authors(self, service):
        """测试作者提取"""
        # 正常情况
        authors = [{"given": "John", "family": "Doe"}, {"name": "Jane Smith"}]
        result = service._extract_authors(authors)
        assert result == ["John Doe", "Jane Smith"]

        # 空列表
        assert service._extract_authors([]) == []

        # 包含 None 值
        authors_with_none = [{"given": "John", "family": "Doe"}, None, {"name": "Jane Smith"}]
        result = service._extract_authors(authors_with_none)
        assert result == ["John Doe", "Jane Smith"]

    def test_format_references(self, service):
        """测试参考文献格式化"""
        references = [
            {
                "DOI": "10.1234/ref1",
                "unstructured": "Reference 1",  # 使用 unstructured 字段
                "author": [{"name": "Ref Author"}],
                "year": "2023",  # 直接提供年份
            },
            {"DOI": None},  # 最小数据
        ]

        result = service._format_references(references)

        assert len(result) == 2
        assert result[0]["doi"] == "10.1234/ref1"
        assert result[0]["title"] == "Reference 1"
        assert result[0]["authors"] == ["Ref Author"]
        assert result[0]["year"] == "2023"
        assert result[1]["doi"] is None
        assert result[1]["title"] == ""
        assert result[1]["authors"] == []
        assert result[1]["year"] == ""

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_get_work_by_doi_success(self, mock_get_client):
        """测试通过 DOI 获取文章成功（异步版本）"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {
                "message": {
                    "title": ["Test Article"],
                    "author": [{"name": "Test Author"}],
                    "DOI": "10.1234/test",
                }
            },
        }
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)
        service._async_api_client = mock_client

        result = await service.get_work_by_doi_async("10.1234/test")

        assert result["success"] is True
        assert result["article"]["title"] == "Test Article"
        assert result["source"] == "crossref"

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_get_work_by_doi_not_found(self, mock_get_client):
        """测试通过 DOI 获取文章未找到（异步版本）"""
        mock_client = AsyncMock()
        # CrossRef API 返回空消息表示未找到
        mock_client.get.return_value = {"success": True, "data": {"message": {}}}
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)
        service._async_api_client = mock_client

        result = await service.get_work_by_doi_async("10.9999/nonexistent")

        # 空消息会返回 success=True 但文章为空
        assert result["success"] is True
        # 空文章格式化后应该有默认空值
        assert result["article"]["title"] == ""
        assert result["article"]["authors"] == []
        assert result["source"] == "crossref"

    @patch("article_mcp.services.crossref_service.get_async_api_client")
    async def test_search_works_async_performance(self, mock_get_client):
        """测试异步搜索性能"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {"message": {"items": [], "total-results": 0}},
        }
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)
        service._async_api_client = mock_client

        # 测试异步调用正常工作
        result = await service.search_works_async("test", max_results=5)

        assert result["success"] is True
        assert len(result["articles"]) == 0
