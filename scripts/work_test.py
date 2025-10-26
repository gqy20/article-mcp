#!/usr/bin/env python3
"""
工作功能测试 - 快速检查脚本
这是 test_working_functions.py 的简化别名
"""

import sys
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 导入并运行工作功能测试
from test_working_functions import main

if __name__ == "__main__":
    sys.exit(main())