import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 🛠️ 사장님 전용 설정
# ==========================================
SHEET_ID = "1hbrT_QQWwCrxsG0Jg81xAJH9_gLzc2ORtmava8tqqUw"
URL_AUCTION = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_MEMBERS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=773051258" 

SELL_FEE_RATE = 0.14
DEFAULT_BUY_FEE_RATE = 0.05
APP_PASSWORD = "4989" 
# ==========================================

st.set_page_config(page_title="골동품사나이들 관리자", layout="wide")

# --- [라이트모드 강제 고정 및 인쇄 최적화 스타일] ---
st.markdown("""
    <style>
    /* 화면 표시 설정 */
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: white !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    h1, h2, h3, p, span, div, label, .stMarkdown {
        color: black !important;
    }
    
    .stTable { width: 100% !important; table-layout: auto !important; border-collapse: collapse; }
    .stTable th { 
        text-align: center !important; 
        background-color: #f0f2f6 !important; 
        color: black !important; 
    }
    .stTable td { 
        background-color: white !important; 
        color: black !important; 
        border-bottom: 1px solid #ddd !important;
    }
    
    [data-testid="stMetricValue"] { font-size: clamp(22px, 5vw, 32px) !important; color: black !important; }

    /* --- 인쇄 시 적용되는 설정 --- */
    @media print {
        [data-testid="stSidebar"], 
        [data-testid="stHeader"], 
        .stButton, 
        button,
        header { 
            display: none !important; 
        }
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .stTable { 
            font-size: 10pt !important; 
        }
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data():
    try:
        df_auction = pd.read_csv(URL_AUCTION)
        df_auction.columns = ['경매일자', '판매자', '품목', '가격', '구매자', '낙찰시간']
        df_auction['가격'] = pd.to_numeric(df_auction['가격'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
        df_auction['경매일자'] = pd.to_datetime(df_auction['경매일자']).dt.date
        df_auction = df_auction.drop(columns=['낙찰시간'])
        df_members = pd.read_csv(URL_MEMBERS)
        df_members.columns = ['닉네임', '이름', '전화번호', '주소', '수수료면제여부', '전미수', '금액']
        return df_auction, df_members
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None, None

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    empty1, col_login, empty2 = st.columns([1, 2, 1])
    with col_login:
        st.write("")
        st.markdown("<h1 style='text-align: center;'>🔐 보안 접속</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>비밀번호를 입력해주세요</p>", unsafe_allow_html=True)
        input_pw = st.text_input("", type="password", placeholder="Password", label_visibility="collapsed")
        login_btn = st.button("로그인", use_container_width=True)
        if login_btn:
            if input_pw == APP_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        st.markdown("<div style='text-align: center; font-size: 80px;'>🔓</div>", unsafe_allow_html=True)

else:
    df, df_members = load_data()
    if df is not None:
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.title("📜 골동품사나이들 경매내역서 조회")
        st.write("---")

        view_mode = st.sidebar.radio("🔎 조회 모드 선택", ["일별 조회", "기간별 조회"])
        
        if view_mode == "일별 조회":
            available_dates = sorted(df['경매일자'].unique(), reverse=True)
            if not available_dates:
                st.info("시트에 경매 데이터가 없습니다.")
                filtered_df = pd.DataFrame()
                date_title = ""
            else:
                selected_date = st.sidebar.selectbox("📅 1. 경매 날짜 선택", available_dates)
                filtered_df = df[df['경매일자'] == selected_date]
                date_title = f"📅 경매일자: {selected_date}"
        else:
            col_d1, col_d2 = st.sidebar.columns(2)
            with col_d1:
                start_date = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
            with col_d2:
                end_date = st.date_input("종료일", datetime.now().date())
            filtered_df = df[(df['경매일자'] >= start_date) & (df['경매일자'] <= end_date)]
            date_title = f"🗓️ 조회 기간: {start_date} ~ {end_date}"

        if not filtered_df.empty:
            participants = pd.concat([filtered_df['판매자'], filtered_df['구매자']]).dropna().unique()
            participants = sorted([p for p in participants if str(p).strip() != ""])
            selected_person = st.sidebar.selectbox(f"👤 2. 고객 선택 ({len(participants)}명)", participants)

            if selected_person:
                member_row = df_members[df_members['닉네임'] == selected_person]
                is_exempt = False
                real_name, phone, address = "정보 미등록", "정보 미등록", "정보 미등록"
                if not member_row.empty:
                    if str(member_row.iloc[0]['수수료면제여부']).strip() == "면제":
                        is_exempt = True
                    real_name = member_row.iloc[0]['이름']
                    phone = member_row.iloc[0]['전화번호']
                    address = member_row.iloc[0]['주소']

                # --- [수정된 부분] 상세정보 위에 날짜 추가 ---
                st.markdown(f"### {date_title}")
                st.markdown(f"## 👤 {selected_person} 님의 상세 정보")
                
                info_col1, info_col2, info_col3 = st.columns([1, 1.2, 2.5])
                with info_col1: st.markdown(f"**🏷️ 성함**\n{real_name}")
                with info_col2: st.markdown(f"**📞 연락처**\n{phone}")
                with info_col3: st.markdown(f"**🏠 주소**\n{address}")
                if is_exempt: st.success("✨ 수수료 면제 대상 회원입니다")
                st.write("---")

                sell_data = filtered_df[filtered_df['판매자'] == selected_person].copy()
                buy_data = filtered_df[filtered_df['구매자'] == selected_person].copy()
                
                s_total = int(sell_data['가격'].sum())
                s_fee = int(s_total * SELL_FEE_RATE)
                s_net = s_total - s_fee
                
                current_buy_rate = 0 if is_exempt else DEFAULT_BUY_FEE_RATE
                b_total_raw = int(buy_data['가격'].sum())
                b_fee = int(b_total_raw * current_buy_rate)
                b_total_final = b_total_raw + b_fee
                final_balance = s_net - b_total_final

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("📤 판매 정산금", f"{s_net:,.0f}원")
                    st.caption(f"판매금액:{s_total:,.0f} / 수수료14%:-{s_fee:,.0f}")
                with c2:
                    st.metric("📥 구매 청구금", f"{b_total_final:,.0f}원")
                    st.caption(f"구매금액:{b_total_raw:,.0f} / 수수료5%:+{b_fee:,.0f}")
                with c3:
                    label = "💵 입금해드릴 돈" if final_balance > 0 else "📩 입금받을 돈"
                    st.metric(label, f"{abs(final_balance):,.0f}원")

                st.write("---")
                col1, col2 = st.columns(2)
                
                if view_mode == "일별 조회":
                    s_cols, b_cols = ['품목', '가격', '구매자'], ['품목', '가격', '판매자']
                else:
                    s_cols, b_cols = ['경매일자', '품목', '가격'], ['경매일자', '품목', '가격']

                with col1:
                    st.markdown("### [판매 내역]")
                    if not sell_data.empty:
                        sell_disp = sell_data[s_cols].reset_index(drop=True)
                        sell_disp.index += 1
                        sell_disp['가격'] = sell_disp['가격'].map('{:,.0f}'.format)
                        st.table(sell_disp)
                    else: st.write("판매 내역 없음")
                with col2:
                    st.markdown("### [구매 내역]")
                    if not buy_data.empty:
                        buy_disp = buy_data[b_cols].reset_index(drop=True)
                        buy_disp.index += 1
                        buy_disp['가격'] = buy_disp['가격'].map('{:,.0f}'.format)
                        st.table(buy_disp)
                    else: st.write("구매 내역 없음")
