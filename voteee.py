import streamlit as st
import time

@st.cache_data(ttl=3600)
def get_shared_test_data():
    return {"votes": 0, "voters": []}

shared_data = get_shared_test_data()

st.title("最简单的跨设备测试")

if st.button("投票"):
    shared_data["votes"] += 1
    shared_data["voters"].append(f"用户{time.time()}")
    st.cache_data.clear()
    st.rerun()

st.write(f"总票数: {shared_data['votes']}")
st.write(f"投票者: {shared_data['voters']}")

if st.button("刷新"):
    st.cache_data.clear()
    st.rerun()
