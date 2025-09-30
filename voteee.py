import streamlit as st
import pandas as pd
import time
import hashlib
import json
import os

def save_data():
    """保存数据到临时文件（在Streamlit Cloud上可能有限制）"""
    try:
        with open('/tmp/voting_data.json', 'w') as f:
            json.dump(st.session_state.shared_data, f)
    except:
        pass  # 忽略错误，依赖session_state

def load_data():
    """从文件加载数据"""
    try:
        with open('/tmp/voting_data.json', 'r') as f:
            return json.load(f)
    except:
        return None
# 更健壮的共享数据初始化
def init_shared_data():
    if "shared_data" not in st.session_state:
        st.session_state.shared_data = {
            "current_round": 1,
            # 使用嵌套字典确保数据共享
            "rounds": {
                1: {
                    "votes": {},
                    "voters": set(),
                    "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
                    "active": True
                }
            }
        }

init_shared_data()

# 获取当前轮次数据
current_round = st.session_state.shared_data["current_round"]
if current_round not in st.session_state.shared_data["rounds"]:
    # 初始化新轮次
    prev_round = current_round - 1
    prev_data = st.session_state.shared_data["rounds"][prev_round]
    # 继承上一轮的活跃选项（淘汰最低票后）
    st.session_state.shared_data["rounds"][current_round] = {
        "votes": {},
        "voters": set(),
        "options": prev_data["options"].copy(),  # 会在淘汰逻辑中更新
        "active": True
    }

round_data = st.session_state.shared_data["rounds"][current_round]
votes = round_data["votes"]
voters = round_data["voters"]
options = round_data["options"]

st.title("🧠 多人实时德尔菲投票系统")

# 显示实时状态
st.sidebar.subheader("📊 系统状态")
st.sidebar.write(f"当前轮次: **{current_round}**")
st.sidebar.write(f"活跃选项: **{len(options)}** 个")
st.sidebar.write(f"本轮投票: **{len(voters)}** 人")

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票")

if options and len(options) > 0:
    choice = st.radio("请选择：", options, key=f"choice_{current_round}")
    voter_id = st.text_input("你的姓名：", key=f"voter_{current_round}")
    
    if st.button("🗳️ 提交投票", type="primary") and voter_id:
        if voter_id in voters:
            st.error("❌ 你已投过票！")
        else:
            # 更新投票数据 - 确保使用正确的方式
            if choice not in votes:
                votes[choice] = 0
            votes[choice] += 1
            voters.add(voter_id)
            st.success(f"✅ 投票成功！")
            st.balloons()
            
            # 立即显示更新后的结果
            st.rerun()

# 实时结果显示 - 确保正确读取数据
st.subheader("📈 实时投票结果")

# 重新获取最新数据（避免缓存问题）
current_votes = st.session_state.shared_data["rounds"][current_round]["votes"]
current_voters = st.session_state.shared_data["rounds"][current_round]["voters"]

if current_votes:
    # 创建结果表格
    vote_list = []
    for option in options:  # 显示所有选项，包括0票的
        count = current_votes.get(option, 0)
        vote_list.append({"选项": option, "票数": count, "投票率": f"{(count/len(current_voters))*100:.1f}%" if current_voters else "0%"})
    
    df = pd.DataFrame(vote_list)
    df = df.sort_values("票数", ascending=False)
    
    # 显示结果
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 只显示有票数的图表
        chart_data = df[df["票数"] > 0]
        if not chart_data.empty:
            st.bar_chart(chart_data.set_index("选项")["票数"])
        else:
            st.info("📊 图表等待数据...")
    
    with col2:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 投票详情
    with st.expander("👥 查看投票详情"):
        if current_voters:
            st.write(f"**总投票人数**: {len(current_voters)}")
            st.write("**已投票用户**:", list(current_voters))
        else:
            st.write("暂无投票")
else:
    st.info("👆 等待第一票...")

# 主持人控制
st.subheader("🎯 主持人控制")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 进入下一轮", type="secondary", use_container_width=True):
        if current_votes and len(current_voters) > 0:
            # 找到最低票选项
            valid_votes = {opt: current_votes.get(opt, 0) for opt in options if current_votes.get(opt, 0) > 0}
            
            if len(valid_votes) >= 2:
                min_votes = min(valid_votes.values())
                eliminated = [opt for opt, count in valid_votes.items() if count == min_votes]
                
                # 更新选项
                new_options = [opt for opt in options if opt not in eliminated]
                
                # 更新共享数据
                st.session_state.shared_data["current_round"] += 1
                next_round = st.session_state.shared_data["current_round"]
                
                # 初始化下一轮
                st.session_state.shared_data["rounds"][next_round] = {
                    "votes": {},
                    "voters": set(),
                    "options": new_options,
                    "active": True
                }
                
                st.success(f"✅ 进入第 {next_round} 轮")
                st.info(f"淘汰: {', '.join(eliminated)}")
                time.sleep(2)
                st.rerun()
            else:
                st.error("选项不足，无法淘汰")
        else:
            st.warning("需要投票数据")

with col2:
    if st.button("📊 刷新结果", use_container_width=True):
        st.rerun()

with col3:
    if st.button("🔄 重置系统", use_container_width=True):
        st.session_state.shared_data = {
            "current_round": 1,
            "rounds": {
                1: {
                    "votes": {},
                    "voters": set(),
                    "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
                    "active": True
                }
            }
        }
        st.success("系统已重置！")
        time.sleep(1)
        st.rerun()

# 调试信息
with st.sidebar.expander("🔧 调试信息"):
    st.write("当前轮次数据:", st.session_state.shared_data["rounds"][current_round])
    st.write("Session ID:", hash(str(st.session_state.shared_data)))

# 自动刷新
st.info("🔄 页面自动刷新中...")
time.sleep(10)
st.rerun()


