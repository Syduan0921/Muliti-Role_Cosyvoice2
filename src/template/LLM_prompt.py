import copy
import os, sys
from typing import Any, Dict, List
from openai import OpenAI
import langchain

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from template.BaseClassTemp.BaseEvalClass import EvalClass
    from template.BaseClassTemp.BaseClass import JsonObjCrud
    from utils.tools import fine_grained_post_process, parse_list_of_dicts, replace_ta_to_name
except:
    from src.template.BaseClassTemp.BaseEvalClass import EvalClass
    from src.template.BaseClassTemp.BaseClass import JsonObjCrud
    from src.utils.tools import fine_grained_post_process, parse_list_of_dicts, replace_ta_to_name

class LLM_prompt:
    """
    LLM_prompt类，用于定义LLM的提示接口模板
    """
    def __init__(self, api_key_default:str, api_default: str = "https://ark.cn-beijing.volces.com/api/v3", prompt_path: str = "src\llm\prompts") -> None:
        """
        预留的LLM提示词模板列表
        默认使用火山引擎
        """
        # 读取prompt_path目录下的所有文件
        self.prompt_list = os.listdir(prompt_path)
        self.api_key_default = api_key_default
        self.api_default = api_default
        self.api, self.api_faster = {"api": "doubao-seed-1-6-thinking-250715", "think": "enabled"}, {"api": "doubao-seed-1-6-250615", "think": "disable"}
        try:
            self.client = OpenAI(
                api_key=self.api_key_default,
                base_url=self.api_default
            )
        except Exception as e:
            raise Exception(f"初始化OpenAI API失败：{e}")
        # 过滤所有md文件
        self.prompt_path_list = [os.path.join(prompt_path, prompt) for prompt in self.prompt_list if prompt.endswith(".md")]
        self.prompt_list = []
        for prompt_path in self.prompt_path_list:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                self.prompt_list.append({"class": prompt_path.split("\\")[-1].split(".")[0], "prompt": prompt})
        # 打印所有提示词模板
        print(self.prompt_list)
        # 初始化openai api
        
    def update_api(self, api_key_default: str | None, api_default: str | None, api: str | None = None, think: str | None = None, api_faster: str | None = None, think_faster: str | None = None):
        self.api_key_default = api_key_default if api_key_default is not None else self.api_key_default
        self.api_default = api_default if api_default is not None else self.api_default
        self.api = {"api": api, "think": think} if api is not None and think is not None else self.api
        self.api_faster = {"api": api_faster, "think": think_faster} if api_faster is not None and think_faster is not None else self.api_faster
        try:
            self.client = OpenAI(
                api_key=self.api_key_default,
                base_url=self.api_default
            )
        except Exception as e:
            print(f"更新OpenAI API失败：{e}")

    def _default_api_interface(self, prompt_full: str) -> Any:
        """
        内部类，所有的提示词接口，当其出现问题时，需要采用默认的api接口处理该逻辑，则需要通过这个接口实现
        """
        completion = self.client.chat.completions.create(
            model=self.api["api"],
            messages=[
                {"role": "system", "content": "你是一个专业的对话分析员，下面根据任务对现有文本进行标注！"},

                {"role": "user", "content": prompt_full},
            ],
            extra_body = {"thinking": {"type": self.api["think"]}} if self.api["think"] != "disable" else None
        )
        raw = completion.choices[0].message.content
        return raw
    
    def _classify_text_interface(self, prompt_template: str, ctx: JsonObjCrud, message: List[Dict[str, str]] | None = None) -> JsonObjCrud:
        """
        分类文本接口
        ctx: 包含文本分类任务的上下文信息
        返回值:
        ctx
        """
        if message is not None:
            # 如果提供了message参数，直接使用
            _prompt = message
            completion = self.client.chat.completions.create(
                model=self.api_faster["api"],
                messages=message,
                extra_body = {"thinking": {"type": self.api_faster["think"]}} if self.api_faster["think"] != "disable" else None
            )
        else:
            # 否则使用默认的消息结构
            context, clause = ctx.read_sentence(), ctx.read_sub_sentence()
            _prompt = prompt_template.format(context=context, clause=clause)
            completion = self.client.chat.completions.create(
                model=self.api_faster["api"],
                messages=[
                    {"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的复杂文本进行分割，将其分为语言、内心独白和旁白。你还需要灵活利用上下文来判断，例如观察上文是否正在延续没有说完的话或思考，这会对你后续的判断产生很重要的影响。"},

                    {"role": "user", "content": _prompt},
                ],
                extra_body = {"thinking": {"type": self.api_faster["think"]}} if self.api_faster["think"] != "disable" else None
            )
        raw = completion.choices[0].message.content
        ctx = parse_list_of_dicts(raw)
        if not ctx:
            _max_times, i = 3, 0
            while not ctx and i < _max_times:
                raw = self._default_api_interface(_prompt)
                ctx = parse_list_of_dicts(raw)
                i += 1
            if not ctx:
                raise ValueError(f"分类文本接口调用{_max_times}次均失败")
        return ctx

    def _classify_ta_name(self, prompt_template: str, ctx: JsonObjCrud) -> List[Dict[str, str]]:
        """
        代词-角色映射解析
    
    参数:
    
    返回:
        代词-角色映射列表，格式[{"ta":代词, "name":角色名}]
        """
        context, clause = ctx.read_sentence(), ctx.read_origin_sub_sentence()
        _prompt = prompt_template.format(context=context, clause=clause)
        completion = self.client.chat.completions.create(
            model=self.api["api"],
            messages=[
                {"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的代词替换为具体的说话人."},

                {"role": "user", "content": _prompt},
            ],
            extra_body = {"thinking": {"type": self.api["think"]}} if self.api["think"] != "disable" else None
        )
        ctx = parse_list_of_dicts(completion.choices[0].message.content)
        if not ctx:
            _max_times, i = 3, 0
            while not ctx and i < _max_times:
                raw = self._default_api_interface(_prompt)
                ctx = parse_list_of_dicts(raw)
                i += 1
            if not ctx:
                raise ValueError(f"分类文本接口调用{_max_times}次均失败")
        return ctx
            
    def _batch_classify_role(self, prompt_template: str, ctx: JsonObjCrud) -> List[Dict[str, Any]]:
        context, clause = ctx.read_sentence(), ctx.read_sub_sentence()
        _prompt = prompt_template.format(context=context, clause=clause)
        completion = self.client.chat.completions.create(
            # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
            model=self.api["api"],
            messages=[
                {"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的代词替换为具体的说话人。"},

                {"role": "user", "content": _prompt},
            ],
            extra_body = {"thinking": {"type": self.api["think"]}} if self.api["think"] != "disable" else None
        )
        response = {"describe": {"role": completion.choices[0].message.content}}
        return response

    def _fine_grained_text_interface(self, prompt_template: str, ctx: JsonObjCrud) -> Dict[str, Any]:
        context, clause = ctx.read_sentence(), ctx.read_sub_sentence()
        _prompt = prompt_template.format(context=context, clause=clause)
        completion = self.client.chat.completions.create(
        # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
        model=self.api["api"],
        messages=[
            {"role": "system", "content": "你是一个专业的台本润色员"},
            {"role": "user", "content": _prompt},
        ],
        extra_body = {"thinking": {"type": self.api["think"]}} if self.api["think"] != "disable" else None
        )
        raw_output = completion.choices[0].message.content
        raw_output = raw_output.replace(" ", "")
        return fine_grained_post_process({"text": raw_output, "style": None})
    
    def _evaluate_model_response(self, prompt_class: str, ctx: EvalClass) -> EvalClass:
        """
        对模型响应进行评估
        """
        completion = self.client.chat.completions.create(
        # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
        model=self.api["api"],
        messages=[
            {"role": "system", "content": "你是一个专业的评审人员"},
            {"role": "user", "content": prompt_class},
        ],
        extra_body = {"thinking": {"type": self.api["think"]}} if self.api["think"] != "disable" else None
        )
        raw_output = completion.choices[0].message.content
        ctx = parse_list_of_dicts(raw_output)
        if not ctx:
            _max_times, i = 3, 0
            while not ctx and i < _max_times:
                raw = self._default_api_interface(_prompt)
                ctx = parse_list_of_dicts(raw)
                i += 1
            if not ctx:
                raise ValueError(f"分类文本接口调用{_max_times}次均失败")
        return ctx
        

    def eval_with_class(self, prompt_class: str, ctx: EvalClass):
        """
        对给定的几个接口进行badcase测试，并评分
        """
        # 查找评估模型响应的提示词
        eval_prompt_items = [item for item in self.prompt_list if item["class"] == "evaluate_model_response"]
        if not eval_prompt_items:
            raise ValueError("未找到 evaluate_model_response 提示词模板")
        eval_prompt = eval_prompt_items[0]["prompt"]
        
        # 查找指定的提示词类别
        prompt_template = None
        for prompt in self.prompt_list:
            if prompt["class"] == prompt_class:
                prompt_template = prompt["prompt"]
                break
        
        if not prompt_template:
            raise ValueError(f"未找到类名为 {prompt_class} 的提示词模板")
        
        ## 使用api调用prompt
        if prompt_class == "fine_split_process":
            # 这里返回的一定是一个List[JsonObjCrud]对象，因此需要对_classify_text_interface的结果做后处理
            feedback = self._classify_text_interface(None, None, message=ctx.read_origin_input())
            sentence, reference_response, response = ctx.read_origin_input(), ctx.read_ref_resp(), feedback
            eval_prompt = eval_prompt.format(sentence=sentence, reference_response=reference_response, response=response)
            resp = self._evaluate_model_response(eval_prompt, ctx)[0]
            
        elif prompt_class == "classify_ta_name":
            pass
        elif prompt_class == "batch_classify_role":
            pass
        elif prompt_class == "fine_grained_process":
            pass
        else:
            raise ValueError(f"不支持的提示词类别: {prompt_class}")
            
        return resp

    def use_prompt_with_class(self, prompt_class: str, ctx: JsonObjCrud) -> List[JsonObjCrud] | JsonObjCrud:
        """
        根据提示词模板的类名，返回对应的提示词模板
        """
        for prompt in self.prompt_list:
            if prompt["class"] == prompt_class:
                prompt_template = prompt["prompt"]
                ## 使用api调用prompt
                if prompt_class == "fine_split_process":
                    # 这里返回的一定是一个List[JsonObjCrud]对象，因此需要对_classify_text_interface的结果做后处理
                    feedback = self._classify_text_interface(prompt_template, ctx)
                    ctx_list = []
                    for item in feedback:
                        _new_ctx = copy.deepcopy(ctx)
                        _new_ctx.write_sub_sentence(item["content"])
                        _new_ctx.write_class(item["class"])
                        ctx_list.append(_new_ctx)
                    return ctx_list
                elif prompt_class == "classify_ta_name":
                    feedback = self._classify_ta_name(prompt_template, ctx)
                    _new_ctx_sentence = ctx.read_origin_sub_sentence()
                    _new_ctx_sentence = replace_ta_to_name(feedback, _new_ctx_sentence)
                    ctx.write_origin_sub_sentence(_new_ctx_sentence)
                    return ctx
                elif prompt_class == "batch_classify_role":
                    feedback = self._batch_classify_role(prompt_template, ctx)
                    ctx.write_describe_role(feedback.get("describe", {}).get("role", ""))
                    return ctx
                elif prompt_class == "fine_grained_process":
                    feedback = self._fine_grained_text_interface(prompt_template, ctx)
                    ctx.write_sub_sentence(feedback.get("text", ""))
                    return ctx
                break
        raise ValueError(f"未找到类名为{prompt_class}的提示词模板")
