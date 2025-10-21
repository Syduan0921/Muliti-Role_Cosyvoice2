from typing import Dict, Optional, Any, List
from enum import Enum
from abc import ABC, abstractmethod
import os

class SentenceKeys(Enum):
    """句子JSON键枚举"""
    ID = "id"
    SENTENCE_CLASS = "class"
    SENTENCE = "sentence"
    SUB_SENTENCE = "sub_sentence"
    DESCRIBE = "describe"

class SentenceClassKey(Enum):
    """句子Class键枚举"""
    SPEAK = "语言"
    THINK = "内心独白"
    NARRATION = "旁白"


class BaseJsonCrud(ABC):

    def __init__(self, file_path: Optional[str] = None, list_num: Optional[int] = None) -> Dict[str, Any]:
        self.file_path = file_path
        self.list_num = list_num
        self.data: Dict[str, Any] = {}  # 内存中的JSON列表数据
        if os.path.exists(self.file_path) and self.list_num >= 0:
            try:
                self.load_data()
            except:
                raise RuntimeError("加载数据失败")
        else:
            self.data = {}
            print(f"文件不存在或列表索引无效，已创建空数据结构 {self.__getattribute__}")
    
    @abstractmethod
    def load_data(self) -> bool:
        """
        从文件加载数据
        Args:
            
        Returns:
            处理结果
        """
        pass

    @abstractmethod
    def create(self, item: Dict[str, Any]) -> bool:
        """
        创建新项并返回结果
        
        Args:
            item: 要创建的项数据
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def read(self, key_name: SentenceKeys) -> str | Dict[str, Any]:
        """
        读取指定项的键值
        Args:
            key_name: 要读取的键名
        Returns:
            键对应的值
        """
        pass

    @abstractmethod
    def update(self, key_name: SentenceKeys, value: str | Dict[str, Any]) -> bool:
        """
        更新项的指定键值
        
        Args:
            key_name: 要更新的键名
            value: 新值
            
        Returns:
            处理结果
        """
        pass

    @abstractmethod
    def delete(self, key_name: SentenceKeys) -> bool:
        """
        删除项的指定键值，恢复为默认值
        
        Args:
            key_name: 要删除的键名
            
        Returns:
            处理结果
        """
        pass


    @abstractmethod
    def save_data(self) -> bool:
        """
        将指定的JSON列表保存到具体的json文件中
        Returns:
            处理结果
        """
        pass


class BaseJsonListCrud(ABC):
    """
    基础JSON列表CRUD操作类
    提供对JSON列表进行CRUD操作的基本功能
    """
    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path
        self.data: List['JsonObjCrud'] = []  # 内存中的JSON列表数据
        if self.file_path and os.path.exists(self.file_path):
            try:
                self.load_data()
            except:
                raise RuntimeError("加载数据失败")
        else:
            self.data = []
            print(f"文件不存在，已创建空数据结构 {self.__getattribute__}")


class JsonObjCrud:
    def __init__(self, id: int | None = -1, class_name: SentenceClassKey | None = None, Sentence: Dict[str, Any] | None = None, sub_sentence: str | None = None, describe: Dict[str, Any] | None = None, describe_role: str | None = None, describe_style: str | None = None) -> None:
        self.id = id
        self.class_name = class_name
        self.Sentence = Sentence
        self.sub_sentence = sub_sentence
        self.origin_sub_sentence = sub_sentence
        self.describe = describe if describe is not None else {}
        if describe_role is not None:
            self.describe["role"] = describe_role
        if describe_style is not None:
            self.describe["style"] = describe_style
    def to_dict(self) -> Dict[str, Any]:
        """
        将对象转换为字典格式
        """
        return {
            "id": self.id,
            "class": self.class_name,
            "sentence": self.Sentence,
            "sub_sentence": self.sub_sentence,
            "origin_sub_sentence": self.origin_sub_sentence,
            "describe": self.describe,
        } if self.describe else {
            "id": self.id,
            "class": self.class_name,
            "sentence": self.Sentence,
            "sub_sentence": self.sub_sentence,
            "origin_sub_sentence": self.origin_sub_sentence,
            "describe": {"role": None, "style": None}
        }
    def write_all(self, json_obj: Dict[str, Any]) -> bool:
        """
        从JSON对象加载数据
        """
        self.id = json_obj["id"] if "id" in json_obj else -1
        self.class_name = json_obj["class"] if "class" in json_obj else "旁白"
        if "sentence" in json_obj:
            self.Sentence = json_obj["sentence"] if isinstance(json_obj["sentence"], dict) else {"now_flag": -1, "sentence": json_obj["sentence"]}
        else:
            self.Sentence = {"now_flag": -1, "sentence": None}
        self.sub_sentence = json_obj["sub_sentence"]
        self.origin_sub_sentence = json_obj["origin_sub_sentence"] if "origin_sub_sentence" in json_obj else json_obj["sub_sentence"]
        self.describe = json_obj["describe"] if "describe" in json_obj else {"role": None, "style": None}
    def write_id(self, id: int) -> None:
        """
        写入ID
        """
        self.id = id
    def write_describe(self, describe: Dict[str, Any]) -> None:
        """
        写入描述
        """
        self.describe = describe
    def write_describe_role(self, describe_role: str) -> None:
        """
        写入描述角色
        """
        self.describe["role"] = describe_role
    def write_describe_style(self, describe_style: str) -> None:
        """
        写入描述样式
        """
        self.describe["style"] = describe_style
    def write_class(self, class_name: SentenceClassKey) -> None:
        """
        写入句子类别
        """
        self.class_name = class_name
    def write_sentence(self, Sentence: List, now_flag: int) -> None:
        """
        写入句子
        """
        self.Sentence = {"now_flag": now_flag, "sentence": Sentence}
    def write_sub_sentence(self, sub_sentence: str) -> None:
        """
        写入子句
        """
        self.sub_sentence = sub_sentence
    def write_origin_sub_sentence(self, origin_sub_sentence: str) -> None:
        """
        写入原始子句
        """
        self.origin_sub_sentence = origin_sub_sentence
    def read_id(self) -> int:
        """
        读取ID
        """
        return self.id
    def read_describe(self) -> Dict[str, Any]:
        """
        读取描述
        """
        return self.describe
    def read_describe_role(self) -> str:
        """
        读取描述角色
        """
        return self.describe.get("role", None)
    def read_describe_style(self) -> str:
        """
        读取描述样式
        """
        return self.describe.get("role", None)
    def read_class(self) -> SentenceClassKey:
        """
        读取句子类别
        """
        return self.class_name
    def read_sentence(self) -> str:
        """
        读取句子，并整合为上下文展示str
        """
        _sentence = ""
        for i, item in enumerate(self.Sentence["sentence"]):
            if i < self.Sentence["now_flag"]:
                _sentence += "[上文]{} \n".format(item)
            elif i == self.Sentence["now_flag"]:
                _sentence += "[当前]{} \n".format(item)
            else:
                _sentence += "[下文]{} \n".format(item)
        return _sentence
        
    def read_sub_sentence(self) -> str:
        return self.sub_sentence    
    
    def read_sub_sentence(self) -> str:
        """
        读取子句
        """
        return self.sub_sentence
    def read_origin_sub_sentence(self) -> str:
        """
        读取原始子句
        """
        return self.origin_sub_sentence
    def read_all(self) -> Dict[str, Any]:
        """
        读取所有数据
        """
        return self.to_dict()
    def read_all_vis(self) -> Dict[str, Any]:
        """
        读取所有数据，以可显示的形式展示出来，尤其是sentence
        """
        return {
            "id": self.id,
            "class": self.class_name,
            "sentence": self.read_sentence(),
            "sub_sentence": self.sub_sentence,
            "describe": self.describe,
        } if self.describe else {
            "id": self.id,
            "class": self.class_name,
            "sentence": self.read_sentence(),
            "sub_sentence": self.sub_sentence,
            "describe": {"role": None, "style": None}
        }
