# 🐸RoleTTS-Finetune
RoleTTS-Finetune致力于提供一个**开源工具箱**，以解决那些**原始长文本**（如小说，长剧本）的**角色语音**合成问题。本工具箱由四个核心部分组成：
- LongText-to-RoleText：将原始长文本转化为**分角色，分情感，分段落**的角色 or 旁白的可配音文本。
- RoleText-to-Audio: 利用本地或线上**TTS**将可配音文本转化为完整音频 and 字幕文件。
- LLM Finetune: 利用本地大模型或线上api，对提供的**badcase**进行微调，该工具箱提供了完整的dataset收集，DPO,SFT等微调workflow以及validation.
- TTS Finetune: 利用本地TTS或线上api，对提供的数据进行**标注，微调，分角色生成**以及结果评估。
生成结果推荐参考 [如我所声](https://www.bilibili.com/video/BV1DmpnznEM7/?share_source=copy_web&vd_source=858c84601b6002829615c837139d7d4e).

## Why use RoleTTS-Finetune?
### 生动的分角色音频生成
我们使用Doubao api与本地cosyvoice2作为基准模型，结果显示相比于无分角色音频，分角色音频的合成效果**更生动，更符合角色的情感**。模型在TTS之前加入了显示的情感tag作为提示词，文本内部也内嵌了**情绪SpecialToken**(如<\Strong>)作为语气的区分。

### 完善的工作流
提供了数**据收集->微调->文本切分->音频生成->效果评估**的完整工作流，适配现有的绝大多数LLM+TTS模型。（测试包括不限于DeepSeek, Doubao, Seed, Kimi与Cosyvoice2, Fish-TTS等）。

### 简便的一键式启用能力
本工具箱提供了一键式启用能力，用户只需要按照Guideline配置好环境，即可在短时间内完成模型的微调与音频生成。**无/低显卡需求**，直接调用api可以实现项目100%的功能。

## Guideline
### Example in Distince part
该部分对现有实现的所有功能（分LLM与TTS）进行演示，包括数据收集，原始模型效果，微调效果三个部分。
1. 数据收集 LLM部分 

    Wait for update.

2. 数据收集 TTS部分

    Wait for update.
    
4. 原始模型效果 LLM部分
   
    | 模型       | Classify       |           | Role Judgement      |           | Pronoun Judgement      |           | Special Token Generation       |           |
    | :--------- | :---------- | :-------- | :---------- | :-------- | :---------- | :-------- | :---------- | :-------- |
    |            | Acc         | Scores    | Acc         | Scores    | Acc         | Scores    | Acc         | Scores    |
    | Doubao-1.6 | \           | \         | \           | \         | \           | \         | \           | \         |
    | Qwen3-4B    | \           | \         | \           | \         | \           | \         | \           | \         |

5. 原始模型效果 TTS部分
6. 微调效果 LLM部分
7. 微调效果 TTS部分

## How to use RoleTTS-Finetune?
**Wait for update.**