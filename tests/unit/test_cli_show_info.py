#!/usr/bin/env python3
"""CLI show_info 输出验证测试
验证 show_info() 输出与实际工具签名一致
"""

# 添加src目录到Python路径
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402

from article_mcp.cli import show_info  # noqa: E402


class TestShowInfoOutput:
    """show_info() 输出验证测试"""

    @pytest.mark.unit
    def test_show_info_displays_five_tools(self, capsys):
        """测试 show_info 显示5个核心工具"""
        show_info()
        captured = capsys.readouterr()

        # 验证5个工具都存在
        assert "search_literature" in captured.out
        assert "get_article_details" in captured.out
        assert "get_references" in captured.out
        assert "get_literature_relations" in captured.out
        assert "get_journal_quality" in captured.out

    @pytest.mark.unit
    def test_get_article_details_params_correct(self, capsys):
        """测试 get_article_details 参数描述正确

        实际签名: async def get_article_details_async(
            pmcid: str | list[str],
            sections: str | list[str] | None = None,
            format: str = "markdown",
        )
        """
        show_info()
        captured = capsys.readouterr()

        # 提取 get_article_details 部分
        lines = captured.out.split("\n")
        in_article_details = False
        param_line = None

        for line in lines:
            if "2. get_article_details" in line:
                in_article_details = True
            elif in_article_details and "参数：" in line:
                param_line = line
                break
            elif in_article_details and "3." in line:
                break

        assert param_line is not None, "未找到 get_article_details 参数行"

        # 验证参数：应该包含 pmcid, sections, format
        # 不应该包含 identifier, id_type, sources, include_quality_metrics
        assert "pmcid" in param_line, f"参数行应包含 pmcid，实际: {param_line}"
        assert "sections" in param_line, f"参数行应包含 sections，实际: {param_line}"
        assert "format" in param_line, f"参数行应包含 format，实际: {param_line}"

        # 验证不包含旧的错误参数
        assert "identifier" not in param_line.lower() or "pmcid" in param_line
        assert "id_type" not in param_line.lower()

    @pytest.mark.unit
    def test_get_literature_relations_params_correct(self, capsys):
        """测试 get_literature_relations 参数描述正确

        实际签名: async def get_literature_relations(
            identifier: str,
            id_type: str = "auto",
            relation_types: list[str] | None = None,
            max_results: int = 20,
            sources: list[str] | None = None,
        )
        """
        show_info()
        captured = capsys.readouterr()

        # 提取 get_literature_relations 部分
        lines = captured.out.split("\n")
        in_relations = False
        param_line = None

        for line in lines:
            if "4. get_literature_relations" in line:
                in_relations = True
            elif in_relations and "参数：" in line:
                param_line = line
                break
            elif in_relations and "5." in line:
                break

        assert param_line is not None, "未找到 get_literature_relations 参数行"

        # 验证关键参数存在
        assert "identifier" in param_line, f"参数行应包含 identifier，实际: {param_line}"
        assert "relation_types" in param_line, f"参数行应包含 relation_types，实际: {param_line}"

        # 不应该有 max_depth
        assert "max_depth" not in param_line, f"参数行不应包含 max_depth，实际: {param_line}"

    @pytest.mark.unit
    def test_get_journal_quality_params_correct(self, capsys):
        """测试 get_journal_quality 参数描述正确

        实际签名: async def get_journal_quality_async(
            journal_name: str,
            include_metrics: list[str] | None = None,
            use_cache: bool = True,
        )
        """
        show_info()
        captured = capsys.readouterr()

        # 提取 get_journal_quality 部分
        lines = captured.out.split("\n")
        in_quality = False
        param_line = None

        for line in lines:
            if "5. get_journal_quality" in line:
                in_quality = True
            elif in_quality and "参数：" in line:
                param_line = line
                break

        assert param_line is not None, "未找到 get_journal_quality 参数行"

        # 验证关键参数存在
        assert "journal_name" in param_line, f"参数行应包含 journal_name，实际: {param_line}"
        assert "include_metrics" in param_line, f"参数行应包含 include_metrics，实际: {param_line}"

        # 不应该有旧的参数
        assert "journals" not in param_line, f"参数行不应包含 journals，实际: {param_line}"
        assert "operation" not in param_line, f"参数行不应包含 operation，实际: {param_line}"
        assert "evaluation_criteria" not in param_line, (
            f"参数行不应包含 evaluation_criteria，实际: {param_line}"
        )

    @pytest.mark.unit
    def test_show_info_mentions_parameter_tolerance(self, capsys):
        """测试 show_info 提及参数容错特性"""
        show_info()
        captured = capsys.readouterr()

        # 验证参数容错特性被提及
        assert "参数容错" in captured.out or "自动修正" in captured.out, (
            "show_info 应该提及参数容错特性"
        )

    @pytest.mark.unit
    def test_show_info_displays_data_sources(self, capsys):
        """测试 show_info 显示数据源信息"""
        show_info()
        captured = capsys.readouterr()

        # 验证主要数据源被提及
        assert "Europe PMC" in captured.out or "europe_pmc" in captured.out
        assert "PubMed" in captured.out or "pubmed" in captured.out
        assert "arXiv" in captured.out or "arxiv" in captured.out
        assert "CrossRef" in captured.out or "crossref" in captured.out
        assert "OpenAlex" in captured.out or "openalex" in captured.out
