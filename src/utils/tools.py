import ast
import json
import re
from typing import List, Dict, Any

def mapping_windows_size(windows_size: int, list_id: int, list_length: int):
    """
    映射窗口大小到列表索引
    Args:
        windows_size: 窗口大小
        list_num: 列表索引
        list_length: 列表长度
    Returns:
        映射后的窗口大小
    """
    if list_id < windows_size:
        return list_id + windows_size + 1, list_id
    elif list_id >= list_length - windows_size:
        return windows_size - (list_id - list_length), windows_size
    else:
        return 2 * windows_size + 1, windows_size

def is_all_symbols(s: str) -> bool:
    """
    检测输入的字符串是否完全由符号组成（不含汉字、字母和数字）
    
    参数:
        s: 输入的字符串
        
    返回:
        如果字符串完全由符号组成则返回True，否则返回False
    """
    # 检查字符串是否为空
    if not s:
        return False  # 空字符串不视为由符号组成
    
    # 遍历字符串中的每个字符
    for char in s:
        # 判断字符是否为汉字、字母或数字
        # 汉字的Unicode范围：\u4e00-\u9fff
        if (char.isalnum() or  # 字母或数字
            '\u4e00' <= char <= '\u9fff'):  # 汉字
            return False
    
    # 所有字符都不是汉字、字母或数字，即完全由符号组成
    return True

def _strip_code_fences(text: str) -> str:
    """
    去除代码围栏标记（```json等）
    
    参数:
        text: 可能包含代码围栏的文本
    
    返回:
        去除围栏后的纯文本
    """
    if not text:
        return text
    
    # 匹配常见的代码块围栏格式
    pattern = r"^```[a-zA-Z]*\n([\s\S]*?)\n```\s*$"
    match = re.match(pattern, text.strip())
    return match.group(1).strip() if match else text

def parse_list_of_dicts(text: str) -> List[Dict[str, Any]] | bool:
    """
    解析模型输出的JSON字符串为字典列表
    
    参数:
        text: 模型输出的文本（可能包含JSON）
    
    返回:
        解析后的字典列表
    
    异常:
        解析失败时抛出ValueError
    

    解析顺序：
    1) 去围栏后尝试严格JSON解析；
    2) 失败则使用ast.literal_eval解析Python字面量；
    3) 再失败尝试提取首个方括号片段再JSON解析；
    4) 尝试修复常见的格式问题后再次解析；
    5) 最终失败抛出异常。
    """
    if text is None:
        return False

    normalized = _strip_code_fences(text).strip()
    print(f"去围栏后: {repr(normalized)}")  # 调试信息

    # 优先JSON
    try:
        parsed = json.loads(normalized)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("Parsed JSON is not a list")
        return [dict(item) for item in parsed]
    except Exception as e:
        print(f"JSON解析失败: {e}")  # 调试信息
        pass

    # 尝试Python字面量
    try:
        parsed_py = ast.literal_eval(normalized)
        if isinstance(parsed_py, dict):
            parsed_list = [parsed_py]
        elif isinstance(parsed_py, list):
            parsed_list = parsed_py
        else:
            raise ValueError("Literal is not list or dict")
        return [dict(item) for item in parsed_list]
    except Exception as e:
        print(f"Python字面量解析失败: {e}")  # 调试信息
        pass

    # 提取首个形如 [...] 的片段再尝试JSON
    bracket_match = re.search(r"\[[\s\S]*\]", normalized)
    if bracket_match:
        try:
            bracket_content = bracket_match.group(0)
            print(f"提取括号内容: {repr(bracket_content)}")  # 调试信息
            parsed = json.loads(bracket_content)
            if isinstance(parsed, dict):
                parsed = [parsed]
            if not isinstance(parsed, list):
                raise ValueError("Extracted JSON is not a list")
            return [dict(item) for item in parsed]
        except Exception as e:
            print(f"括号内容JSON解析失败: {e}")  # 调试信息
            pass

    # 尝试修复常见格式问题
    try:
        # 修复缺少引号的问题
        fixed_text = normalized
        # 如果class和content没有引号，尝试添加
        if '"class"' not in fixed_text and 'class' in fixed_text:
            fixed_text = re.sub(r'class:\s*([^,}\]]+)', r'"class": "\1"', fixed_text)
        if '"content"' not in fixed_text and 'content' in fixed_text:
            fixed_text = re.sub(r'content:\s*([^,}\]]+)', r'"content": "\1"', fixed_text)
        
        print(f"修复后文本: {repr(fixed_text)}")  # 调试信息
        
        # 再次尝试JSON解析
        parsed = json.loads(fixed_text)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("Fixed JSON is not a list")
        return [dict(item) for item in parsed]
    except Exception as e:
        print(f"修复后JSON解析失败: {e}")  # 调试信息
        pass

    print("错误：无法解析模型输出为List[Dict]格式，跳过此内容")
    return False

def replace_ta_to_name(ta_list: List, sub_sentence: str) -> str:
    """
    代词替换：将文本中的代词（他/她/它）替换为具体角色名
    
    参数:
        ta_list: 代词-角色映射列表，格式 [{"ta": "他", "name": "张三"}, ...]
        sub_sentence: 待处理的子句文本
    
    返回:
        替换后的文本字符串
    """
    if ta_list is None or len(ta_list) == 0:
        print(f"[WARN] 代词映射表为空，无法处理子句: {sub_sentence}")
        return sub_sentence
    
    result = ""
    index = 0
    sentence_len = len(sub_sentence)
    
    # 遍历文本字符
    while index < sentence_len:
        replaced = False
        
        # 尝试匹配所有代词映射项
        for ta_item in ta_list[:]:  # 使用副本遍历
            ta_str = ta_item["ta"]
            ta_len = len(ta_str)
            
            # 检查当前位置是否匹配当前代词
            if sub_sentence.startswith(ta_str, index):
                # 执行替换：添加角色名注释
                result += f"{ta_str}({ta_item['name']})"
                index += ta_len
                ta_list.remove(ta_item)  # 移除已使用的映射
                replaced = True
                break
        
        # 未匹配到代词，直接添加当前字符
        if not replaced:
            result += sub_sentence[index]
            index += 1
    
    return result

def check_sub_ta(ctx: str) -> bool:
    """
    检查文本是否包含待解析的代词
    
    参数:
        ctx: 待检查的文本
    
    返回:
        包含代词返回True，否则返回False
    """
    # 定义需要检测的代词列表
    pronouns = ["他", "她", "它", "你", "我", "自己", "ta", "您"]
    return any(pronoun in ctx for pronoun in pronouns)

def fine_grained_post_process(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    对可能存在的额外think删除
    """
    sub_sentence = ctx.get("text", "")
    if "<think>" in sub_sentence:
        sub_sentence = sub_sentence.split("<think>")[-1]
    if "</think>" in sub_sentence:
        sub_sentence = sub_sentence.split("</think>")[-1]
    if "\n" in sub_sentence:
        sub_sentence = sub_sentence.split("\n")[-1]
    return {"text": sub_sentence, "style": ctx.get("style", None)}

if __name__ == "__main__":
    print(mapping_windows_size(3, 9, 10))
