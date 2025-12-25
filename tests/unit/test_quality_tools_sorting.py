"""期刊质量工具排序功能单元测试

测试 get_journal_quality 的排序功能：
- sort_by 参数：按不同指标排序
- sort_order 参数：升序/降序
- 边界情况处理
"""

import sys
from pathlib import Path

import pytest

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestJournalQualitySorting:
    """测试期刊质量排序功能"""

    @pytest.fixture
    def sample_batch_results(self):
        """模拟的批量期刊查询结果（无序）"""
        return {
            "success": True,
            "total_journals": 5,
            "successful_evaluations": 5,
            "cache_hits": 0,
            "cache_hit_rate": 0.0,
            "success_rate": 1.0,
            "journal_results": {
                "Journal B": {
                    "success": True,
                    "journal_name": "Journal B",
                    "quality_metrics": {
                        "impact_factor": 3.5,
                        "quartile": "Q2",
                        "jci": "1.5",
                        "cas_zone": "中科院二区",
                    },
                    "ranking_info": {"rank_in_category": 80},
                },
                "Journal A": {
                    "success": True,
                    "journal_name": "Journal A",
                    "quality_metrics": {
                        "impact_factor": 8.2,
                        "quartile": "Q1",
                        "jci": "3.5",
                        "cas_zone": "中科院一区",
                    },
                    "ranking_info": {"rank_in_category": 10},
                },
                "Journal C": {
                    "success": True,
                    "journal_name": "Journal C",
                    "quality_metrics": {
                        "impact_factor": 1.8,
                        "quartile": "Q4",
                        "jci": "0.8",
                        "cas_zone": "中科院四区",
                    },
                    "ranking_info": {"rank_in_category": 180},
                },
                "Journal D": {
                    "success": True,
                    "journal_name": "Journal D",
                    "quality_metrics": {
                        "impact_factor": 4.7,
                        "quartile": "Q1",
                        "jci": "2.1",
                        "cas_zone": "中科院一区",
                    },
                    "ranking_info": {"rank_in_category": 25},
                },
                "Journal E": {
                    "success": True,
                    "journal_name": "Journal E",
                    "quality_metrics": {
                        "impact_factor": 2.9,
                        "quartile": "Q3",
                        "jci": "1.2",
                        "cas_zone": "中科院三区",
                    },
                    "ranking_info": {"rank_in_category": 120},
                },
            },
            "processing_time": 1.5,
        }

    @pytest.mark.unit
    def test_sort_by_impact_factor_desc(self, sample_batch_results):
        """测试按影响因子降序排序（默认）"""
        # 直接测试 _apply_sorting 函数
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(sample_batch_results, sort_by="impact_factor", sort_order="desc")

        # 验证返回列表格式
        assert "journals" in result
        assert isinstance(result["journals"], list)

        # 验证排序：影响因子从高到低
        journal_names = [j["journal_name"] for j in result["journals"]]
        assert journal_names == ["Journal A", "Journal D", "Journal B", "Journal E", "Journal C"]

        # 验证排序信息
        assert result["sort_info"]["field"] == "impact_factor"
        assert result["sort_info"]["order"] == "desc"

    @pytest.mark.unit
    def test_sort_by_impact_factor_asc(self, sample_batch_results):
        """测试按影响因子升序排序"""
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(sample_batch_results, sort_by="impact_factor", sort_order="asc")

        # 验证排序：影响因子从低到高
        journal_names = [j["journal_name"] for j in result["journals"]]
        assert journal_names == ["Journal C", "Journal E", "Journal B", "Journal D", "Journal A"]

        assert result["sort_info"]["order"] == "asc"

    @pytest.mark.unit
    def test_sort_by_quartile_desc(self, sample_batch_results):
        """测试按分区降序排序（Q1 > Q2 > Q3 > Q4）"""
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(sample_batch_results, sort_by="quartile", sort_order="desc")

        # 验证排序：Q1 > Q2 > Q3 > Q4
        journal_names = [j["journal_name"] for j in result["journals"]]
        assert journal_names[0] in ["Journal A", "Journal D"]  # Q1 期刊在前
        assert journal_names[-1] in ["Journal C"]  # Q4 期刊在后

        assert result["sort_info"]["field"] == "quartile"

    @pytest.mark.unit
    def test_sort_by_jci(self, sample_batch_results):
        """测试按 JCI 指数排序"""
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(
            {
                **sample_batch_results,
                "journal_results": dict(list(sample_batch_results["journal_results"].items())[:3]),
            },
            sort_by="jci",
            sort_order="desc",
        )

        # JCI: A(3.5) > B(1.5) > C(0.8)
        journal_names = [j["journal_name"] for j in result["journals"]]
        assert journal_names == ["Journal A", "Journal B", "Journal C"]

    @pytest.mark.unit
    def test_sort_with_missing_metrics(self):
        """测试排序时处理缺失指标的情况"""
        results_with_missing = {
            "success": True,
            "total_journals": 3,
            "journal_results": {
                "Journal A": {
                    "success": True,
                    "journal_name": "Journal A",
                    "quality_metrics": {"impact_factor": 8.2, "quartile": "Q1"},
                },
                "Journal B": {
                    "success": True,
                    "journal_name": "Journal B",
                    "quality_metrics": {"quartile": "Q2"},  # 缺少 impact_factor
                },
                "Journal C": {
                    "success": True,
                    "journal_name": "Journal C",
                    "quality_metrics": {"impact_factor": 5.5, "quartile": "Q1"},
                },
            },
        }

        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(results_with_missing, sort_by="impact_factor", sort_order="desc")

        # 缺少指标的期刊应该排在最后
        journal_names = [j["journal_name"] for j in result["journals"]]
        assert journal_names[-1] == "Journal B"  # 缺少 IF 的排最后
        assert journal_names[0] == "Journal A"  # 有 IF 的排在前面

    @pytest.mark.unit
    def test_no_sort_returns_list(self, sample_batch_results):
        """测试不排序时也返回列表格式（统一格式）"""
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(sample_batch_results, sort_by=None)

        # 统一返回列表格式
        assert "journals" in result
        assert isinstance(result["journals"], list)
        assert len(result["journals"]) == 5
        assert result["sort_info"] is None  # 不排序时 sort_info 为 None

    @pytest.mark.unit
    def test_invalid_sort_by_field(self, sample_batch_results):
        """测试无效的排序字段"""
        from article_mcp.tools.core.quality_tools import _apply_sorting

        result = _apply_sorting(sample_batch_results, sort_by="invalid_field")

        # 无效字段也返回列表格式，sort_info 为 None
        assert "journals" in result
        assert isinstance(result["journals"], list)
        assert result["sort_info"] is None


class TestSortKeyFunction:
    """测试排序键值函数"""

    @pytest.mark.unit
    def test_quartile_order_mapping(self):
        """测试分区排序映射"""
        from article_mcp.tools.core.quality_tools import _get_quartile_order

        # Q1 > Q2 > Q3 > Q4
        assert _get_quartile_order("Q1") == 4
        assert _get_quartile_order("Q2") == 3
        assert _get_quartile_order("Q3") == 2
        assert _get_quartile_order("Q4") == 1

        # 中文分区
        assert _get_quartile_order("1区") == 4
        assert _get_quartile_order("2区") == 3
        assert _get_quartile_order("3区") == 2
        assert _get_quartile_order("4区") == 1

        # 无效分区
        assert _get_quartile_order("Unknown") == 0

    @pytest.mark.unit
    def test_get_sort_key_impact_factor(self):
        """测试获取影响因子排序键"""
        from article_mcp.tools.core.quality_tools import _get_sort_key

        journal_a = {"quality_metrics": {"impact_factor": 8.2}, "journal_name": "Journal A"}
        journal_b = {"quality_metrics": {"impact_factor": 3.5}, "journal_name": "Journal B"}
        journal_c = {"quality_metrics": {}, "journal_name": "Journal C"}  # 缺少 IF

        key_a = _get_sort_key(journal_a, "impact_factor")
        key_b = _get_sort_key(journal_b, "impact_factor")
        key_c = _get_sort_key(journal_c, "impact_factor")

        # 新格式：(has_value, value, journal_name)
        assert key_a == (1, 8.2, "Journal A")
        assert key_b == (1, 3.5, "Journal B")
        assert key_c == (0, 0, "Journal C")  # 缺失值排最后

        # 验证排序顺序（降序）
        assert key_a > key_b > key_c

    @pytest.mark.unit
    def test_get_sort_key_quartile(self):
        """测试获取分区排序键"""
        from article_mcp.tools.core.quality_tools import _get_sort_key

        journal_q1 = {"quality_metrics": {"quartile": "Q1"}, "journal_name": "Journal Q1"}
        journal_q2 = {"quality_metrics": {"quartile": "Q2"}, "journal_name": "Journal Q2"}
        journal_unknown = {"quality_metrics": {}, "journal_name": "Unknown"}

        key_q1 = _get_sort_key(journal_q1, "quartile")
        key_q2 = _get_sort_key(journal_q2, "quartile")
        key_unknown = _get_sort_key(journal_unknown, "quartile")

        # 新格式：(order, quartile, journal_name)
        assert key_q1 == (4, "Q1", "Journal Q1")
        assert key_q2 == (3, "Q2", "Journal Q2")
        assert key_unknown == (0, "", "Unknown")

        # 验证排序顺序
        assert key_q1 > key_q2 > key_unknown
