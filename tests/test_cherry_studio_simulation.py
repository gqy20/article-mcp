#!/usr/bin/env python3
"""
模拟Cherry Studio的MCP调用方式
"""

import subprocess
import json
import time
import os

def simulate_cherry_studio_calls():
    """模拟Cherry Studio的MCP调用序列"""

    print("🍒 Cherry Studio调用模拟测试")
    print("=" * 60)

    # 1. 初始化调用
    print("1. 🚀 模拟初始化请求...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "Cherry Studio",
                "version": "1.0.0"
            }
        }
    }

    # 2. 工具列表请求
    print("2. 📋 模拟工具列表请求...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    # 3. 测试原版本
    print("3. 🔍 测试原版本 (v0.1.3):")
    test_server("原版本", "article-mcp", ["server"], [init_request, tools_request])

    print()
    
    # 4. 测试修复版本
    print("4. 🔧 测试修复版本:")
    test_server("修复版", "python", ["test_fixed_mcp.py"], [init_request, tools_request])

def test_server(name, command, args, requests):
    """测试服务器的MCP响应"""
    
    print(f"   测试 {name}...")
    
    try:
        # 启动服务器进程
        process = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        # 等待服务器启动
        time.sleep(1)

        for i, request in enumerate(requests):
            try:
                # 发送请求
                request_json = json.dumps(request)
                print(f"     发送请求 {i+1}: {request['method']}")
                
                process.stdin.write(request_json + "\n")
                process.stdin.flush()

                # 读取响应
                response_lines = []
                timeout_counter = 0
                while timeout_counter < 10:  # 最多等待5秒
                    line = process.stdout.readline()
                    if line:
                        try:
                            response = json.loads(line.strip())
                            response_lines.append(response)
                            
                            if "result" in response:
                                if request["method"] == "initialize":
                                    server_info = response["result"]["serverInfo"]
                                    print(f"     ✅ 初始化成功: {server_info['name']} v{server_info['version']}")
                                elif request["method"] == "tools/list":
                                    tools = response["result"].get("tools", [])
                                    print(f"     ✅ 工具列表: {len(tools)} 个工具")
                                    
                                    # 检查工具描述长度
                                    for tool in tools[:3]:  # 只检查前3个
                                        desc_len = len(tool.get("description", ""))
                                        status = "⚠️" if desc_len > 500 else "✅"
                                        print(f"        {status} {tool['name']}: {desc_len} 字符")
                                break
                            elif "error" in response:
                                print(f"     ❌ 错误: {response['error']}")
                                break
                        except json.JSONDecodeError:
                            # 可能是启动信息或其他非JSON输出
                            if "FastMCP" in line:
                                continue
                            print(f"     ⚠️  非JSON响应: {line.strip()[:50]}...")
                    else:
                        timeout_counter += 0.5
                        time.sleep(0.5)
                
                if timeout_counter >= 10:
                    print(f"     ⚠️  请求 {i+1} 超时")
                    
            except Exception as e:
                print(f"     ❌ 请求 {i+1} 失败: {e}")

        # 清理进程
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    except FileNotFoundError:
        print(f"     ❌ 命令未找到: {command}")
    except Exception as e:
        print(f"     ❌ 测试失败: {e}")

if __name__ == "__main__":
    simulate_cherry_studio_calls()
