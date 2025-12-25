"""PMC 全文转换测试 - TDD 驱动开发

设计原则：
1. 必须有 PMCID 才能获取全文
2. 无 PMCID 直接报错，不降级
3. 只返回全文格式（XML/Markdown/Text），不返回元数据
4. 职责单一，与其他工具配合
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 添加 src 目录到路径
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# ============================================================================
# 测试数据 - 模拟 PMC XML 响应
# ============================================================================

SAMPLE_PMC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article>
    <article-meta>
      <article-title>Machine Learning in Healthcare: A Comprehensive Review</article-title>
      <contrib-group>
        <contrib contrib-type="author">
          <name>
            <surname>Smith</surname>
            <given-names>John</given-names>
          </name>
        </contrib>
      </contrib-group>
    </article-meta>
    <abstract>
      <title>Abstract</title>
      <p>This study explores machine learning in healthcare.</p>
    </abstract>
    <body>
      <sec sec-type="intro">
        <title>Introduction</title>
        <p>Machine learning is transforming healthcare.</p>
      </sec>
      <sec sec-type="methods">
        <title>Methods</title>
        <p>We collected data from 1000 patients.</p>
      </sec>
    </body>
  </article>
</pmc-articleset>
"""


# ============================================================================
# 测试类
# ============================================================================


class TestPMCFulltextCore:
    """核心功能测试：有 PMCID 返回全文"""

    @pytest.fixture
    def pubmed_service(self):
        """创建 PubMed 服务实例"""
        from article_mcp.services.pubmed_search import PubMedService

        return PubMedService(logger=Mock())

    def test_with_pmcid_returns_three_formats(self, pubmed_service):
        """测试：有 PMCID 时返回 XML、Markdown、Text 三种格式"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_PMC_XML
            mock_response.content = SAMPLE_PMC_XML.encode("utf-8")
            mock_get.return_value = mock_response

            result = pubmed_service.get_pmc_fulltext_html("PMC1234567")

            # 核心验证：三种格式都存在
            assert result["pmc_id"] == "PMC1234567"
            assert result["fulltext_available"] is True
            assert result["error"] is None

            assert "fulltext_xml" in result
            assert "fulltext_markdown" in result
            assert "fulltext_text" in result

            # 内容非空
            assert result["fulltext_xml"] is not None
            assert result["fulltext_markdown"] is not None
            assert result["fulltext_text"] is not None

            # 验证不包含冗余的元数据字段（其他工具负责）
            assert "title" not in result or result.get("title") is None
            assert (
                "authors" not in result
                or result.get("authors") is None
                or result.get("authors") == []
            )
            assert "journal_name" not in result or result.get("journal_name") is None
            assert "abstract" not in result or result.get("abstract") is None
            assert "publication_date" not in result or result.get("publication_date") is None
            assert "pmc_link" not in result or result.get("pmc_link") is None
            assert "fulltext_html" not in result or result.get("fulltext_html") is None

    def test_markdown_format_is_valid(self, pubmed_service):
        """测试：Markdown 格式只包含正文，不包含标题、作者、摘要"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_PMC_XML
            mock_response.content = SAMPLE_PMC_XML.encode("utf-8")
            mock_get.return_value = mock_response

            result = pubmed_service.get_pmc_fulltext_html("PMC1234567")

            markdown = result["fulltext_markdown"]

            # Markdown 应该有结构
            assert len(markdown) > 100
            # 不应该有 XML 标签
            assert "<article-title>" not in markdown
            assert "</article-title>" not in markdown
            assert "<sec" not in markdown

            # 不应该包含元数据（标题、作者、摘要）
            # Markdown 不应该以文章标题开头（那是元数据）
            assert not markdown.startswith("# Machine Learning")
            # 不应该包含 "Authors:" 标记
            assert "Authors:" not in markdown
            # 不应该包含 "Abstract" 标题
            assert markdown.find("Abstract") == -1 or markdown.find("Abstract") > markdown.find(
                "Introduction"
            )

    def test_text_format_is_clean(self, pubmed_service):
        """测试：纯文本格式干净，无标签"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_PMC_XML
            mock_response.content = SAMPLE_PMC_XML.encode("utf-8")
            mock_get.return_value = mock_response

            result = pubmed_service.get_pmc_fulltext_html("PMC1234567")

            text = result["fulltext_text"]

            # 纯文本应该有内容
            assert len(text) > 100
            # 不应该有任何 XML 标签
            assert "<article-title>" not in text
            assert "</article-title>" not in text
            assert "<sec" not in text
            assert "<p>" not in text
            assert "</p>" not in text
            assert "<?xml" not in text


class TestPMCFulltextErrors:
    """错误处理测试：无 PMCID 或请求失败"""

    @pytest.fixture
    def pubmed_service(self):
        """创建 PubMed 服务实例"""
        from article_mcp.services.pubmed_search import PubMedService

        return PubMedService(logger=Mock())

    def test_empty_pmcid_returns_error(self, pubmed_service):
        """测试：空 PMCID 返回错误"""
        result = pubmed_service.get_pmc_fulltext_html("")

        # 应该返回错误
        assert result["error"] is not None
        assert result["fulltext_available"] is False
        assert result["pmc_id"] is None

    def test_none_pmcid_returns_error(self, pubmed_service):
        """测试：None PMCID 返回错误"""
        result = pubmed_service.get_pmc_fulltext_html(None)

        # 应该返回错误
        assert result["error"] is not None
        assert result["fulltext_available"] is False

    def test_network_error_returns_error(self, pubmed_service):
        """测试：网络错误返回错误"""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = pubmed_service.get_pmc_fulltext_html("PMC1234567")

            # 应该返回错误
            assert result["error"] is not None
            assert result["fulltext_available"] is False
            assert result["pmc_id"] == "PMC1234567"

    def test_empty_xml_returns_error(self, pubmed_service):
        """测试：空 XML 返回错误"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_response.content = b""
            mock_get.return_value = mock_response

            result = pubmed_service.get_pmc_fulltext_html("PMC1234567")

            # 应该返回错误
            assert result.get("error") is not None or result.get("fulltext_available") is False


class TestPMCFulltextNormalization:
    """PMCID 标准化测试"""

    @pytest.fixture
    def pubmed_service(self):
        """创建 PubMed 服务实例"""
        from article_mcp.services.pubmed_search import PubMedService

        return PubMedService(logger=Mock())

    def test_pmcid_without_prefix_normalized(self, pubmed_service):
        """测试：不带 PMC 前缀的 ID 被标准化"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_PMC_XML
            mock_response.content = SAMPLE_PMC_XML.encode("utf-8")
            mock_get.return_value = mock_response

            result = pubmed_service.get_pmc_fulltext_html("1234567")

            # 应该自动添加 PMC 前缀
            assert result["pmc_id"] == "PMC1234567"
            assert result["fulltext_available"] is True


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
