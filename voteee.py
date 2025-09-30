import streamlit as st
import pandas as pd
import time
import hashlib

# 修复初始化函数
def init_shared_data():
    if "shared_data" not in st.session_state:
        st.session_state.shared_data = {
            "current_round": 1,
            "rounds": {
                1: {
                    "votes": {},
                    "voters": [],
                    "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],  # 修复：移除重复项
                    "active": True
                }
            }
        }

init_shared_data()

# 获取当前数据
current_round = st.session_state.shared_data["current_round"]

# 确保当前轮次存在
if current_round not in st.session_state.shared_data["rounds"]:
    # 从上一轮继承选项（淘汰后）
    prev_round = current_round - 1
    if prev_round in st.session_state.shared_data["rounds"]:
        prev_options = st.session_state.shared_data["rounds"][prev_round]["options"]
        st.session_state.shared_data["rounds"][current_round] = {
            "votes": {},
            "voters": [],
            "options": prev_options.copy(),
            "active": True
        }
    else:
        # 回退到第一轮
        st.session_state.shared_data["rounds"][current_round] = {
            "votes": {},
            "voters": [],
            "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
            "active": True
        }

round_data = st.session_state.shared_data["rounds"][current_round]
votes = round_data["votes"]
voters = round_data["voters"]
options = round_data["options"]

st.title("🧠 多人实时德尔菲投票系统")

# 显示系统状态
st.sidebar.subheader("📊 系统状态")
st.sidebar.write(f"**当前轮次**: {current_round}")
st.sidebar.write(f"**活跃选项**: {len(options)} 个")
st.sidebar.write(f"**本轮投票**: {len(voters)} 人")

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票")

if options and len(options) > 0:
    choice = st.radio("请选择：", options, key=f"choice_{current_round}")
    voter_id = st.text_input("你的姓名：", key=f"voter_{current_round}")
    
    if st.button("🗳️ 提交投票", type="primary") and voter_id:
        if voter_id in voters:
            st.error("❌ 你已投过票！")
        else:
            # 更新投票数据
            if choice not in votes:
                votes[choice] = 0
            votes[choice] += 1
            voters.append(voter_id)  # 使用列表而不是set
            
            st.success(f"✅ 投票成功！选择了: {choice}")
            st.balloons()
            
            # 强制刷新显示最新结果
            st.rerun()

# 实时结果显示 - 修复显示问题
st.subheader("📈 实时投票结果")

# 重新获取最新数据
current_votes = st.session_state.shared_data["rounds"][current_round]["votes"]
current_voters = st.session_state.shared_data["rounds"][current_round]["voters"]

if current_votes or len(current_voters) > 0:
    # 创建结果表格 - 修复票数显示
    vote_list = []
    total_votes = len(current_voters)
    
    for option in options:
        count = current_votes.get(option, 0)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        vote_list.append({
            "选项": option, 
            "票数": count,  # 修复：显示实际票数，不是百分比
            "投票率": f"{percentage:.1f}%"
        })
    
    df = pd.DataFrame(vote_list)
    df = df.sort_values("票数", ascending=False)
    
    # 显示结果
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 显示所有选项的图表
        st.bar_chart(df.set_index("选项")["票数"])
    
    with col2:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 显示投票详情
    with st.expander("👥 查看投票详情"):
        st.write(f"**总投票人数**: {len(current_voters)}")
        if current_voters:
            st.write("**已投票用户**:", ", ".join(current_voters))
        else:
            st.write("暂无投票")
        
        st.write("**详细票数分布**:")
        for option in options:
            count = current_votes.get(option, 0)
            st.write(f"- {option}: {count} 票")
else:
    st.info("👆 等待第一票...")

# 主持人控制
st.subheader("🎯 主持人控制")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 进入下一轮", type="secondary", use_container_width=True):
        if len(current_voters) > 0:
            # 找到有效的投票选项（票数>0）
            valid_options = []
            for opt in options:
                if current_votes.get(opt, 0) > 0:
                    valid_options.append(opt)
            
            if len(valid_options) >= 2:
                # 找到最低票选项
                min_votes = min([current_votes.get(opt, 0) for opt in valid_options])
                eliminated = [opt for opt in valid_options if current_votes.get(opt, 0) == min_votes]
                
                # 更新选项（淘汰最低票）
                new_options = [opt for opt in options if opt not in eliminated]
                
                # 进入下一轮
                next_round = current_round + 1
                st.session_state.shared_data["current_round"] = next_round
                
                # 初始化下一轮数据
                st.session_state.shared_data["rounds"][next_round] = {
                    "votes": {},
                    "voters": [],
                    "options": new_options,
                    "active": True
                }
                
                st.success(f"✅ 已进入第 {next_round} 轮")
                st.warning(f"淘汰的选项: {', '.join(eliminated)}")
                
                # 等待后刷新
                time.sleep(3)
                st.rerun()
            else:
                st.error("🚫 有效选项不足，无法淘汰")
        else:
            st.warning("⚠️ 还没有人投票")

with col2:
    if st.button("📊 强制刷新", use_container_width=True):
        st.rerun()

# 系统管理
st.subheader("⚙️ 系统管理")
if st.button("🔄 重置整个系统"):
    st.session_state.shared_data = {
        "current_round": 1,
        "rounds": {
            1: {
                "votes": {},
                "voters": [],
                "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
                "active": True
            }
        }
    }
    st.success("✅ 系统已重置！")
    time.sleep(2)
    st.rerun()

# 调试信息
with st.sidebar.expander("🔧 调试信息"):
    st.json(st.session_state.shared_data["rounds"][current_round])

# 跨设备同步测试
with st.sidebar.expander("🌐 同步测试"):
    st.write("请在两台设备测试：")
    st.write("1. 设备A投票")
    st.write("2. 设备B点击'强制刷新'")
    st.write("3. 检查设备B是否看到设备A的投票")

# 自动刷新
st.info("🔄 页面每15秒自动刷新...")
time.sleep(15)
st.rerun()


