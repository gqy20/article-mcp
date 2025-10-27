"""
CrossRef 服务单元测试
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from src.crossref_service import CrossRefService


class TestCrossRefService:
    """CrossRef 服务测试类"""

    @pytest.fixture
    def service(self, logger):
        """创建 CrossRef 服务实例"""
        return CrossRefService(logger)

    def test_init(self, service):
        """测试服务初始化"""
        assert service.base_url == "https://api.crossref.org"
        assert service.api_client is not None
        assert hasattr(service, "search_works")
        assert hasattr(service, "get_work_by_doi")
        assert hasattr(service, "get_references")

    @patch("src.crossref_service.get_api_client")
    def test_search_works_success(self, mock_get_client, service):
        """测试成功搜索"""
        # 模拟 API 客户端
        mock_client = Mock()
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

        result = service.search_works("test query", max_results=10)

        assert result["success"] is True
        assert len(result["articles"]) == 1
        assert result["total_count"] == 1
        assert result["source"] == "crossref"

    @patch("src.crossref_service.get_api_client")
    def test_search_works_api_failure(self, mock_get_client, service):
        """测试 API 调用失败"""
        mock_client = Mock()
        mock_client.get.return_value = {"success": False, "error": "API Error"}
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)

        result = service.search_works("test query", max_results=10)

        assert result["success"] is False
        assert result["error"] == "API调用失败"
        assert len(result["articles"]) == 0
        assert result["source"] == "crossref"

    @patch("src.crossref_service.get_api_client")
    def test_search_works_exception(self, mock_get_client, service):
        """测试搜索过程中的异常"""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Network Error")
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)

        result = service.search_works("test query", max_results=10)

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
                "title": ["Reference 1"],
                "author": [{"name": "Ref Author"}],
                "created": {"date-parts": [[2023]]},
            },
            {"DOI": None, "title": None, "author": None, "created": None},
        ]

        result = service._format_references(references)

        assert len(result) == 2
        assert result[0]["doi"] == "10.1234/ref1"
        assert result[0]["title"] == "Reference 1"
        assert result[0]["authors"] == ["Ref Author"]
        assert result[0]["year"] == 2023
        assert result[1]["doi"] is None
        assert result[1]["title"] == ""
        assert result[1]["authors"] == []
        assert result[1]["year"] is None

    @patch("src.crossref_service.get_api_client")
    def test_get_work_by_doi_success(self, mock_get_client):
        """测试通过 DOI 获取文章成功"""
        mock_client = Mock()
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

        result = service.get_work_by_doi("10.1234/test")

        assert result["success"] is True
        assert result["article"]["title"] == "Test Article"
        assert result["source"] == "crossref"

    @patch("src.crossref_service.get_api_client")
    def test_get_work_by_doi_not_found(self, mock_get_client):
        """测试通过 DOI 获取文章未找到"""
        mock_client = Mock()
        mock_client.get.return_value = {"success": True, "data": {"message": {"items": []}}}
        mock_get_client.return_value = mock_client

        service = CrossRefService(None)

        result = service.get_work_by_doi("10.9999/nonexistent")

        assert result["success"] is False
        assert result["article"] is None
        assert result["source"] == "crossref"

    def test_lru_cache_behavior(self, service):
        """测试 LRU 缓存行为"""
        # 这个测试检查缓存装饰器是否正常工作
        # 由于我们使用了 @lru_cache，相同的调用应该使用缓存

        with patch.object(service, "api_client") as mock_client:
            mock_client.get.return_value = {
                "success": True,
                "data": {"message": {"items": [], "total-results": 0}},
            }

            # 第一次调用
            result1 = service.search_works("test", max_results=5)
            # 第二次调用应该使用缓存
            result2 = service.search_works("test", max_results=5)

            # 验证只调用了一次 API
            assert mock_client.get.call_count == 1
            assert result1 == result2
