"""
核心处理步骤接口：
将输入的JSON_List中的代词替换为对应的人称代词。
"""
try:
    from src.template.sentences_json import SentencesJsonListCrud, SentencesJsonCrud
except:
    from template.sentences_json import SentencesJsonListCrud, SentencesJsonCrud

def process_pronoun(json_list: SentencesJsonListCrud) -> SentencesJsonListCrud:
    """
    处理JSON_List中的代词
    
    Args:
        json_list: 输入的JSON_List
        
    Returns:
        处理后的JSON_List
    """