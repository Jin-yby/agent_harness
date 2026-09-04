import json
import os
import requests
import subprocess

API_KEY="sk-954b985639774ee2bce7991423e35443"
BASE_URL="https://api.deepseek.com/v1"
MAX_HISTORY_LENGTH = 20  # 保留最近20条消息
MEMORY_FILE = "agent_memory.json"
#工具定义

tools =[
    {
        "type":"function",
        "function":{
            "name":"write_file",
            "description":"write content to a file",
            "parameters":{
                "type":"object",
                "properties":{
                    "filename":{"type":"string","description":"File name"},
                    "content":{"type":"string","description":"Content to write"}
                },
                "required":["filename","content"]
            }
        }
    },

    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"Read content from a file",
            "parameters":{
                "type":"object",
                "properties":{
                    "filename":{"type":"string","description":"File name"}
                },
                "required":["filename"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a terminal command and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The terminal command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    # 在 tools 列表里添加
    {
        "type": "function",
        "function": {
            "name": "remember_me",
            "description": "记住用户告诉你的重要信息，比如名字、喜好、要求等",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "要记住的事实"}
                },
                "required": ["fact"]
            }
        }


    }



]

#工具执行函数
def write_file(filename,content):
    try:
        with open(filename,'w',encoding="utf-8") as f:
            f.write(content)
        return f"File'{filename}'written successfully"
    except Exception as e:
        return f"Error:{e}"

def read_file(filename,content):
    try:
        with open(filename,'w',encoding='utf-8')as f:
            f.write(content)
            return f"File'{filename}' written successfully"
    except Exception as e:
        return f"Error:{e}"

def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"❌ File '{filename}' not found"
    except Exception as e:
        return f"❌ Error: {e}"

def run_bash(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        return output if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "❌ Command timed out after 30 seconds"
    except Exception as e:
        return f"❌ Error: {e}"

def execute_tool_call(tool_name,arguments):
    try:
        if tool_name=="run_bash":
            result= run_bash(arguments["command"])
        if tool_name=="write_file":
            return write_file(arguments["filename"],arguments["content"])
        elif tool_name=="read_file":
            return read_file(arguments["filename"])
        elif tool_name == "run_bash":  # 👈 新增
            return run_bash(arguments["command"])
        else:
            return f"Unknown tool:{tool_name}"
        return{
            "status":"success",
            "data":result
        }
    except Exception as e:
        return {
            "status": "error",
            "data": str(e)
        }

def trim_history(history):
    """裁剪历史，防止上下文溢出"""
    if len(history) > MAX_HISTORY_LENGTH:
        # 保留系统消息 + 最近的消息
        return history[-MAX_HISTORY_LENGTH:]
    return history

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"facts": []}

def save_memory(fact):
    memory = load_memory()
    memory["facts"].append(fact)
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def load_memory_as_prompt():
    memory = load_memory()
    facts = memory.get("facts", [])
    if not facts:
        return ""
    return "【长期记忆】以下是你之前了解到的事实，请参考：\n" + "\n".join(f"- {fact}" for fact in facts)

def remember_me(fact):
    save_memory(fact)
    return f"✅ 已记住：{fact}"

#======================Agent主循环===========================
def agent_loop(message,history=None):
    if history is None:
        history=[]
    history.append({"role":"user","content":message})

    while True:
        # 在调用 API 之前
        trimmed_history = trim_history(history)
        data = {
            "model": "deepseek-v4-flash",
            "messages": trimmed_history,  # 用裁剪后的
            "tools": tools,
            "tool_choice": "auto"
        }

        #调用API
        headers={
            "Content-Type":"application/json",
            "Authorization":f"Bearer {API_KEY}"
        }

        data = {
            "model": "deepseek-v4-flash",
            "messages": history,
            "tools": tools,
            "tool_choice": "auto"
        }

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            print(f"API错误：{response.status_code}")
            print(response.text)
            return None,history

        result=response.json()
        reply=result["choices"][0]["message"]

        #把回复加入历史
        history.append(reply)

        # 检查是否有工具调用
        if "tool_calls" in reply and reply["tool_calls"]:
            tool_calls=reply["tool_calls"]

            for tool_call in tool_calls:
                func_name=tool_call["function"]["name"]
                arguments=json.loads(tool_call["function"]["arguments"])

                print(f"🔧 调用工具: {func_name}({arguments})")
                # 执行工具
                tool_result = execute_tool_call(func_name, arguments)

                # 把工具结果加入历史
                # 带上状态
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result["data"] if tool_result[
                                                          "status"] == "success" else f"❌ 执行失败: {tool_result['data']}"
                })


        # 继续循环，让 LLM 处理工具结果
        else:
            # 没有工具调用，返回最终回答
            return reply.get("content", ""), history


# ========== 运行 ==========

if __name__ == "__main__":
    print("🤖 Agent with Tools 已启动")
    print("可用工具: write_file, read_file")
    print("输入 exit 退出\n")

    history = []

    while True:
        user_input = input("你: ")
        if user_input == "exit":
            print("👋 再见！")
            break

        reply, history = agent_loop(user_input, history)
        if reply:
            print(f"AI: {reply}\n")
