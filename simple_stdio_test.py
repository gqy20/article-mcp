#!/usr/bin/env python3
"""
简单的 stdio 模式测试
"""

import subprocess
import json
import time
import signal
import sys

def test_stdio_server():
    """测试 stdio 服务器是否能正常启动和响应"""
    print("🚀 测试 Article MCP v0.1.5 stdio 模式服务器启动...")

    # 启动服务器
    try:
        process = subprocess.Popen(
            ["uvx", "--from", ".", "article-mcp", "server", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print("✅ 服务器进程已启动，PID:", process.pid)

        # 等待服务器完全启动
        time.sleep(3)

        # 发送初始化消息
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print("📤 发送初始化请求...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # 读取响应（带超时）
        start_time = time.time()
        response = ""
        timeout = 10

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                stderr = process.stderr.read()
                print(f"❌ 进程意外结束，返回码: {process.returncode}")
                print(f"错误输出: {stderr}")
                return False

            line = process.stdout.readline()
            if line:
                response += line.strip()
                try:
                    parsed = json.loads(response)
                    print("✅ 收到有效响应:", json.dumps(parsed, indent=2, ensure_ascii=False))
                    break
                except json.JSONDecodeError:
                    continue

        if not response:
            print("❌ 未收到响应")
            return False

        # 测试工具列表
        print("\n📋 测试获取工具列表...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()

        # 读取工具列表响应
        start_time = time.time()
        tools_response = ""

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                break

            line = process.stdout.readline()
            if line:
                tools_response += line.strip()
                try:
                    parsed = json.loads(tools_response)
                    result = parsed.get("result", {})
                    tools = result.get("tools", []) if isinstance(result, dict) else []
                    print(f"✅ 发现 {len(tools)} 个工具:")
                    for tool in tools:
                        if isinstance(tool, dict):
                            name = tool.get('name', 'Unknown')
                            desc = tool.get('description', 'No description')
                            print(f"   - {name}: {desc[:50]}...")
                        else:
                            print(f"   - {tool}")
                    break
                except json.JSONDecodeError:
                    continue

        if not tools_response:
            print("❌ 未收到工具列表响应")
            return False

        print("\n🎉 stdio 模式基本功能测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
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
    success = test_stdio_server()
    sys.exit(0 if success else 1)