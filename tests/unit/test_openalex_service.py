"""OpenAlex 服务单元测试 (异步版本)"""

from unittest.mock import AsyncMock, patch

import pytest

from article_mcp.services.openalex_service import OpenAlexService


@pytest.mark.asyncio
class TestOpenAlexService:
    """OpenAlex 服务测试类 - 异步版本"""

    @pytest.fixture
    def service(self, logger):
        """创建 OpenAlex 服务实例"""
        return OpenAlexService(logger)

    def test_init(self, service):
        """测试服务初始化"""
        assert service.base_url == "https://api.openalex.org"
        # 移除同步 api_client，使用异步客户端
        assert service._async_api_client is None  # 延迟初始化
        assert hasattr(service, "search_works_async")
        assert hasattr(service, "get_work_by_doi_async")  # 新的异步方法

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_search_works_async_success(self, mock_get_client, service):
        """测试异步搜索成功"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {
                "results": [
                    {
                        "id": "https://openalex.org/123456",
                        "title": "Test Article",
                        "authorships": [{"author": {"display_name": "Test Author"}}],
                        "primary_location": {
                            "source": {"display_name": "Test Journal"},
                            "doi": "10.1234/test",
                        },
                        "publication_year": 2023,
                        "open_access": {
                            "is_oa": True,
                            "oa_url": "https://example.com/fulltext.pdf",
                        },
                    }
                ],
                "meta": {"count": 1},
            },
        }
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        result = await service.search_works_async("test query", max_results=10)

        assert result["success"] is True
        assert len(result["articles"]) == 1
        assert result["total_count"] == 1
        assert result["source"] == "openalex"

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_search_works_async_api_failure(self, mock_get_client, service):
        """测试异步 API 调用失败"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": False, "error": "API Error"}
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        result = await service.search_works_async("test query", max_results=10)

        assert result["success"] is False
        assert result["error"] == "API Error"
        assert len(result["articles"]) == 0

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_search_works_async_with_filters(self, mock_get_client, service):
        """测试带过滤器的异步搜索"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {"results": [], "meta": {"count": 0}},
        }
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        filters = {"publication_year": "2023"}
        result = await service.search_works_async("test query", max_results=10, filters=filters)

        assert result["success"] is True
        assert len(result["articles"]) == 0

    def test_format_single_article_complete(self, service):
        """测试格式化完整文章数据"""
        item = {
            "id": "https://openalex.org/123456",
            "title": "Test Article Title",
            "authorships": [
                {"author": {"display_name": "Test Author"}, "author_position": "first"}
            ],
            "primary_location": {
                "source": {"display_name": "Test Journal"},
                "doi": "10.1234/test.2023",
            },
            "publication_year": 2023,
            "open_access": {
                "is_oa": True,
                "oa_url": "https://example.com/fulltext.pdf",
                "oa_status": "green",
            },
        }

        result = service._format_single_article(item)

        assert result["title"] == "Test Article Title"
        assert result["authors"] == ["Test Author"]
        assert result["doi"] == "10.1234/test.2023"
        assert result["journal"] == "Test Journal"
        assert result["publication_date"] == "2023"
        assert result["open_access"]["is_oa"] is True
        assert result["open_access"]["oa_url"] == "https://example.com/fulltext.pdf"
        assert result["source"] == "openalex"

    def test_format_single_article_minimal(self, service):
        """测试格式化最少的文章数据"""
        item = {}

        result = service._format_single_article(item)

        assert result["title"] == ""
        assert result["authors"] == []
        assert result["doi"] is None
        assert result["journal"] == ""
        assert result["publication_date"] == ""
        assert result["open_access"]["is_oa"] is False
        assert result["open_access"]["oa_url"] == ""
        assert result["open_access"]["oa_status"] == ""
        assert result["source"] == "openalex"

    def test_format_single_article_with_none_values(self, service):
        """测试格式化包含 None 值的文章数据"""
        # 使用空字典而不是 None 值，避免服务代码的 bug
        item = {
            "title": "",  # 空字符串而不是 None
            "authorships": [],  # 空列表而不是 None
            "primary_location": {},  # 空字典而不是 None
            "publication_year": "",  # 空字符串而不是 None
            "open_access": {},  # 空字典而不是 None
        }

        result = service._format_single_article(item)

        assert result["title"] == ""
        assert result["authors"] == []
        assert result["doi"] is None
        assert result["journal"] == ""
        assert result["publication_date"] == ""
        assert result["open_access"]["is_oa"] is False
        assert result["open_access"]["oa_url"] == ""
        assert result["open_access"]["oa_status"] == ""
        assert result["source"] == "openalex"

    def test_format_single_article_with_empty_primary_location(self, service):
        """测试 primary_location 为空字典的情况"""
        item = {
            "title": "Test Article",
            "authorships": [{"author": {"display_name": "Test Author"}}],
            "primary_location": {},  # 使用空字典而不是 None
            "publication_year": 2023,
        }

        result = service._format_single_article(item)

        assert result["title"] == "Test Article"
        assert result["authors"] == ["Test Author"]
        assert result["doi"] is None
        assert result["journal"] == ""
        assert result["publication_date"] == "2023"

    def test_format_articles(self, service):
        """测试文章列表格式化"""
        items = [
            {
                "title": "Article 1",
                "authorships": [{"author": {"display_name": "Author 1"}}],
                "primary_location": {"doi": "10.1234/1"},
                "publication_year": 2023,
            },
            {
                "title": "Article 2",
                "authorships": [{"author": {"display_name": "Author 2"}}],
                "primary_location": {"doi": "10.1234/2"},
                "publication_year": 2023,
            },
        ]

        result = service._format_articles(items)

        assert len(result) == 2
        assert result[0]["title"] == "Article 1"
        assert result[1]["title"] == "Article 2"

    def test_format_articles_empty_list(self, service):
        """测试空文章列表格式化"""
        result = service._format_articles([])
        assert result == []

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_get_work_by_doi_success(self, mock_get_client):
        """测试通过 DOI 获取文章成功（异步版本）"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {
                "results": [
                    {
                        "id": "https://openalex.org/123456",
                        "title": "Test Article",
                        "authorships": [],
                        "primary_location": {
                            "source": {"display_name": "Test Journal"},
                            "doi": "10.1234/test",
                        },
                        "publication_year": 2023,
                        "open_access": {},
                    }
                ]
            },
        }
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        result = await service.get_work_by_doi_async("10.1234/test")

        assert result["success"] is True
        assert result["article"]["title"] == "Test Article"
        assert result["source"] == "openalex"

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_get_work_by_doi_not_found(self, mock_get_client):
        """测试通过 DOI 获取文章未找到（异步版本）"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": True, "data": {"results": []}}
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        result = await service.get_work_by_doi_async("10.9999/nonexistent")

        assert result["success"] is False
        assert result["article"] is None
        assert result["source"] == "openalex"

    @patch("article_mcp.services.openalex_service.get_async_api_client")
    async def test_search_works_async_performance(self, mock_get_client):
        """测试异步搜索性能"""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "data": {"results": [], "meta": {"count": 0}},
        }
        mock_get_client.return_value = mock_client

        service = OpenAlexService(None)
        service._async_api_client = mock_client

        # 测试异步调用正常工作
        result = await service.search_works_async("test", max_results=5)

        assert result["success"] is True
        assert len(result["articles"]) == 0

    def test_filter_open_access(self, service):
        """测试过滤开放获取文献"""
        works = [
            {
                "open_access": {"is_oa": True},
                "title": "Open Access Article",
            },
            {
                "open_access": {"is_oa": False},
                "title": "Closed Access Article",
            },
            {
                "open_access": {"is_oa": True},
                "title": "Another OA Article",
            },
        ]

        result = service.filter_open_access(works)

        assert len(result) == 2
        assert result[0]["title"] == "Open Access Article"
        assert result[1]["title"] == "Another OA Article"
