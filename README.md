# 🤖 Agent Harness

从零手写的一个 AI Agent，不依赖任何框架（LangChain、AutoGen 等），仅使用 `requests` + `subprocess` 实现。

## ✨ 功能

- ✅ 文件读写 (`write_file`, `read_file`)
- ✅ 终端命令执行 (`run_bash`)
- ✅ Tool Calling（函数调用）
- ✅ Agent Loop（自主决策循环）
- ✅ 多步任务协同
- ✅ 对话历史管理

## 🛠️ 技术栈

- Python 3.10+
- DeepSeek API (兼容 OpenAI 接口)
- requests + subprocess（零框架依赖）

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/agent_harness.git
cd agent_harness

# 2. 安装依赖
pip install requests

# 3. 配置 API Key
# 修改 agent_with_tools.py 中的 API_KEY 和 BASE_URL

# 4. 运行
python agent_with_tools.py
