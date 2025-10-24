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

if __name__ == "__main__":
    EvalClassList_ctx = EvalClassList(save_path="examples\eval\step1_eval.json")
    data1 = EvalClass(task_id=0, origin_input=None,
    ref_resp=[{"class": "语言", "content": "'萧炎,斗之力,三段!级别:低级!'"}, {"class": "旁白", "content": "测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"}],
    )
    data1.write_origin_input({"context": "[上文]'斗之力,三段!' \n[上文]望着测验魔石碑上面闪亮得甚至有些刺眼的五个大字,少年面无表情,唇角有着一抹自嘲,紧握的手掌,因为大力,而导致略微尖锐的指甲深深的刺进了掌心之中,带来一阵阵钻心的疼痛… \n[当前]'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来 \n[下文]中年男子话刚刚脱口,便是不出意外的在人头汹涌的广场上带起了一阵嘲讽的骚动. \n[下文]'三段?嘿嘿,果然不出我所料,这个'天才'这一年又是在原地踏步!' \n[下文]'哎,这废物真是把家族的脸都给丢光了.' \n[下文]'要不是族长是他的父亲,这种废物,早就被驱赶出家族,任其自生自灭了,哪还有机会待在家族中白吃白喝.' \n[下文]'唉,昔年那名闻乌坦城的天才少年,如今怎么落魄成这般模样了啊?' \n", "clause": "'萧炎,斗之力,三段!级别:低级!'测验魔石碑之旁,一位中年男子,看了一眼碑上所显示出来的信息,语气漠然的将之公布了出来"})
    EvalClassList_ctx.add_sample(data1)

    data2 = EvalClass (task_id=0, origin_input=None,
    ref_resp=[{"class": "语言", "content": "' 这把剑，名为‘青冥’，随我征战三十年，饮血无数'"}, {"class": "旁白", "content": "老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意"}],)
    data2.write_origin_input({"context": "[上文] 演武场中央，白发老者手持剑鞘，目光如炬地望着前方的少年，苍老的声音带着几分威严… \n [当前]' 这把剑，名为‘青冥’，随我征战三十年，饮血无数 ' 老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意 ' \n [下文] 少年望着那柄散发着凛冽气息的长剑，眼中闪过一丝敬畏，拱手道：' 晚辈愧不敢受如此神兵…'\n [下文] 老者轻抚剑身，叹道：' 兵器有价，传承无价，你且接好 '\n", "clause": "' 这把剑，名为‘青冥’，随我征战三十年，饮血无数 ' 老者缓缓拔出腰间长剑，剑身青光流转，映得周围空气都泛起丝丝凉意 '"})
    EvalClassList_ctx.add_sample(data2)

    data3 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "内心独白", "content": "她怎么会出现在这里？难道是特意跟踪我？"}, {"class": "旁白", "content": "陈默猛地转身，后背的冷汗瞬间浸湿了衬衫."}])
    data3.write_origin_input({"context": "[上文] 巷口的路灯忽明忽暗，陈默攥紧了口袋里的信封，脚步匆匆地往家赶，总觉得身后有双眼睛在盯着自己… \n [当前] 她怎么会出现在这里？难道是特意跟踪我？陈默猛地转身，后背的冷汗瞬间浸湿了衬衫 \n [下文] 路灯的光晕里，一个穿着红色连衣裙的女人正站在不远处，嘴角噙着若有若无的笑意，正是他下午在咖啡馆见到的那个神秘女子 \n [下文]' 找我有事？' 陈默强装镇定，声音却有些发颤 \n", "clause": "她怎么会出现在这里？难道是特意跟踪我？陈默猛地转身，后背的冷汗瞬间浸湿了衬衫"})
    EvalClassList_ctx.add_sample(data3)

    data4 = EvalClass(task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头"}, {"class": "语言", "content": "' 这鬼天气，怕是要下到后半夜了 '"}, {"class": "旁白", "content": "掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆"}],)
    data4.write_origin_input({"context": "[上文] 暮色四合，镇上的茶馆渐渐热闹起来，跑堂的伙计穿梭在桌椅间，吆喝声此起彼伏… \n [当前] 暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' 这鬼天气，怕是要下到后半夜了 ' 掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' \n [下文] 正在喝茶的客人纷纷探头看向门外，议论着这场突如其来的大雨 \n [下文]' 王掌柜，您这茶馆的屋檐够结实不？别给雨冲塌了哟 ' 一个糙汉打趣道 \n", "clause": "暴雨如注，砸在琉璃瓦上噼啪作响，庭院里的芭蕉叶被打得抬不起头 ' 这鬼天气，怕是要下到后半夜了 ' 掌柜的抖了抖油纸伞上的水珠，推门走进了茶馆 '"})
    EvalClassList_ctx.add_sample(data4)

    data5 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "语言", "content": "' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 '"}, {"class": "旁白", "content": "控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里"}],)
    data5.write_origin_input({"context": "[上文] 地下实验室里，各种仪器运转的嗡鸣声交织成一片，李教授盯着屏幕上跳动的数据流，眉头拧成了疙瘩… \n [当前]' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 ' 控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里 ' \n [下文] 李教授猛地拍向紧急制动按钮，却发现按钮早已失灵，他咬了咬牙，抄起扳手冲向能量核心舱 \n [下文]' 小张，快带其他人撤离！这里我来处理 ' 他朝着对讲机嘶吼道 \n", "clause": "' 警告！能量核心温度超过临界值，三分钟后将发生爆炸 ' 控制台的警报灯疯狂闪烁，红色的光芒映在李教授布满血丝的眼睛里"})
    EvalClassList_ctx.add_sample(data5)

    data6 = EvalClass(task_id=0, origin_input=None,ref_resp=[{"class": "旁白", "content": "月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟，阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱"}])
    data6.write_origin_input({"context": "[上文] 村子里的人都已睡去，只有祠堂还亮着一盏孤灯，阿秀抱着一个布包，蹑手蹑脚地推开了沉重的木门… \n [当前] 月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱月光穿过雕花窗棂 \n [下文] 族谱在某一页停住了，那是二十年前的记录，上面赫然写着她母亲的名字，旁边还有一个模糊的朱砂印记 \n [下文] 阿秀从布包里取出一枚玉佩，玉佩上的纹路竟与那朱砂印记一模一样 \n", "clause": "月光穿过雕花窗棂，在青石板上投下斑驳的影子，祠堂里的香炉还燃着最后一缕青烟阿秀跪在蒲团上，指尖轻轻拂过供桌上泛黄的族谱月光穿过雕花窗棂"})
    EvalClassList_ctx.add_sample(data6)

    data7 = EvalClass(task_id=0, origin_input=None, ref_resp=[{"class": "内心独白", "content": "这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？"}, {"class": "旁白", "content": "老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白"}])
    data7.write_origin_input ({"context": "[上文] 古玩市场的角落里，老周蹲在摊位前，目光被一枚布满铜绿的古币吸引，摊主说这是刚从城郊古墓附近收来的… \n [当前] 这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白这枚古币的纹路和古籍记载的一模一样 \n [下文] 摊主看出他的兴趣，搓着手笑道：' 老哥好眼光，这可是稀罕物件，给个实在价就出手 ' \n [下文] 老周不动声色地将古币放回摊位，心里却在盘算着该如何验证它的真伪 \n", "clause": "这枚古币的纹路和古籍记载的一模一样，难道传说都是真的？老周用放大镜反复端详着掌心的青铜币，指腹因用力而泛白这枚古币的纹路和古籍记载的一模一样"})
    EvalClassList_ctx.add_sample (data7)

    data8 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里"}, {"class": "语言", "content": "' 再过三日，就是采莲节了呢 '"}])
    data8.write_origin_input ({"context": "[上文] 江南的三月总是多雨，今日难得放晴，湖边的柳树抽出了新绿，游人三三两两地沿着湖岸散步… \n [当前] 春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里 ' 再过三日，就是采莲节了呢 '  '… \n [下文] 身后传来木屐踏地的声响，阿莲回头，看见同村的阿明提着竹篮，里面装着刚摘的莲蓬 \n [下文]' 阿莲姐，娘让我送些新采的莲子给你尝尝 ' 阿明把竹篮递过来，脸颊有些发红 \n", "clause": "春风卷着漫天柳絮掠过湖面，画舫上的丝竹声断断续续飘过来，阿莲坐在岸边的石阶上，把脚伸进微凉的湖水里 ' 再过三日，就是采莲节了呢 ' "})
    EvalClassList_ctx.add_sample (data8)

    data9 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "语言", "content": "' 各单位注意，目标已进入三号区域，准备实施抓捕 '"}, {"class": "旁白", "content": "张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影"}])
    data9.write_origin_input ({"context": "[上文] 深夜的森林公园里，警灯被蒙住了光芒，十余名特警潜伏在树丛中，蚊虫在耳边嗡嗡作响，每个人都屏住了呼吸… \n [当前]' 各单位注意，目标已进入三号区域，准备实施抓捕 ' 张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影 '  \n [下文] 黑影似乎察觉到了什么，突然停下脚步，从背包里掏出一把匕首，警惕地环顾四周 \n [下文] 张队打了个手势，左侧的两名特警如同猎豹般迅猛扑出，树枝被撞得哗哗作响 \n", "clause": "' 各单位注意，目标已进入三号区域，准备实施抓捕 ' 张队对着对讲机低声下令，手指紧紧扣着腰间的配枪，视线穿过茂密的灌木丛锁定前方的黑影 '"})
    EvalClassList_ctx.add_sample (data9)

    data10 = EvalClass (task_id=0, origin_input=None, ref_resp=[{"class": "旁白", "content": "壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册"}, {"class": "内心独白", "content": "那时候爸爸还在，我们一家人去海边拍的这张照片呢…"}])
    data10.write_origin_input ({"context": "[上文] 窗外飘着初雪，一片银装素裹，苏菲刚煮好一壶热可可，白色的雾气在玻璃杯口氤氲开来… \n [当前] 壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册那时候爸爸还在，我们一家人去海边拍的这张照片呢… \n [下文] 相册里掉出一张明信片，是爸爸生前在异国出差时寄来的，邮戳已经模糊不清 \n [下文] 苏菲拿起明信片，指尖划过上面熟悉的字迹，眼眶渐渐湿润了 \n", "clause": "壁炉里的火焰噼啪作响，将客厅映照得暖意融融，苏菲裹着毛毯蜷缩在沙发上，翻看着一本泛黄的相册那时候爸爸还在，我们一家人去海边拍的这张照片呢…"})
    EvalClassList_ctx.add_sample (data10)

    EvalClassList_ctx.save_samples()


