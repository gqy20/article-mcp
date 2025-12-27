"""PMC 全文转换测试 - TDD 驱动开发

✅ v0.2.1 更新：所有测试已重写为异步版本，使用 aiohttp mock

设计原则：
1. 必须有 PMCID 才能获取全文
2. 无 PMCID 直接报错，不降级
3. 只返回全文格式（XML/Markdown/Text），不返回元数据
4. 职责单一，与其他工具配合
5. 支持按章节提取内容
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加 src 目录到路径
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# ============================================================================
# 测试数据 - 模拟 PMC XML 响应
# ============================================================================

# 基础 XML（用于原有测试）
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

# 完整 XML（用于章节提取测试）
SAMPLE_PMC_XML_WITH_SECTIONS = """<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article>
    <article-meta>
      <article-title>Machine Learning in Healthcare</article-title>
    </article-meta>
    <body>
      <sec sec-type="intro">
        <title>Introduction</title>
        <p>This is the introduction section.</p>
        <p>Machine learning is transforming healthcare.</p>
      </sec>
      <sec sec-type="methods">
        <title>Methods</title>
        <p>We collected data from 1000 patients.</p>
        <p>The study was approved by the ethics committee.</p>
      </sec>
      <sec sec-type="results">
        <title>Results</title>
        <p>Our model achieved 95% accuracy.</p>
      </sec>
      <sec sec-type="discussion">
        <title>Discussion</title>
        <p>The results demonstrate the potential of ML in healthcare.</p>
      </sec>
      <sec sec-type="conclusion">
        <title>Conclusion</title>
        <p>Further research is needed to validate these findings.</p>
      </sec>
    </body>
  </article>
</pmc-articleset>
"""


# ============================================================================
# aiohttp Mock 辅助函数
# ============================================================================


def create_mock_aiohttp_response(text_content: str, status: int = 200) -> Mock:
    """创建模拟的 aiohttp 响应对象"""
    mock_response = Mock()
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=text_content)
    return mock_response


def create_mock_aiohttp_session(xml_content: str) -> Mock:
    """创建模拟的 aiohttp.ClientSession

    返回一个可以用于 patch('aiohttp.ClientSession') 的 mock 对象
    """
    # 创建 mock 响应
    mock_response = create_mock_aiohttp_response(xml_content, 200)

    # 创建模拟的 async context manager (用于 session.get() 的返回值)
    # 关键：不能使用 AsyncMock，因为它本身就是一个 coroutine
    # 我们需要一个普通对象，但有 __aenter__ 和 __aexit__ 异步方法
    class MockGetContextManager:
        async def __aenter__(self):
            return mock_response

        async def __aexit__(self, *args):
            pass

    # 创建 mock session
    mock_session = Mock()
    mock_session.get = Mock(return_value=MockGetContextManager())

    # session 本身也需要是 async context manager
    class MockSessionContextManager:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, *args):
            pass

    return MockSessionContextManager()


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

    @pytest.mark.asyncio
    async def test_with_pmcid_returns_three_formats(self, pubmed_service):
        """测试：有 PMCID 时返回 XML、Markdown、Text 三种格式"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(SAMPLE_PMC_XML)

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567")

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

    @pytest.mark.asyncio
    async def test_markdown_format_is_valid(self, pubmed_service):
        """测试：Markdown 格式只包含正文，不包含标题、作者、摘要"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(SAMPLE_PMC_XML)

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567")

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

    @pytest.mark.asyncio
    async def test_text_format_is_clean(self, pubmed_service):
        """测试：纯文本格式干净，无标签"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(SAMPLE_PMC_XML)

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567")

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
        """测试：空 PMCID 返回错误（不需要网络调用，保持同步测试）"""
        result = pubmed_service.get_pmc_fulltext_html("")

        # 应该返回错误
        assert result["error"] is not None
        assert result["fulltext_available"] is False
        assert result["pmc_id"] is None

    def test_none_pmcid_returns_error(self, pubmed_service):
        """测试：None PMCID 返回错误（不需要网络调用，保持同步测试）"""
        result = pubmed_service.get_pmc_fulltext_html(None)

        # 应该返回错误
        assert result["error"] is not None
        assert result["fulltext_available"] is False

    @pytest.mark.asyncio
    async def test_network_error_returns_error(self, pubmed_service):
        """测试：网络错误返回错误"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # 模拟网络错误 - 在 text() 调用时抛出异常
            mock_session = AsyncMock()

            mock_get_cm = AsyncMock()
            mock_get_cm.__aenter__.side_effect = Exception("Network error")
            mock_get_cm.__aexit__.return_value = None

            mock_session.get.return_value = mock_get_cm
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None

            mock_session_class.return_value = mock_session

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567")

            # 应该返回错误
            assert result["error"] is not None
            assert result["fulltext_available"] is False
            assert result["pmc_id"] == "PMC1234567"

    @pytest.mark.asyncio
    async def test_empty_xml_returns_error(self, pubmed_service):
        """测试：空 XML 返回错误"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session("")

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567")

            # 应该返回错误
            assert result.get("error") is not None or result.get("fulltext_available") is False


class TestPMCFulltextNormalization:
    """PMCID 标准化测试"""

    @pytest.fixture
    def pubmed_service(self):
        """创建 PubMed 服务实例"""
        from article_mcp.services.pubmed_search import PubMedService

        return PubMedService(logger=Mock())

    @pytest.mark.asyncio
    async def test_pmcid_without_prefix_normalized(self, pubmed_service):
        """测试：不带 PMC 前缀的 ID 被标准化"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(SAMPLE_PMC_XML)

            result = await pubmed_service.get_pmc_fulltext_html_async("1234567")

            # 应该自动添加 PMC 前缀
            assert result["pmc_id"] == "PMC1234567"
            assert result["fulltext_available"] is True


# ============================================================================
# 新增：章节提取测试
# ============================================================================


class TestPMCSectionExtraction:
    """章节提取功能测试"""

    @pytest.fixture
    def pubmed_service(self):
        """创建 PubMed 服务实例"""
        from article_mcp.services.pubmed_search import PubMedService

        return PubMedService(logger=Mock())

    @pytest.mark.asyncio
    async def test_extract_single_section_methods(self, pubmed_service):
        """测试：提取单个章节（Methods）"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async(
                "PMC1234567", sections=["methods"]
            )

            # 验证返回值
            assert result["fulltext_available"] is True
            assert "fulltext_markdown" in result

            markdown = result["fulltext_markdown"]

            # 只包含 Methods 章节
            assert "Methods" in markdown
            assert "We collected data from 1000 patients" in markdown

            # 不包含其他章节
            assert "Introduction" not in markdown or markdown.index("Methods") < markdown.index(
                "Introduction"
            )
            assert "Results" not in markdown
            assert "Discussion" not in markdown
            assert "Conclusion" not in markdown

            # 验证章节信息
            assert result.get("sections_requested") == ["methods"]
            assert result.get("sections_found") == ["methods"]
            assert result.get("sections_missing") == []

    @pytest.mark.asyncio
    async def test_extract_multiple_sections(self, pubmed_service):
        """测试：提取多个章节（Methods + Discussion）"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async(
                "PMC1234567", sections=["methods", "discussion"]
            )

            markdown = result["fulltext_markdown"]

            # 包含 Methods 和 Discussion
            assert "Methods" in markdown
            assert "Discussion" in markdown
            assert "We collected data from 1000 patients" in markdown
            assert "results demonstrate the potential" in markdown

            # 不包含其他章节
            assert "Results" not in markdown or markdown.index("Results") > markdown.index(
                "Discussion"
            )
            assert "Conclusion" not in markdown

            # 验证章节信息
            assert set(result.get("sections_found", [])) == {"methods", "discussion"}
            assert result.get("sections_missing") == []

    @pytest.mark.asyncio
    async def test_extract_nonexistent_section(self, pubmed_service):
        """测试：提取不存在的章节"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async(
                "PMC1234567",
                sections=["appendix"],  # 不存在的章节
            )

            # 仍然成功返回，但章节未找到
            assert result["fulltext_available"] is True
            assert result.get("sections_found") == []
            assert result.get("sections_missing") == ["appendix"]

            # Markdown 为空或只有占位符
            markdown = result.get("fulltext_markdown", "")
            assert len(markdown) == 0 or "appendix" not in markdown.lower()

    @pytest.mark.asyncio
    async def test_sections_none_returns_all(self, pubmed_service):
        """测试：sections=None 返回全部章节"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567", sections=None)

            markdown = result["fulltext_markdown"]

            # 包含所有章节
            assert "Introduction" in markdown
            assert "Methods" in markdown
            assert "Results" in markdown
            assert "Discussion" in markdown
            assert "Conclusion" in markdown

            # 不包含章节信息字段（全部章节时不标记）
            assert "sections_requested" not in result
            assert "sections_found" not in result

    @pytest.mark.asyncio
    async def test_partial_sections_found(self, pubmed_service):
        """测试：部分章节找到，部分未找到"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async(
                "PMC1234567", sections=["methods", "appendix"]
            )

            # Methods 找到了，Appendix 未找到
            assert result.get("sections_found") == ["methods"]
            assert result.get("sections_missing") == ["appendix"]

            # Markdown 只包含 Methods
            markdown = result.get("fulltext_markdown", "")
            assert "Methods" in markdown
            assert "appendix" not in markdown.lower()

    @pytest.mark.asyncio
    async def test_empty_sections_list(self, pubmed_service):
        """测试：空章节列表"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = create_mock_aiohttp_session(
                SAMPLE_PMC_XML_WITH_SECTIONS
            )

            result = await pubmed_service.get_pmc_fulltext_html_async("PMC1234567", sections=[])

            # 返回空内容
            assert result["fulltext_available"] is True
            markdown = result.get("fulltext_markdown", "")
            assert len(markdown) == 0 or markdown.strip() == ""

            assert result.get("sections_found") == []
            assert result.get("sections_requested") == []


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
