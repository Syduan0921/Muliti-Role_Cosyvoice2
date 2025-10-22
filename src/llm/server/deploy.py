import torch
import os
import json
import time
import uuid
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict, Any

# Get absolute path to model directory
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "..", "model_path")
model_path = os.path.abspath(model_path)

print(f"Loading model from: {model_path}")

# Check if CUDA is available
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    device_map=device,
    trust_remote_code=True
).eval()

# FastAPI app
app = FastAPI(title="Qwen3 API Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False
    extra_body: Optional[dict] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = "stop"

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Usage
    system_fingerprint: Optional[str] = None

def generate_response(messages: List[Message], max_tokens: int = 4096):
    """Generate response using the local Qwen3 model"""
    try:
        # Convert messages to the format expected by tokenizer
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Apply chat template
        text = tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        # Tokenize input and count tokens
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        prompt_tokens = len(model_inputs.input_ids[0])
        
        # Generate response
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Extract and decode response
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        content = tokenizer.decode(output_ids, skip_special_tokens=True)
        completion_tokens = len(output_ids)
        
        return content.strip(), prompt_tokens, completion_tokens
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint"""
    try:
        print(f"Received request: model={request.model}, messages={len(request.messages)}")
        if request.extra_body:
            print(f"Extra body: {request.extra_body}")
        
        # Generate response with token counts
        response_content, prompt_tokens, completion_tokens = generate_response(
            messages=request.messages,
            max_tokens=request.max_tokens
        )
        
        total_tokens = prompt_tokens + completion_tokens
        
        # Create response in OpenAI format
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response_content
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ),
            system_fingerprint=f"qwen3-{uuid.uuid4().hex[:8]}"
        )
        
        print(f"Generated response: {len(response_content)} characters, {completion_tokens} tokens")
        return response
        
    except Exception as e:
        print(f"Error in create_chat_completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": True}

# Pydantic model for eval response
class EvalChatCompletionResponse(BaseModel):
    id: str
    created: int
    model: str
    input_ids: List[int]
    generated_ids: List[int]
    full_sequence_ids: List[int]
    generated_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@app.post("/eval/chat/completions", response_model=EvalChatCompletionResponse)
async def create_eval_chat_completion(request: ChatCompletionRequest):
    """Evaluation endpoint that returns raw generation data"""
    try:
        print(f"Eval request: model={request.model}, messages={len(request.messages)}")
        
        # Convert messages to the format expected by tokenizer
        formatted_messages = []
        for msg in request.messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Apply chat template
        text = tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        # Tokenize input and count tokens
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        prompt_tokens = len(model_inputs.input_ids[0])
        input_ids = model_inputs.input_ids[0].tolist()
        
        # Generate response
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=request.max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=False
        )
        
        # Get all generated sequences
        generated_sequences = generated_ids.sequences
        
        # For eval, we return the first sequence (batch size 1)
        full_sequence = generated_sequences[0].tolist()
        
        # Extract the generated part (after input)
        output_ids = full_sequence[len(input_ids):]
        completion_tokens = len(output_ids)
        total_tokens = prompt_tokens + completion_tokens
        
        # Decode the generated text
        generated_text = tokenizer.decode(output_ids, skip_special_tokens=True)
        
        # Create eval response with raw data
        response = EvalChatCompletionResponse(
            id=f"eval-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            input_ids=input_ids,
            generated_ids=output_ids,
            full_sequence_ids=full_sequence,
            generated_text=generated_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        print(f"Eval response: {len(generated_text)} characters, {completion_tokens} tokens")
        return response
        
    except Exception as e:
        print(f"Error in create_eval_chat_completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Qwen3 API Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "eval": "/eval/chat/completions",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    print("Starting Qwen3 API server on http://localhost:15387")
    uvicorn.run(app, host="0.0.0.0", port=15387)
