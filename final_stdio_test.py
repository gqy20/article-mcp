#!/usr/bin/env python3
"""
最终版本的 stdio 模式功能测试
正确处理 MCP 协议响应格式
"""

import subprocess
import json
import time
import sys

def send_mcp_request(process, method, params=None, id=1):
    """发送 MCP 请求并等待响应"""
    request = {
        "jsonrpc": "2.0",
        "id": id,
        "method": method
    }
    if params:
        request["params"] = params

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    # 读取响应
    start_time = time.time()
    response = ""
    timeout = 60  # 60秒超时

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            return {"error": f"Process ended with code {process.returncode}"}

        line = process.stdout.readline()
        if not line:
            break

        response += line.strip()
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            continue

    return {"error": f"Timeout after {timeout} seconds"}

def extract_mcp_result(response):
    """从 MCP 响应中提取实际结果"""
    if "error" in response:
        return {"success": False, "error": response["error"]}

    if "result" not in response:
        return {"success": False, "error": "No result field in response"}

    result = response["result"]

    # 检查是否有 content 字段
    if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
        content = result["content"][0]
        if "text" in content:
            try:
                # 尝试解析 JSON 文本
                actual_result = json.loads(content["text"])
                return actual_result
            except json.JSONDecodeError:
                # 如果不是 JSON，直接返回文本
                return {"success": True, "message": content["text"]}

    # 如果不是标准格式，直接返回 result
    return result

def test_tool(process, tool_name, params, test_description):
    """测试单个工具"""
    print(f"\n🧪 测试: {test_description}")
    print(f"工具: {tool_name}")
    print(f"参数: {json.dumps(params, ensure_ascii=False, indent=6)}")

    try:
        response = send_mcp_request(
            process,
            "tools/call",
            {
                "name": tool_name,
                "arguments": params
            }
        )

        result = extract_mcp_result(response)

        if not result.get("success", False):
            print(f"❌ 失败: {result.get('error', result.get('message', '未知错误'))}")
            return False

        print(f"✅ 成功: {result.get('message', '操作完成')}")

        # 显示具体结果
        if "articles" in result and isinstance(result["articles"], list):
            print(f"📊 找到 {len(result['articles'])} 篇文献")
            if result["articles"]:
                first = result["articles"][0]
                if isinstance(first, dict):
                    title = first.get("title", "N/A")[:50]
                    print(f"   示例: {title}...")

        elif "article" in result and isinstance(result["article"], dict):
            article = result["article"]
            title = article.get("title", "N/A")[:50]
            print(f"📄 获取到文献详情: {title}...")

        elif "references" in result and isinstance(result["references"], list):
            print(f"📚 找到 {len(result['references'])} 条参考文献")

        elif "relations" in result and isinstance(result["relations"], dict):
            relations = result["relations"]
            total_refs = sum(len(relations.get(key, [])) for key in ["references", "similar", "citing"] if isinstance(relations.get(key), list))
            print(f"🔗 分析了文献关系，共 {total_refs} 条关联信息")

        elif "quality_metrics" in result and isinstance(result["quality_metrics"], dict):
            metrics = result["quality_metrics"]
            if metrics.get("impact_factor"):
                print(f"⭐ 影响因子: {metrics['impact_factor']}")
            if metrics.get("quartile"):
                print(f"📈 分区: {metrics['quartile']}")

        elif "processing_time" in result:
            print(f"⏱️ 处理时间: {result['processing_time']}s")

        elif "total_count" in result:
            print(f"📈 总结果数: {result['total_count']}")

        return True

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Article MCP v0.1.5 stdio 模式完整功能测试")
    print("=" * 70)

    # 启动服务器
    try:
        process = subprocess.Popen(
            ["uvx", "--from", ".", "article-mcp", "server", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        time.sleep(3)

        # 初始化
        init_response = send_mcp_request(process, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })

        if "error" in init_response:
            print(f"❌ 初始化失败: {init_response['error']}")
            return False

        print("✅ 服务器初始化成功")

        # 测试用例
        test_cases = [
            {
                "tool": "search_literature",
                "params": {"keyword": "COVID-19", "max_results": 2},
                "description": "1. 文献搜索功能"
            },
            {
                "tool": "get_article_details",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi"},
                "description": "2. 文献详情获取功能"
            },
            {
                "tool": "get_references",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi", "max_results": 3},
                "description": "3. 参考文献获取功能"
            },
            {
                "tool": "get_literature_relations",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi", "relation_types": ["references"], "max_results": 2},
                "description": "4. 文献关系分析功能"
            },
            {
                "tool": "get_journal_quality",
                "params": {"journal_name": "Nature"},
                "description": "5. 期刊质量评估功能"
            },
            {
                "tool": "export_batch_results",
                "params": {"results": [{"test": "data", "count": 1}], "format_type": "json"},
                "description": "6. 批量结果导出功能"
            }
        ]

        # 执行测试
        success_count = 0
        total_count = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} 测试 {i}/{total_count} {'='*20}")
            success = test_tool(
                process,
                test_case["tool"],
                test_case["params"],
                test_case["description"]
            )
            if success:
                success_count += 1
                print(f"✅ 测试 {i} 通过")
            else:
                print(f"❌ 测试 {i} 失败")

            # 测试间隔，避免API限制
            time.sleep(3)

        # 总结
        print("\n" + "=" * 70)
        print(f"📊 测试完成！")
        print(f"✅ 成功: {success_count}/{total_count} 个功能")
        print(f"❌ 失败: {total_count - success_count}/{total_count} 个功能")

        success_rate = (success_count / total_count) * 100
        print(f"📈 成功率: {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 大部分功能测试通过！Article MCP v0.1.5 stdio 模式工作正常。")
        elif success_rate >= 50:
            print("⚠️ 部分功能存在问题，但基本可用。")
        else:
            print("❌ 多个功能存在问题，需要进一步检查。")

        print(f"\n🔧 测试环境:")
        print(f"   - 包版本: Article MCP v0.1.5")
        print(f"   - 传输模式: stdio")
        print(f"   - 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        return success_rate >= 50

    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        return False
    finally:
        # 清理进程
        if 'process' in locals():
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print("✅ 服务器进程已停止")
            except:
                pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)