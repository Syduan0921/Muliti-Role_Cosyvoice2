"""
FreeTalk 核心管线，其主要功能为：
将给定的小说或任何长文本形式的内容转化为可语音化，可播放的形式。
"""
import os

try:
    from src.template.sentences_json import SentencesJsonListCrud, SentencesJsonCrud
    from src.utils.tools import is_all_symbols, check_sub_ta
    from src.template.LLM_prompt import LLM_prompt
    from src.template.BaseClassTemp.BaseClass import JsonObjCrud
except:
    from template.sentences_json import SentencesJsonListCrud, SentencesJsonCrud
    from utils.tools import is_all_symbols, check_sub_ta
    from template.LLM_prompt import LLM_prompt
    from template.BaseClassTemp.BaseClass import JsonObjCrud

class FreeTalkPipeline:
    """FreeTalk 核心管线类"""
    def __init__(self, file_path: str, coarse_length = 30, Windows_Size: int = 3) -> None:
        """
        初始化文本部分以及准备各类超参数，例如温度，Windows_Size等
        """
        self.file_path = file_path
        if not self.file_path and os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件路径 {self.file_path} 不存在")
        with open(file_path, "r", encoding="utf-8") as f:
            self.origin_text = f.read()
            self.origin_text = self.origin_text.strip().replace(" ", "")
        
        self.COARSE_LENGTH = coarse_length
        self.WINDOW_SIZE = Windows_Size
        self.data = SentencesJsonListCrud(Windows_Size=Windows_Size)
        self.LLM_prompt = LLM_prompt("3e0e9ea7-a110-4bfb-9b23-172318fa0e04")
    
    def forward(self):
        self.coarse_split_process()
        self.fine_split_process()
        self.batch_classify_role()
        self.fine_grained_text()

    def coarse_split_process(self) -> SentencesJsonListCrud:
        """
        步骤一，对原始文本进行粗粒度非AI处理，令其初步具备基础的Json List格式
        """

        # 首先，对原始文本进行粗分句，基于换行符号以及句长
        _coarse_sentence = self.origin_text.split("\n")
        _coarse_sentence = [s.strip() for s in _coarse_sentence if s.strip()]
        coarse_sentence, _temp_sentence = [], ""

        for i, item in enumerate(_coarse_sentence):
            if len(_temp_sentence) + len(item) < self.COARSE_LENGTH:
                _temp_sentence += item
                continue
            else:
                coarse_sentence.append("".join(_temp_sentence))
                _temp_sentence = ""
                _temp_sentence += item
        if _temp_sentence != "":
            coarse_sentence.append(_temp_sentence)
        ## 删除空的行以及只有符号的行
        coarse_sentence = [s for s in coarse_sentence if s and not is_all_symbols(s)]
        
        # 然后，简单管理前后文的array,建立基础的json_file
        for i, item in enumerate(coarse_sentence):
            self.data.create(i, {"class": None, "sub_sentence": item, "describe": {"role": None, "style": None}})

        #最后，保存备份当前进度。
        self.data.save_date("examples\example1\step1.json")
    
    def fine_split_process(self, reload_file_path: str | None = None) -> SentencesJsonListCrud:
        """
        第二步，使用api对每个句子进行细粒度处理，以赋予其真实的类别标签
        """
        # 首先，留下接口，当客户认为当前的data数据保存有误的时候，可以调用此函数重载
        if reload_file_path:
            self.data.load_data(reload_file_path)

        # 然后，人称处理，对句子中含有代词，例如"他"，则对其进行标注。
        for i, item in enumerate(self.data.data):
            if not check_sub_ta(item.read_sub_sentence()):
                continue
            ctx = self.LLM_prompt.use_prompt_with_class("classify_ta_name", item)
            item.write_origin_sub_sentence(ctx.read_origin_sub_sentence())
            print(f"代词新子句: {item.read_all()}")
        
        # 然后，开始调用api对现有现有粗颗粒度无类别结果进行处理。
        _data = SentencesJsonListCrud(Windows_Size=self.WINDOW_SIZE)

        for i, item in enumerate(self.data.data):
            ctx_list = self.LLM_prompt.use_prompt_with_class("fine_split_process", item)
            # 需要删除原先的整句，然后
            for ctx in ctx_list:
                #查看该子句是否为不可语音句子，也就是全空或者符号等
                if not ctx.read_sub_sentence() or is_all_symbols(ctx.read_sub_sentence()) or ctx.read_sub_sentence() == "":
                    print(f"生成不可语音化句子: {ctx.read_all()}")
                    continue
                print(f"创建新子句: {ctx.read_all()}")
                _data.create(None, {"class": ctx.read_class(), "sub_sentence": ctx.read_sub_sentence(), "origin_sub_sentence": item.read_origin_sub_sentence(), "describe": {"role": None, "style": None}})
        self.data = _data
        
        # 最后，保存备份当前进度。
        self.data.save_date("examples\example1\step2.json")
        return self.data

    
    def batch_classify_role(self, reload_file_path: str | None = None) -> SentencesJsonListCrud:
        # 首先，留下接口，当客户认为当前的data数据保存有误的时候，可以调用此函数重载
        if reload_file_path:
            self.data.load_data(reload_file_path)
        # 对之前分类为语言和内心独白的说话人进行分类，找出其真实的说话人姓名或者代号
        for i, item in enumerate(self.data.data):
            if item.read_class() not in ["语言", "内心独白"]:
                continue
            ctx = self.LLM_prompt.use_prompt_with_class("batch_classify_role", item)
            item.write_describe_role(ctx.read_describe_role())
            print(f"子句的说话人: {item.read_all()}")
        self.data.save_date("examples\example1\step3.json")

        # 合并之前的相同类型的连续子句
        _data = SentencesJsonListCrud(Windows_Size=self.WINDOW_SIZE)
        # 缓冲区
        _data_temp = JsonObjCrud()
        for i, item in enumerate(self.data.data):
            if i == 0:
                _data_temp.write_all(item.to_dict())
                continue
            if (_data_temp.read_class() == item.read_class() and _data_temp.read_describe_role() == item.read_describe_role()) or (_data_temp.read_describe_role() != None and _data_temp.read_describe_role() == item.read_describe_role()):
                # 可以合并
                _data_temp.write_sub_sentence(_data_temp.read_sub_sentence() + item.read_sub_sentence())
                class_name = item.read_class() if item.read_class() == "旁白" else "语言"
                _data_temp.write_class(class_name)
            else:
                _data.create(None, _data_temp.to_dict())
                _data_temp.write_all(item.to_dict())
        if _data_temp.read_sub_sentence != None:
                _data.create(None, _data_temp.to_dict())
        self.data = _data
        self.data.save_date("examples\example1\step3_5.json")

        return self.data

    
    def fine_grained_text(self, reload_file_path: str | None = None) -> SentencesJsonListCrud:
        """
        对当前的子句进行进一步润色，添加语气描述，语气词，扩张短句等
        """
        # 首先，留下接口，当客户认为当前的data数据保存有误的时候，可以调用此函数重载
        if reload_file_path:
            self.data.load_data(reload_file_path)
        
        for i, item in enumerate(self.data.data):
            if item.read_class() not in ["语言", "内心独白"]:
                continue
            ctx = self.LLM_prompt.use_prompt_with_class("fine_grained_process", item)
            item.write_sub_sentence(ctx.read_sub_sentence())
            item.write_describe_style(ctx.read_describe_style())
            print(f"子句的语气描述: {item.read_all()}")
        self.data.save_date("examples\example1\step4.json")

        return self.data
        



if __name__ == "__main__":
    pipeline = FreeTalkPipeline("examples\example1\origin.txt")
    pipeline.forward()

