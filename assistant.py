import os
import requests

# ===== 配置区（想改什么只改这里）=====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
NOTES_FILE = os.path.join(BASE_DIR, "notes.txt")
TOP_N = 5            # 检索几块资料（改成 5 试试）
DEBUG = True        # 想看检索过程就改成 True
# ===================================

if not API_KEY:
    print("❌ 未找到 DEEPSEEK_API_KEY，请先运行：setx DEEPSEEK_API_KEY \"sk-...\"")
    raise SystemExit


def ask_llm(prompt):
    """统一的模型调用入口"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}

    try:
        resp = requests.post(URL, headers=headers, json=body, timeout=60)
    except requests.exceptions.RequestException as e:
        return f"网络出错了：{e}"

    if resp.status_code != 200:
        return f"API 出错 {resp.status_code}: {resp.text}"

    return resp.json()["choices"][0]["message"]["content"]


# ===== ① 读资料并切片 =====
try:
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        text = f.read()
except FileNotFoundError:
    print(f"❌ 找不到资料文件：{NOTES_FILE}")
    raise SystemExit

chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
print(f"资料被切成 {len(chunks)} 块")


# ===== ② 检索 =====
def retrieve(question, chunks, top):
    scored = []
    for c in chunks:
        score = sum(1 for ch in question if ch.strip() and ch in c)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top]]


# ===== ③ 组装提示词 → 交给 ask_llm =====
def ask(question):
    relevant = retrieve(question, chunks, TOP_N)      # ★ 用配置里的 TOP_N

    if DEBUG:
        print(f"[调试] 检索到 {len(relevant)} 块：")
        for c in relevant:
            print("   -", c[:40])

    context = "\n---\n".join(relevant)
    prompt = f"""请只根据下面提供的资料回答问题。
如果资料里没有答案，就回答"资料中没有提到"，不要自己编。

【资料】
{context}

【问题】{question}"""

    return ask_llm(prompt)


# ===== ④ 主循环 =====
print("开始提问吧（输入 exit 退出）")
while True:
    q = input("\n你的问题（exit 退出）：").strip()

    if q == "exit":
        print("再见！")
        break
    if not q:
        print("请先输入一个问题")
        continue

    print("思考中…")
    print("\nAI：", ask(q))