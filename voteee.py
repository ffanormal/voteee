import streamlit as st
import pandas as pd
import time

st.set_page_config(
    page_title="多人德尔菲投票系统",
    layout="wide"
)

# 初始化共享数据 - 使用更健壮的方式
if "shared_voting_data" not in st.session_state:
    st.session_state.shared_voting_data = {
        "current_round": 1,
        "votes": {},
        "voters": {},
        "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
        "last_update": time.time()
    }

# 获取共享数据引用
data = st.session_state.shared_voting_data
current_round = data["current_round"]
votes = data["votes"]
voters = data["voters"]
active_options = data["active_options"]

st.title("🧠 多人实时德尔菲投票系统")

# 显示同步状态
st.sidebar.info(f"🔄 最后更新: {time.strftime('%H:%M:%S')}")

# 初始化当前轮次
if current_round not in votes:
    votes[current_round] = {option: 0 for option in active_options}
if current_round not in voters:
    voters[current_round] = set()

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票 📝")

if active_options and len(active_options) > 1:
    choice = st.radio("请选择选项：", active_options, key=f"vote_round_{current_round}")
    voter_id = st.text_input("请输入你的姓名：", key=f"voter_{current_round}")
    
    if st.button("🗳️ 提交投票", type="primary") and voter_id:
        if voter_id in voters[current_round]:
            st.error("❌ 你已经投过票了！")
        else:
            votes[current_round][choice] = votes[current_round].get(choice, 0) + 1
            voters[current_round].add(voter_id)
            data["last_update"] = time.time()  # 更新时间戳
            st.success(f"✅ 投票成功！选择: {choice}")
elif len(active_options) == 1:
    st.success(f"🎉 投票结束！获胜选项: {active_options[0]}")
else:
    st.warning("⚠️ 没有可用选项")

# 显示结果
st.subheader("📊 实时投票结果")
current_votes = votes.get(current_round, {})
if current_votes and any(votes.get(current_round, {}).values()):
    df = pd.DataFrame([
        {"选项": opt, "票数": count} 
        for opt, count in current_votes.items() 
        if count > 0
    ]).sort_values("票数", ascending=False)
    
    if not df.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(df.set_index("选项"))
        with col2:
            st.dataframe(df, use_container_width=True)
        st.write(f"投票人数: {len(voters[current_round])}")
else:
    st.info("等待第一票...")

# 主持人控制 - 修复同步问题
st.subheader("🎯 主持人控制")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 进入下一轮", type="secondary", use_container_width=True):
        if current_votes and any(count > 0 for count in current_votes.values()):
            # 找到要淘汰的选项
            valid_options = [opt for opt in active_options if current_votes.get(opt, 0) > 0]
            if len(valid_options) > 1:
                vote_counts = [current_votes.get(opt, 0) for opt in valid_options]
                min_votes = min(vote_counts)
                eliminated = [opt for opt in valid_options if current_votes.get(opt, 0) == min_votes]
                
                # 更新共享数据 - 这是同步的关键！
                new_options = [opt for opt in active_options if opt not in eliminated]
                data["active_options"] = new_options
                data["current_round"] = current_round + 1
                data["last_update"] = time.time()
                
                st.warning(f"淘汰: {', '.join(eliminated)}")
                st.success(f"进入第 {current_round + 1} 轮！")
                
                # 强制刷新
                time.sleep(2)
                st.rerun()
            else:
                st.error("只剩一个选项，无法淘汰")
        else:
            st.warning("没有投票数据")

with col2:
    if st.button("🔄 重置系统", use_container_width=True):
        st.session_state.shared_voting_data = {
            "current_round": 1,
            "votes": {},
            "voters": {},
            "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
            "last_update": time.time()
        }
        st.success("系统已重置！")
        time.sleep(1)
        st.rerun()

# 自动刷新机制
if st.button("🔄 手动刷新"):
    st.rerun()

# 显示同步状态
st.sidebar.subheader("同步状态")
st.sidebar.write(f"轮次: {current_round}")
st.sidebar.write(f"选项数: {len(active_options)}")
st.sidebar.write(f"投票数: {len(voters.get(current_round, []))}")

# 自动刷新
st.info("页面每20秒自动刷新...")
time.sleep(20)
st.rerun()
