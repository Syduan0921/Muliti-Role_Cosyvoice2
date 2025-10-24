import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), './third_party/Matcha-TTS'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)

from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torch
import torchaudio
from fastapi import FastAPI, Response
from pydantic import BaseModel
import io
from vllm import ModelRegistry
from cosyvoice.vllm.cosyvoice2 import CosyVoice2ForCausalLM
ModelRegistry.register_model("CosyVoice2ForCausalLM", CosyVoice2ForCausalLM)

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    prompts: dict  # {"prompt_key": {"audio_path": "path/to/audio.wav", "text": "prompt text", "class_name": "class_name"}}

# 初始化模型
cosyvoice_pangbai = None
cosyvoice = None

@app.on_event("startup")
async def startup_event():
    global cosyvoice, cosyvoice_pangbai
    cosyvoice = CosyVoice2('pretrained_models/CosyVoice2-0.5B', 
                          load_jit=True, 
                          load_trt=True, 
                          load_vllm=True, 
                          fp16=False,
                          class_name=None)
    cosyvoice_pangbai = CosyVoice2('pretrained_models/CosyVoice2-0.5B', 
                          load_jit=True, 
                          load_trt=True, 
                          load_vllm=True, 
                          fp16=False,
                          class_name="旁白")

@app.post("/generate")
async def generate_audio(request: TTSRequest):
    # 提取第一个提示词（根据实际需求可扩展）
    prompt_key = next(iter(request.prompts.keys()))
    prompt_info = request.prompts[prompt_key]
    
    # 加载提示音频
    prompt_speech_16k = load_wav(prompt_info["audio_path"], 16000)
    class_name = prompt_info["class_name"]
    
    # 生成音频
    audio_segments = []
    if class_name == "旁白":
        for segment in cosyvoice_pangbai.inference_zero_shot(
            request.text, 
            prompt_info["text"], 
            prompt_speech_16k, 
            stream=False
        ):
            audio_segments.append(segment["tts_speech"])
    else:
        for segment in cosyvoice.inference_zero_shot(
            request.text, 
            prompt_info["text"], 
            prompt_speech_16k, 
            stream=False
        ):
            audio_segments.append(segment["tts_speech"])
    
    audio_tensor = torch.cat(audio_segments, dim=-1)
    
    # 将音频转换为字节流
    buffer = io.BytesIO()
    torchaudio.save(buffer, audio_tensor, cosyvoice.sample_rate, format="wav")
    buffer.seek(0)
    audio_bytes = buffer.read()
    
    return Response(content=audio_bytes, media_type="audio/wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=15376)
