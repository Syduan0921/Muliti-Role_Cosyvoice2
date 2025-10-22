"""
基础类，服务于Eval LLM大模型的评价
"""
import json
from operator import index
import os
from typing import Any, List, Dict

class EvalClass:
    """
    包含元素
    origin_input: List[Dict[str, Any]] -> 指代LLM的基础输入，其已经被封装到可以被直接使用的message中
        例如：[
                    {"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的复杂文本进行分割，将其分为语言、内心独白和旁白。你还需要灵活利用上下文来判断，例如观察上文是否正在延续没有说完的话或思考，这会对你后续的判断产生很重要的影响。"},

                    {"role": "user", "content": XXX},
            ]
    ref_resp: List[Dict[Any]] -> 封装着希望回答的结果，当结果不分条的时候，其List只有一个元素，内部Dict可能包含着class与content，分别对应着分类与生成。
        例如：[
                    {"class": "旁白", "content": "白厄苦笑着举起新来的酒杯，手微微颤抖，酒液差点洒出来："}, 
                    {"class": "语言", "content": "为蹩脚的分手理由干杯！为我的天真干杯！"}, 
                    {"class": "旁白", "content": "他仰头一饮而尽，喉结随着吞咽动作上下滚动。"}
            ]
    """
    def __init__(self, task_id: int, origin_input: List[Dict[str, Any]] | None, ref_resp: List[Dict[str, Any]] | None) -> None:
        # 任务id，分别指代0-2, 0为分句任务，1为人称代换任务，2为语句分类任务， 3为润色优化任务。
        if not (task_id >= 0 and task_id < 4):
            raise print(f"任务Tag: {task_id} 不符合规范！")
        self.task_id = task_id
        self.origin_input = origin_input
        self.ref_resp = ref_resp
        self.resp = [] # 放置为空
        self.scores = [] # 放置为空，等待后续计算
        self.describe = None # 额外的篮子，等待额外的信息
    
    def write_task_id(self, task_id: int) -> None:
        """
        任务id，分别指代0-2, 0为分句任务，1为人称代换任务，2为语句分类任务， 3为润色优化任务。
        """
        if not (task_id >= 0 and task_id < 4):
            raise print(f"任务Tag: {task_id} 不符合规范！")
        self.task_id = task_id

    def write_origin_input(self, origin_input: Dict) -> None:
        """
        修改任务的原始输入
        """
        if self.task_id == 0:
            with open("src/llm/prompts/fine_split_process.md", "r", encoding="utf-8") as f:
                prompt = f.read()
                origin_input = prompt.format(context=origin_input.get("context", ""), clause=origin_input.get("clause", ""))
        else:
            raise print("错误")
        self.origin_input = origin_input

    def write_ref_resp(self, ref_resp: List[Dict[str, Any]]) -> None:
        """
        修改任务的参考输出
        """
        self.ref_resp = ref_resp

    def write_resp(self, resp: List[Dict[str, Any]]):
        """
        修改任务的真实输出
        """
        self.resp = resp
    
    def write_scores(self, scores: List):
        """
        修改任务的得分
        """
        self.scores = scores
    
    def write_describe(self, describe: Any):
        """
        修改任务的得分
        """
        self.describe = describe

    def update_all(self, ctx: Dict):
        """
        利用字典，批量的修改
        """
        if "task_id" in ctx:
            self.write_task_id(ctx.get("task_id", ""))
        if "origin_input" in ctx:
            self.write_origin_input(ctx.get("origin_input", ""))
        if "ref_resp" in ctx:
            self.write_ref_resp(ctx.get("ref_resp", ""))
        if "resp" in ctx:
            self.write_resp(ctx.get("resp", ""))
        if "scores" in ctx:
            self.write_scores(ctx.get("scores", ""))
        if "describe" in ctx:
            self.write_describe(ctx.get("describe", ""))

    def read_task_id(self) -> int:
        """
        任务id，分别指代0-2, 0为分句任务，1为人称代换任务，2为语句分类任务， 3为润色优化任务。
        """
        
        return self.task_id

    def read_origin_input(self) -> List[Dict[str, Any]]:
        """
        修改任务的原始输入
        """
        return self.origin_input

    def read_ref_resp(self) -> List[Dict[str, Any]]:
        """
        修改任务的参考输出
        """
        return self.ref_resp

    def read_resp(self) -> List[Dict[str, Any]]:
        """
        修改任务的真实输出
        """
        return self.resp
    
    def read_scores(self) -> List | None:
        """
        修改任务的得分
        """
        return self.scores
    
    def read_describe(self) -> Any | None:
        """
        修改任务的得分
        """
        return self.describe

    def read_all(self) -> Dict:
        return {
            "task_id": self.task_id,
            "origin_input": self.origin_input,
            "ref_resp": self.ref_resp,
            "resp": self.resp,
            "scores": self.scores,
            "describe": self.describe
        }
    

class EvalClassList:
    def __init__(self, save_path: str) -> None:
        """
        是一组EvalClass的核心组成格式，它可以随时通过to_list方法转化回去，其保留原始的记忆位置，并支持对每个元素的操作
        后续将添加检验代码
        """
        self.save_path = save_path
        # 例如[{id: 0, content: EvalClass}, {id: 1, content: EvalClass}]
        self.data: List[Dict[str, EvalClass]] = []
        self.reload_data()
    
    def reload_data(self) -> bool:
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding="utf-8") as f:
                    loaded = json.load(f)
                    if not isinstance(loaded, List):
                        print(f"JSON数据格式错误，必须是列表类型，当前类型为：{type(loaded)}")
                        return False
                    _data = loaded
                    self.data = [EvalClass() for i in range(len(_data))]
                    for i, item in enumerate(self.data):
                        item.update_all(_data[i]) 
                    return True
            except Exception as e:
                print(f"加载JSON数据时出错：{e}")
                return False

    def add_sample(self, ctx: EvalClass):
        self.data.append(ctx)
    
    def pop_sample(self, ids: int):
        if ids >= -1 and ids < len(self.data):
            self.data.pop(index=ids)
        else:
            raise print(f"删除不存在的元素{ids}！")
    
    def save_samples(self, save_path: str | None = None):
        try:
            if save_path:
                with open(save_path, 'w', encoding="utf-8") as f:
                    json.dump([item.read_all() for item in self.data], f, ensure_ascii=False, indent=4)
            else:
                with open(self.save_path, 'w', encoding="utf-8") as f:
                    json.dump([item.read_all() for item in self.data], f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise f"保存数据到文件时出错：{e}"
            return False
        return True

if __name__ == "__main__":
    data1 = EvalClass(task_id=0, origin_input=None,
    ref_resp=[{"class": "语言", "content": "'萧炎,斗之力,三段!级别:低级!'"}, {"class": "旁白", "content": "测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来..."}],
    )
    data1.write_origin_input({"content": "[上文]'斗之力,三段!' \n[上文]望着测验魔石碑上面闪亮得甚至有些刺眼的五个大字,少年面无表情,唇角有着一抹自嘲,紧握的手掌,因为大力,而导致略微尖锐的指甲深深的刺进了掌心之中,带来一阵阵钻心的疼痛… \n[当前]'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来... \n[下文]中年男子话刚刚脱口,便是不出意外的在人头汹涌的广场上带起了一阵嘲讽的骚动. \n[下文]'三段?嘿嘿,果然不出我所料,这个'天才'这一年又是在原地踏步!' \n[下文]'哎,这废物真是把家族的脸都给丢光了.' \n[下文]'要不是族长是他的父亲,这种废物,早就被驱赶出家族,任其自生自灭了,哪还有机会待在家族中白吃白喝.' \n[下文]'唉,昔年那名闻乌坦城的天才少年,如今怎么落魄成这般模样了啊?' \n", "clause": "'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来..."})
    EvalClassList_ctx = EvalClassList(save_path="examples\doupo\step1_eval.json")
    EvalClassList_ctx.add_sample(data1)
    EvalClassList_ctx.save_samples()


