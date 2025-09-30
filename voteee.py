import streamlit as st
import pandas as pd
import time
import json

# 使用 st.cache_data 创建真正共享的数据存储
@st.cache_data(ttl=3600, show_spinner=False)
def get_shared_voting_data():
    """这个函数返回的数据在所有用户间共享"""
    return {
        "current_round": 1,
        "rounds": {
            1: {
                "votes": {},
                "voters": [],
                "options": ["穿刺2次", "穿刺3次", "穿刺≥2次", "多次穿刺"],
                "last_updated": time.time()
            }
        }
    }

# 获取共享数据
shared_data = get_shared_voting_data()

# 在session_state中保存对共享数据的引用
if "data_initialized" not in st.session_state:
    st.session_state.data_initialized = True
    st.session_state.shared_data_ref = shared_data

st.title("🧠 多人实时德尔菲投票系统 - 跨设备版")

# 获取当前轮次数据
current_round = st.session_state.shared_data_ref["current_round"]

# 确保当前轮次存在
if current_round not in st.session_state.shared_data_ref["rounds"]:
    st.session_state.shared_data_ref["rounds"][current_round] = {
        "votes": {},
        "voters": [],
        "options": st.session_state.shared_data_ref["rounds"][current_round-1]["options"].copy(),
        "last_updated": time.time()
    }

round_data = st.session_state.shared_data_ref["rounds"][current_round]
votes = round_data["votes"]
voters = round_data["voters"]
options = round_data["options"]

# 显示实时状态
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("当前轮次", current_round)
with col2:
    st.metric("活跃选项", len(options))
with col3:
    st.metric("投票人数", len(voters))

# 用户投票界面
st.subheader(f"第 {current_round} 轮投票")

if options and len(options) > 0:
    choice = st.radio("请选择：", options)
    voter_id = st.text_input("你的姓名：")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🗳️ 提交投票", type="primary", use_container_width=True) and voter_id:
            if voter_id in voters:
                st.error("❌ 你已投过票！")
            else:
                # 更新共享数据
                if choice not in votes:
                    votes[choice] = 0
                votes[choice] += 1
                voters.append(voter_id)
                round_data["last_updated"] = time.time()  # 更新时间戳
                
                st.success(f"✅ 投票成功！选择了: {choice}")
                st.balloons()
                
                # 清除缓存，强制所有用户重新加载数据
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
    
    with col_btn2:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# 显示投票结果
st.subheader("📊 实时投票结果")

if voters:
    # 创建结果表格
    results = []
    total_votes = len(voters)
    
    for option in options:
        count = votes.get(option, 0)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "选项": option,
            "票数": count,
            "得票率": f"{percentage:.1f}%"
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values("票数", ascending=False)
    
    # 显示图表和表格
    tab1, tab2, tab3 = st.tabs(["📈 图表", "📋 表格", "👥 详情"])
    
    with tab1:
        chart_df = df[df["票数"] > 0]
        if not chart_df.empty:
            st.bar_chart(chart_df.set_index("选项")["票数"])
        else:
            st.info("暂无投票数据")
    
    with tab2:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab3:
        st.write(f"**总投票人数**: {len(voters)}")
        st.write("**已投票用户**:", ", ".join(voters) if voters else "暂无")
        
        # 显示每个选项的详细投票
        st.write("**详细分布**:")
        for option in options:
            count = votes.get(option, 0)
            st.write(f"- {option}: {count} 票")
else:
    st.info("👆 等待第一票...")

# 主持人控制
st.subheader("🎯 主持人控制")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 进入下一轮", type="secondary", use_container_width=True):
        if len(voters) > 0:
            # 找到有票的选项
            valid_options = [opt for opt in options if votes.get(opt, 0) > 0]
            
            if len(valid_options) >= 2:
                # 淘汰最低票选项
                vote_counts = [votes.get(opt, 0) for opt in valid_options]
                min_votes = min(vote_counts)
                eliminated = [opt for opt in valid_options if votes.get(opt, 0) == min_votes]
                
                # 更新选项
                new_options = [opt for opt in options if opt not in eliminated]
                
                # 进入下一轮
                next_round = current_round + 1
                st.session_state.shared_data_ref["current_round"] = next_round
                
                # 初始化下一轮
                st.session_state.shared_data_ref["rounds"][next_round] = {
                    "votes": {},
                    "voters": [],
                    "options": new_options,
                    "last_updated": time.time()
                }
                
                st.success(f"✅ 进入第 {next_round} 轮")
                st.warning(f"淘汰: {', '.join(eliminated)}")
                
                # 清除缓存并刷新
                st.cache_data.clear()
                time.sleep(2)
                st.rerun()
            else:
                st.error("有效选项不足")
        else:
            st.warning("还没有投票")

with col2:
    if st.button("🔄 重置系统", use_container_width=True):
        # 清除所有缓存数据
        st.cache_data.clear()
        st.session_state.clear()
        st.success("系统已重置！")
        time.sleep(2)
        st.rerun()

# 跨设备同步状态
st.sidebar.subheader("🌐 同步状态")
st.sidebar.write(f"最后更新: {time.strftime('%H:%M:%S')}")
st.sidebar.write(f"数据版本: {hash(str(shared_data))}")

# 调试信息
with st.sidebar.expander("🔧 调试信息"):
    st.write("当前数据:")
    st.json(round_data)
    
    st.write("所有轮次:")
    st.json(st.session_state.shared_data_ref["rounds"])

# 跨设备测试说明
st.sidebar.info("""
**跨设备测试:**
1. 设备A: 投票
2. 设备B: 点击刷新按钮
3. 应该看到相同数据
""")

# 自动刷新机制
refresh_time = st.sidebar.slider("自动刷新间隔(秒)", 5, 30, 10)
if st.sidebar.button("立即刷新"):
    st.cache_data.clear()
    st.rerun()

st.info(f"🔄 自动刷新中... ({refresh_time}秒)")
time.sleep(refresh_time)
st.cache_data.clear()
st.rerun()
