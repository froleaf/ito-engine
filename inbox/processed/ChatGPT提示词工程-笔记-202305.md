https://learn.deeplearning.ai/chatgpt-prompt-eng/lesson/2/guidelines
import openai
import os

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.getenv('OPENAI_API_KEY')
def get_completion(prompt, model="gpt-3.5-turbo",temperature=0): # Andrew mentioned that the prompt/ completion paradigm is preferable for this class
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

提示的基本原则
- 原则1：给出清晰且具体的指令
  - 策略1：使用一些分隔符号来指示内容，如```、<>、<tag> </tag>；
  - 策略2：可以让模型返回指定格式的输出，如python、json、HTML等；
  - 策略3：可以让模型检查一段话是否满足某种描述；
    - 例如，判断是否由N个步骤组成：是，则按给定的模版拆出步骤；否，则返回指定关键句；
  - 策略4：给出一些示例，直接让模型模仿；
- 原则2：给模型一些思考的时间
  - 策略1：明确指定完成任务需要的步骤；对于需要的输出样式，给出明确的格式描述；
  - 策略2：指示模型先自己制定解决方案，而不是匆忙给出结论。
- 模型限制：幻觉（Hallucinations），会笃定地给一些错误信息
  - 优化：首先让模型找到相关的信息，再让它基于相关信息来回答问题。

提示的迭代方法
Idea --> Implementation --> Experimental result --> Error Analysis
大部分情况下，第一次训练都不会很好；这里用一个例子讲如何迭代提示工程
- 工程内容：基于技术部的清单，为市场部写一段关于气垫椅的产品介绍
  - 遇到问题1：输出太长
  - 解决方案：限制字数；或限制句子数。
  - 遇到问题2：focuses on the wrong details
  - 解决方案：说明“介绍的面向对象是家具零售商，需要技术性的材料细节为主”并“要求在末尾加上产品ID”。
  - 遇到问题3：还需要一个关于椅子规格的表格
  - 解决方案：“在介绍后面，附上x行x列的表格描述椅子的规格，每列分别描述xxx；表名为xxx”，并用HTML格式输出。

如何使用Summarizing功能（总结）
- 让模型【summarize/extract】一段内容：
  - 给出限制词数；
  - 可以明确说明段落来源、阅读对象、输出形式（反馈等）、关注重点等；
  - “总结”时，模型会尽可能在满足需求的同时顾及到各方面内容；
  - “提取”时，模型仅给出指令里提到的关注重点内容；

如何使用inferring功能（推断）
- 情绪识别：在购物反馈领域的使用
  - 让模型推测文案的【情绪sentiment】：
  - 这段文字的情绪是怎样的？给出你的回答，使用单个词“positive”or“negative”；
  - 让模型识别emotions的type（情绪词列表）；
  - 让模型识别“气愤”；
  - 提取产品和公司的名字（提取信息）；
- 可以一次进行多个上述任务；
- 主题提取：段落的topic推断
  - 推断段落的N个topic；限制每个topic使用1-2个词；
  - 关键词推断（通过与新闻主题的匹配，进行新闻标签分类；或对特定主题新闻进行alert）；

如何使用Transforming功能（转换）
翻译、拼写和语法检查、语气调整和格式转换。
- 翻译：可以指定对应的语言，以及场景（正式、非正式、英国海盗语气……）
- 对话：用接收到的语言类型（识别语言），进行对话输出
- 语气调整：将一句话调整为商务邮件/学术邮件等语气（business letter）
- 格式转换：将JSON格式转换为HTML；将文字输出为markdown格式；
- 拼写与语法检查：【proofread】or【proofread and correct】模型使用
from redlines import Redlines

diff = Redlines(text,response)
display(Markdown(diff.output_markdown))

如何使用Expanding功能（扩展）
用小段文字扩展为大段文字
- 基于用户的来信以及来信的情绪，分情况生成回信；
  - 正面或中立情绪，则表达感谢；
  - 负面情绪则表达歉意，并建议他们联系客服服务；
  - 回复基于指定的语气（简洁、专业等）
  - temperature参数：模型输出的随机程度，取值为[0,1]
    - 默认为0，此时生成的文字永远是最高概率的值

Build a chatbot
def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
#     print(str(response.choices[0].message))
    return response.choices[0].message["content"]
- 通过user角色与assistant角色对话，而system角色则是更高层的指导者。
- 需要在message内输入前面的所有对话，来形成非单次对话的记忆。
# 示例
messages =  [  
{'role':'system', 'content':'You are an assistant that speaks like Shakespeare.'},    
{'role':'user', 'content':'tell me a joke'},   
{'role':'assistant', 'content':'Why did the chicken cross the road'},   
{'role':'user', 'content':'I don\'t know'}  ]
response = get_completion_from_messages(messages, temperature=1)
print(response)
- 搭建语序机器人需要建立一个收集过去对话的能力：
def collect_messages(_):
    prompt = inp.value_input
    inp.value = ''
    context.append({'role':'user', 'content':f"{prompt}"})
    response = get_completion_from_messages(context) 
    context.append({'role':'assistant', 'content':f"{response}"})
    panels.append(
        pn.Row('User:', pn.pane.Markdown(prompt, width=600)))
    panels.append(
        pn.Row('Assistant:', pn.pane.Markdown(response, width=600, style={'background-color': '#F6F6F6'})))
 
    return pn.Column(*panels)

- 以点单系统为例：
  - 系统设定点单系统的搭建方式和对话方式
  - 模型通过对话系统与用户确认菜单
  - 系统向模型发送指令，生成订单的JSON模式，确定包含内容，并输出