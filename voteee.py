import streamlit as st
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
import json

# 配置 Google Sheets
def init_google_sheets():
    # 你需要先设置 Google Sheets API
    # 1. 访问 https://console.cloud.google.com/
    # 2. 创建服务账户并下载 JSON 密钥文件
    # 3. 将密钥文件内容粘贴到 Streamlit Cloud 的 Secrets 中
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # 从 Streamlit Secrets 获取凭据
    creds_dict = st.secrets["google_sheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # 打开或创建表格
    try:
        sheet = client.open("投票系统数据").sheet1
    except:
        # 如果表格不存在，创建一个
        sheet = client.create("投票系统数据").sheet1
        # 初始化表头
        sheet.append_row(["timestamp", "voter_id", "round", "vote", "action"])
    
    return sheet

# 简化版：使用 Streamlit 的静态存储（有限共享）
def get_shared_data():
    """使用 st.cache_resource 尝试实现共享"""
    if "votes" not in st.session_state:
        st.session_state.votes = {}
        st.session_state.voters = {}
        st.session_state.current_round = 1
        st.session_state.options = ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"]
    return st.session_state

# 主应用
st.title("🧠 多人德尔菲投票系统 - 外部存储版")

# 尝试使用更激进的缓存策略
@st.cache_resource(experimental_allow_widgets=True)
def get_global_state():
    return {
        "current_round": 1,
        "votes": {},
        "voters": set(),
        "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
        "last_update": time.time()
    }

# 获取全局状态
global_state = get_global_state()

# 显示状态
st.sidebar.subheader("系统状态")
st.sidebar.write(f"轮次: {global_state['current_round']}")
st.sidebar.write(f"投票数: {len(global_state['voters'])}")
st.sidebar.write(f"最后更新: {time.strftime('%H:%M:%S')}")

# 投票界面
st.subheader(f"第 {global_state['current_round']} 轮投票")

choice = st.radio("选择:", global_state["options"])
voter_id = st.text_input("你的姓名:")

if st.button("🗳️ 投票"):
    if voter_id in global_state["voters"]:
        st.error("已投过票!")
    else:
        # 更新投票数据
        if choice not in global_state["votes"]:
            global_state["votes"][choice] = 0
        global_state["votes"][choice] += 1
        global_state["voters"].add(voter_id)
        global_state["last_update"] = time.time()
        
        st.success("投票成功!")
        
        # 强制清除所有缓存
        try:
            st.cache_resource.clear()
        except:
            pass
        st.rerun()

# 显示结果
st.subheader("投票结果")
if global_state["votes"]:
    df = pd.DataFrame([
        {"选项": k, "票数": v} 
        for k, v in global_state["votes"].items()
    ])
    st.bar_chart(df.set_index("选项"))
    st.dataframe(df)
else:
    st.info("暂无投票")

# 手动刷新
if st.button("🔄 强制刷新所有数据"):
    try:
        st.cache_resource.clear()
    except:
        pass
    st.rerun()
