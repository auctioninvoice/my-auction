import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 🛠️ 사장님 전용 설정
# ==========================================
SHEET_ID = "1hbrT_QQWwCrxsG0Jg81xAJH9_gLzc2ORtmava8tqqUw"
# 데이터 깨짐 방지를 위해 인코딩 설정을 강화한 주소
URL_AUCTION = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_MEMBERS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=773051258" 

SELL_FEE_RATE = 0.14
DEFAULT_BUY_FEE_RATE = 0.05
APP_PASSWORD = "4989" 
# ==========================================

st.set_page_config(page_title="골동품사나이들 관리자", layout="wide")

# --- 스타일 설정 (라이트모드 고정 및 인쇄 설정) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: white !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: black !important; font-family: 'Malgun Gothic', sans-serif; }
    
    .stTable { width: 100% !important; border-collapse: collapse; }
    .stTable th { background-color: #f0f2f6 !important; color: black !important; border: 1px solid #ddd !important; text-align: center !important; }
    .stTable td { background-color: white !important; color: black !important; border: 1px solid #ddd !important; text-align: center !important; }
    
    @media print {
        [data-testid="stSidebar"], header, button, .stDownloadButton, .print-hide { display: none !important; }
        .main { margin: 0 !important; padding: 0 !important; }
        .stTable { font-size: 10pt !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=5) # 데이터 갱신을 위해 시간을 줄였습니다.
def load_data():
    try:
        # 한글 깨짐 방지를 위해 encoding='utf-8' 명시
        df_a = pd.read_csv(URL_AUCTION, encoding='utf-8')
        df_a.columns = ['경매일자', '판매자', '품목', '가격', '구매자', '낙찰시간']
        df_a['가격'] = pd.to_numeric(df_a['가격'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
        df_a['경매일자'] = pd.to_datetime(df_a['경매일자']).dt.date
        
        df_m = pd.read_csv(URL_MEMBERS, encoding='utf-8')
        df_m.columns = ['닉네임', '이름', '전화번호', '주소', '수수료면제여부', '전미수', '금액']
        return df_a, df_m
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None, None

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 로그인 ---
if not st.session_state['logged_in']:
    empty1, col_login, empty2 = st.columns([1, 2, 1])
    with col_login:
        st.write("")
        st.markdown("<h1 style='text-align: center;'>🔐 보안 접속</h1>", unsafe_allow_html=True)
        input_pw = st.text_input("", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        if st.button("로그인", use_container_width=True):
            if input_pw == APP_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("비밀번호가 틀렸습니다.")
else:
    df, df_members = load_data()
    if df is not None:
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.sidebar.write("---")
        view_mode = st.sidebar.radio("🔎 조회 모드", ["일별 조회", "기간별 조회"])
        
        if view_mode == "일별 조회":
            available_dates = sorted(df['경매일자'].unique(), reverse=True)
            selected_date = st.sidebar.selectbox("📅 날짜 선택", available_dates)
            f_df = df[df['경매일자'] == selected_date]
            title_text = f"📅 {selected_date} 정산 내역"
        else:
            col_d1, col_d2 = st.sidebar.columns(2)
            with col_d1: start_d = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
            with col_d2: end_d = st.date_input("종료일", datetime.now().date())
            f_df = df[(df['경매일자'] >= start_d) & (df['경매일자'] <= end_d)]
            title_text = f"🗓️ {start_d} ~ {end_d} 기간 정산"

        participants = sorted([p for p in pd.concat([f_df['판매자'], f_df['구매자']]).dropna().unique() if str(p).strip() != ""])
        name = st.sidebar.selectbox(f"👤 고객 선택 ({len(participants)}명)", participants)

        if name:
            m_info = df_members[df_members['닉네임'] == name]
            is_exempt = not m_info.empty and str(m_info.iloc[0]['수수료면제여부']).strip() == "면제"
            
            st.title(title_text)
            st.markdown(f"### 👤 {name} 님 정보")
            c1, c2, c3 = st.columns([1, 1.2, 2.5])
            c1.markdown(f"**🏷️ 성함:** {m_info.iloc[0]['이름'] if not m_info.empty else '미등록'}")
            c2.markdown(f"**📞 연락처:** {m_info.iloc[0]['전화번호'] if not m_info.empty else '미등록'}")
            c3.markdown(f"**🏠 주소:** {m_info.iloc[0]['주소'] if not m_info.empty else '미등록'}")
            if is_exempt: st.success("✨ 수수료 면제 대상 회원입니다")
            st.write("---")

            # 계산
            s_df = f_df[f_df['판매자'] == name].copy()
            b_df = f_df[f_df['구매자'] == name].copy()
            
            s_sum = int(s_df['가격'].sum()); s_fee = int(s_sum * SELL_FEE_RATE); s_net = s_sum - s_fee
            b_sum = int(b_df['가격'].sum()); b_fee = 0 if is_exempt else int(b_sum * DEFAULT_BUY_FEE_RATE); b_net = b_sum + b_fee
            bal = s_net - b_net

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("📤 판매 정산금", f"{s_net:,.0f}원")
            mc1.caption(f"판매합계:{s_sum:,.0f} / 수수료14%:-{s_fee:,.0f}")
            mc2.metric("📥 구매 청구금", f"{b_net:,.0f}원")
            mc2.caption(f"낙찰합계:{b_sum:,.0f} / 수수료5%:+{b_fee:,.0f}")
            label = "💵 입금해드릴 돈" if bal > 0 else "📩 입금받을 돈"
            mc3.metric(label, f"{abs(bal):,.0f}원")

            st.write("---")
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.markdown("#### [판매 내역]")
                if not s_df.empty:
                    cols = ['품목', '가격', '구매자'] if view_mode == "일별 조회" else ['경매일자', '품목', '가격']
                    disp_s = s_df[cols].reset_index(drop=True)
                    disp_s.index += 1; disp_s['가격'] = disp_s['가격'].map('{:,.0f}'.format)
                    st.table(disp_s)
                else: st.write("내역 없음")
            with col_r:
                st.markdown("#### [구매 내역]")
                if not b_df.empty:
                    cols = ['품목', '가격', '판매자'] if view_mode == "일별 조회" else ['경매일자', '품목', '가격']
                    disp_b = b_df[cols].reset_index(drop=True)
                    disp_b.index += 1; disp_b['가격'] = disp_b['가격'].map('{:,.0f}'.format)
                    st.table(disp_b)
                else: st.write("내역 없음")

            # --- [인쇄 버튼: 가장 확실한 방법] ---
            st.write("---")
            st.markdown("""
                <a href="javascript:window.print()" class="print-hide" style="
                    text-decoration: none; display: block; width: 100%; background-color: #4CAF50; 
                    color: white; padding: 15px; text-align: center; border-radius: 5px; 
                    font-size: 18px; font-weight: bold;
                ">📄 이 화면 그대로 인쇄하기 (A4)</a>
                <p class="print-hide" style="text-align:center; color:gray; font-size:12px; margin-top:5px;">
                    * 버튼 클릭이 안 되면 'Ctrl + P'를 누르거나 브라우저 메뉴에서 '인쇄'를 선택하세요.
                </p>
            """, unsafe_allow_html=True)
