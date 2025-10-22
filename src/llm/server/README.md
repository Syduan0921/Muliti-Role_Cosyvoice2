# 描述
该部分主要负责**本地搭建**LLM以实现离线推理流程以及微调流程

# 主要功能
1. 单模块调用与验证
2. 本地部署
3. 微调

# How to test and deploy
wait for update

# 工程上的讨论
## 如何下载模型
建议使用huggingface(例如[Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507))直接下载到model_path

`huggingface-cli download --resume-download Qwen/Qwen3-4B-Instruct-2507 --local-dir /use/you/path/here --local-dir-use-symlinks False`

## 服务器如何测试搭建是否正常
需要注意的是，该模块下的脚本均是搭建在服务器（GPU机器）上的，因此需要测试模型是否可以正常工作，使用./test_file/test_avaiable.py 如果正常返回且GPU正常负载，则说明模型端是正常的。

## 测试时使用的全流程介绍
- 服务器端: 为了方便测试，训练与微调，直接使用了transformers框架来加载模型，然后Fastapi搭建服务，uvicorn处理端口。
参考deploy.py,直接访问ip:端口/v1/chat/completions则访问到api

- 用户端: 统一使用openai作为分发，整个data结构如下
```
message_body = [
    {"role": "system", "content": "你是一个专业的对话分析员，下面将对将要被用于配音的台本进行分割任务，任务是将台本中的复杂文本进行分割，将其分为语言、内心独白和旁白。你还需要灵活利用上下文来判断，例如观察上文是否正在延续没有说完的话或思考，这会对你后续的判断产生很重要的影响。"},

    {"role": "user", "content": "Your Question Here!"},
]
headers = {
    "Content-Type": "application/json"
}
# 标准的openai接口
data = {
    "model": "model_name",
    "messages": "message_body"
    "max_token": 可选int
    "temperature": float 默认为0.7
    "top_p": float 默认为0.9核
    "stream": False
    "extra_body": Dict[Any] #目前没有设计
}
```
使用post指令封装发送出去
```
response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
```
捕获返回值，可以得到如下的返回值数据(见deploy.py)
```
response = {
    id: str, # 为回复的唯一可识别id
    created: int, # 为生成时间
    model: str, # 为req.model中指定的名字
    choices: List[Obj], # 为核心数据，但实际上目前封装只封装了一个对象
    usage: Dict[str, int], # 额外数据，包含token数量统计。
    system_fingerprint: str # 包含唯一可识别uuid
}

choices = [
    {
        index: int #表示topk的第几个结果。
        message: ChatMessage # 表示核心反馈结果
        finish_reason: str # 目前写死为stop
    }
]

message = {
    role: str # 写死为assistant
    content: str # 反馈结果的json格式
}
```

## 为什么post中使用/v1/chat/completions但是openai的url为/v1？
openai的设计: 如果我将openai改为默认的/v1/chat/completions，则它会访问的是/v1/chat/completions/chat/completions



