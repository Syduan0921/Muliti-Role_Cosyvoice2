"""
文本分割分类测评数据收集器
专门用于收集step1.json到step2.json流程中的badcase
适配测评网站的jsonl格式
"""
import json
from typing import Dict, List, Any, Optional
import os


class TextSplitEvalItem:
    """文本分割分类测评数据项"""
    
    def __init__(
        self,
        session_id: int,
        messages: List[Dict[str, Any]],
        reference_response: str,
        responses: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        self.session_id = session_id
        self.messages = messages
        self.reference_response = reference_response
        self.responses = responses or []
    
    def add_response(
        self,
        content: str,
        parameters: Dict[str, Any],
        usage: Dict[str, int],
        score: float,
        analysis: str
    ) -> None:
        """添加模型响应数据"""
        response_data = {
            "parameters": parameters,
            "usage": usage,
            "content": content,
            "score": score,
            "analysis": analysis
        }
        self.responses.append(response_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，适配测评网站输出格式"""
        # 构建完整的messages列表，包含assistant消息
        output_messages = []
        
        # 添加原始的system和user消息
        for msg in self.messages:
            output_messages.append(msg)
        
        # 添加assistant消息，包含reference_response和responses
        assistant_msg = {
            "role": "assistant",
            "reference_response": self.reference_response,
            "responses": self.responses
        }
        output_messages.append(assistant_msg)
        
        return {
            "session_id": self.session_id,
            "messages": output_messages
        }


class EvalCollector:
    """
    文本分割分类测评数据收集器
    专门用于收集文本分割分类流程中的badcase
    """
    
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.data = []
        self._load_file()
    
    def _load_file(self) -> None:
        """
        加载文件，支持多种格式
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self.data = []
                    return
                
                # 尝试解析为JSON数组
                try:
                    json_data = json.loads(content)
                    if isinstance(json_data, list):
                        self.data = json_data
                    else:
                        self.data = [json_data]
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，尝试按行解析jsonl
                    self.data = []
                    for line in content.split('\n'):
                        if line.strip():
                            try:
                                self.data.append(json.loads(line.strip()))
                            except json.JSONDecodeError:
                                continue
        except FileNotFoundError:
            self.data = []
        except Exception as e:
            print(f"加载文件时出错: {e}")
            self.data = []
    
    def add_text_split_case(
        self,
        context: str,
        clause: str,
        reference_response: str
    ) -> int:
        """
        添加文本分割分类样例
        参考LLM_prompt.py的封装方法构建system和user消息
        
        Args:
            context: 上下文文本
            clause: 待分类子句
            reference_response: 用户提供的期望响应，格式如 '[{"class": "语言", "content": "..."}]'
        
        Returns:
            session_id: 添加的样例ID
        """
        session_id = len(self.data)
        
        # 构建messages，参考LLM_prompt.py的格式
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的对话分析员。"
            },
            {
                "role": "user",
                "content": f"{context}"
            }
        ]
        
        # 创建测评数据项
        eval_item = TextSplitEvalItem(
            session_id=session_id,
            messages=messages,
            reference_response=reference_response
        )
        
        self.data.append(eval_item.to_dict())
        return session_id
    
    def add_from_step1(
        self,
        step1_file: str,
        item_id: int,
        reference_response: str
    ) -> Optional[int]:
        """
        从step1.json添加样例
        通过指定step1中的id和用户提供的reference_response来添加样例
        
        Args:
            step1_file: step1.json文件路径
            item_id: step1.json中的id
            reference_response: 用户提供的期望响应
        
        Returns:
            session_id: 成功添加的样例ID，失败返回None
        """
        try:
            # 加载step1数据
            with open(step1_file, "r", encoding="utf-8") as f:
                step1_data = json.load(f)
            
            # 查找对应的item
            step1_item = None
            for item in step1_data:
                if item.get("id") == item_id:
                    step1_item = item
                    break
            
            if not step1_item:
                print(f"未找到id为{item_id}的数据项")
                return None
            
            # 提取上下文和子句信息
            sentence = step1_item.get("sentence", "")
            sub_sentence = step1_item.get("sub_sentence", "")
            
            # 构建context_prompt
            ## 准备原始提示词
            with open("src/llm/prompts/fine_split_process.md", "r", encoding="utf-8") as f:
                ori_prompt = f.read()
                context_prompt = ori_prompt.format(context=sentence, clause=sub_sentence)
            context = context_prompt
            
            # 添加样例
            return self.add_text_split_case(context, sub_sentence, reference_response)
            
        except Exception as e:
            print(f"从step1添加数据时出错: {e}")
            return None
    
    def add_model_response(
        self, 
        session_id: int, 
        content: str, 
        parameters: Dict[str, Any], 
        usage: Dict[str, int], 
        score: float, 
        analysis: str
    ) -> bool:
        """
        为指定session添加模型响应数据
        """
        for item in self.data:
            if item.get("session_id") == session_id:
                # 找到对应的session，添加response
                for message in item.get("messages", []):
                    if message.get("role") == "assistant" and "responses" in message:
                        message["responses"].append({
                            "parameters": parameters,
                            "usage": usage,
                            "content": content,
                            "score": score,
                            "analysis": analysis
                        })
                        return True
        return False
    
    def write_file(self, jsonl_path: str | None = None) -> None:
        """
        写入文件jsonl格式
        """
        output_path = jsonl_path or self.file_path
        with open(output_path, "w", encoding="utf-8") as f:
            for item in self.data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计数据
        """
        total_cases = len(self.data)
        classes_count = {}
        responses_count = 0
        
        for item in self.data:
            for message in item.get("messages", []):
                if message.get("role") == "assistant":
                    reference_response = message.get("reference_response", "")
                    if "语言" in reference_response:
                        classes_count["语言"] = classes_count.get("语言", 0) + 1
                    elif "内心独白" in reference_response:
                        classes_count["内心独白"] = classes_count.get("内心独白", 0) + 1
                    elif "旁白" in reference_response:
                        classes_count["旁白"] = classes_count.get("旁白", 0) + 1
                    
                    responses_count += len(message.get("responses", []))
                    break  # 每个item只有一个assistant消息
        
        return {
            "total_cases": total_cases,
            "classes_distribution": classes_count,
            "total_responses": responses_count
        }


# 使用示例
if __name__ == "__main__":
    # 创建收集器
    collector = EvalCollector("text_split_eval.jsonl")
    
    # 示例1: 添加自定义文本分割样例
    # session_id = collector.add_text_split_case(
    #     context="他看着这面相，方彻忍不住就为前身相了个面",
    #     clause="这货必然偏激，爱走极端",
    #     reference_response='[{"class": "内心独白", "content": "这货必然偏激，爱走极端"}]'
    # )
    
    # 示例2: 从step1.json添加样例
    collector.add_from_step1(
        step1_file="examples/example1/step1.json",
        item_id=2,
        reference_response='[{"class": "语言", "content": "两周就回来，你要乖乖的。"}, {"class": "旁白", "content": "这是万敌临走前的最后一句话，甚至还顺手揉了揉白厄柔软的白发，动作轻柔得仿佛只是出门办件小事，而不是去继承什么该死的王位。"}]'
    )

    collector.add_from_step1(
        step1_file="examples/example1/step1.json",
        item_id=4,
        reference_response='[{"class": "语言", "content": "这算哪门子分手理由？"}, {"class": "旁白", "content": "白厄喃喃自语，手指无意识地卷着一缕白发，这个习惯性动作通常在他焦虑或思考时出现，"}, {"class": "语言", "content": "连编个像样的借口都不愿意吗？我就这么不值得一个认真的告别？"}]'
    )

    collector.add_from_step1(
        step1_file="examples/example1/step1.json",
        item_id=30,
        reference_response='[{"class": "旁白", "content": "白厄苦笑着举起新来的酒杯，手微微颤抖，酒液差点洒出来："}, {"class": "语言", "content": "为蹩脚的分手理由干杯！为我的天真干杯！"}, {"class": "旁白", "content": "他仰头一饮而尽，喉结随着吞咽动作上下滚动。"}]'
    )
    
    # 添加模型响应
    # collector.add_model_response(
    #     session_id=session_id,
    #     content='[{"class": "旁白", "content": "这货必然偏激，爱走极端"}]',
    #     parameters={"temperature": 1.0, "top_p": 0.7},
    #     usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    #     score=0.5,
    #     analysis="模型错误地将内心独白分类为旁白，没有识别出第一人称的心理活动特征。"
    # )
    
    # 写入文件
    collector.write_file()
    
    # 查看统计信息
    stats = collector.get_statistics()
    print("统计信息:", stats)
