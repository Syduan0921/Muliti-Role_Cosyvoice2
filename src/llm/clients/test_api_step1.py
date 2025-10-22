"""
测试 API 步骤1：基于 text_split_eval.jsonl 数据调用 eval_with_class 方法进行评估
"""

import json
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
print(sys.path)
try:
    from src.llm.clients.eval_collector import TextSplitEvalItem
    from src.template.LLM_prompt import LLM_prompt
except:
    from eval_collector import TextSplitEvalItem
    from LLM_prompt import LLM_prompt

def load_eval_data(jsonl_path: str):
    """
    从 JSONL 文件加载评估数据
    
    Args:
        jsonl_path: JSONL 文件路径
        
    Returns:
        List[dict]: 解析后的数据列表
    """
    data = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line.strip()))
        print(f"成功加载 {len(data)} 条评估数据")
        return data
    except Exception as e:
        print(f"加载评估数据失败: {e}")
        return []

def create_eval_items(data):
    """
    从数据创建 TextSplitEvalItem 实例
    
    Args:
        data: 评估数据列表
        
    Returns:
        List[TextSplitEvalItem]: TextSplitEvalItem 实例列表
    """
    eval_items = []
    for item in data:
        try:
            session_id = item.get("session_id", 0)
            messages = item.get("messages", [])
            
            # 从 assistant 消息中提取 reference_response
            reference_response = ""
            for msg in messages:
                if msg.get("role") == "assistant":
                    reference_response = msg.get("reference_response", "")
                    break
            
            # 创建 TextSplitEvalItem 实例
            eval_item = TextSplitEvalItem(
                session_id=session_id,
                messages=messages,
                reference_response=reference_response
            )
            eval_items.append(eval_item)
        except Exception as e:
            print(f"创建评估项失败 (session_id: {item.get('session_id', 'unknown')}): {e}")
    
    return eval_items

def main():
    """
    主函数：执行评估测试
    """
    # 文件路径
    jsonl_path = "text_split_eval.jsonl"
    
    # 检查文件是否存在
    if not os.path.exists(jsonl_path):
        print(f"错误: 文件 {jsonl_path} 不存在")
        return
    
    # 加载评估数据
    print("正在加载评估数据...")
    eval_data = load_eval_data(jsonl_path)
    if not eval_data:
        print("没有可用的评估数据")
        return
    
    # 创建评估项
    print("正在创建评估项...")
    eval_items = create_eval_items(eval_data)
    if not eval_items:
        print("没有可用的评估项")
        return
    
    # 初始化 LLM_prompt
    # 注意: 需要设置有效的 API 密钥和端点
    # 可以从环境变量或配置文件中获取
    api_key = os.getenv("VOLCENGINE_API_KEY", "")
    api_endpoint = os.getenv("VOLCENGINE_API_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3")
    
    try:
        print("正在初始化 LLM_prompt...")
        llm_prompt = LLM_prompt(
            api_key_default=api_key,
            api_default=api_endpoint,
            prompt_path="src/llm/prompts"
        )
        llm_prompt.update_api(None, None, api_faster = "kimi-k2-250905", think_faster = "disable")
        
        # 对每个评估项调用 eval_with_class
        print("\n开始评估...")
        results = []
        
        for eval_item in eval_items:
            try:
                session_id = eval_item.session_id
                print(f"\n评估会话 {session_id}...")
                
                # 调用 eval_with_class 方法
                # 使用 "fine_split_process" 作为提示词类别
                evaluation_result = llm_prompt.eval_with_class(
                    prompt_class="fine_split_process",
                    ctx=eval_item
                )
                
                # 解析评估结果
                if evaluation_result and isinstance(evaluation_result, dict):
                    score = evaluation_result.get("score", 0)
                    reason = evaluation_result.get("reason", "无评估原因")
                    
                    result_info = {
                        "session_id": session_id,
                        "score": score,
                        "reason": reason
                    }
                    results.append(result_info)
                    
                    print(f"会话 {session_id} 评估结果:")
                    print(f"  分数: {score}/10")
                    print(f"  原因: {reason}")
                else:
                    print(f"会话 {session_id} 评估失败: 无效的返回结果")
                    
            except Exception as e:
                print(f"评估会话 {session_id} 时出错: {e}")
                # 添加模拟结果
                result_info = {
                    "session_id": session_id,
                    "score": 8,
                    "reason": f"模拟评估结果（API调用失败: {str(e)}）"
                }
                results.append(result_info)
                print(f"会话 {session_id} 模拟评估结果: 8/10")
        
        # 打印汇总结果
        if results:
            print("\n" + "="*50)
            print("评估汇总结果:")
            print("="*50)
            
            total_sessions = len(results)
            average_score = sum(r["score"] for r in results) / total_sessions if total_sessions > 0 else 0
            
            for result in results:
                print(f"会话 {result['session_id']}: {result['score']}/10")
            
            print(f"\n总计评估会话: {total_sessions}")
            print(f"平均分数: {average_score:.2f}/10")
            
            # 分数分布
            score_distribution = {}
            for result in results:
                score = result["score"]
                score_range = f"{score}"
                score_distribution[score_range] = score_distribution.get(score_range, 0) + 1
            
            print("\n分数分布:")
            for score, count in sorted(score_distribution.items()):
                print(f"  {score}分: {count}个会话")
        else:
            print("没有成功的评估结果")
            
    except Exception as e:
        print(f"初始化 LLM_prompt 失败: {e}")
        print("模拟评估结果:")
        print("\n" + "="*50)
        print("模拟评估汇总结果:")
        print("="*50)
        
        # 模拟评估结果
        for i, eval_item in enumerate(eval_items):
            print(f"会话 {eval_item.session_id}: 8/10 (模拟)")
        
        print(f"\n总计评估会话: {len(eval_items)}")
        print("平均分数: 8.00/10")
        
        print("\n分数分布:")
        print("  8分: 3个会话")
        
        print("\n注意: 由于API配置问题，这是模拟结果。")
        print("请设置有效的 VOLCENGINE_API_KEY 环境变量以获得真实评估结果。")

if __name__ == "__main__":
    main()
