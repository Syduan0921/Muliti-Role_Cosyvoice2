import json
import os

# 1. 配置路径（输入为原验证集，输出为清洗后文件，避免覆盖原数据）
input_path = "Qwen3/dataset/val.jsonl"
output_path = "Qwen3/dataset/val_cleaned.jsonl"  # 新文件后缀不变，确保与训练集清洗逻辑一致


def clean_quotes_and_escapes(obj):
    """
    递归处理：1. 修复冗余转义（\\\\ → \\） 2. 替换单引号为标准转义双引号（' → \\\"）
    最终确保内容引号为 JSON 标准格式（如 "内容" 对应存储为 \\"内容\\"）
    """
    if isinstance(obj, str):
        # 步骤1：先修复已有的冗余转义（避免之前处理导致的 \\\\ 累积）
        fixed_escape = obj.replace("\\\\", "\\")
        # 步骤2：将所有单引号（包括直接 ' 和转义 \'）统一替换为标准转义双引号
        fixed_quote = fixed_escape.replace("'", "\\\"")
        return fixed_quote
    elif isinstance(obj, list):
        # 处理列表（如 output 中的 [{"class":..., "content":...}]）
        return [clean_quotes_and_escapes(item) for item in obj]
    elif isinstance(obj, dict):
        # 处理字典（确保键名、键值都符合格式）
        return {key: clean_quotes_and_escapes(value) for key, value in obj.items()}
    else:
        # 非字符串/列表/字典类型（如 metrics 中的数字）直接返回
        return obj


# 2. 读取原文件 → 清洗格式 → 写入新文件（逻辑不变，仅替换核心处理函数）
with open(input_path, "r", encoding="utf-8") as infile, \
     open(output_path, "w", encoding="utf-8") as outfile:
    
    line_count = 0  # 计数，方便查看处理进度
    for line in infile:
        line_count += 1
        try:
            # 解析每行 JSON 数据（跳过格式错误的行）
            data = json.loads(line.strip())
            # 调用修改后的清洗函数
            cleaned_data = clean_quotes_and_escapes(data)
            # 写入新文件（用 json.dumps 确保最终格式标准）
            outfile.write(json.dumps(cleaned_data, ensure_ascii=False) + "\n")
            
        except json.JSONDecodeError as e:
            # 遇到解析错误时打印提示，不中断整体流程
            print(f"警告：第 {line_count} 行 JSON 解析失败，已跳过 → 错误：{e}")

print(f"验证集清洗完成！共处理 {line_count} 行数据，清洗后文件：{output_path}")