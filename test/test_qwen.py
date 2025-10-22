"""
此时本地部署的qwen3.4b模型，需要进行测试
10.193.151.23: 15387 
预留接口为 http://10.193.151.23:15387/v1/chat/completions
"""
from openai import OpenAI
import requests
import json
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.template.LLM_prompt import LLM_prompt
    from src.template.BaseClassTemp.BaseClass import JsonObjCrud
except:
    from template.LLM_prompt import LLM_prompt
    from template.BaseClassTemp.BaseClass import JsonObjCrud

def test_qwen():
    """测试本地部署的Qwen模型"""
    url = "http://10.193.151.23:15387/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-3.4b",
        "messages": [{"role": "user", "content": "Hello, how are you?"}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()  # 检查HTTP状态码
        
        result = response.json()
        print("测试成功！")
        print(f"响应状态码: {response.status_code}")
        print(f"模型响应: {result}")
        
        # 检查响应结构
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0].get('message', {})
            content = message.get('content', '')
            print(f"回复内容: {content}")
            return {
                "success": True,
                "status_code": response.status_code,
                "response": result,
                "content": content
            }
        else:
            print("警告: 响应中没有找到choices字段")
            return {
                "success": False,
                "status_code": response.status_code,
                "response": result,
                "error": "No choices in response"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return {
            "success": False,
            "error": f"JSON decode error: {e}"
        }

def test_qwen_openai():
    """测试openai的接口是否可以正常连接到服务器"""
    url = "http://10.193.151.23:15387/v1"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-3.4b",
        "messages": [{"role": "user", "content": "Hello, how are you?"}]
    }
    agent = OpenAI(api_key="", base_url=url)
    resp = agent.chat.completions.create(
        model="qwen-3.4b",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        extra_body={"thinking": {"type": "disable"}}
    )   
    return resp.choices[0].message.content

def test_qwen_llm_prompt():
    """测试LLM_prompt类"""
    llm_prompt = LLM_prompt(api_key_default="", api_default="http://10.193.151.23:15387/v1")
    llm_prompt.update_api(None, None, api_faster = "qwen-3.4b", think_faster = "disable")
    # 构建数据样例
    ctx = JsonObjCrud(sub_sentence="“萧炎，斗之力，三段！级别：低级！”测验魔石碑之旁，一位中年男子，看了一眼碑上所显示出来的信息，语气漠然的将之公布了出来…", Sentence={"now_flag": 2, "sentence": ["“斗之力，三段！”", "望着测验魔石碑上面闪亮得甚至有些刺眼的五个大字，少年面无表情，唇角有着一抹自嘲，紧握的手掌，因为大力，而导致略微尖锐的指甲深深的刺进了掌心之中，带来一阵阵钻心的疼痛…", "“萧炎，斗之力，三段！级别：低级！”测验魔石碑之旁，一位中年男子，看了一眼碑上所显示出来的信息，语气漠然的将之公布了出来…", "中年男子话刚刚脱口，便是不出意外的在人头汹涌的广场上带起了一阵嘲讽的骚动。", "“三段？嘿嘿，果然不出我所料，这个“天才”这一年又是在原地踏步！”"]})
    resp = llm_prompt.use_prompt_with_class("fine_split_process", ctx)
    return resp[0].read_all()
    


if __name__ == "__main__":
    print("开始测试Qwen模型...")
    result = test_qwen_llm_prompt()
    print(f"\n测试结果: {result}")
