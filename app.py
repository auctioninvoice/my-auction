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

# --- [스타일 설정] ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: white !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: black !important; }
    
    .stTable { width: 100% !important; table-layout: auto !important; border-collapse: collapse; }
    .stTable th { text-align: center !important; background-color: #f0f2f6 !important; color: black !important; border: 1px solid #ddd !important; }
    .stTable td { background-color: white !important; color: black !important; border: 1px solid #ddd !important; text-align: center !important; }
    
    /* 품목 열 정렬 */
    .stTable td:nth-child(2), .stTable td:nth-child(3) { text-align: left !important; }
    
    [data-testid="stMetricValue"] { font-size: clamp(22px, 5vw, 32px) !important; color: black !important; }

    /* 인쇄 전용 CSS */
    @media print {
        [data-testid="stSidebar"], .stButton, header, .stDownloadButton, footer, .print-ignore { display: none !important; }
        .main { margin: 0 !important; padding: 0 !important; }
        .stTable { font-size: 10pt !important; }
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
        st.error(f"데이터 로드 실패: {e}"); return None, None

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    empty1, col_login, empty2 = st.columns([1, 2, 1])
    with col_login:
        st.write(""); st.markdown("<h1 style='text-align: center;'>🔐 보안 접속</h1>", unsafe_allow_html=True)
        input_pw = st.text_input("", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        if st.button("로그인", use_container_width=True):
            if input_pw == APP_PASSWORD: st.session_state['logged_in'] = True; st.rerun()
            else: st.error("비밀번호가 틀렸습니다.")
else:
    df, df_members = load_data()
    if df is not None:
        if st.sidebar.button("로그아웃"): st.session_state['logged_in'] = False; st.rerun()

        st.sidebar.write("---")
        view_mode = st.sidebar.radio("🔎 조회 모드 선택", ["일별 조회", "기간별 조회"])
        
        if view_mode == "일별 조회":
            available_dates = sorted(df['경매일자'].unique(), reverse=True)
            selected_date = st.sidebar.selectbox("📅 날짜 선택", available_dates)
            filtered_df = df[df['경매일자'] == selected_date]
            display_title = f"📅 {selected_date} 경매 내역서"
        else:
            col_d1, col_d2 = st.sidebar.columns(2)
            with col_d1: start_d = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
            with col_d2: end_d = st.date_input("종료일", datetime.now().date())
            filtered_df = df[(df['경매일자'] >= start_d) & (df['경매일자'] <= end_d)]
            display_title = f"🗓️ {start_d} ~ {end_d} 기간 정산서"

        participants = sorted([p for p in pd.concat([filtered_df['판매자'], filtered_df['구매자']]).dropna().unique() if str(p).strip() != ""])
        selected_person = st.sidebar.selectbox(f"👤 고객 선택 ({len(participants)}명)", participants)

        if selected_person:
            m = df_members[df_members['닉네임'] == selected_person]
            is_exempt = not m.empty and str(m.iloc[0]['수수료면제여부']).strip() == "면제"
            
            st.title(display_title)
            st.markdown(f"### 👤 {selected_person} 님 정보")
            c1, c2, c3 = st.columns([1, 1.2, 2.5])
            c1.markdown(f"**🏷️ 성함**\n{m.iloc[0]['이름'] if not m.empty else '미등록'}")
            c2.markdown(f"**📞 연락처**\n{m.iloc[0]['전화번호'] if not m.empty else '미등록'}")
            c3.markdown(f"**🏠 주소**\n{m.iloc[0]['주소'] if not m.empty else '미등록'}")
            if is_exempt: st.success("✨ 수수료 면제 대상 회원입니다")
            st.write("---")

            # 정산 계산
            s_data = filtered_df[filtered_df['판매자'] == selected_person].copy()
            b_data = filtered_df[filtered_df['구매자'] == selected_person].copy()
            s_sum = int(s_data['가격'].sum()); s_f = int(s_sum * SELL_FEE_RATE); s_n = s_sum - s_f
            b_rate = 0 if is_exempt else DEFAULT_BUY_FEE_RATE
            b_sum = int(b_data['가격'].sum()); b_f = int(b_sum * b_rate); b_n = b_sum + b_f
            bal = s_n - b_n

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("📤 판매 정산금", f"{s_n:,.0f}원")
            mc1.caption(f"판매액:{s_total:,.0f} / 수수료14%:-{s_fee:,.0f}") if 's_fee' in locals() else mc1.caption(f"판매액:{s_sum:,.0f} / 수수료14%:-{s_f:,.0f}")
            mc2.metric("📥 구매 청구금", f"{b_n:,.0f}원")
            mc2.caption(f"낙찰가:{b_sum:,.0f} / 수수료5%:+{b_f:,.0f}")
            label = "💵 입금해드릴 돈" if bal > 0 else "📩 입금받을 돈"
            mc3.metric(label, f"{abs(bal):,.0f}원")

            st.write("---")
            col_l, col_r = st.columns(2)
            
            if view_mode == "일별 조회":
                s_cols, b_cols = ['품목', '가격', '구매자'], ['품목', '가격', '판매자']
            else:
                s_cols, b_cols = ['경매일자', '품목', '가격'], ['경매일자', '품목', '가격']

            with col_l:
                st.markdown("#### [판매 내역]")
                if not s_data.empty:
                    disp_s = s_data[s_cols].reset_index(drop=True)
                    disp_s.index += 1; disp_s['가격'] = disp_s['가격'].map('{:,.0f}'.format)
                    st.table(disp_s)
                else: st.write("내역 없음")
            with col_r:
                st.markdown("#### [구매 내역]")
                if not b_data.empty:
                    disp_b = b_data[b_cols].reset_index(drop=True)
                    disp_b.index += 1; disp_b['가격'] = disp_b['가격'].map('{:,.0f}'.format)
                    st.table(disp_b)
                else: st.write("내역 없음")

            st.write("---")
            
            # --- [인쇄 해결책: 버튼을 2개로 제공] ---
            pc1, pc2 = st.columns(2)
            with pc1:
                # 1. 자바스크립트를 이용한 직접 인쇄 (버튼 디자인 보강)
                st.markdown("""
                    <button onclick="parent.window.print();" style="
                        width: 100%; background-color: #4CAF50; color: white; padding: 15px; 
                        border: none; border-radius: 5px; cursor: pointer; font-size: 18px; font-weight: bold;
                    ">📄 화면 바로 인쇄하기</button>
                    <p style="font-size: 12px; color: gray; text-align: center;">* 반응이 없으면 아래 '장부 다운로드'를 이용하세요.</p>
                """, unsafe_allow_html=True)
            
            with pc2:
                # 2. 엑셀로 저장하기 (백업용)
                csv = filtered_df[((filtered_df['판매자'] == selected_person) | (filtered_df['구매자'] == selected_person))].to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 장부 파일로 저장 (Excel)",
                    data=csv,
                    file_name=f"{selected_person}_{display_title}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# 브라우저별 인쇄 팁 안내 (인쇄 버튼 클릭 후 설명)
st.sidebar.info("💡 **인쇄 팁**\n인쇄 버튼이 작동하지 않으면 브라우저 상단의 '점 세 개' 메뉴에서 '인쇄'를 직접 누르셔도 깔끔하게 나옵니다.")
