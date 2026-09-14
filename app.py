# ============================================================
# AI 资料问答助手（网页版）
# 功能：读取本地资料 → 检索相关片段 → 让大模型基于资料回答
# 运行：py -m streamlit run app.py   （或双击 启动网页版.bat）
# ============================================================

import os                 # 读环境变量、拼路径
import streamlit as st    # 网页界面库：用 st.xxx() 往页面放控件
import requests           # 给大模型发 HTTP 请求


# ------------------------------------------------------------
# ① 配置区：所有"可调参数"集中放这里，改东西只改这一段
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# __file__     → 当前脚本自己的路径（Python 内置变量）
# abspath(...) → 转成完整的绝对路径
# dirname(...) → 取它所在的文件夹
# 作用：不管从哪个目录启动，都能找到同目录下的 notes.txt

def get_api_key():
    """本地读环境变量；部署到 Streamlit Cloud 时改读 secrets"""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        return None

API_KEY = get_api_key()
URL = "https://api.deepseek.com/chat/completions"   # 接口地址
MODEL = "deepseek-chat"                              # 用哪个模型
NOTES_FILE = os.path.join(BASE_DIR, "notes.txt")     # 资料文件（拼成绝对路径）
TOP_N = 5                                            # 检索几块资料给模型看


# ------------------------------------------------------------
# ② 读资料并切片
# ------------------------------------------------------------
@st.cache_data          # 装饰器：把函数结果缓存起来，避免每次交互都重读文件
def load_chunks(path):
    """读取资料文件，按空行切成小块，返回一个列表"""
    with open(path, "r", encoding="utf-8") as f:
        # with 会在用完后自动关闭文件；encoding="utf-8" 防止中文乱码
        text = f.read()          # 一次性读入全部文字

    return [c.strip() for c in text.split("\n\n") if c.strip()]
    # text.split("\n\n")  → 按"空行"把整段资料切成列表
    # c.strip()            → 去掉每一块首尾的空白和换行
    # if c.strip()         → 过滤掉空块
    # 这叫"列表推导式"，等价于下面三行：
    #   result = []
    #   for c in text.split("\n\n"):
    #       if c.strip():
    #           result.append(c.strip())
    #   return result


# ------------------------------------------------------------
# ③ 检索：从所有小块里挑出和问题最相关的 top 块
# ------------------------------------------------------------
def retrieve(question, chunks, top):
    """简单打分：问句里的字在哪个块里出现得多，就认为哪块更相关"""
    scored = []                              # 准备一个空列表，装 (分数, 块)
    for c in chunks:                         # 遍历每一块
        score = sum(1 for ch in question if ch.strip() and ch in c)
        # 逐个取问句里的字 ch：只要 ch 出现在块 c 里就记 1，最后求和
        scored.append((score, c))            # 把(分数, 块)这一对存进列表

    scored.sort(key=lambda x: x[0], reverse=True)
    # sort 排序；key=lambda x: x[0] 表示"按每对的第 0 个元素（分数）比"
    # reverse=True 表示从大到小

    return [c for _, c in scored[:top]]
    # 取前 top 个，并且只把"块"拿出来（丢掉分数）


# ------------------------------------------------------------
# ④ 问模型：把提示词发给大模型，拿回回答
# ------------------------------------------------------------
def ask_llm(prompt):
    """统一的模型调用入口：给它一句话，返回模型的回答"""
    headers = {                              # 请求头：身份证明 + 数据格式
        "Authorization": f"Bearer {API_KEY}",  # Bearer 是固定格式，后面接你的 Key
        "Content-Type": "application/json",    # 告诉服务器：我发的是 JSON
    }
    body = {                                 # 请求体：一个字典
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],   # 消息列表
    }

    try:                                     # 网络可能失败，所以"试试看"
        resp = requests.post(URL, headers=headers, json=body, timeout=60)
        # post = 发送 POST 请求；timeout=60 表示最多等 60 秒，避免永远卡住
    except requests.exceptions.RequestException as e:
        return f"网络出错了：{e}"             # 失败就返回提示，不让程序崩溃

    if resp.status_code != 200:              # 状态码不是 200 就是失败
        return f"API 出错 {resp.status_code}: {resp.text}"

    return resp.json()["choices"][0]["message"]["content"]
    # resp.json() 把返回的 JSON 变成字典 → 一层层取出回答文字


# ============================================================
# ⑤ 页面部分（Streamlit）
# 重要：Streamlit 每次交互都会"从头执行整个脚本"
# ============================================================

st.title("📚 我的资料问答助手")      # 在页面顶部放一个大标题

if not API_KEY:                       # 没配置 Key 就直接停
    st.error("未找到 DEEPSEEK_API_KEY，请先设置环境变量")
    st.stop()                         # 停止往下执行

chunks = load_chunks(NOTES_FILE)      # 加载资料（有缓存，只读一次）
st.caption(f"已加载资料：{len(chunks)} 块")   # 小号灰字说明

question = st.text_input("请输入你的问题：")
# text_input = 放一个输入框；用户输入的内容会赋值给 question

if st.button("提问"):                  # button 在"这次被点击"时返回 True
    if not question.strip():          # 如果输入是空的
        st.warning("请先输入一个问题")
    else:
        with st.spinner("思考中…"):    # with 块内会显示转圈动画
            relevant = retrieve(question, chunks, TOP_N)   # ① 检索
            context = "\n---\n".join(relevant)             # ② 拼成一段资料
            prompt = f"""你有两种回答方式：
1. 如果问题和下面的资料有关，只根据资料回答；资料里没有就说"资料中没有提到"。
2. 如果是其他问题，可以直接回答，但要在开头注明"[非资料内容]"。


【资料】
{context}

【问题】{question}"""
            answer = ask_llm(prompt)                       # ③ 问模型

        st.markdown("### 回答")        # 小标题
        st.write(answer)              # 显示模型的回答

        with st.expander("查看检索到的资料片段"):   # 可折叠区域（点开才显示）
            for c in relevant:        # 把检索到的每一块列出来
                st.write("- " + c[:80] + "…")   # 只显示前 80 个字

