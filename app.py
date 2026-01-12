import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# ==========================================
# ⚙️ 설정 및 상수 정의
# ==========================================
SHEET_ID = "1hbrT_QQWwCrxsG0Jg81xAJH9_gLzc2ORtmava8tqqUw"
URL_AUCTION = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_MEMBERS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=773051258" 

SELL_FEE_RATE = 0.14
DEFAULT_BUY_FEE_RATE = 0.05
APP_PASSWORD = "4989" 

# CSS 스타일 정의 (가독성을 위해 분리)
CUSTOM_CSS = """
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: white !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: black !important; font-family: 'Pretendard', sans-serif; }
    .stTable { width: 100% !important; }
    .stTable th { text-align: center !important; background-color: #f1f3f5 !important; color: #333 !important; font-weight: bold; }
    .stTable td { text-align: center !important; border-bottom: 1px solid #e9ecef !important; }
    
    /* 카드 스타일 */
    .vvip-box { background-color: #fff3cd; padding: 12px; border-radius: 8px; border: 1px solid #ffeeba; margin-bottom: 8px; border-left: 5px solid #ffc107; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .benefit-tag { background-color: #d1ecf1; color: #0c5460; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8em; margin-left: 5px; }
    .summary-box { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .summary-box h3 { font-size: 1rem; color: #495057; margin-bottom: 10px; }
    .summary-box h2 { font-size: 1.8rem; font-weight: 800; color: #212529; margin: 0; }
    
    .total-highlight { background-color: #e9ecef; padding: 15px; border-radius: 8px; text-align: right; font-weight: bold; font-size: 1.2em; color: #212529; margin-bottom: 15px; border-right: 6px solid #495057; }
    
    /* 프로필 카드 */
    .profile-card { background-color: white; padding: 25px; border-radius: 16px; border: 1px solid #e9ecef; border-left: 6px solid #3498db; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 25px; }
    .bank-box { background-color: #fffde7; padding: 15px; border: 2px dashed #fbc02d; border-radius: 10px; margin: 15px 0; font-size: 1.2em; color: #f57f17 !important; font-weight: bold; text-align: center; }
    
    @media print {
        [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, button, header { display: none !important; }
        .block-container { max-width: 100% !important; padding: 0 !important; }
    }
    </style>
"""

st.set_page_config(page_title="골동품사나이들 관리자", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# 🛠️ 유틸리티 함수
# ==========================================
def get_ko_date(dt):
    """날짜를 'YYYY-MM-DD (요일)' 형식으로 변환"""
    if pd.isna(dt): return ""
    days_ko = ['월', '화', '수', '목', '금', '토', '일']
    try:
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        return f"{dt.strftime('%Y-%m-%d')} ({days_ko[dt.weekday()]})"
    except:
        return str(dt)

def clean_currency(val):
    """문자열 가격을 정수로 변환"""
    try:
        return int(str(val).replace(',', '').split('.')[0])
    except:
        return 0

def parse_time_smart(t_str):
    """구글 시트의 다양한 시간 형식을 처리하여 24시간제 정수(14~26)로 변환"""
    if pd.isna(t_str): return None
    s = str(t_str).strip()
    
    # 1. 시:분:초 형식 추출
    match = re.search(r'(\d{1,2}):(\d{2})', s)
    if not match: return None
    
    hour = int(match.group(1))
    
    # 2. 오후/PM 체크 및 시간 보정
    is_pm = '오후' in s or 'PM' in s.upper()
    is_am = '오전' in s or 'AM' in s.upper()
    
    if is_pm and hour < 12:
        hour += 12
    if is_am and hour == 12: # 오전 12시는 0시
        hour = 0
        
    # 3. 비즈니스 로직 적용 (새벽 0~2시는 24~26시로 취급하여 당일 경매로 간주)
    if 0 <= hour <= 6: # 새벽 6시까지는 전날의 연장으로 봄
        hour += 24
        
    return hour if hour >= 10 else None # 오전 10시 이전 데이터는 무시 (오류 방지)

# ==========================================
# 📥 데이터 로드 및 전처리
# ==========================================
@st.cache_data(ttl=15)
def load_data():
    try:
        # 경매 내역 로드
        df_a = pd.read_csv(URL_AUCTION)
        df_a.columns = ['경매일자', '판매자', '품목', '가격', '구매자', '낙찰시간']
        
        # 데이터 정제
        df_a = df_a.dropna(subset=['경매일자'])
        df_a['가격'] = df_a['가격'].apply(clean_currency)
        df_a['경매일자_dt'] = pd.to_datetime(df_a['경매일자'], errors='coerce')
        df_a = df_a.dropna(subset=['경매일자_dt']) # 날짜 오류 행 제거
        df_a['경매일자'] = df_a['경매일자_dt'].dt.date
        df_a['연월'] = df_a['경매일자_dt'].dt.strftime('%Y-%m')
        df_a['연도'] = df_a['경매일자_dt'].dt.year

        # 회원 명부 로드
        df_m = pd.read_csv(URL_MEMBERS)
        cols = ['닉네임', '이름', '전화번호', '주소', '수수료면제여부', '전미수', '금액', '마지막혜택일', '계좌번호']
        
        # 컬럼 수 맞추기
        current_cols = df_m.columns.tolist()
        if len(current_cols) < len(cols):
            # 부족한 컬럼 채우기
            for _ in range(len(cols) - len(current_cols)):
                current_cols.append(f"col_{len(current_cols)}")
        
        df_m = df_m.iloc[:, :9] # 앞 9개 컬럼만 사용
        df_m.columns = cols[:df_m.shape[1]]
        
        # 결측치 처리
        if '계좌번호' not in df_m.columns: df_m['계좌번호'] = "정보없음"
        df_m['계좌번호'] = df_m['계좌번호'].fillna("정보없음")
        df_m['마지막혜택일'] = pd.to_datetime(df_m['마지막혜택일'], errors='coerce').dt.date
        
        return df_a, df_m
    except Exception as e:
        st.error(f"❌ 데이터 로드 중 치명적 오류: {e}")
        return None, None

def calculate_fees(price, is_exempt=False):
    """수수료 계산 (판매수수료, 구매수수료)"""
    sell_fee = int(price * SELL_FEE_RATE)
    buy_fee = 0 if is_exempt else int(price * DEFAULT_BUY_FEE_RATE)
    return sell_fee, buy_fee

# ==========================================
# 🔒 로그인 처리
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔐 골동품 관리자</h1>", unsafe_allow_html=True)
        input_pw = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인", use_container_width=True):
            if input_pw == APP_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop() # 로그인 전에는 아래 코드 실행 중지

# ==========================================
# 🖥️ 메인 애플리케이션
# ==========================================
df, df_members = load_data()

if df is not None:
    # --- 사이드바 ---
    with st.sidebar:
        st.header("🔎 조회 설정")
        view_mode = st.radio("모드 선택", 
            ["일별 조회", "기간별 조회", "일별 요약(차트)", "월별 요약", "연간 요약", "👤 회원 정보 조회"],
            index=2 # 기본값: 일별 요약
        )
        
        st.write("---")
        
        # 필터링 로직
        filtered_df = pd.DataFrame()
        date_title = ""
        selected_person = "None"
        
        available_dates = sorted(df['경매일자'].unique(), reverse=True)
        
        if view_mode == "일별 조회":
            s_date = st.selectbox("📅 날짜 선택", available_dates)
            filtered_df = df[df['경매일자'] == s_date]
            date_title = f"{get_ko_date(s_date)} 경매 내역"
            # 참여자 리스트 생성
            p_list = sorted(set(filtered_df['판매자'].dropna()) | set(filtered_df['구매자'].dropna()))
            selected_person = st.selectbox("👤 상세 조회할 고객", ["선택하세요"] + p_list)
            
        elif view_mode == "기간별 조회":
            c1, c2 = st.columns(2)
            s_date = c1.date_input("시작일", datetime.now().date() - timedelta(days=7))
            e_date = c2.date_input("종료일", datetime.now().date())
            filtered_df = df[(df['경매일자'] >= s_date) & (df['경매일자'] <= e_date)]
            date_title = f"{get_ko_date(s_date)} ~ {get_ko_date(e_date)}"
            p_list = sorted(set(filtered_df['판매자'].dropna()) | set(filtered_df['구매자'].dropna()))
            selected_person = st.selectbox("👤 상세 조회할 고객", ["선택하세요"] + p_list)

        elif view_mode == "일별 요약(차트)":
            s_date = st.selectbox("📅 요약 날짜 선택", available_dates)
            filtered_df = df[df['경매일자'] == s_date]
            date_title = f"{get_ko_date(s_date)} 판매 요약 보고서"
            
        elif view_mode == "월별 요약":
            months = sorted(df['연월'].unique(), reverse=True)
            s_month = st.selectbox("📅 월 선택", months)
            filtered_df = df[df['연월'] == s_month]
            date_title = f"{s_month} 월간 실적"
            
        elif view_mode == "연간 요약":
            years = sorted(df['연도'].unique(), reverse=True)
            s_year = st.selectbox("📅 연도 선택", years)
            filtered_df = df[df['연도'] == s_year]
            date_title = f"{s_year}년 연간 결산"
            
        elif view_mode == "👤 회원 정보 조회":
            search_nick = st.selectbox("회원 검색", sorted(df_members['닉네임'].unique()))
        
        # 배송비 이벤트 명단 (사이드바 하단)
        st.write("---")
        st.subheader("💎 배송비 이벤트 (VIP)")
        
        # VIP 계산 로직 (캐싱 불가능하므로 간결하게 작성)
        vip_list = []
        # 성능을 위해 구매 기록이 있는 사람만 필터링
        active_buyers = df['구매자'].unique()
        for nick in active_buyers:
            m_row = df_members[df_members['닉네임'] == nick]
            if m_row.empty: continue
            
            last_dt = m_row.iloc[0]['마지막혜택일']
            user_logs = df[df['구매자'] == nick]
            
            # 마지막 혜택일 이후 데이터만 필터링
            if pd.notna(last_dt):
                user_logs = user_logs[user_logs['경매일자'] > last_dt]
            
            total = user_logs['가격'].sum()
            if total >= 3000000:
                vip_list.append((nick, total))
        
        vip_list.sort(key=lambda x: x[1], reverse=True)
        
        if vip_list:
            for nick, amt in vip_list:
                grade = "30%" if amt < 5000000 else "50%" if amt < 10000000 else "전액"
                st.markdown(f"""
                <div class="vvip-box">
                    <strong>{nick}</strong> <span class="benefit-tag">{grade} 지원</span><br>
                    <span style="font-size:0.9em; color:#666;">누적: {amt:,.0f}원</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("현재 대상자가 없습니다.")
            
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- 메인 화면 렌더링 ---
    
    # 1. 회원 정보 통합 조회
    if view_mode == "👤 회원 정보 조회":
        st.title(f"👤 {search_nick} 회원 상세 정보")
        m_info = df_members[df_members['닉네임'] == search_nick].iloc[0]
        
        # 개인 실적 계산
        p_buy = df[df['구매자'] == search_nick]
        p_sell = df[df['판매자'] == search_nick]
        
        raw_buy = p_buy['가격'].sum()
        raw_sell = p_sell['가격'].sum()
        is_exempt = str(m_info['수수료면제여부']) == '면제'
        
        buy_fee = 0 if is_exempt else int(raw_buy * DEFAULT_BUY_FEE_RATE)
        sell_fee = int(raw_sell * SELL_FEE_RATE)
        
        # 등급 산정
        if raw_buy >= 10000000: grade, g_col = "🔥 전액지원 대상", "#e74c3c"
        elif raw_buy >= 5000000: grade, g_col = "💎 50% 지원 대상", "#3498db"
        elif raw_buy >= 3000000: grade, g_col = "🥇 30% 지원 대상", "#f1c40f"
        else: grade, g_col = "일반 회원", "#95a5a6"
        
        # 프로필 카드 출력
        st.markdown(f"""
        <div class="profile-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style='margin:0;'>{search_nick}</h2>
                <span style='background-color:{g_col}; color:white; padding:5px 15px; border-radius:20px; font-weight:bold;'>{grade}</span>
            </div>
            <div class="bank-box">🏦 계좌: {m_info['계좌번호']}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px;">
                <div><strong>🏷️ 성함:</strong> {m_info['이름']}</div>
                <div><strong>📞 연락처:</strong> {m_info['전화번호']}</div>
                <div><strong>✨ 수수료:</strong> {'✅ 면제' if is_exempt else '기본(5%)'}</div>
            </div>
            <div style="margin-top:10px;"><strong>🏠 주소:</strong> {m_info['주소']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 요약 통계
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='summary-box'><h3>📦 총 낙찰 건수</h3><h2>{len(p_buy):,}건</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"""
            <div class='summary-box'>
                <h3>💰 총 구매(청구)금액</h3>
                <h2>{(raw_buy + buy_fee):,.0f}원</h2>
                <small>낙찰 {raw_buy:,.0f} + 수수료 {buy_fee:,.0f}</small>
            </div>""", unsafe_allow_html=True)
        c3.markdown(f"""
            <div class='summary-box'>
                <h3>📤 총 판매(정산)금액</h3>
                <h2>{(raw_sell - sell_fee):,.0f}원</h2>
                <small>낙찰 {raw_sell:,.0f} - 수수료 {sell_fee:,.0f}</small>
            </div>""", unsafe_allow_html=True)
            
        # 탭 상세 내역
        st.write("---")
        t1, t2 = st.tabs(["🛍️ 구매 내역 상세", "📦 판매 내역 상세"])
        
        with t1:
            if not p_buy.empty:
                disp = p_buy[['경매일자', '품목', '가격', '판매자']].sort_values('경매일자', ascending=False)
                disp['경매일자'] = disp['경매일자'].apply(get_ko_date)
                disp['가격'] = disp['가격'].apply(lambda x: f"{x:,.0f}원")
                st.table(disp.reset_index(drop=True))
            else: st.info("구매 내역이 없습니다.")
            
        with t2:
            if not p_sell.empty:
                disp = p_sell[['경매일자', '품목', '가격', '구매자']].sort_values('경매일자', ascending=False)
                disp['경매일자'] = disp['경매일자'].apply(get_ko_date)
                disp['가격'] = disp['가격'].apply(lambda x: f"{x:,.0f}원")
                st.table(disp.reset_index(drop=True))

    # 2. 일별/기간별 요약 (차트 포함)
    elif view_mode == "일별 요약(차트)":
        st.title(date_title)
        
        if not filtered_df.empty:
            # 시간대 분석 데이터 생성
            chart_df = filtered_df.copy()
            chart_df['정렬시간'] = chart_df['낙찰시간'].apply(parse_time_smart)
            
            # 14시 ~ 26시(익일 2시) 범위 생성
            full_hours = pd.DataFrame({'정렬시간': range(14, 27)})
            
            agg = chart_df.groupby('정렬시간').agg(
                매출=('가격', 'sum'),
                건수=('가격', 'count')
            ).reset_index()
            
            final_agg = pd.merge(full_hours, agg, on='정렬시간', how='left').fillna(0)
            
            # 라벨 생성 (14, 15... 24(0시), 25(1시), 26(2시))
            def make_label(h):
                h = int(h)
                if h < 24: return f"{h}시"
                elif h == 24: return "자정"
                else: return f"익일 {h-24}시"
                
            final_agg['시간표시'] = final_agg['정렬시간'].apply(make_label)
            
            # Plotly 차트
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(
                x=final_agg['시간표시'], y=final_agg['매출'], name="매출액",
                marker_color='#3498db', opacity=0.7,
                hovertemplate="%{x}<br>매출: %{y:,.0f}원"
            ), secondary_y=False)
            
            fig.add_trace(go.Scatter(
                x=final_agg['시간표시'], y=final_agg['건수'], name="낙찰건수",
                mode='lines+markers+text', line=dict(color='#e74c3c', width=3),
                text=final_agg['건수'].apply(lambda x: f"{int(x)}건" if x > 0 else ""),
                textposition="top center"
            ), secondary_y=True)
            
            fig.update_layout(height=500, title="🕒 시간대별 매출 흐름 (14:00 ~ 02:00)", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
            # 정산 요약
            st.write("---")
            total_sales = filtered_df['가격'].sum()
            total_count = len(filtered_df)
            
            # 예상 수수료 및 정산 계산
            # 모든 참여자(판매자+구매자)에 대해 정산 잔액 계산
            all_participants = set(filtered_df['판매자']) | set(filtered_df['구매자'])
            pay_in = []  # 받을 돈 (구매 > 판매)
            pay_out = [] # 줄 돈 (판매 > 구매)
            total_profit = 0
            
            for p in all_participants:
                # 해당 날짜 해당 사람의 거래 내역
                s_amt = filtered_df[filtered_df['판매자'] == p]['가격'].sum()
                b_amt = filtered_df[filtered_df['구매자'] == p]['가격'].sum()
                
                # 회원 정보 확인 (수수료 면제 여부)
                mem_info = df_members[df_members['닉네임'] == p]
                is_ex = False
                if not mem_info.empty:
                    is_ex = str(mem_info.iloc[0]['수수료면제여부']) == '면제'
                
                s_fee, _ = calculate_fees(s_amt, is_ex)
                _, b_fee = calculate_fees(b_amt, is_ex)
                
                total_profit += (s_fee + b_fee)
                
                # 정산 잔액 (판매금 - 수수료) - (구매금 + 수수료)
                balance = (s_amt - s_fee) - (b_amt + b_fee)
                
                if balance > 0: pay_out.append({'name': p, 'amt': balance})
                elif balance < 0: pay_in.append({'name': p, 'amt': abs(balance)})
                
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='summary-box'><h3>💰 당일 총 매출</h3><h2>{total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='summary-box'><h3>📉 예상 수익(수수료)</h3><h2>{total_profit:,.0f}원</h2></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='summary-box'><h3>📦 총 낙찰 건수</h3><h2>{total_count:,}건</h2></div>", unsafe_allow_html=True)

            # 입출금 리스트
            st.write("---")
            col_in, col_out = st.columns(2)
            
            with col_in:
                st.subheader("📩 입금 받아야 할 돈 (구매자)")
                st.info("체크박스를 선택하여 입금 확인 처리를 하세요 (임시)")
                total_in_rem = 0
                pay_in_sorted = sorted(pay_in, key=lambda x: x['amt'], reverse=True)
                for item in pay_in_sorted:
                    col_chk, col_txt, col_val = st.columns([1, 4, 3])
                    is_checked = col_chk.checkbox("", key=f"in_{item['name']}")
                    col_txt.write(f"**{item['name']}**")
                    col_val.write(f"{item['amt']:,.0f}원")
                    if not is_checked: total_in_rem += item['amt']
                st.markdown(f"<div class='total-highlight'>미수금 합계: {total_in_rem:,.0f}원</div>", unsafe_allow_html=True)
                
            with col_out:
                st.subheader("💵 정산 해줘야 할 돈 (판매자)")
                st.warning("송금 후 체크박스를 선택하세요")
                total_out_rem = 0
                pay_out_sorted = sorted(pay_out, key=lambda x: x['amt'], reverse=True)
                for item in pay_out_sorted:
                    col_chk, col_txt, col_val = st.columns([1, 4, 3])
                    is_checked = col_chk.checkbox("", key=f"out_{item['name']}")
                    col_txt.write(f"**{item['name']}**")
                    col_val.write(f"{item['amt']:,.0f}원")
                    if not is_checked: total_out_rem += item['amt']
                st.markdown(f"<div class='total-highlight'>미지급 합계: {total_out_rem:,.0f}원</div>", unsafe_allow_html=True)

        else:
            st.info("해당 날짜에 데이터가 없습니다.")

    # 3. 상세 내역 조회 (일별/기간별 상세)
    elif selected_person != "None" and selected_person != "선택하세요":
        st.title("📜 경매내역서 (상세)")
        st.markdown(f"### 🗓️ {date_title}")
        
        # 회원 정보 불러오기
        mem_row = df_members[df_members['닉네임'] == selected_person]
        is_exempt = False
        
        st.markdown(f"## 👤 {selected_person}")
        if not mem_row.empty:
            info = mem_row.iloc[0]
            is_exempt = str(info['수수료면제여부']) == '면제'
            st.info(f"연락처: {info['전화번호']} | 주소: {info['주소']} | 계좌: {info['계좌번호']}")
        else:
            st.warning("회원 명부에 정보가 없는 비회원입니다.")
            
        # 데이터 필터링
        my_sell = filtered_df[filtered_df['판매자'] == selected_person].copy()
        my_buy = filtered_df[filtered_df['구매자'] == selected_person].copy()
        
        # 금액 계산
        s_sum = my_sell['가격'].sum()
        b_sum = my_buy['가격'].sum()
        s_fee, _ = calculate_fees(s_sum, is_exempt)
        _, b_fee = calculate_fees(b_sum, is_exempt)
        
        s_net = s_sum - s_fee
        b_total = b_sum + b_fee
        final_bal = s_net - b_total
        
        # 카드형 요약
        c1, c2, c3 = st.columns(3)
        c1.metric("📤 판매 정산금", f"{s_net:,.0f}원", f"수수료 -{s_fee:,.0f}원")
        c2.metric("📥 구매 청구금", f"{b_total:,.0f}원", f"수수료 +{b_fee:,.0f}원")
        c3.metric(
            "💵 최종 입금해드릴 돈" if final_bal > 0 else "📩 최종 입금받을 돈", 
            f"{abs(final_bal):,.0f}원",
            delta_color="normal"
        )
        
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("판매 내역")
            if not my_sell.empty:
                disp = my_sell[['경매일자', '품목', '가격', '구매자']].sort_values('경매일자', ascending=False)
                disp['가격'] = disp['가격'].apply(lambda x: f"{x:,.0f}원")
                st.table(disp.reset_index(drop=True))
            else: st.caption("내역 없음")
            
        with col2:
            st.subheader("구매 내역")
            if not my_buy.empty:
                disp = my_buy[['경매일자', '품목', '가격', '판매자']].sort_values('경매일자', ascending=False)
                disp['가격'] = disp['가격'].apply(lambda x: f"{x:,.0f}원")
                st.table(disp.reset_index(drop=True))
            else: st.caption("내역 없음")

    # 4. 월별/연간 요약
    elif view_mode in ["월별 요약", "연간 요약"]:
        st.title(date_title)
        if not filtered_df.empty:
            total = filtered_df['가격'].sum()
            st.markdown(f"<div class='summary-box'><h2>총 매출: {total:,.0f}원</h2></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🏆 구매 랭킹 TOP 10")
                top_b = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(10)
                st.dataframe(top_b, use_container_width=True)
            with c2:
                st.subheader("💰 판매 랭킹 TOP 10")
                top_s = filtered_df.groupby('판매자')['가격'].sum().sort_values(ascending=False).head(10)
                st.dataframe(top_s, use_container_width=True)
                
            st.subheader("📈 매출 추세")
            if view_mode == "월별 요약":
                date_agg = filtered_df.groupby('경매일자')['가격'].sum()
                st.line_chart(date_agg)
            else:
                filtered_df['월'] = filtered_df['경매일자_dt'].dt.month
                month_agg = filtered_df.groupby('월')['가격'].sum()
                st.bar_chart(month_agg)
        else:
            st.info("데이터가 없습니다.")
            
    else:
        st.info("👈 왼쪽 사이드바에서 조회 조건을 선택해주세요.")
