"""
SentencesJsonCrud 测试用例

测试句子JSON CRUD类的增删改查功能，基于实际数据文件
"""

import unittest
import os
import sys
import tempfile
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.template.sentences_json import SentencesJsonCrud


class TestSentencesJsonCrud(unittest.TestCase):
    """SentencesJsonCrud CRUD操作测试类"""

    def setUp(self):
        """测试前置设置"""
        # 使用实际的测试数据文件
        self.test_file = "examples/example1/final.json"
        self.list_num = 1  # 测试第二个句子项
        
        # 创建测试实例
        self.crud_instance = SentencesJsonCrud(file_path=self.test_file, list_num=self.list_num)

    def test_initialization(self):
        """测试初始化"""
        # 测试正常初始化
        crud = SentencesJsonCrud(file_path=self.test_file, list_num=self.list_num)
        self.assertIsNotNone(crud)
        self.assertEqual(crud.file_path, self.test_file)
        self.assertEqual(crud.list_num, self.list_num)
        
        # 测试文件不存在的情况
        crud_empty = SentencesJsonCrud(file_path="nonexistent.json", list_num=0)
        self.assertEqual(crud_empty.data, {})

    def test_load_data_success(self):
        """测试成功加载数据"""
        # 重新创建实例以触发load_data
        crud = SentencesJsonCrud(file_path=self.test_file, list_num=self.list_num)
        
        # 验证数据正确加载
        self.assertEqual(crud.data["sub_sentence"], "两周<strong>就</strong>回来，你要<strong>乖乖的</strong>。")
        self.assertEqual(crud.data["class"], "语言")
        self.assertIn("两周就回来，你要乖乖的", crud.data["sentence"])
        self.assertEqual(crud.data["describe"]["role"], "万敌")
        self.assertIsNone(crud.data["describe"]["style"])

    def test_load_data_failure(self):
        """测试加载数据失败情况"""
        # 测试无效JSON文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as bad_file:
            bad_file.write("invalid json content")
            bad_file_path = bad_file.name
        
        try:
            crud = SentencesJsonCrud(file_path=bad_file_path, list_num=0)
            # 由于load_data失败，数据应该为空
            self.assertEqual(crud.data, {})
        finally:
            if os.path.exists(bad_file_path):
                os.unlink(bad_file_path)
        
        # 测试列表索引越界
        crud_out_of_range = SentencesJsonCrud(file_path=self.test_file, list_num=999)
        self.assertEqual(crud_out_of_range.data, {})

    def test_read_success(self):
        """测试成功读取数据"""
        # 测试读取各个字段
        sub_sentence_value = self.crud_instance.read("sub_sentence")
        class_value = self.crud_instance.read("class")
        sentence_value = self.crud_instance.read("sentence")
        describe_value = self.crud_instance.read("describe")
        
        self.assertEqual(sub_sentence_value, "两周<strong>就</strong>回来，你要<strong>乖乖的</strong>。")
        self.assertEqual(class_value, "语言")
        self.assertIn("两周就回来，你要乖乖的", sentence_value)
        self.assertEqual(describe_value["role"], "万敌")
        self.assertIsNone(describe_value["style"])

    def test_read_all(self):
        """测试读取所有数据"""
        all_data = self.crud_instance.read_all()
        
        self.assertIsInstance(all_data, dict)
        self.assertEqual(all_data["sub_sentence"], "两周<strong>就</strong>回来，你要<strong>乖乖的</strong>。")
        self.assertEqual(all_data["class"], "语言")
        self.assertIn("两周就回来，你要乖乖的", all_data["sentence"])
        self.assertEqual(all_data["describe"]["role"], "万敌")
        self.assertIsNone(all_data["describe"]["style"])

    def test_update_success(self):
        """测试成功更新数据"""
        # 更新各个字段
        result_sub_sentence = self.crud_instance.update("sub_sentence", "更新后的子句内容")
        result_class = self.crud_instance.update("class", "旁白")
        result_sentence = self.crud_instance.update("sentence", "更新后的完整句子内容")
        result_describe = self.crud_instance.update("describe", {"role": "小王", "style": "轻松"})
        
        self.assertTrue(result_sub_sentence)
        self.assertTrue(result_class)
        self.assertTrue(result_sentence)
        self.assertTrue(result_describe)
        
        # 验证数据已更新
        self.assertEqual(self.crud_instance.data["sub_sentence"], "更新后的子句内容")
        self.assertEqual(self.crud_instance.data["class"], "旁白")
        self.assertEqual(self.crud_instance.data["sentence"], "更新后的完整句子内容")
        self.assertEqual(self.crud_instance.data["describe"]["role"], "小王")
        self.assertEqual(self.crud_instance.data["describe"]["style"], "轻松")

    def test_update_failure(self):
        """测试更新数据失败情况"""
        # 测试更新不存在的键
        result = self.crud_instance.update("nonexistent_key", "value")
        self.assertFalse(result)

    def test_delete_success(self):
        """测试成功删除数据"""
        # 删除各个字段（设置为None）
        result_sub_sentence = self.crud_instance.delete("sub_sentence")
        result_class = self.crud_instance.delete("class")
        result_sentence = self.crud_instance.delete("sentence")
        result_describe = self.crud_instance.delete("describe")
        
        self.assertTrue(result_sub_sentence)
        self.assertTrue(result_class)
        self.assertTrue(result_sentence)
        self.assertTrue(result_describe)
        
        # 验证数据已被删除（设置为None）
        self.assertIsNone(self.crud_instance.data["sub_sentence"])
        self.assertIsNone(self.crud_instance.data["class"])
        self.assertIsNone(self.crud_instance.data["sentence"])
        self.assertIsNone(self.crud_instance.data["describe"])

    def test_delete_failure(self):
        """测试删除数据失败情况"""
        # 测试删除不存在的键
        result = self.crud_instance.delete("nonexistent_key")
        self.assertFalse(result)

    def test_save_data(self):
        """测试保存数据功能"""
        # 当前save_data方法返回False并打印消息
        result = self.crud_instance.save_data()
        self.assertFalse(result)

    def test_integration_workflow(self):
        """测试完整的CRUD工作流程"""
        # 1. 初始状态
        initial_data = self.crud_instance.read_all()
        self.assertEqual(initial_data["sub_sentence"], "两周<strong>就</strong>回来，你要<strong>乖乖的</strong>。")
        
        # 2. 更新数据
        update_success = self.crud_instance.update("sub_sentence", "工作流更新后的子句")
        self.assertTrue(update_success)
        
        # 3. 读取验证更新
        updated_sub_sentence = self.crud_instance.read("sub_sentence")
        self.assertEqual(updated_sub_sentence, "工作流更新后的子句")
        
        # 4. 删除数据
        delete_success = self.crud_instance.delete("sub_sentence")
        self.assertTrue(delete_success)
        
        # 5. 验证删除
        deleted_sub_sentence = self.crud_instance.read("sub_sentence")
        self.assertIsNone(deleted_sub_sentence)
        
        # 6. 重新创建数据
        new_item = {
            "sub_sentence": "最终测试子句",
            "class": "动作",
            "sentence": "最终测试句子内容",
            "describe": {"role": "最终角色", "style": "最终风格"}
        }
        
        # 由于当前create方法需要遍历所有SentenceKeys，而我们的测试使用字符串键
        # 这里我们直接使用update来模拟创建
        self.crud_instance.update("sub_sentence", new_item["sub_sentence"])
        self.crud_instance.update("class", new_item["class"])
        self.crud_instance.update("sentence", new_item["sentence"])
        self.crud_instance.update("describe", new_item["describe"])
        
        # 7. 验证最终状态
        final_data = self.crud_instance.read_all()
        self.assertEqual(final_data["sub_sentence"], "最终测试子句")
        self.assertEqual(final_data["class"], "动作")
        self.assertEqual(final_data["sentence"], "最终测试句子内容")
        self.assertEqual(final_data["describe"]["role"], "最终角色")

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试空字符串值
        self.crud_instance.update("sub_sentence", "")
        self.assertEqual(self.crud_instance.read("sub_sentence"), "")
        
        # 测试None值
        self.crud_instance.update("describe", None)
        self.assertIsNone(self.crud_instance.read("describe"))
        
        # 测试复杂嵌套结构
        complex_describe = {
            "role": "复杂角色",
            "style": "复杂风格",
            "additional": {"nested": "data"}
        }
        self.crud_instance.update("describe", complex_describe)
        describe_data = self.crud_instance.read("describe")
        self.assertEqual(describe_data["additional"]["nested"], "data")

    def test_different_list_indexes(self):
        """测试不同的列表索引"""
        # 测试第一个句子项
        crud0 = SentencesJsonCrud(file_path=self.test_file, list_num=0)
        self.assertEqual(crud0.data["class"], "旁白")
        
        # 测试第二个句子项
        crud1 = SentencesJsonCrud(file_path=self.test_file, list_num=1)
        self.assertEqual(crud1.data["class"], "语言")
        
        # 测试第三个句子项
        crud2 = SentencesJsonCrud(file_path=self.test_file, list_num=2)
        self.assertEqual(crud2.data["class"], "旁白")


class TestSentencesJsonCrudUsageExample(unittest.TestCase):
    """测试用户提供的使用示例"""
    
    def test_usage_example(self):
        """测试用户提供的使用示例"""
        crud = SentencesJsonCrud("examples/example1/final.json", 1)
        result = crud.update("describe", {"role": "小王", "style": None})
        self.assertTrue(result)
        
        all_data = crud.read_all()
        self.assertEqual(all_data["describe"]["role"], "小王")
        self.assertIsNone(all_data["describe"]["style"])


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
