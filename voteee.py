import streamlit as st
import pandas as pd
import time

# 启用 Session State 共享
st.set_page_config(
    page_title="多人德尔菲投票系统",
    layout="wide"
)

# 初始化共享数据
if "voting_initialized" not in st.session_state:
    st.session_state.voting_initialized = True
    st.session_state.shared_voting_data = {
        "current_round": 1,
        "votes": {},
        "voters": {},
        "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"]
    }

# 获取共享数据
data = st.session_state.shared_voting_data
current_round = data["current_round"]
votes = data["votes"]
voters = data["voters"]
active_options = data["active_options"]

st.title("🧠 多人实时德尔菲投票系统")

# 显示系统状态
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("当前轮次", current_round)
with col2:
    st.metric("剩余选项", len(active_options))
with col3:
    current_voters = len(voters.get(current_round, set()))
    st.metric("本轮投票人数", current_voters)

# 初始化当前轮次数据
if current_round not in votes:
    votes[current_round] = {option: 0 for option in active_options}
if current_round not in voters:
    voters[current_round] = set()

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票 📝")

if active_options:
    choice = st.radio("请选择你认为最合适的选项：", active_options)
    voter_id = st.text_input("请输入你的姓名（用于标识）：")
    
    if st.button("🗳️ 提交投票", type="primary") and voter_id:
        if voter_id in voters[current_round]:
            st.error("❌ 你已经在本轮投过票了！")
        else:
            votes[current_round][choice] += 1
            voters[current_round].add(voter_id)
            st.success(f"✅ 投票成功！你选择了：{choice}")
            st.balloons()
else:
    st.success("🎉 投票已结束！")

# 实时显示结果
st.subheader("📊 实时投票结果")

current_votes = votes.get(current_round, {})
if current_votes and any(count > 0 for count in current_votes.values()):
    vote_data = []
    for option, count in current_votes.items():
        if count > 0 or option in active_options:
            vote_data.append({"选项": option, "票数": count})
    
    df = pd.DataFrame(vote_data)
    df = df.sort_values("票数", ascending=False)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(df.set_index("选项"))
    with col2:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.write(f"**总投票人数**: {len(voters[current_round])}")
else:
    st.info("👆 还没有人投票，成为第一个投票者吧！")

# 主持人控制
st.subheader("🎯 主持人控制")

if st.button("🔄 进入下一轮投票"):
    if current_votes and any(count > 0 for count in current_votes.values()):
        valid_votes = {opt: count for opt, count in current_votes.items() 
                      if count > 0 and opt in active_options}
        
        if len(valid_votes) > 1:
            min_votes = min(valid_votes.values())
            eliminated = [opt for opt, count in valid_votes.items() if count == min_votes]
            
            st.warning(f"🎯 淘汰选项：{', '.join(eliminated)}")
            data["active_options"] = [opt for opt in active_options if opt not in eliminated]
            data["current_round"] = current_round + 1
            
            st.success(f"✅ 已进入第 {current_round + 1} 轮！")
            time.sleep(2)
            st.rerun()
        else:
            st.error("只剩一个选项或有票选项不足，无法淘汰")
    else:
        st.warning("没有有效的投票数据，无法进入下一轮")

# 系统管理
st.subheader("⚙️ 系统管理")
if st.button("🔄 重置整个系统"):
    st.session_state.shared_voting_data = {
        "current_round": 1,
        "votes": {},
        "voters": {},
        "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"]
    }
    st.success("系统已重置！")
    time.sleep(1)
    st.rerun()

# 自动刷新
st.info("💡 页面会自动刷新以显示最新结果")
time.sleep(15)
st.rerun()
