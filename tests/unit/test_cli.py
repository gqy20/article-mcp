#!/usr/bin/env python3
"""
CLI单元测试
测试命令行接口功能
"""

# 导入要测试的CLI模块
import sys
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402

from article_mcp.cli import create_mcp_server  # noqa: E402
from article_mcp.cli import main
from article_mcp.cli import run_test
from article_mcp.cli import show_info
from article_mcp.cli import start_server
from tests.utils.test_helpers import TestTimer  # noqa: E402


class TestCLIBasics:
    """CLI基础功能测试"""

    @pytest.mark.unit
    def test_create_mcp_server(self):
        """测试MCP服务器创建"""
        with patch("article_mcp.cli.FastMCP") as mock_fastmcp:
            mock_server = Mock()
            mock_fastmcp.return_value = mock_server

            # 模拟服务创建
            with patch.multiple(
                "article_mcp.cli",
                create_europe_pmc_service=Mock(),
                create_pubmed_service=Mock(),
                CrossRefService=Mock(),
                OpenAlexService=Mock(),
                create_reference_service=Mock(),
                create_literature_relation_service=Mock(),
                create_arxiv_service=Mock(),
                register_search_tools=Mock(),
                register_article_tools=Mock(),
                register_reference_tools=Mock(),
                register_relation_tools=Mock(),
                register_quality_tools=Mock(),
                register_batch_tools=Mock(),
            ):
                server = create_mcp_server()

                # 验证服务器创建
                mock_fastmcp.assert_called_once_with("Article MCP Server", version="2.0.0")
                assert server is not None

    @pytest.mark.unit
    def test_show_info(self, capsys):
        """测试显示信息功能"""
        show_info()
        captured = capsys.readouterr()

        # 验证输出内容
        assert "Article MCP 文献搜索服务器" in captured.out
        assert "基于 FastMCP 框架" in captured.out
        assert "支持搜索 Europe PMC" in captured.out
        assert "🚀 核心功能" in captured.out

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_test(self):
        """测试运行测试功能"""
        with patch("article_mcp.cli.create_mcp_server") as mock_create:
            mock_server = Mock()
            mock_create.return_value = mock_server

            result = await run_test()

            # 验证测试结果
            assert result is True
            mock_create.assert_called_once()


class TestServerCommands:
    """服务器命令测试"""

    @pytest.fixture
    def mock_server(self):
        """模拟MCP服务器"""
        server = Mock()
        server.run = Mock()
        return server

    @pytest.mark.unit
    def test_start_server_stdio(self, mock_server, capsys):
        """测试stdio模式启动服务器"""
        with patch("article_mcp.cli.create_mcp_server", return_value=mock_server):
            start_server(transport="stdio")

            captured = capsys.readouterr()
            assert "启动 Article MCP 服务器" in captured.out
            assert "stdio 传输模式" in captured.out
            mock_server.run.assert_called_once_with(transport="stdio")

    @pytest.mark.unit
    def test_start_server_sse(self, mock_server, capsys):
        """测试SSE模式启动服务器"""
        with patch("article_mcp.cli.create_mcp_server", return_value=mock_server):
            start_server(transport="sse", host="localhost", port=9000)

            captured = capsys.readouterr()
            assert "启动 Article MCP 服务器" in captured.out
            assert "SSE 传输模式" in captured.out
            assert "http://localhost:9000/sse" in captured.out
            mock_server.run.assert_called_once_with(transport="sse", host="localhost", port=9000)

    @pytest.mark.unit
    def test_start_server_streamable_http(self, mock_server, capsys):
        """测试Streamable HTTP模式启动服务器"""
        with patch("article_mcp.cli.create_mcp_server", return_value=mock_server):
            start_server(transport="streamable-http", host="0.0.0.0", port=8080, path="/api")

            captured = capsys.readouterr()
            assert "启动 Article MCP 服务器" in captured.out
            assert "Streamable HTTP 传输模式" in captured.out
            assert "http://0.0.0.0:8080/api" in captured.out
            mock_server.run.assert_called_once_with(
                transport="streamable-http", host="0.0.0.0", port=8080, path="/api"
            )

    @pytest.mark.unit
    def test_start_server_invalid_transport(self, capsys):
        """测试无效传输模式"""
        with pytest.raises(SystemExit):
            start_server(transport="invalid")


class TestArgumentParsing:
    """参数解析测试"""

    @pytest.fixture
    def mock_args(self):
        """模拟命令行参数"""

        class MockArgs:
            def __init__(
                self, command=None, transport="stdio", host="localhost", port=9000, path="/mcp"
            ):
                self.command = command
                self.transport = transport
                self.host = host
                self.port = port
                self.path = path

        return MockArgs()

    @pytest.mark.unit
    def test_parse_server_command(self, mock_args):
        """测试解析服务器命令"""
        mock_args.command = "server"
        mock_args.transport = "sse"
        mock_args.host = "0.0.0.0"
        mock_args.port = 8080

        with patch("article_mcp.cli.start_server") as mock_start:
            with patch(
                "sys.argv",
                [
                    "article_mcp",
                    "server",
                    "--transport",
                    "sse",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8080",
                ],
            ):
                main()

        # 验证参数传递正确
        mock_start.assert_called_once_with(transport="sse", host="0.0.0.0", port=8080, path="/mcp")

    @pytest.mark.unit
    def test_parse_test_command(self, mock_args):
        """测试解析测试命令"""
        mock_args.command = "test"

        with patch("article_mcp.cli.run_test", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = True
            with patch("sys.argv", ["article_mcp", "test"]):
                main()

        mock_run.assert_called_once()

    @pytest.mark.unit
    def test_parse_info_command(self, mock_args):
        """测试解析信息命令"""
        mock_args.command = "info"

        with patch("article_mcp.cli.show_info") as mock_show:
            with patch("sys.argv", ["article_mcp", "info"]):
                main()

        mock_show.assert_called_once()

    @pytest.mark.unit
    def test_parse_no_command(self, capsys):
        """测试无命令参数"""
        with patch("sys.argv", ["article_mcp"]):
            main()

        capsys.readouterr()
        # 应该显示帮助信息


class TestCLIErrorHandling:
    """CLI错误处理测试"""

    @pytest.mark.unit
    def test_keyboard_interrupt_handling(self):
        """测试键盘中断处理"""
        with patch("article_mcp.cli.start_server", side_effect=KeyboardInterrupt()):
            with patch("sys.argv", ["article_mcp", "server"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_server_start_error(self):
        """测试服务器启动错误"""
        with patch("article_mcp.cli.start_server", side_effect=Exception("Server error")):
            with patch("sys.argv", ["article_mcp", "server"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_test_command_error(self):
        """测试命令错误"""
        with patch("article_mcp.cli.run_test", side_effect=Exception("Test error")):
            with patch("sys.argv", ["article_mcp", "test"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1


class TestCLIIntegration:
    """CLI集成测试"""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_full_server_startup_sequence(self):
        """测试完整的服务器启动序列"""
        with TestTimer() as timer:
            mock_server = Mock()

            with patch.multiple(
                "article_mcp.cli",
                create_europe_pmc_service=Mock(return_value=Mock()),
                create_pubmed_service=Mock(return_value=Mock()),
                CrossRefService=Mock(),
                OpenAlexService=Mock(),
                create_reference_service=Mock(return_value=Mock()),
                create_literature_relation_service=Mock(return_value=Mock()),
                create_arxiv_service=Mock(return_value=Mock()),
                register_search_tools=Mock(),
                register_article_tools=Mock(),
                register_reference_tools=Mock(),
                register_relation_tools=Mock(),
                register_quality_tools=Mock(),
                register_batch_tools=Mock(),
                FastMCP=Mock(return_value=mock_server),
            ):
                start_server(transport="stdio")

        # 验证启动时间合理
        assert timer.stop() < 5.0  # 应该在5秒内完成
        mock_server.run.assert_called_once()

    @pytest.mark.unit
    def test_service_dependency_injection(self):
        """测试服务依赖注入"""
        with patch("article_mcp.cli.FastMCP") as mock_fastmcp:
            mock_server = Mock()
            mock_fastmcp.return_value = mock_server

            # 模拟各种服务
            mock_services = {
                "create_europe_pmc_service": Mock(return_value=Mock()),
                "create_pubmed_service": Mock(return_value=Mock()),
                "CrossRefService": Mock(return_value=Mock()),
                "OpenAlexService": Mock(return_value=Mock()),
                "create_reference_service": Mock(return_value=Mock()),
                "create_literature_relation_service": Mock(return_value=Mock()),
                "create_arxiv_service": Mock(return_value=Mock()),
            }

            with patch.multiple("article_mcp.cli", **mock_services):
                create_mcp_server()

            # 验证所有服务都被创建
            for _service_name, service_mock in mock_services.items():
                if callable(service_mock):
                    service_mock.assert_called()


class TestCLIConfiguration:
    """CLI配置测试"""

    @pytest.mark.unit
    def test_default_configuration(self):
        """测试默认配置"""
        with patch("article_mcp.cli.start_server") as mock_start:
            with patch("sys.argv", ["article_mcp", "server"]):
                main()

        # 验证默认配置
        mock_start.assert_called_once_with(
            transport="stdio", host="localhost", port=9000, path="/mcp"
        )

    @pytest.mark.unit
    def test_configuration_overrides(self):
        """测试配置覆盖"""
        with patch("article_mcp.cli.start_server") as mock_start:
            with patch(
                "sys.argv",
                [
                    "article_mcp",
                    "server",
                    "--transport",
                    "sse",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8080",
                    "--path",
                    "/api",
                ],
            ):
                main()

        # 验证配置覆盖
        mock_start.assert_called_once_with(transport="sse", host="0.0.0.0", port=8080, path="/api")
