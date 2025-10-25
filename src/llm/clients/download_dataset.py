from datasets import load_dataset
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# 定义数据集名称和本地保存路径
dataset_name = "krisfu/delicate_medical_r1_data_chinese"
save_dir = os.path.join("data", "dataset")  # 使用os.path.join确保跨平台兼容

try:
    # 尝试加载数据集，只加载train分割以避免验证分割的转换错误
    print("Loading dataset...")
    dataset = load_dataset(dataset_name, split='train', ignore_verifications=True)
    print(f"Dataset loaded successfully with {len(dataset)} examples")
    
    # 保存到本地
    print(f"Saving dataset to {save_dir}...")
    dataset.save_to_disk(save_dir)
    print("Dataset saved successfully!")
    
except Exception as e:
    print(f"Error loading dataset: {e}")
    print("Trying alternative approach with manual download...")
    
    # 备用方法：手动下载JSONL文件
    try:
        from huggingface_hub import snapshot_download
        print("Downloading dataset files manually...")
        snapshot_download(
            repo_id=dataset_name,
            local_dir=save_dir,
            repo_type="dataset",
            allow_patterns=["*.jsonl", "*.json", "*.txt", "README.md"]
        )
        print("Dataset files downloaded manually!")
        
        # 尝试从本地文件加载
        print("Loading dataset from local files...")
        dataset = load_dataset(save_dir, split='train')
        print(f"Dataset loaded from local files with {len(dataset)} examples")
        
    except Exception as e2:
        print(f"Manual download also failed: {e2}")
        print("Please try downloading the dataset manually from Hugging Face Hub.")
        print(f"Dataset URL: https://huggingface.co/datasets/{dataset_name}")
