import streamlit as st
import pandas as pd

# ==========================================
# 🛠️ 사장님 전용 설정
# ==========================================
SHEET_ID = "1hbrT_QQWwCrxsG0Jg81xAJH9_gLzc2ORtmava8tqqUw"
URL_AUCTION = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_MEMBERS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=773051258" 

SELL_FEE_RATE = 0.14
DEFAULT_BUY_FEE_RATE = 0.05
# ==========================================

st.set_page_config(page_title="골동품사나이들 경매내역서 관리", layout="wide")

# --- [추가] 폰트 크기 및 순번 너비 조절 CSS ---
st.markdown("""
    
    <style>
    /* 1. 전체 기본 폰트 설정 */
    html, body, [class*="css"] {
        font-size: 18px !important; 
    }

    /* 2. 표 레이아웃 설정 */
    .stTable {
        width: 100% !important;
        table-layout: auto !important;
    }

    /* 3. 표 헤더(품목, 가격, 구매자/판매자) 가운데 정렬 */
    .stTable th {
        text-align: center !important;
        background-color: #f0f2f6; /* 헤더 배경색 살짝 넣어 구분감 부여 */
    }

    /* 4. 열별 너비 및 정렬 세부 설정 */
    
    /* [1열: 순번] 가운데 정렬 */
    .stTable td:nth-child(1) {
        width: 45px !important;
        text-align: center !important;
    }

    /* [2열: 품목] 왼쪽 정렬 (품목은 왼쪽에서 시작하는 게 읽기 편함) */
    .stTable td:nth-child(2) {
        width: auto !important;
        min-width: 150px !important;
        text-align: left !important;
    }

    /* [3열: 가격] 가운데 정렬 + 검정색 + 줄바꿈 방지 */
    .stTable td:nth-child(3) {
        width: 110px !important; 
        text-align: center !important; /* 모든 행 가운데 정렬 */
        white-space: nowrap !important;
        color: black !important;      /* 폰트색 검정 */
        font-weight: bold;
        font-size: clamp(14px, 2.8vw, 18px) !important; /* 자동 크기 조절 */
    }

    /* [4열: 구매자/판매자] 가운데 정렬 */
    .stTable td:nth-child(4) {
        width: 90px !important;
        text-align: center !important;
        white-space: nowrap;
    }

    /* 5. 표 내부 여백 조절 */
    .stTable td, .stTable th {
        padding: 8px 4px !important;
    }
    
    /* 6. 메트릭(상단 카드) 글자 크기 */
    [data-testid="stMetricValue"] {
        font-size: clamp(22px, 5vw, 32px) !important;
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

df, df_members = load_data()

if df is not None:
    st.title("📜 골동품사나이들 경매내역서 조회")
    st.write("---")

    available_dates = sorted(df['경매일자'].unique(), reverse=True)
    if not available_dates:
        st.info("시트에 경매 데이터가 없습니다.")
    else:
        selected_date = st.sidebar.selectbox("📅 1. 경매 날짜 선택", available_dates)
        date_df = df[df['경매일자'] == selected_date]

        participants = pd.concat([date_df['판매자'], date_df['구매자']]).dropna().unique()
        participants = sorted([p for p in participants if str(p).strip() != ""])
        selected_person = st.sidebar.selectbox(f"👤 2. 고객 선택 ({len(participants)}명)", participants)

        if selected_person:
            # --- 회원정보 매칭 ---
            member_row = df_members[df_members['닉네임'] == selected_person]
            is_exempt = False
            real_name, phone, address = "정보 미등록", "정보 미등록", "정보 미등록"

            if not member_row.empty:
                if str(member_row.iloc[0]['수수료면제여부']).strip() == "면제":
                    is_exempt = True
                real_name = member_row.iloc[0]['이름']
                phone = member_row.iloc[0]['전화번호']
                address = member_row.iloc[0]['주소']

            # --- 고객 정보 섹션 ---
            st.markdown(f"## 👤 {selected_person} 님의 상세 정보")
            info_col1, info_col2, info_col3 = st.columns([1, 1.2, 2.5])
            with info_col1:
                st.markdown(f"**🏷️ 성함**\n{real_name}")
            with info_col2:
                st.markdown(f"**📞 연락처**\n{phone}")
            with info_col3:
                st.markdown(f"**🏠 주소**\n{address}")
            
            if is_exempt:
                st.success("✨ 수수료 면제 대상 회원입니다")
            
            st.write("---")

            # --- 정산 계산 ---
            sell_data = date_df[date_df['판매자'] == selected_person].copy()
            buy_data = date_df[date_df['구매자'] == selected_person].copy()

            s_total = int(sell_data['가격'].sum())
            s_fee = int(s_total * SELL_FEE_RATE)
            s_net = s_total - s_fee

            current_buy_rate = 0 if is_exempt else DEFAULT_BUY_FEE_RATE
            b_total_raw = int(buy_data['가격'].sum())
            b_fee = int(b_total_raw * current_buy_rate)
            b_total_final = b_total_raw + b_fee
            final_balance = s_net - b_total_final

            # --- 요약 카드 ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("📤 판매 정산금", f"{s_net:,.0f}원")
                st.caption(f"판매액:{s_total:,.0f} / 수수료14%:-{s_fee:,.0f}")
            with c2:
                st.metric("📥 구매 청구금", f"{b_total_final:,.0f}원")
                st.caption(f"낙찰가:{b_total_raw:,.0f} / 수수료5%:+{b_fee:,.0f}")
            with c3:
                label = "💵 입금해드릴 돈" if final_balance > 0 else "📩 입금받을 돈"
                st.metric(label, f"{abs(final_balance):,.0f}원")

            st.write("---")
            
            # --- 상세 내역 (순번 칸 너비 확보) ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### [판매 내역]")
                if not sell_data.empty:
                    sell_disp = sell_data[['품목', '가격', '구매자']].reset_index(drop=True)
                    sell_disp.index += 1
                    sell_disp['가격'] = sell_disp['가격'].map('{:,.0f}'.format)
                    st.table(sell_disp)
                else:
                    st.write("판매 내역 없음")

            with col2:
                st.markdown("### [구매 내역]")
                if not buy_data.empty:
                    buy_disp = buy_data[['품목', '가격', '판매자']].reset_index(drop=True)
                    buy_disp.index += 1
                    buy_disp['가격'] = buy_disp['가격'].map('{:,.0f}'.format)
                    st.table(buy_disp)
                else:
                    st.write("구매 내역 없음")