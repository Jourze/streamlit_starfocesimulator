import streamlit as st
import time
from simulator import StarForceSimulator

# 페이지 설정
st.set_page_config(page_title="메이플스토리 스타포스 시뮬레이터", page_icon="🌟", layout="wide")

# 세션 상태 초기화
if 'sim' not in st.session_state:
    st.session_state.sim = StarForceSimulator()
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'auto_running' not in st.session_state:
    st.session_state.auto_running = False

sim = st.session_state.sim

# ==========================================
# 사이드바 (설정 패널)
# ==========================================
with st.sidebar:
    st.header("⚙️ 설정 (Configuration)")
    
    level = st.selectbox("장비 레벨", [130, 140, 150, 160, 200, 250], index=3)
    target_star = st.number_input("목표 스타포스", min_value=1, max_value=30, value=22, step=1)
    
    st.subheader("강화 옵션")
    safeguard = st.checkbox("파괴 방지 (15~17성, 메소 200%)")
    spare_cost = st.number_input("스페어(복구) 가격 (메소)", min_value=0, value=0, step=100000000)
    
    st.subheader("할인 및 이벤트")
    
    shining_full = st.checkbox("🌟 샤이닝 스타포스 (비용 30%↓ + 5/10/15 100% 성공)")
    shining_half = st.checkbox("🌟 샤이닝 스타포스 (비용 30% 할인만)", disabled=shining_full)
    
    # 썬데이 30% 할인은 샤이닝 할인과 중복 적용 불가
    sunday30 = st.checkbox("썬데이 메이플 (비용 30% 할인)", disabled=(shining_full or shining_half))
    
    # 5/10/15 100% 성공은 샤이닝 전체 적용 시 이미 포함됨
    sunday100 = st.checkbox("5/10/15성 100% 성공", disabled=shining_full)
    sunday1plus1 = st.checkbox("10성 이하 1+1 강화")
    
    mvp_discount_str = st.selectbox("MVP 할인", ["없음", "MVP 실버 (3%)", "MVP 골드 (5%)", "MVP 다이아/레드 (10%)"])
    mvp_mapping = {"없음": 0.0, "MVP 실버 (3%)": 0.03, "MVP 골드 (5%)": 0.05, "MVP 다이아/레드 (10%)": 0.1}
    mvp_discount = mvp_mapping[mvp_discount_str]
    
    pc_discount = st.checkbox("PC방 할인 (5%)")

    # 시뮬레이터 옵션 업데이트
    sim.set_options(
        level=level,
        target_star=target_star,
        safeguard=safeguard,
        spare_cost=spare_cost,
        shining_full=shining_full,
        shining_half=shining_half,
        sunday30=sunday30,
        sunday100=sunday100,
        sunday1plus1=sunday1plus1,
        mvp_discount=mvp_discount,
        pc_discount=pc_discount
    )

# ==========================================
# 커스텀 CSS 주입
# ==========================================
st.markdown("""
<style>
.star-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    width: 270px;
    margin: 0 auto;
    gap: 2px;
}
.star {
    font-size: 20px;
    color: rgba(255, 255, 255, 0.1);
    width: 24px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-shadow: 0 0 2px rgba(0,0,0,0.5);
}
.star.filled {
    color: #fcd34d;
    text-shadow: 0 0 8px rgba(252, 211, 77, 0.8), 0 0 15px rgba(252, 211, 77, 0.4);
}
.star-gap {
    margin-right: 8px;
}
.current-star-text {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    color: #fcd34d;
    margin-top: 10px;
    text-shadow: 0 0 15px rgba(252, 211, 77, 0.4);
}
.log-box {
    height: 400px;
    overflow-y: auto;
    background: rgba(15, 23, 42, 0.6);
    padding: 15px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.log-box::-webkit-scrollbar {
    width: 8px;
}
.log-box::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}
.log-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.03);
    padding: 10px 15px;
    border-radius: 8px;
    border-left: 4px solid #334155;
    transition: transform 0.1s, background 0.1s;
}
.log-item:hover {
    background: rgba(255, 255, 255, 0.08);
}
.log-stars {
    font-weight: bold;
    color: #f8fafc;
    width: 100px;
}
.log-status {
    font-weight: 600;
    flex: 1;
    text-align: center;
    letter-spacing: 1px;
}
.log-success { color: #34d399; }
.log-maintain { color: #94a3b8; }
.log-destroy { color: #f87171; }
.log-cost {
    color: #cbd5e1;
    font-family: monospace;
    font-size: 0.95em;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 별(Star) 렌더링 UI
# ==========================================
def render_stars(current_star):
    stars_html = '<div class="star-container">'
    for i in range(30):
        classes = ['star']
        if i < current_star:
            classes.append('filled')
        if i % 10 == 4:
            classes.append('star-gap')
        
        stars_html += f'<div class="{" ".join(classes)}">★</div>'
    stars_html += '</div>'
    stars_html += f'<div class="current-star-text">{current_star}성</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==========================================
# 메인 화면
# ==========================================
st.title("STAR FORCE SIMULATOR")
st.markdown("최신(30성 확장, 하락 삭제) 확률 및 메소 공식 적용")

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("강화 진행")
    
    # 별 UI 렌더링 컨테이너
    star_placeholder = st.empty()
    with star_placeholder:
        render_stars(sim.current_star)
        
    st.markdown("---")
    
    # 확률 및 비용 정보
    prob = sim.get_probabilities(sim.current_star)
    cost = sim.get_cost(sim.current_star)
    
    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("성공", f"{prob['success']*100:.2f}%")
    pc2.metric("유지", f"{prob['maintain']*100:.2f}%")
    pc3.metric("파괴", f"{prob['destroy']*100:.2f}%")
    
    st.metric("1회 강화 비용", f"{cost:,} 메소")
    
    st.markdown("---")
    
    # 버튼 액션
    bc1, bc2, bc3 = st.columns([1, 1, 1])
    
    def do_enhance():
        res = sim.enhance_once()
        if res['result'] == 'max':
            return
        
        # 로그 추가
        result_text = res['result']
        if result_text == 'success':
            r_class, r_text, r_icon, border_col = 'log-success', '성공', '✨', '#34d399'
        elif result_text == 'success_1plus1':
            r_class, r_text, r_icon, border_col = 'log-success', '성공 (1+1)', '🌟', '#34d399'
        elif result_text == 'maintain':
            r_class, r_text, r_icon, border_col = 'log-maintain', '유지', '➖', '#94a3b8'
        elif result_text == 'destroy':
            r_class, r_text, r_icon, border_col = 'log-destroy', '파괴됨', '💥', '#f87171'
        
        log_html = f"<div class='log-item' style='border-left-color: {border_col};'><div class='log-stars'>{res['beforeStar']}성 ➔ {res['afterStar']}성</div> <div class='log-status {r_class}'>{r_icon} {r_text}</div> <div class='log-cost'>(-{res['cost']:,} 메소)</div></div>"
        st.session_state.logs.insert(0, log_html)
        
        # 최대 100개 로그 유지
        if len(st.session_state.logs) > 100:
            st.session_state.logs.pop()

    if bc1.button("🔨 1회 강화", use_container_width=True):
        st.session_state.auto_running = False
        do_enhance()

    auto_btn_text = "⏹️ 자동 강화 중지" if st.session_state.auto_running else "⚡ 목표까지 자동 강화"
    if bc2.button(auto_btn_text, use_container_width=True):
        if st.session_state.auto_running:
            st.session_state.auto_running = False
        else:
            if sim.current_star >= sim.target_star:
                st.warning("이미 목표 스타포스에 도달했습니다.")
            else:
                st.session_state.auto_running = True
                
    if bc3.button("🔄 초기화", type="primary", use_container_width=True):
        st.session_state.auto_running = False
        sim.reset()
        st.session_state.logs = []
        st.rerun()

    # 별 UI 다시 렌더링 (강화 버튼 누른 후 즉각 반영)
    with star_placeholder:
        render_stars(sim.current_star)

    if sim.current_star >= sim.target_star and sim.try_count > 0:
        exp_cost = sim.get_expected_values()['cost']
        actual_cost = sim.get_grand_total()
        diff = actual_cost - exp_cost
        
        st.markdown("<br>", unsafe_allow_html=True)
        if diff > 0:
            st.error(f"🎉 목표 달성! 기댓값 대비 **{diff:,.0f} 메소 손해** 보셨습니다... 😢")
        elif diff < 0:
            st.success(f"🎉 목표 달성! 기댓값 대비 **{abs(diff):,.0f} 메소 이득** 보셨습니다! 😆")
        else:
            st.info(f"🎉 목표 달성! 정확히 기댓값만큼 소모하셨습니다. 😐")

with col2:
    st.subheader("통계 및 로그")
    
    # 통계 메트릭
    st.metric("누적 소모 메소", f"{sim.total_meso:,}")
    mc1, mc2 = st.columns(2)
    mc1.metric("총 강화 시도", f"{sim.try_count:,} 회")
    mc2.metric("파괴 횟수", f"{sim.destroy_count:,} 회")
    
    st.metric("스페어 비용 합계", f"{sim.total_spare_cost:,}")
    st.metric("총 비용 (강화+스페어)", f"{sim.get_grand_total():,}")
    
    st.markdown("---")
    
    exp_vals = sim.get_expected_values()
    st.markdown(f"**🎯 목표({sim.target_star}성)까지 기댓값**")
    ec1, ec2 = st.columns(2)
    ec1.metric("기대 소모 비용", f"{int(exp_vals['cost']):,} 메소")
    ec2.metric("기대 파괴 횟수", f"{exp_vals['destroy']:.2f} 회")
    
    st.markdown("---")
    
    # 강화 로그 렌더링
    logs_html = "".join(st.session_state.logs)
    st.markdown(f'<div class="log-box">{logs_html}</div>', unsafe_allow_html=True)

# 자동 강화 로직 처리
if st.session_state.auto_running:
    if sim.current_star >= sim.target_star:
        st.session_state.auto_running = False
        st.success("목표 스타포스 달성!")
        st.rerun()
    else:
        do_enhance()
        time.sleep(0.05) # 약간의 딜레이
        st.rerun()
