# AI 资料问答助手

一个基于大模型的资料问答小工具：读取本地资料，回答你关于资料的问题。

## 功能
- 读取本地 notes.txt 并自动切片
- 根据问题检索最相关的片段
- 让大模型只依据资料回答，资料没有就说"没提到"

## 安装
1. 安装 Python 3.10+
2. 安装依赖：
   pip install -r requirements.txt
3. 配置 API Key（环境变量）：
   setx DEEPSEEK_API_KEY "sk-你的key"

## 使用
py assistant.py

## 示例
你：笔记编号是什么？
AI：笔记编号是 PY-W2-007。
---

## 快速启动（不用记命令）

### 方式一：双击运行（推荐）
- `启动网页版.bat` —— 双击，浏览器自动打开网页版
- `启动命令行版.bat` —— 双击，在终端里问答

### 方式二：终端命令
```powershell
cd "E:\Deepseek工作区\ai学习\git仓库\项目\assistant"

# 网页版
py -m streamlit run app.py

# 命令行版
py assistant.py
```

停止网页版：在终端按 Ctrl + C
