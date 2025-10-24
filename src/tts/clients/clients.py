import requests
import json
import argparse
import os
import tempfile
import soundfile as sf
import numpy as np

# 服务端地址
SERVER_URL = "http://localhost:15376/generate"

def generate_audio(text, prompt_text, prompt_wav, class_name):
    """生成单个音频文件"""
    data = {
        "text": text,
        "prompts": {
            "example_prompt": {
                "class_name": class_name,
                "audio_path": prompt_wav,
                "text": prompt_text
            }
        }
    }
    
    response = requests.post(
        SERVER_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    
    if response.status_code == 200:
        return response.content
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")
        return None

def merge_wav_files(file_paths, output_path):
    """合并多个WAV文件，并在每个文件之间添加500ms静音，返回每个文件的开始时间和持续时间"""
    if not file_paths:
        return []
    
    # 读取第一个文件获取参数
    data, sample_rate = sf.read(file_paths[0])
    combined_data = data
    
    # 获取第一个文件的声道数
    if len(data.shape) == 1:
        num_channels = 1
    else:
        num_channels = data.shape[1]
    
    # 初始化时间信息列表
    time_info = []
    
    # 计算第一个文件的持续时间
    first_duration = len(data) / sample_rate
    time_info.append({
        'start_time': 0.0,
        'duration': first_duration
    })
    
    current_time = first_duration  # 当前累计时间
    
    # 处理剩余文件
    for i, file_path in enumerate(file_paths[1:], 1):
        print(f"合并第 {i+1}/{len(file_paths)} 个音频文件")
        
        # 添加500ms静音
        silence_duration = 0.0  # 500ms = 0.5秒
        silence_samples = int(sample_rate * silence_duration)
        current_time += silence_duration  # 添加静音时间
        
        # 创建静音数据，确保与当前数据的维度匹配
        if num_channels == 1:
            silence = np.zeros(silence_samples)
        else:
            silence = np.zeros((silence_samples, num_channels))
        
        # 读取当前文件
        current_data, current_sample_rate = sf.read(file_path)
        
        # 确保采样率一致
        if current_sample_rate != sample_rate:
            raise ValueError(f"采样率不一致: 第一个文件 {sample_rate}Hz, 当前文件 {current_sample_rate}Hz")
        
        # 确保声道数一致，如果不一致则进行转换
        if len(current_data.shape) != len(combined_data.shape):
            if len(current_data.shape) == 1 and len(combined_data.shape) == 2:
                # 当前文件是单声道，但合并数据是立体声，需要转换
                current_data = np.column_stack((current_data, current_data))
            elif len(current_data.shape) == 2 and len(combined_data.shape) == 1:
                # 当前文件是立体声，但合并数据是单声道，需要转换
                current_data = np.mean(current_data, axis=1)
        
        # 计算当前文件的持续时间
        current_duration = len(current_data) / sample_rate
        
        # 记录时间信息
        time_info.append({
            'start_time': current_time,
            'duration': current_duration
        })
        
        # 更新当前时间
        current_time += current_duration
        
        # 合并数据
        combined_data = np.concatenate((combined_data, silence, current_data))
    
    # 写入合并后的文件
    sf.write(output_path, combined_data, sample_rate)
    print(f"音频文件已保存为 {output_path}")
    
    return time_info

def process_json_file(json_file_path, output_file="output_combined.wav"):
    """处理JSON文件并生成合并的音频，同时生成时间信息JSON文件"""
    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return
    
    if not isinstance(data_list, list):
        print("JSON文件应该包含一个列表")
        return
    
    # 创建临时目录保存临时音频文件
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    # 保存有效的句子索引和内容
    valid_sentences = []
    
    print(f"开始处理 {len(data_list)} 个句子...")
    
    # 处理每个条目
    for i, item in enumerate(data_list):
        item['sub_sentence'] = item['sub_sentence'].replace(" ", "")
        item['sub_sentence'] = item['sub_sentence'].replace("…", "...")
        print(f"处理第 {i+1}/{len(data_list)} 个句子: {item['sub_sentence'][:50]}...")
        
        # 获取提示信息
        class_name = item.get("class", '')
        describe = item.get('describe', {})
        prompt_text = describe.get('prompt_text', '')
        prompt_wav = describe.get('prompt_wav', '')
        sub_sentence = item.get('sub_sentence', '')
        
        if not sub_sentence:
            print(f"第 {i+1} 个条目缺少 sub_sentence")
            continue
        
        # 生成音频
        audio_content = generate_audio(sub_sentence, prompt_text, prompt_wav, class_name)
        
        if audio_content:
            # 保存临时音频文件
            temp_file = os.path.join(temp_dir, f"temp_{i}.wav")
            with open(temp_file, "wb") as f:
                f.write(audio_content)
            temp_files.append(temp_file)
            # 记录有效的句子信息
            valid_sentences.append({
                'index': i,
                'sentence': sub_sentence,
                'original_item': item
            })
    
    # 合并音频文件
    if temp_files:
        print("开始合并音频文件...")
        time_info = merge_wav_files(temp_files, output_file)
        print(f"音频文件已保存为 {output_file}")
        
        # 生成时间信息JSON文件
        if time_info and len(time_info) == len(valid_sentences):
            # 创建输出JSON文件名
            json_output_file = os.path.splitext(output_file)[0] + '.json'
            
            # 构建时间信息列表
            time_data = []
            for i, (sentence_info, time_data_item) in enumerate(zip(valid_sentences, time_info)):
                time_data.append({
                    'sentence': sentence_info['sentence'],
                    'start_time': round(time_data_item['start_time'], 3),  # 保留3位小数
                    'duration': round(time_data_item['duration'], 3),      # 保留3位小数
                })
            
            # 写入JSON文件
            with open(json_output_file, 'w', encoding='utf-8') as f:
                json.dump(time_data, f, ensure_ascii=False, indent=2)
            
            print(f"时间信息已保存为 {json_output_file}")
        else:
            print(f"时间信息不匹配: 有效句子数 {len(valid_sentences)}, 时间信息数 {len(time_info)}")
        
        # 清理临时文件
        for temp_file in temp_files:
            os.remove(temp_file)
        os.rmdir(temp_dir)
        
        print("处理完成！")
    else:
        print("没有成功生成任何音频文件")
        os.rmdir(temp_dir)

def main():
    """主函数"""
    # python interfaces/client.py context_resources/anon_1_mapping.json -o ./outputs/anon_1.wav
    parser = argparse.ArgumentParser(description='处理JSON文件并生成合并的TTS音频')
    parser.add_argument('json_file', help='JSON文件路径')
    parser.add_argument('-o', '--output', default='output_combined.wav', 
                       help='输出音频文件名（默认: output_combined.wav）')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.json_file):
        print(f"文件不存在: {args.json_file}")
        return
    
    process_json_file(args.json_file, args.output)

if __name__ == "__main__":
    main()
