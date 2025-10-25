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

    def write_origin_input(self, origin_input: Dict | str) -> None:
        """
        修改任务的原始输入
        """
        if self.task_id == 0:
            if isinstance(origin_input, Dict):
                with open("src/llm/prompts/fine_split_process.md", "r", encoding="utf-8") as f:
                    prompt = f.read()
                    origin_input = prompt.format(context=origin_input.get("context", ""), clause=origin_input.get("clause", ""))
            else:
                origin_input = origin_input
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
        if "task_id" in ctx.keys():
            self.write_task_id(ctx.get("task_id", ""))
        if "origin_input" in ctx.keys():
            self.write_origin_input(ctx.get("origin_input", ""))
        if "ref_resp" in ctx.keys():
            self.write_ref_resp(ctx.get("ref_resp", ""))
        if "resp" in ctx.keys():
            self.write_resp(ctx.get("resp", ""))
        if "scores" in ctx.keys():
            self.write_scores(ctx.get("scores", ""))
        if "describe" in ctx.keys():
            self.write_describe(ctx.get("describe", ""))

    def read_task_id(self) -> int:
        """
        任务id，分别指代0-2, 0为分句任务，1为人称代换任务，2为语句分类任务， 3为润色优化任务。
        """
        
        return self.task_id

    def read_origin_input(self) -> str:
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
                    self.data = []
                    _data = loaded
                    for i, item in enumerate(_data):
                        self.data.append(EvalClass(task_id=item.get("task_id", 0), origin_input=None, ref_resp=None))
                        self.data[-1].update_all(item) 
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

    def transfer_jsonl(self, save_file):
        # 首先整理数据为需要格式
        instruct = "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的复杂文本进行分割，将其分为语言、内心独白和旁白。你还需要灵活利用上下文来判断，例如观察上文是否正在延续没有说完的话或思考，这会对你后续的判断产生很重要的影响。"
        think, metrics = "", {"quality_f1": 1}
        _data = self.data
        with open(save_file, "w", encoding="utf-8") as f:
            for i, ctx in enumerate(_data):
                ori_input = ctx.read_origin_input()
                answer = ctx.read_ref_resp()
                preload_data = {"instruct": instruct, "question": ori_input, "think": think, "answer": answer, "metrics": metrics}
                ## 开始写入jsonl
                json.dump(preload_data, f, ensure_ascii=False)
                f.write('\n')



if __name__ == "__main__":
    EvalClassList_ctx = EvalClassList(save_path="examples\eval\\train_data.json")

    EvalClassList_ctx.transfer_jsonl(save_file="examples\eval\\train.jsonl")

    # data11 = EvalClass(task_id=0, origin_input=None,
    # ref_resp=[{"class": "语言", "content": "'这坛酒埋了二十年，今天该开封了'"}, {"class": "旁白", "content": "赵老抚摸着酒坛上的封泥，指缝里还沾着田埂的泥土"}])
    # data11.write_origin_input({"context": "[上文] 秋收后的晒谷场空落落的，只有墙角堆着几捆稻草，赵老扛着锄头刚从地里回来，裤脚还沾着露水… \n [当前] '这坛酒埋了二十年，今天该开封了' 赵老抚摸着酒坛上的封泥，指缝里还沾着田埂的泥土这坛酒埋了二十年 \n [下文] 孙子蹦蹦跳跳地跑过来，手里拿着两个粗瓷碗，嚷嚷着要尝尝爷爷的藏酒 \n [下文] 赵老笑骂着推开他的手：' 小孩子家喝什么酒，去把你爹叫回来 ' \n", "clause": "'这坛酒埋了二十年，今天该开封了' 赵老抚摸着酒坛上的封泥，指缝里还沾着田埂的泥土这坛酒埋了二十年"})
    # EvalClassList_ctx.add_sample(data11)

    # data12 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这串钥匙怎么会在他口袋里？难道库房失窃是他干的？"}, {"class": "旁白", "content": "林管家捏着那串黄铜钥匙，指节因为用力而发白，烛火在他脸上投下晃动的阴影"}])
    # data12.write_origin_input({"context": "[上文] 深夜的书房里，老爷的咳嗽声断断续续传来，林管家端着汤药进来时，发现少爷的房门虚掩着，地上掉着个布包… \n [当前] 这串钥匙怎么会在他口袋里？难道库房失窃是他干的？林管家捏着那串黄铜钥匙，指节因为用力而发白这串钥匙怎么会在他口袋里 \n [下文] 布包里滚出几锭银子，正是库房丢失的那批，林管家的心沉了下去 \n [下文] 少爷的鼾声从房内传来，林管家犹豫着要不要立刻叫醒老爷 \n", "clause": "这串钥匙怎么会在他口袋里？难道库房失窃是他干的？林管家捏着那串黄铜钥匙，指节因为用力而发白这串钥匙怎么会在他口袋里"})
    # EvalClassList_ctx.add_sample(data12)

    # data13 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "戏台子上的锣鼓突然停了，扮相俊美的小生愣在原地，脸上的胭脂被冷汗冲开一道痕迹"}, {"class": "语言", "content": "'台下那位客官，您的玉佩掉了'"}])
    # data13.write_origin_input({"context": "[上文] 戏园子里座无虚席，喝彩声此起彼伏，台上正演到《霸王别姬》的高潮，虞姬拔剑自刎的身段引来满堂彩… \n [当前] 戏台子上的锣鼓突然停了，扮相俊美的小生愣在原地，脸上的胭脂被冷汗冲开一道痕迹 '台下那位客官，您的玉佩掉了' 戏台子上的锣鼓突然停了 \n [下文] 台下众人顺着他的目光看去，只见角落里一个黑衣男子正慌忙将手伸进袖袋 \n [下文] 小生突然提高声调：' 那可是大内侍卫的腰牌呢 ' \n", "clause": "戏台子上的锣鼓突然停了，扮相俊美的小生愣在原地，脸上的胭脂被冷汗冲开一道痕迹 '台下那位客官，您的玉佩掉了' 戏台子上的锣鼓突然停了"})
    # EvalClassList_ctx.add_sample(data13)

    # data14 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "'这株草药的叶脉纹路不对，怕是有毒'"}, {"class": "旁白", "content": "采药人拨开少年的手，将那株开着紫花的植物连根拔起，根茎处渗出乳白色的汁液"}])
    # data14.write_origin_input({"context": "[上文] 云雾缭绕的山腰上，少年背着竹篓跟在采药人身后，手里攥着刚摘的野果，不时好奇地打量路边的植物… \n [当前] '这株草药的叶脉纹路不对，怕是有毒' 采药人拨开少年的手，将那株开着紫花的植物连根拔起这株草药的叶脉纹路不对 \n [下文] 少年吐了吐舌头，刚才他差点就把这株草放进竹篓里了 \n [下文] 采药人将毒草扔进火堆：' 山里的草，看着像的未必是好东西 ' \n", "clause": "'这株草药的叶脉纹路不对，怕是有毒' 采药人拨开少年的手，将那株开着紫花的植物连根拔起这株草药的叶脉纹路不对"})
    # EvalClassList_ctx.add_sample(data14)

    # data15 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这封信的笔迹和爹临终前的字条一模一样，难道他还活着？"}, {"class": "旁白", "content": "婉儿展开信纸的手指在颤抖，烛泪滴在信纸上晕开一小片墨迹"}])
    # data15.write_origin_input({"context": "[上文] 镖局送来一个没有署名的木盒，婉儿打开时发现里面只有一封折叠的信纸，纸张已经有些发黄… \n [当前] 这封信的笔迹和爹临终前的字条一模一样，难道他还活着？婉儿展开信纸的手指在颤抖这封信的笔迹和爹临终前的字条一模一样 \n [下文] 信里只写了一句话：' 八月十五，老地方见 '，没有落款也没有日期 \n [下文] 婉儿猛地想起爹失踪那天也是八月十五，心口一阵发紧 \n", "clause": "这封信的笔迹和爹临终前的字条一模一样，难道他还活着？婉儿展开信纸的手指在颤抖这封信的笔迹和爹临终前的字条一模一样"})
    # EvalClassList_ctx.add_sample(data15)

    # data16 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "黄沙卷着碎石打在驼队的帐篷上，向导掀起帘子看了眼天色，将羊皮水袋往腰间紧了紧"}, {"class": "语言", "content": "' 沙尘暴要来了，赶紧把骆驼拴好 '"}])
    # data16.write_origin_input({"context": "[上文] 戈壁滩的日头正毒，商队的人们都躲在帐篷里休息，只有几个伙计在给骆驼喂草料… \n [当前] 黄沙卷着碎石打在驼队的帐篷上，向导掀起帘子看了眼天色，将羊皮水袋往腰间紧了紧 ' 沙尘暴要来了，赶紧把骆驼拴好 ' 黄沙卷着碎石打在驼队的帐篷上 \n [下文] 帐篷外传来一阵慌乱的脚步声，有人大喊着' 骆驼惊了 ' \n [下文] 向导骂了句脏话，抓起弯刀冲出去，风沙已经开始模糊视线 \n", "clause": "黄沙卷着碎石打在驼队的帐篷上，向导掀起帘子看了眼天色，将羊皮水袋往腰间紧了紧 ' 沙尘暴要来了，赶紧把骆驼拴好 ' 黄沙卷着碎石打在驼队的帐篷上"})
    # EvalClassList_ctx.add_sample(data16)

    # data17 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 这道符咒的朱砂里掺了雄鸡血，非同一般 '"}, {"class": "旁白", "content": "道长用指尖蘸着符纸上的朱砂，放在鼻尖轻嗅，眉头微微皱起"}])
    # data17.write_origin_input({"context": "[上文] 破庙里的香烛早已燃尽，只有供桌上还摆着一张泛黄的符咒，书生夜里避雨时发现它在发光… \n [当前] ' 这道符咒的朱砂里掺了雄鸡血，非同一般 ' 道长用指尖蘸着符纸上的朱砂，放在鼻尖轻嗅这道符咒的朱砂里掺了雄鸡血 \n [下文] 书生想起昨夜梦见的白衣女子，忍不住问道：' 道长，这符是用来镇什么的？' \n [下文] 道长没回答，只是从袖中取出桃木剑，在符纸周围画了个圈 \n", "clause": "' 这道符咒的朱砂里掺了雄鸡血，非同一般 ' 道长用指尖蘸着符纸上的朱砂，放在鼻尖轻嗅这道符咒的朱砂里掺了雄鸡血"})
    # EvalClassList_ctx.add_sample(data17)

    # data18 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "他袖口的绣纹和通缉令上的一样，难道是官府要抓的采花贼？"}, {"class": "旁白", "content": "酒楼小二端着托盘经过雅间时，眼角的余光瞥见客人露出的袖口，脚步顿了一下"}])
    # data18.write_origin_input({"context": "[上文] 县城的酒楼里人声鼎沸，说书先生正在讲采花贼夜闯王府的故事，听客们不时发出惊呼… \n [当前] 他袖口的绣纹和通缉令上的一样，难道是官府要抓的采花贼？酒楼小二端着托盘经过雅间时他袖口的绣纹和通缉令上的一样 \n [下文] 客人似乎察觉到了什么，猛地抬头瞪过来，小二吓得差点把托盘摔了 \n [下文] 掌柜的在柜台后咳嗽了一声，给小二使了个眼色，让他别多管闲事 \n", "clause": "他袖口的绣纹和通缉令上的一样，难道是官府要抓的采花贼？酒楼小二端着托盘经过雅间时他袖口的绣纹和通缉令上的一样"})
    # EvalClassList_ctx.add_sample(data18)

    # data19 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "雪落在梅枝上簌簌作响，大小姐披着狐裘站在庭院里，手里把玩着一枚暖玉"}, {"class": "语言", "content": "' 这梅花比去年开得晚了三天呢 '"}])
    # data19.write_origin_input({"context": "[上文] 深冬的清晨，丫鬟刚扫完廊下的积雪，就看见大小姐已经站在梅树下，呼出的白气在冷空气中很快消散… \n [当前] 雪落在梅枝上簌簌作响，大小姐披着狐裘站在庭院里，手里把玩着一枚暖玉 ' 这梅花比去年开得晚了三天呢 ' 雪落在梅枝上簌簌作响 \n [下文] 管家匆匆走来，手里捧着一个锦盒：' 小姐，京城来的贺礼送到了 ' \n [下文] 大小姐没回头，只是问：' 三公子的信到了吗？' \n", "clause": "雪落在梅枝上簌簌作响，大小姐披着狐裘站在庭院里，手里把玩着一枚暖玉 ' 这梅花比去年开得晚了三天呢 ' 雪落在梅枝上簌簌作响"})
    # EvalClassList_ctx.add_sample(data19)

    # data20 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 这船底的裂缝修补过，但手法太粗糙 '"}, {"class": "旁白", "content": "老船夫用篙子敲了敲船帮，浑浊的眼睛里闪过一丝警惕，水面泛起一圈圈涟漪"}])
    # data20.write_origin_input({"context": "[上文] 渡口的雾气还没散，穿黑袍的客人出双倍价钱要租船夜游，老船夫犹豫着解开了缆绳… \n [当前] ' 这船底的裂缝修补过，但手法太粗糙 ' 老船夫用篙子敲了敲船帮，浑浊的眼睛里闪过一丝警惕这船底的裂缝修补过 \n [下文] 黑袍客突然笑了：' 老人家好眼力，这船是我从河湾捡的 ' \n [下文] 老船夫握紧了篙子，悄悄将手摸向腰间的短刀 \n", "clause": "' 这船底的裂缝修补过，但手法太粗糙 ' 老船夫用篙子敲了敲船帮，浑浊的眼睛里闪过一丝警惕这船底的裂缝修补过"})
    # EvalClassList_ctx.add_sample(data20)

    # data21 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这枚令牌的缺口和师父临终前说的一样，难道他就是师兄？"}, {"class": "旁白", "content": "小和尚攥着怀里的令牌，指腹摩挲着那个月牙形的缺口，香火气在鼻尖萦绕"}])
    # data21.write_origin_input({"context": "[上文] 寺庙的钟声刚过午时，香客渐渐散去，小和尚在打扫庭院时发现石阶上放着个布包，里面只有半块令牌… \n [当前] 这枚令牌的缺口和师父临终前说的一样，难道他就是师兄？小和尚攥着怀里的令牌这枚令牌的缺口和师父临终前说的一样 \n [下文] 后山传来脚步声，一个背着行囊的中年男子站在月亮门那里，腰间挂着另一半令牌 \n [下文] 小和尚的心跳突然加速，想起师父说过师兄当年是被逐出师门的 \n", "clause": "这枚令牌的缺口和师父临终前说的一样，难道他就是师兄？小和尚攥着怀里的令牌这枚令牌的缺口和师父临终前说的一样"})
    # EvalClassList_ctx.add_sample(data21)

    # data22 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "铁匠铺的炉火映红了半个院子，王铁匠抡着锤子砸在烧红的铁块上，火星溅在他黧黑的脸上"}, {"class": "语言", "content": "' 这把刀要淬火三次，不然砍不断铁链 '"}])
    # data22.write_origin_input({"context": "[上文] 镇西头的铁匠铺叮当作响，穿囚服的汉子蹲在门口，看着王铁匠把一块铁坯烧得通红… \n [当前] 铁匠铺的炉火映红了半个院子，王铁匠抡着锤子砸在烧红的铁块上，火星溅在他黧黑的脸上 ' 这把刀要淬火三次，不然砍不断铁链 ' 铁匠铺的炉火映红了半个院子 \n [下文] 囚服汉子往炉子里添了块柴：' 王师傅，多给我淬几次，钱不是问题 ' \n [下文] 王铁匠哼了一声：' 不是钱的事，是规矩 ' \n", "clause": "铁匠铺的炉火映红了半个院子，王铁匠抡着锤子砸在烧红的铁块上，火星溅在他黧黑的脸上 ' 这把刀要淬火三次，不然砍不断铁链 ' 铁匠铺的炉火映红了半个院子"})
    # EvalClassList_ctx.add_sample(data22)

    # data23 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 这布的经纬里掺了蚕丝，遇水不会皱 '"}, {"class": "旁白", "content": "老板娘用指甲刮了刮布料的边缘，将样品往水盆里浸了浸，水面浮起一层细密的泡沫"}])
    # data23.write_origin_input({"context": "[上文] 绸缎庄刚到了一批新货，掌柜的正在盘点账目，穿青衫的客人拿着块布料翻来覆去地看… \n [当前] ' 这布的经纬里掺了蚕丝，遇水不会皱 ' 老板娘用指甲刮了刮布料的边缘这布的经纬里掺了蚕丝 \n [下文] 青衫客突然笑了：' 老板娘好眼力，这是贡品的料子 ' \n [下文] 掌柜的从账房探出头：' 客官要是诚心要，我给您打个八折 ' \n", "clause": "' 这布的经纬里掺了蚕丝，遇水不会皱 ' 老板娘用指甲刮了刮布料的边缘这布的经纬里掺了蚕丝"})
    # EvalClassList_ctx.add_sample(data23)

    # data24 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这串佛珠的颗数和方丈的一样，难道他是寺里的僧人？"}, {"class": "旁白", "content": "茶客盯着对面汉子手腕上的紫檀佛珠，看见他捻珠的手法十分娴熟，不像寻常香客"}])
    # data24.write_origin_input({"context": "[上文] 山脚下的茶馆里，说书先生刚讲完一段因果报应，茶客们正议论着城西的寺庙… \n [当前] 这串佛珠的颗数和方丈的一样，难道他是寺里的僧人？茶客盯着对面汉子手腕上的紫檀佛珠这串佛珠的颗数和方丈的一样 \n [下文] 汉子突然开口：' 施主好像对小僧的佛珠很感兴趣 '，声音里带着僧人的平和 \n [下文] 茶客脸一红，连忙端起茶杯掩饰自己的失态 \n", "clause": "这串佛珠的颗数和方丈的一样，难道他是寺里的僧人？茶客盯着对面汉子手腕上的紫檀佛珠这串佛珠的颗数和方丈的一样"})
    # EvalClassList_ctx.add_sample(data24)

    # data25 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "马车在石板路上颠簸着，货郎掀开布帘看了眼天色，将最后一块麦芽糖塞进嘴里"}, {"class": "语言", "content": "' 再过两个时辰，就能到下一个镇子了 '"}])
    # data25.write_origin_input({"context": "[上文] 官道上的尘土飞扬，货郎的马车装着满满当当的杂货，铃铛随着车身摇晃叮当作响… \n [当前] 马车在石板路上颠簸着，货郎掀开布帘看了眼天色，将最后一块麦芽糖塞进嘴里 ' 再过两个时辰，就能到下一个镇子了 ' 马车在石板路上颠簸着 \n [下文] 路边突然窜出个孩子，手里举着几枚铜板：' 大叔，我要买糖人 ' \n [下文] 货郎勒住马缰，笑着从箱子里拿出一个孙悟空造型的糖人 \n", "clause": "马车在石板路上颠簸着，货郎掀开布帘看了眼天色，将最后一块麦芽糖塞进嘴里 ' 再过两个时辰，就能到下一个镇子了 ' 马车在石板路上颠簸着"})
    # EvalClassList_ctx.add_sample(data25)

    # data26 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 这弓箭的弓弦是鹿筋做的，拉力比寻常的强三成 '"}, {"class": "旁白", "content": "猎户拉开弓试了试手感，箭头瞄准远处的野兔，指节因为用力而凸起"}])
    # data26.write_origin_input({"context": "[上文] 集市的角落里，卖弓箭的摊主正在演示新做的武器，围了不少看热闹的猎人… \n [当前] ' 这弓箭的弓弦是鹿筋做的，拉力比寻常的强三成 ' 猎户拉开弓试了试手感这弓箭的弓弦是鹿筋做的 \n [下文] 摊主得意地说：' 这是我儿子做的，他年轻时在军营里当过弓箭手 ' \n [下文] 猎户松开弓弦，发出嗡的一声：' 给我来两把 ' \n", "clause": "' 这弓箭的弓弦是鹿筋做的，拉力比寻常的强三成 ' 猎户拉开弓试了试手感这弓箭的弓弦是鹿筋做的"})
    # EvalClassList_ctx.add_sample(data26)

    # data27 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这枚印章的篆字和县志里记载的一样，难道真是前朝遗物？"}, {"class": "旁白", "content": "秀才用毛笔蘸着印泥，将印章按在宣纸上，红色的印记里藏着细小的龙纹"}])
    # data27.write_origin_input({"context": "[上文] 旧货市场快散场时，秀才在一个地摊上发现枚铜印，上面的锈迹里隐约能看见篆字… \n [当前] 这枚印章的篆字和县志里记载的一样，难道真是前朝遗物？秀才用毛笔蘸着印泥这枚印章的篆字和县志里记载的一样 \n [下文] 摊主不耐烦地说：' 十文钱要不要，不卖我就收摊了 ' \n [下文] 秀才连忙掏钱，手心里全是汗，生怕被别人抢了去 \n", "clause": "这枚印章的篆字和县志里记载的一样，难道真是前朝遗物？秀才用毛笔蘸着印泥这枚印章的篆字和县志里记载的一样"})
    # EvalClassList_ctx.add_sample(data27)

    # data28 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "雨打在油纸伞上沙沙作响，药铺的伙计背着药箱走在巷子里，鞋尖已经湿透了"}, {"class": "语言", "content": "' 张大爷的药得赶紧送去，不然耽误了时辰 '"}])
    # data28.write_origin_input({"context": "[上文] 傍晚的雨越下越大，药铺的掌柜把一包草药递给伙计，嘱咐他一定要送到城南的张大爷家… \n [当前] 雨打在油纸伞上沙沙作响，药铺的伙计背着药箱走在巷子里，鞋尖已经湿透了 ' 张大爷的药得赶紧送去，不然耽误了时辰 ' 雨打在油纸伞上沙沙作响 \n [下文] 巷口突然跑出个孩子，撞在伙计身上，药箱掉在地上散开了 \n [下文] 伙计顾不上骂孩子，赶紧蹲下去捡散落的草药 \n", "clause": "雨打在油纸伞上沙沙作响，药铺的伙计背着药箱走在巷子里，鞋尖已经湿透了 ' 张大爷的药得赶紧送去，不然耽误了时辰 ' 雨打在油纸伞上沙沙作响"})
    # EvalClassList_ctx.add_sample(data28)

    # data29 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 这缸醋的酸度刚好，再陈半年就能当贡品了 '"}, {"class": "旁白", "content": "醋坊老板舀起一勺醋尝了尝，眉头舒展开来，作坊里弥漫着刺鼻的酸味"}])
    # data29.write_origin_input({"context": "[上文] 镇子东头的醋坊正在开新缸，伙计们光着膀子搬运陶缸，老板拿着长勺在每个缸前停留片刻… \n [当前] ' 这缸醋的酸度刚好，再陈半年就能当贡品了 ' 醋坊老板舀起一勺醋尝了尝这缸醋的酸度刚好 \n [下文] 账房先生在一旁记录：' 老板，今年的贡品份额比去年多了五成 ' \n [下文] 老板把勺子一放：' 那就再多酿三缸，不能误了宫里的差事 ' \n", "clause": "' 这缸醋的酸度刚好，再陈半年就能当贡品了 ' 醋坊老板舀起一勺醋尝了尝这缸醋的酸度刚好"})
    # EvalClassList_ctx.add_sample(data29)

    # data30 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "这把梳子的刻痕和母亲的一样，难道她来过这里？"}, {"class": "旁白", "content": "姑娘摩挲着梳妆台上的桃木梳，梳齿间还缠着几根长发，和自己的发色不同"}])
    # data30.write_origin_input({"context": "[上文] 客栈的房间刚打扫干净，姑娘放下行李准备梳头时，发现梳妆台上留着一把桃木梳… \n [当前] 这把梳子的刻痕和母亲的一样，难道她来过这里？姑娘摩挲着梳妆台上的桃木梳这把梳子的刻痕和母亲的一样 \n [下文] 店小二路过门口，解释道：' 这是上一位客人落下的，我这就收起来 ' \n [下文] 姑娘连忙拦住：' 不用，我先替她收着吧 ' \n", "clause": "这把梳子的刻痕和母亲的一样，难道她来过这里？姑娘摩挲着梳妆台上的桃木梳这把梳子的刻痕和母亲的一样"})
    # EvalClassList_ctx.add_sample(data30)

    # # 单类示例（仅旁白）
    # data31 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "晨雾漫过青石板路，卖花姑娘的竹篮里插着带露的蔷薇，裙摆扫过墙角时惊起几片枯叶，远处传来第一声鸡鸣"}])
    # data31.write_origin_input({"context": "[上文] 天刚蒙蒙亮，巷子里还没什么人，只有几家早点铺子开始冒烟… \n [当前] 晨雾漫过青石板路，卖花姑娘的竹篮里插着带露的蔷薇，裙摆扫过墙角时惊起几片枯叶，远处传来第一声鸡鸣晨雾漫过青石板路 \n [下文] 包子铺的伙计探出头：' 阿薇，今天的花真新鲜 ' \n [下文] 姑娘笑着应了声，脚步轻快地走向街心的集市 \n", "clause": "晨雾漫过青石板路，卖花姑娘的竹篮里插着带露的蔷薇，裙摆扫过墙角时惊起几片枯叶，远处传来第一声鸡鸣晨雾漫过青石板路"})
    # EvalClassList_ctx.add_sample(data31)

    # # 单类示例（仅语言）
    # data32 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "语言", "content": "' 东边的山神庙塌了一角！'' 听说夜里闹了山神！'' 官府要派人来修了！'' 咱们要不要去烧香祈福？'"}])
    # data32.write_origin_input({"context": "[上文] 村口的老槐树下围了一群人，手里的农具还没放下，都在议论着什么… \n [当前] ' 东边的山神庙塌了一角！'' 听说夜里闹了山神！'' 官府要派人来修了！'' 咱们要不要去烧香祈福？' 东边的山神庙塌了一角！ \n [下文] 村长拄着拐杖走来：' 别瞎传，是昨夜的雷劈坏了梁 ' \n [下文] 人群里有人嘀咕：' 哪有那么巧的事 ' \n", "clause": "' 东边的山神庙塌了一角！'' 听说夜里闹了山神！'' 官府要派人来修了！'' 咱们要不要去烧香祈福？' 东边的山神庙塌了一角！"})
    # EvalClassList_ctx.add_sample(data32)

    # # 单类示例（仅内心独白）
    # data33 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "内心独白", "content": "他说的地址和爹留下的纸条一致，这箱东西不能交出去，他们肯定是冲着藏宝图来的，得想办法跑"}])
    # data33.write_origin_input({"context": "[上文] 码头的仓库里，黑衣人像铁塔一样堵着门，为首的递过来一张银票：' 把箱子交出来，这钱归你 '… \n [当前] 他说的地址和爹留下的纸条一致，这箱东西不能交出去，他们肯定是冲着藏宝图来的，得想办法跑他说的地址和爹留下的纸条一致 \n [下文] 少年突然掀翻旁边的木箱，铁钉滚落一地，趁黑衣人躲闪时冲向侧门 \n [下文] ' 抓住他！' 为首的怒吼着追了上来 \n", "clause": "他说的地址和爹留下的纸条一致，这箱东西不能交出去，他们肯定是冲着藏宝图来的，得想办法跑他说的地址和爹留下的纸条一致"})
    # EvalClassList_ctx.add_sample(data33)

    # # 三类示例（旁白+语言+内心独白）
    # data34 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "旁白", "content": "戏台后的帷幕被风掀起一角，青衣演员捏着水袖的手停在半空"},
    #         {"class": "语言", "content": "' 今日这妆化得太紧，唱不了高腔 '"},
    #         {"class": "内心独白", "content": "台下第三排那个戴玉扳指的，和当年害我爹的人太像了"}
    #     ])
    # data34.write_origin_input({"context": "[上文] 戏班刚到镇上，头场就座无虚席，班主反复叮嘱演员们务必拿出看家本领… \n [当前] 戏台后的帷幕被风掀起一角，青衣演员捏着水袖的手停在半空 ' 今日这妆化得太紧，唱不了高腔 ' 台下第三排那个戴玉扳指的，和当年害我爹的人太像了戏台后的帷幕被风掀起一角 \n [下文] 班主在一旁急得直搓手：' 忍忍，这出戏唱完给你加钱 ' \n [下文] 锣鼓声再次响起，演员深吸一口气走上台，眼神却瞟向台下 \n", "clause": "戏台后的帷幕被风掀起一角，青衣演员捏着水袖的手停在半空 ' 今日这妆化得太紧，唱不了高腔 ' 台下第三排那个戴玉扳指的，和当年害我爹的人太像了戏台后的帷幕被风掀起一角"})
    # EvalClassList_ctx.add_sample(data34)

    # # 三类示例（语言+旁白+语言）
    # data35 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "语言", "content": "' 这匹马的前蹄有点瘸 '"},
    #         {"class": "旁白", "content": "马夫蹲下身掰开马蹄铁，发现里面卡着块碎石，苍蝇在马背上嗡嗡盘旋"},
    #         {"class": "语言", "content": "' 清理干净还能赶路，耽误了镖期要扣工钱的 '"}
    #     ])
    # data35.write_origin_input({"context": "[上文] 镖局的队伍在驿站歇脚，镖师们围着篝火吃干粮，只有马夫在检查马匹… \n [当前] ' 这匹马的前蹄有点瘸 ' 马夫蹲下身掰开马蹄铁，发现里面卡着块碎石 ' 清理干净还能赶路，耽误了镖期要扣工钱的 ' 这匹马的前蹄有点瘸 \n [下文] 总镖头走过来：' 不行就换匹备用马，别勉强 ' \n [下文] 马夫摆摆手：' 小毛病，半个时辰就好 ' \n", "clause": "' 这匹马的前蹄有点瘸 ' 马夫蹲下身掰开马蹄铁，发现里面卡着块碎石 ' 清理干净还能赶路，耽误了镖期要扣工钱的 ' 这匹马的前蹄有点瘸"})
    # EvalClassList_ctx.add_sample(data35)

    # # 四类示例（旁白+内心独白+语言+旁白）
    # data36 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "旁白", "content": "当铺的铜铃晃了晃，穿长衫的客人把锦盒放在柜台上，指节泛白"},
    #         {"class": "内心独白", "content": "这玉佩要是当了，母亲的药钱就够了，可这是祖传的物件啊"},
    #         {"class": "语言", "content": "' 老板看看能当多少 '"},
    #         {"class": "旁白", "content": "掌柜的推了推眼镜，用象牙秤称了称，算盘珠子打得噼啪响"}
    #     ])
    # data36.write_origin_input({"context": "[上文] 深秋的当铺里寒气逼人，掌柜的正拨着算盘，听见门口的铃声抬头望去… \n [当前] 当铺的铜铃晃了晃，穿长衫的客人把锦盒放在柜台上，指节泛白这玉佩要是当了，母亲的药钱就够了 ' 老板看看能当多少 ' 掌柜的推了推眼镜，用象牙秤称了称当铺的铜铃晃了晃 \n [下文] ' 最多五十两 ' 掌柜的把玉佩放回盒里，语气不容置喙 \n [下文] 客人咬了咬牙：' 成交 ' \n", "clause": "当铺的铜铃晃了晃，穿长衫的客人把锦盒放在柜台上，指节泛白这玉佩要是当了，母亲的药钱就够了 ' 老板看看能当多少 ' 掌柜的推了推眼镜，用象牙秤称了称当铺的铜铃晃了晃"})
    # EvalClassList_ctx.add_sample(data36)

    # # 四类示例（语言+内心独白+旁白+语言）
    # data37 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "语言", "content": "' 这砚台的石眼是天然的 '"},
    #         {"class": "内心独白", "content": "老板肯定不知道这是端溪老坑的料子，得压低点价钱"},
    #         {"class": "旁白", "content": "书生用袖口擦了擦砚台边缘，墨痕在布上晕开一小团"},
    #         {"class": "语言", "content": "' 二十文卖不卖？不卖我就再逛逛 '"}
    #     ])
    # data37.write_origin_input({"context": "[上文] 旧货摊前摆着些破旧文房，书生一眼就看中了角落里的砚台，表面蒙着层灰… \n [当前] ' 这砚台的石眼是天然的 ' 老板肯定不知道这是端溪老坑的料子 书生用袖口擦了擦砚台边缘 ' 二十文卖不卖？不卖我就再逛逛 ' 这砚台的石眼是天然的 \n [下文] 摊主挥挥手：' 拿走拿走，占地方 ' \n [下文] 书生强装镇定地掏钱，手心里全是汗 \n", "clause": "' 这砚台的石眼是天然的 ' 老板肯定不知道这是端溪老坑的料子 书生用袖口擦了擦砚台边缘 ' 二十文卖不卖？不卖我就再逛逛 ' 这砚台的石眼是天然的"})
    # EvalClassList_ctx.add_sample(data37)

    # # 三类嵌套示例（内心独白包含模糊表述）
    # data38 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "旁白", "content": "药炉里的药渣泛着苦味，郎中盯着病人的舌苔，手指在脉枕上停顿片刻"},
    #         {"class": "内心独白", "content": "脉象虚浮却带着燥气，是风寒还是内火？这症状太像上个月去世的张屠户了"},
    #         {"class": "语言", "content": "' 先吃三副药看看，忌生冷油腻 '"}
    #     ])
    # data38.write_origin_input({"context": "[上文] 药铺里弥漫着草药味，病人捂着胸口咳嗽，脸色发白… \n [当前] 药炉里的药渣泛着苦味，郎中盯着病人的舌苔脉象虚浮却带着燥气 ' 先吃三副药看看，忌生冷油腻 ' 药炉里的药渣泛着苦味 \n [下文] 病人的儿子急道：' 大夫，我爹这病要不要紧？' \n [下文] 郎中捋着胡须：' 按时吃药，应该无妨 ' \n", "clause": "药炉里的药渣泛着苦味，郎中盯着病人的舌苔脉象虚浮却带着燥气 ' 先吃三副药看看，忌生冷油腻 ' 药炉里的药渣泛着苦味"})
    # EvalClassList_ctx.add_sample(data38)

    # # 单类长文本示例（仅旁白包含多动作）
    # data39 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[{"class": "旁白", "content": "木匠刨子在木板上划出卷曲的木花，木屑落在他的蓝布围裙上，斧头劈在楔子上发出闷响，墨斗弹出的细线在木头上留下淡淡的痕迹，最后他用砂纸打磨着边缘，木桌渐渐显出光滑的轮廓"}])
    # data39.write_origin_input({"context": "[上文] 作坊里堆着刚运来的木料，木匠眯着眼看了看图纸，拿起工具开始干活… \n [当前] 木匠刨子在木板上划出卷曲的木花，木屑落在他的蓝布围裙上，斧头劈在楔子上发出闷响，墨斗弹出的细线在木头上留下淡淡的痕迹，最后他用砂纸打磨着边缘，木桌渐渐显出光滑的轮廓木匠刨子在木板上划出卷曲的木花 \n [下文] 掌柜的走进来：' 王师傅，这批桌子明天能交货吗？' \n [下文] 木匠直起腰：' 放心，误不了事 ' \n", "clause": "木匠刨子在木板上划出卷曲的木花，木屑落在他的蓝布围裙上，斧头劈在楔子上发出闷响，墨斗弹出的细线在木头上留下淡淡的痕迹，最后他用砂纸打磨着边缘，木桌渐渐显出光滑的轮廓木匠刨子在木板上划出卷曲的木花"})
    # EvalClassList_ctx.add_sample(data39)

    # # 四类混合示例（包含重复类）
    # data40 = EvalClass(task_id=0, origin_input=None,
    #     ref_resp=[
    #         {"class": "语言", "content": "' 这井水怎么变浑了 '"},
    #         {"class": "旁白", "content": "村民弯腰舀起一桶水，水面浮着层绿色的泡沫，桶沿沾着滑腻的青苔"},
    #         {"class": "语言", "content": "' 怕是后山的矿脉漏了 '"},
    #         {"class": "内心独白", "content": "去年淹死的二柱，会不会就是喝了这水出事的？"}
    #     ])
    # data40.write_origin_input({"context": "[上文] 村口的老井用了几十年，今天打水的人发现水面不对劲，围了一圈人议论… \n [当前] ' 这井水怎么变浑了 ' 村民弯腰舀起一桶水 ' 怕是后山的矿脉漏了 ' 去年淹死的二柱，会不会就是喝了这水出事的？这井水怎么变浑了 \n [下文] 村长让人拿来明矾：' 先沉淀看看，不行就报官 ' \n [下文] 有人小声说：' 我早就说过那矿不能开 ' \n", "clause": "' 这井水怎么变浑了 ' 村民弯腰舀起一桶水 ' 怕是后山的矿脉漏了 ' 去年淹死的二柱，会不会就是喝了这水出事的？这井水怎么变浑了"})
    # EvalClassList_ctx.add_sample(data40)

    # EvalClassList_ctx.save_samples()

    # data1 = EvalClass(task_id=0, origin_input=None,
    # ref_resp=[{"class": "语言", "content": "'萧炎,斗之力,三段!级别:低级!'"}, {"class": "旁白", "content": "测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"}],
    # )
    # data1.write_origin_input({"context": "[上文]'斗之力,三段!' \n[上文]望着测验魔石碑上面闪亮得甚至有些刺眼的五个大字,少年面无表情,唇角有着一抹自嘲,紧握的手掌,因为大力,而导致略微尖锐的指甲深深的刺进了掌心之中,带来一阵阵钻心的疼痛… \n[当前]'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来 \n[下文]中年男子话刚刚脱口,便是不出意外的在人头汹涌的广场上带起了一阵嘲讽的骚动. \n[下文]'三段?嘿嘿,果然不出我所料,这个'天才'这一年又是在原地踏步!' \n[下文]'哎,这废物真是把家族的脸都给丢光了.' \n[下文]'要不是族长是他的父亲,这种废物,早就被驱赶出家族,任其自生自灭了,哪还有机会待在家族中白吃白喝.' \n[下文]'唉,昔年那名闻乌坦城的天才少年,如今怎么落魄成这般模样了啊?' \n", "clause": "'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"})
    # EvalClassList_ctx.add_sample(data1)
    
    # data1 = EvalClass(task_id=0, origin_input=None,
    # ref_resp=[{"class": "语言", "content": "'萧炎,斗之力,三段!级别:低级!'"}, {"class": "旁白", "content": "测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"}],
    # )
    # data1.write_origin_input({"context": "[上文]'斗之力,三段!' \n[上文]望着测验魔石碑上面闪亮得甚至有些刺眼的五个大字,少年面无表情,唇角有着一抹自嘲,紧握的手掌,因为大力,而导致略微尖锐的指甲深深的刺进了掌心之中,带来一阵阵钻心的疼痛… \n[当前]'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来 \n[下文]中年男子话刚刚脱口,便是不出意外的在人头汹涌的广场上带起了一阵嘲讽的骚动. \n[下文]'三段?嘿嘿,果然不出我所料,这个'天才'这一年又是在原地踏步!' \n[下文]'哎,这废物真是把家族的脸都给丢光了.' \n[下文]'要不是族长是他的父亲,这种废物,早就被驱赶出家族,任其自生自灭了,哪还有机会待在家族中白吃白喝.' \n[下文]'唉,昔年那名闻乌坦城的天才少年,如今怎么落魄成这般模样了啊?' \n", "clause": "'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"})
    # EvalClassList_ctx.add_sample(data1)

    # data2 = EvalClass (task_id=0, origin_input=None,
    # ref_resp=[{"class": "语言", "content": "' 这把剑，名为‘青冥’，随我征战三十年，饮血无数'"}, {"class": "旁白", "content": "老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意"}],)
    # data2.write_origin_input({"context": "[上文] 演武场中央，白发老者手持剑鞘，目光如炬地望着前方的少年，苍老的声音带着几分威严… \n [当前]' 这把剑，名为‘青冥’，随我征战三十年，饮血无数 ' 老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意 ' \n [下文] 少年望着那柄散发着凛冽气息的长剑，眼中闪过一丝敬畏，拱手道：' 晚辈愧不敢受如此神兵…'\n [下文] 老者轻抚剑身，叹道：' 兵器有价，传承无价，你且接好 '\n", "clause": "' 这把剑，名为‘青冥’，随我征战三十年，饮血无数 ' 老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意 '"})
    # EvalClassList_ctx.add_sample(data2)

    # data3 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "内心独白", "content": "她怎么会出现在这里？难道是特意跟踪我？"}, {"class": "旁白", "content": "陈默猛地转身，后背的冷汗瞬间浸湿了衬衫."}])
    # data3.write_origin_input({"context": "[上文] 巷口的路灯忽明忽暗，陈默攥紧了口袋里的信封，脚步匆匆地往家赶，总觉得身后有双眼睛在盯着自己… \n [当前] 她怎么会出现在这里？难道是特意跟踪我？陈默猛地转身，后背的冷汗瞬间浸湿了衬衫 \n [下文] 路灯的光晕里，一个穿着红色连衣裙的女人正站在不远处，嘴角噙着若有若无的笑意，正是他下午在咖啡馆见到的那个神秘女子 \n [下文]' 找我有事？' 陈默强装镇定，声音却有些发颤 \n", "clause": "她怎么会出现在这里？难道是特意跟踪我？陈默猛地转身，后背的冷汗瞬间浸湿了衬衫"})
    # EvalClassList_ctx.add_sample(data3)

    # data4 = EvalClass(task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头"}, {"class": "语言", "content": "' 这鬼天气，怕是要下到后半夜了 '"}, {"class": "旁白", "content": "掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆"}],)
    # data4.write_origin_input({"context": "[上文] 暮色四合，镇上的茶馆渐渐热闹起来，跑堂的伙计穿梭在桌椅间，吆喝声此起彼伏… \n [当前] 暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' 这鬼天气，怕是要下到后半夜了 ' 掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' \n [下文] 正在喝茶的客人纷纷探头看向门外，议论着这场突如其来的大雨 \n [下文]' 王掌柜，您这茶馆的屋檐够结实不？别给雨冲塌了哟 ' 一个糙汉打趣道 \n", "clause": "暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' 这鬼天气，怕是要下到后半夜了 ' 掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆 '"})
    # EvalClassList_ctx.add_sample(data4)

    # data5 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "语言", "content": "' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 '"}, {"class": "旁白", "content": "控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里"}],)
    # data5.write_origin_input({"context": "[上文] 地下实验室里，各种仪器运转的嗡鸣声交织成一片，李教授盯着屏幕上跳动的数据流，眉头拧成了疙瘩… \n [当前]' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 ' 控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里 ' \n [下文] 李教授猛地拍向紧急制动按钮，却发现按钮早已失灵，他咬了咬牙，抄起扳手冲向能量核心舱 \n [下文]' 小张，快带其他人撤离！这里我来处理 ' 他朝着对讲机嘶吼道 \n", "clause": "' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 ' 控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里"})
    # EvalClassList_ctx.add_sample(data5)

    # data6 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "旁白", "content": "月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟，阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱"}])
    # data6.write_origin_input({"context": "[上文] 村子里的人都已睡去，只有祠堂还亮着一盏孤灯，阿秀抱着一个布包，蹑手蹑脚地推开了沉重的木门… \n [当前] 月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱月光穿过雕花窗棂 \n [下文] 族谱在某一页停住了，那是二十年前的记录，上面赫然写着她母亲的名字，旁边还有一个模糊的朱砂印记 \n [下文] 阿秀从布包里取出一枚玉佩，玉佩上的纹路竟与那朱砂印记一模一样 \n", "clause": "月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱月光穿过雕花窗棂"})
    # EvalClassList_ctx.add_sample(data6)

    # data7 = EvalClass(task_id=0, origin_input=None, ref_resp=[{"class": "内心独白", "content": "这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？"}, {"class": "旁白", "content": "老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白"}])
    # data7.write_origin_input ({"context": "[上文] 古玩市场的角落里，老周蹲在摊位前，目光被一枚布满铜绿的古币吸引，摊主说这是刚从城郊古墓附近收来的… \n [当前] 这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白这枚古币的纹路和古籍记载的一模一样 \n [下文] 摊主看出他的兴趣，搓着手笑道：' 老哥好眼光，这可是稀罕物件，给个实在价就出手 ' \n [下文] 老周不动声色地将古币放回摊位，心里却在盘算着该如何验证它的真伪 \n", "clause": "这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白这枚古币的纹路和古籍记载的一模一样"})
    # EvalClassList_ctx.add_sample (data7)

    # data8 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里"}, {"class": "语言", "content": "' 再过三日，就是采莲节了呢 '"}])
    # data8.write_origin_input ({"context": "[上文] 江南的三月总是多雨，今日难得放晴，湖边的柳树抽出了新绿，游人三三两两地沿着湖岸散步… \n [当前] 春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里 ' 再过三日，就是采莲节了呢 '  '… \n [下文] 身后传来木屐踏地的声响，阿莲回头，看见同村的阿明提着竹篮，里面装着刚摘的莲蓬 \n [下文]' 阿莲姐，娘让我送些新采的莲子给你尝尝 ' 阿明把竹篮递过来，脸颊有些发红 \n", "clause": "春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里 ' 再过三日，就是采莲节了呢 ' "})
    # EvalClassList_ctx.add_sample (data8)

    # data9 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "语言", "content": "' 各单位注意，目标已进入三号区域，准备实施抓捕 '"}, {"class": "旁白", "content": "张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影"}])
    # data9.write_origin_input ({"context": "[上文] 深夜的森林公园里，警灯被蒙住了光芒，十余名特警潜伏在树丛中，蚊虫在耳边嗡嗡作响，每个人都屏住了呼吸… \n [当前]' 各单位注意，目标已进入三号区域，准备实施抓捕 ' 张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影 '  \n [下文] 黑影似乎察觉到了什么，突然停下脚步，从背包里掏出一把匕首，警惕地环顾四周 \n [下文] 张队打了个手势，左侧的两名特警如同猎豹般迅猛扑出，树枝被撞得哗哗作响 \n", "clause": "' 各单位注意，目标已进入三号区域，准备实施抓捕 ' 张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影 '"})
    # EvalClassList_ctx.add_sample (data9)

    # data10 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册"}, {"class": "内心独白", "content": "那时候爸爸还在，我们一家人去海边拍的这张照片呢…"}])
    # data10.write_origin_input ({"context": "[上文] 窗外飘着初雪，一片银装素裹，苏菲刚煮好一壶热可可，白色的雾气在玻璃杯口氤氲开来… \n [当前] 壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册那时候爸爸还在，我们一家人去海边拍的这张照片呢… \n [下文] 相册里掉出一张明信片，是爸爸生前在异国出差时寄来的，邮戳已经模糊不清 \n [下文] 苏菲拿起明信片，指尖划过上面熟悉的字迹，眼眶渐渐湿润了 \n", "clause": "壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册那时候爸爸还在，我们一家人去海边拍的这张照片呢…"})
    # EvalClassList_ctx.add_sample (data10)

    # EvalClassList_ctx.save_samples()


