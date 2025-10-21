"""
句子JSON模板类

提供对句子JSON数据的增删改查操作，符合代码规范。
"""
from typing import Dict, Optional, Any, List
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.template.BaseClassTemp.BaseClass import BaseJsonCrud, SentenceKeys, BaseJsonListCrud, JsonObjCrud
    from src.utils.tools import mapping_windows_size
except:
    from BaseClassTemp.BaseClass import BaseJsonCrud, SentenceKeys, BaseJsonListCrud, JsonObjCrud



class SentencesJsonCrud(BaseJsonCrud):
    """单个句子JSON CRUD类"""
    def __init__(self, file_path: Optional[str] = None, list_num: Optional[int] = None) -> None:
        super().__init__(file_path, list_num)
    
    def load_data(self) -> bool:
        """
        初始化原始默认格式
        加载JSON数据
        """
        for key_name in SentenceKeys:
            key_name = key_name.value
            self.data[key_name] = None if key_name != "id" else self.list_num
            self.data["describe"] = {"role": None, "style": None}
        try:
            with open(self.file_path, 'r', encoding="utf-8") as f:
                loaded = json.load(f)
                loaded = loaded[self.list_num]
                if not isinstance(loaded, Dict):
                    print(f"JSON数据格式错误，必须是字典类型，当前类型为：{type(loaded)}")
                    return False
                for key_name in SentenceKeys:
                    key_name = key_name.value
                    if key_name not in loaded:
                        print(f"JSON数据中缺少键 {key_name}")
                        continue
                    self.update(key_name, loaded[key_name])
                return True
        except Exception as e:
            print(f"加载JSON数据时出错：{e}")
            return False
    
    def update(self, key_name: SentenceKeys, value: str | Dict[str, Any]) -> bool:
        """
        更新项的指定键值
        
        Args:
            key_name: 要更新的键名
            value: 新值
            
        Returns:
            处理结果
        """
        try:
            self.data[key_name] = value
        except Exception as e:
            print(f"更新键 {key_name} 时出错：{e}")
            return False
        return True
    
    def create(self, item: Dict[str, Any]) -> bool:
        """
        创建新项并返回结果
        
        Args:
            item: 要创建的项数据
            
        Returns:
            处理结果
        """
        try:
            for key_name in SentenceKeys:
                if key_name not in item:
                    print(f"项数据中缺少键 {key_name}")
                    continue
                self.update(key_name, item[key_name])
        except Exception as e:
            print(f"创建项时出错：{e}")
            return False
        return True

    def read(self, key_name: SentenceKeys) -> str | Dict[str, Any]:
        """
        读取指定项的键值
        Args:
            key_name: 要读取的键名
        Returns:
            键对应的值
        """
        return self.data[key_name]

    def read_all(self) -> Dict[str, Any]:
        """
        读取所有项
        Returns:
            所有项的字典
        """
        return self.data

    def delete(self, key_name: SentenceKeys) -> bool:
        """
        删除指定项的键值
        Args:
            key_name: 要删除的键名
        Returns:
            处理结果
        """
        try:
            self.data[key_name] = None
        except Exception as e:
            print(f"删除键 {key_name} 时出错：{e}")
            return False
        return True

    def save_data(self) -> bool:
        """
        保存数据到文件
        Returns:
            处理结果
        """
        print("该功能尚未开放，需要完整版一起保存！")
        return False

class SentencesJsonListCrud(BaseJsonListCrud):
    """句子JSON列表CRUD类"""
    def __init__(self, file_path: Optional[str] = None, Windows_Size: int = 3) -> None:
        self.WINDOWS_SIZE = Windows_Size
        super().__init__(file_path)

    def __len__(self) -> int:
        """
        返回列表长度
        Returns:
            列表长度
        """
        return len(self.data)

    def _id_check(self) -> None:
        """
        对当前的列表id进行重排，避免显示问题
        """
        for i in range(len(self.data)):
            self.data[i].write_id(i)
    
    def _check_sentence_window(self) -> None:
        """
        维护每个句子的上下文窗口
        """
        self._id_check()
        _temp_windows = []
        for i, item in enumerate(self.data):
            array_size, start_id = mapping_windows_size(self.WINDOWS_SIZE, i, len(self.data))
            _sentence = [item.read_sub_sentence()]
            for j in range(start_id):
                _sentence.insert(0, self.data[i - j - 1].read_origin_sub_sentence())
            for j in range(array_size - start_id - 1):
                _sentence.append(self.data[i + j + 1].read_origin_sub_sentence())
            item.write_sentence(_sentence, start_id)
        self._id_check()
    
    def load_data(self, file_path: Optional[str] = None) -> bool:
        """
        加载JSON数据
        """
        if file_path:
            self.file_path = file_path
        try:
            with open(self.file_path, 'r', encoding="utf-8") as f:
                loaded = json.load(f)
                if not isinstance(loaded, List):
                    print(f"JSON数据格式错误，必须是列表类型，当前类型为：{type(loaded)}")
                    return False
                _data = loaded
                self.data = [JsonObjCrud() for i in range(len(_data))]
                for i, item in enumerate(self.data):
                    item.write_all(_data[i]) 
                self._check_sentence_window()
                return True
        except Exception as e:
            print(f"加载JSON数据时出错：{e}")
            return False
    def read(self, list_num: int) -> Dict[str, Any]:
        """
        读取指定id的句子
        Args:
            list_num: 要读取的id
        Returns:
            id对应的句子
        """
        self._check_sentence_window()
        return self.data[list_num].read_all()

    def read_all(self) -> List[Dict[str, Any]]:
        """
        读取所有项
        Returns:
            所有项的字典
        """
        self._check_sentence_window()
        return [item.read_all() for item in self.data]

    def update(self, list_num: int, key_name: SentenceKeys | str, value: str | Dict[str, Any], flag: int | None = None) -> bool:
        """
        更新项的指定键值
        
        Args:
            key_name: 要更新的键名
            value: 新值
            
        Returns:
            处理结果
        """
        try:
            if key_name == "id":
                self.data[list_num].write_id(value)
            elif key_name == "class":
                self.data[list_num].write_class(value)
            elif key_name == "sub_sentence":
                self.data[list_num].write_sub_sentence(value)
            elif key_name == "sentence":
                self.data[list_num].write_sentence(value, flag)
            elif key_name == "describe":
                self.data[list_num].write_describe(value)
            elif key_name == "role":
                self.data[list_num].write_describe_role(value)
            elif key_name == "style":
                self.data[list_num].write_describe_style(value)
            else:
                print(f"键 {key_name} 不存在")
                return False
        except Exception as e:
            print(f"更新键 {key_name} 时出错：{e}")
            return False
        return True
    
    def update_all(self, list_num: int, item: Dict[str, Any]) -> bool:
        """
        更新指定id的所有键值
        
        Args:
            list_num: 要更新的id
            item: 包含新值的项数据
            
        Returns:
            处理结果
        """
        try:
            self.data[list_num].write_all(item)
        except Exception as e:
            print(f"更新项 {list_num} 时出错：{e}")
            return False
        return True

    def delete(self, list_num: int) -> bool:
        """
        删除指定id的项
        
        Args:
            list_num: 要删除的id
            
        Returns:
            处理结果
        """
        try:
            del self.data[list_num]
        except Exception as e:
            print(f"删除项 {list_num} 时出错：{e}")
            return False
        return True

    def create(self, list_num: int | None, item: Dict[str, Any]) -> bool:
        """
        创建新项并返回结果
        
        Args:
            item: 要创建的项数据
            
        Returns:
            处理结果
        """
        try:
            _new_item = JsonObjCrud(None, None)
            _new_item.write_all(item)
            if list_num and list_num < len(self.data) and list_num >= 0:
                self.data.insert(list_num, _new_item)
            else:
                self.data.append(_new_item)
        except Exception as e:
            print(f"创建项时出错：{e}")
            return False
        return True
    
    def save_date(self, save_file_path: str | None = None):
        """
        保存数据到文件
        """
        try:
            self._check_sentence_window()
            if save_file_path:
                with open(save_file_path, 'w', encoding="utf-8") as f:
                    json.dump([item.read_all_vis() for item in self.data], f, ensure_ascii=False, indent=4)
            else:
                with open(self.file_path, 'w', encoding="utf-8") as f:
                    json.dump([item.read_all_vis() for item in self.data], f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise f"保存数据到文件时出错：{e}"
            return False
        return True

if __name__ == "__main__":
    crud = SentencesJsonListCrud("examples/example1/final.json")
    print(crud.read_all())
    crud.create(2, {"class": "语言", "sub_sentence": "你好", "describe": {"role": "你", "style": "formal"}})
    crud.save_date()
