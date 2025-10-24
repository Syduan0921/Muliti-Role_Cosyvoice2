"""
对阶段1进行评估，调用LLM_prompt来调用api或者本地大模型。
然后使用EvalClassList来保存结果，并对最终结果进行评价
"""
import os, sys
from typing import Dict, List, Any
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.template.LLM_prompt import LLM_prompt
from src.template.BaseClassTemp.BaseEvalClass import EvalClass, EvalClassList


class EvalStepOne:
    def __init__(self, url: str, api_key: str | None, model_name: Dict, eval_path: str) -> None:
        self.url = url
        self.api_key = api_key
        # 格式为{"api": model, "think": False}
        self.model_name = model_name
        self.eval_path = eval_path
        self.data: EvalClassList = None
        self.agent = None
        self._load()

    def _load(self):
        """读取eval_path的数据"""
        try:
            self.data = EvalClassList(save_path=self.eval_path)
            self._api_load()

        except Exception as e:
            raise print(e)

    def _api_load(self):
        if self.api_key is None or self.api_key == "":
            api_key_default = os.getenv("VOLCENGINE_API_KEY", "")
        if self.url is None or self.url == "":
            raise print(f"给定url无效：{self.url}")
        if self.model_name is None or self.model_name == "":
            raise print(f"给定model_name无效：{self.model_name}")
        self.agent = LLM_prompt(api_key_default, self.url)
        # 修改step 1的api为我们需要的
        self.agent.update_api(api_key_default=None, api_default=None, api=self.model_name.get("api", ""), think=self.model_name.get("think", ""), api_faster=self.model_name.get("api", ""), think_faster=self.model_name.get("think", ""))

        
    def eval_step(self):
        """
        核心流程，负责将数据整合为LLM_prompt可以读取的格式
        """

        # 首先，对数据进行处理，让其可以正常输入
        _data: List[EvalClass] = self.data.data

        for i, ctx in enumerate(_data):
            content = message=ctx.read_origin_input()
            message = [{"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的复杂文本进行分割，将其分为语言、内心独白和旁白。你还需要灵活利用上下文来判断，例如观察上文是否正在延续没有说完的话或思考，这会对你后续的判断产生很重要的影响。"}, 
            {"role": "user", "content": content}]
            resp: List[Dict] = self.agent._classify_text_interface(prompt_template=None, ctx=None, message=message)
            if self.data.data[i].resp != [] and self.data.data[i].resp is not None:
                _resp = ctx.read_resp()
                _resp.append({"model": self.model_name, "resp": resp})
                self.data.data[i].write_resp(_resp)
            else:
                self.data.data[i].write_resp([{"model": self.model_name, "resp": resp}])
        self.data.save_samples()

    def score_step(self):
        """
        核心步骤2，将eval后的resp与ref_resp利用LLM中预留的接口，生成分数，并保存在Scores中，统计出总分与评价
        """
        # 准备eval_prompt
        with open("src/llm/prompts/evaluate_model_response.md", "r", encoding="utf-8") as f:
            prompt = f.read()
        # 首先准备好所有需要的数据
        ## 初始化所有模型的scores结果
        _scores_global = {}
        for i, ctx in enumerate(self.data.data):
            ref_resp: List[Dict[str, Any]] = ctx.read_ref_resp()
            resp_all_model: List[Dict[str, Any]] = ctx.read_resp()
            ori_input = ctx.read_origin_input()
            for j, resp in enumerate(resp_all_model):
                model_message = resp.get("model", "")
                resp_message = resp.get("resp", "")
                message = prompt.format(sentence=ori_input, reference_response=ref_resp, response=resp_message)
                scores = self.agent._evaluate_model_response(_prompt=message, ctx=None)[0]
                # 写入分值
                ## 临时列表写入
                if model_message.get("api", "") not in _scores_global.keys():
                    _scores_global[model_message.get("api", "")] = [int(scores.get("score"))]
                else:
                    _scores_global[model_message.get("api", "")].append(int(scores.get("score")))
                ## 写入文件
                now_scores = ctx.read_scores()
                if now_scores is not None and now_scores != []:
                    now_scores.append({"model": model_message, "scores": scores})
                    self.data.data[i].write_scores(now_scores)
                else:
                    now_scores = [{"model": model_message, "scores": scores}]
                    self.data.data[i].write_scores(now_scores)
        self.data.save_samples()
        ### 整理模型输出eval结果
        for index in _scores_global:
            avg_scores = _scores_global[index]
            avg_scores = sum(avg_scores) / len(avg_scores)
            print(f"模型: {index}的平均得分为{avg_scores}!")

        


if __name__ == "__main__":
    eval_one = EvalStepOne(url="https://ark.cn-beijing.volces.com/api/v3", api_key=None, model_name={"api": "doubao-seed-1-6-thinking-250715", "think": "enabled"}, eval_path="examples\eval\step1_eval.json")
    # eval_one = EvalStepOne(url="http://10.193.151.23:15387/v1", api_key=None, model_name={"api": "qwen3", "think": "disable"}, eval_path="examples\eval\step1_eval.json")
    eval_one.score_step()
    # eval_one.eval_step()
    flag = 1