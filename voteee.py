import streamlit as st
import pandas as pd
import time

# 使用 st.session_state 实现跨终端共享
if "shared_voting_data" not in st.session_state:
    st.session_state.shared_voting_data = {
        "current_round": 1,
        "votes": {},  # 格式: {1: {"选项A": 5, "选项B": 3}, 2: {...}}
        "voters": {},  # 格式: {1: ["用户1", "用户2"], 2: [...]}
        "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"]
    }

st.title("🧠 多人实时德尔菲投票系统")

# 获取共享数据
data = st.session_state.shared_voting_data
current_round = data["current_round"]
votes = data["votes"]
voters = data["voters"]
active_options = data["active_options"]

# 初始化当前轮次的投票数据
if current_round not in votes:
    votes[current_round] = {option: 0 for option in active_options}
if current_round not in voters:
    voters[current_round] = set()

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票")

if active_options:
    choice = st.radio("选择你的投票：", active_options)
    voter_id = st.text_input("你的名称（必填）")

    if st.button("🗳️ 提交投票") and voter_id:
        if voter_id in voters[current_round]:
            st.error("⚠️ 你已经在本轮投过票了！")
        else:
            # 记录投票 - 这个修改对所有用户可见
            votes[current_round][choice] += 1
            voters[current_round].add(voter_id)
            st.success("✅ 投票成功！")
else:
    st.success("🎉 投票已结束！")

# 实时显示结果
st.subheader("📊 实时投票结果")

current_votes = votes.get(current_round, {})
if current_votes and any(count > 0 for count in current_votes.values()):
    df = pd.DataFrame(list(current_votes.items()), columns=["选项", "票数"])
    df = df[df["票数"] > 0].sort_values("票数", ascending=False)

    st.bar_chart(df.set_index("选项"))
    st.table(df)
    st.write(f"总投票人数: {len(voters[current_round])}")
else:
    st.info("还没有人投票")

# 主持人控制
st.subheader("🎯 主持人控制")

if st.button("🔄 进入下一轮"):
    if current_votes and any(count > 0 for count in current_votes.values()):
        # 找到最低票选项
        valid_votes = {opt: count for opt, count in current_votes.items() if count > 0}
        if valid_votes:
            min_votes = min(valid_votes.values())
            eliminated = [opt for opt, count in valid_votes.items() if count == min_votes]

            st.write(f"淘汰选项：{eliminated}")

            # 更新活跃选项 - 对所有用户生效
            new_options = [opt for opt in active_options if opt not in eliminated]
            data["active_options"] = new_options
            data["current_round"] = current_round + 1

            st.success(f"已进入第 {current_round + 1} 轮！")
            st.rerun()
    else:
        st.warning("没有投票数据")

# 重置系统
st.subheader("⚙️ 系统管理")
if st.button("🔄 重置投票系统"):
    st.session_state.shared_voting_data = {
        "current_round": 1,
        "votes": {},
        "voters": {},
        "active_options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"]
    }
    st.success("系统已重置！")
    st.rerun()

# 自动刷新
st.write("页面会自动刷新...")
time.sleep(10)
st.rerun()