#!/usr/bin/env python3
"""测试工具4复用工具3获取 references

重构目标：
1. 工具4的 _get_references 应该调用工具3的 get_references_async
2. 删除工具4中重复的 _extract_identifier_type 和 _deduplicate_references
3. 保持工具4的其他关系分析功能不变
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.tools.core import relation_tools

# ============================================================================
# 测试数据
# ============================================================================

SAMPLE_REFERENCES_FROM_TOOL3 = {
    "success": True,
    "identifier": "10.1234/test.2023",
    "id_type": "doi",
    "sources_used": ["crossref"],
    "references_by_source": {},
    "merged_references": [
        {
            "title": "Reference Article 1",
            "authors": ["Author A"],
            "doi": "10.5678/ref1",
            "journal": "Nature",
            "source": "crossref",
        },
        {
            "title": "Reference Article 2",
            "authors": ["Author B"],
            "doi": "10.5678/ref2",
            "journal": "Science",
            "source": "crossref",
        },
    ],
    "total_count": 2,
    "processing_time": 0.5,
}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


@pytest.fixture
def mock_services():
    """模拟服务"""
    return {
        "crossref": Mock(),
        "pubmed": Mock(),
        "openalex": Mock(),
    }


# ============================================================================
# 测试：工具4应该调用工具3获取references
# ============================================================================


@pytest.mark.asyncio
class TestRelationToolsUsesReferenceTools:
    """测试工具4复用工具3的 references 功能"""

    async def test_get_references_calls_tool3(self, mock_services, logger):
        """测试：_get_references 应该调用工具3的 get_references_async"""
        # 模拟工具3的函数
        mock_get_references_async = AsyncMock(return_value=SAMPLE_REFERENCES_FROM_TOOL3)

        # 由于 relation_tools 在文件顶部导入了 get_references_async
        # 我们需要 mock 模块级别的导入
        with patch.object(
            relation_tools,
            "get_references_async",
            mock_get_references_async,
        ):
            # 调用工具4的 _get_references
            result = await relation_tools._get_references(
                identifier="10.1234/test.2023",
                id_type="doi",
                max_results=20,
                sources=["crossref"],
                services=mock_services,
                logger=logger,
            )

            # 验证调用了工具3的函数
            mock_get_references_async.assert_called_once()
            call_args = mock_get_references_async.call_args

            # 验证传递的参数
            assert call_args.kwargs["identifier"] == "10.1234/test.2023"
            assert call_args.kwargs["id_type"] == "doi"
            assert call_args.kwargs["max_results"] == 20
            assert "crossref" in call_args.kwargs["sources"]
            assert not call_args.kwargs["include_metadata"]

            # 验证返回的结果来自工具3
            assert len(result) == 2
            assert result[0]["title"] == "Reference Article 1"
            assert result[1]["title"] == "Reference Article 2"

    async def test_extract_identifier_type_removed(self, mock_services, logger):
        """测试：_extract_identifier_type 函数应该被删除（不再存在）"""
        relation_tools._relation_services = mock_services
        relation_tools._logger = logger

        # 重构后这个函数不应该存在
        has_extract_func = hasattr(relation_tools, "_extract_identifier_type")

        # 现在这个函数还存在，测试会失败
        # 重构后这个函数被删除，测试会通过
        assert not has_extract_func, "_extract_identifier_type 函数应该被删除，请使用工具3的函数"

    async def test_deduplicate_references_removed(self, mock_services, logger):
        """测试：_deduplicate_references 函数应该被删除（不再存在）"""
        relation_tools._relation_services = mock_services
        relation_tools._logger = logger

        # 重构后这个函数不应该存在
        has_dedup_func = hasattr(relation_tools, "_deduplicate_references")

        # 现在这个函数还存在，测试会失败
        # 重构后这个函数被删除，测试会通过
        assert not has_dedup_func, "_deduplicate_references 函数应该被删除，请使用工具3的去重功能"

    async def test_other_relation_functions_unchanged(self, mock_services, logger):
        """测试：其他关系获取函数（similar, citing）应该保持不变"""
        relation_tools._relation_services = mock_services
        relation_tools._logger = logger

        # 这些函数应该仍然存在
        assert hasattr(relation_tools, "_get_similar_articles"), "_get_similar_articles 应该保留"
        assert hasattr(relation_tools, "_get_citing_articles"), "_get_citing_articles 应该保留"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
