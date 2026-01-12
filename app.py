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

# --- 스타일 설정 ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: white !important; }
    .stButton button { width: 100%; padding: 2px !important; height: 32px !important; font-size: 13px !important; border-radius: 5px !important; }
    .total-highlight { background-color: #fff5f5; padding: 12px; border-radius: 8px; text-align: right; font-weight: bold; font-size: 1.2em; color: #e03131; border: 1px solid #ffc9c9; border-right: 6px solid #e03131; margin-bottom: 5px; }
    .summary-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center; }
    .vvip-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 5px solid #ffc107; margin-bottom: 8px; }
    .benefit-tag { background-color: #d1ecf1; color: #0c5460; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }
    table { width: 100%; border-collapse: collapse; margin-top: 5px; }
    th { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; padding: 8px !important; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data():
    try:
        df_a = pd.read_csv(URL_AUCTION)
        df_a.columns = ['경매일자', '판매자', '품목', '가격', '구매자', '낙찰시간']
        df_a['가격'] = pd.to_numeric(df_a['가격'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
        df_a['경매일자'] = pd.to_datetime(df_a['경매일자'], errors='coerce')
        df_a = df_a.dropna(subset=['경매일자']) 
        df_a['경매일자'] = df_a['경매일자'].dt.date
        df_m = pd.read_csv(URL_MEMBERS)
        member_cols = ['닉네임', '이름', '전화번호', '주소', '수수료면제여부', '전미수', '금액']
        df_m = df_m.iloc[:, :8] if len(df_m.columns) >= 8 else df_m
        df_m.columns = member_cols + (['마지막혜택일'] if len(df_m.columns) > 7 else [])
        if '마지막혜택일' in df_m.columns:
            df_m['마지막혜택일'] = pd.to_datetime(df_m['마지막혜택일'], errors='coerce').dt.date
        return df_a, df_m
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}"); return None, None

# 정산 체크 상태 관리용 세션
if 'done_keys' not in st.session_state:
    st.session_state.done_keys = set()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 로그인 로직 생략 (기존과 동일)
if not st.session_state['logged_in']:
    empty1, col_login, empty2 = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>🔐 보안 접속</h1>", unsafe_allow_html=True)
        input_pw = st.text_input("", type="password", placeholder="Password")
        if st.button("로그인", use_container_width=True):
            if input_pw == APP_PASSWORD: st.session_state['logged_in'] = True; st.rerun()
            else: st.error("비밀번호 불일치")
else:
    df, df_members = load_data()
    if df is not None:
        # --- 사이드바 및 공통 로직 ---
        st.sidebar.subheader("🔎 조회 설정")
        view_mode = st.sidebar.radio("모드 선택", ["일별 조회", "기간별 조회", "일별 요약"])
        available_dates = sorted(df['경매일자'].unique(), reverse=True)
        
        if view_mode == "일별 요약":
            selected_date = st.sidebar.selectbox("📅 요약 날짜 선택", available_dates) if available_dates else None
            filtered_df = df[df['경매일자'] == selected_date] if selected_date else pd.DataFrame()
            date_title = f"📊 {selected_date} 판매 요약 보고서"
            selected_person = "SUMMARY_MODE"
        else:
            if view_mode == "일별 조회":
                selected_date = st.sidebar.selectbox("📅 날짜 선택", available_dates) if available_dates else None
                filtered_df = df[df['경매일자'] == selected_date] if selected_date else pd.DataFrame()
                date_title = f"📅 경매일자: {selected_date}"
            else:
                c1, c2 = st.sidebar.columns(2)
                start_date = c1.date_input("시작일", datetime.now().date() - timedelta(days=7))
                end_date = c2.date_input("종료일", datetime.now().date())
                filtered_df = df[(df['경매일자'] >= start_date) & (df['경매일자'] <= end_date)]
                date_title = f"🗓️ 기간: {start_date} ~ {end_date}"
            participants = sorted([p for p in pd.concat([filtered_df['판매자'], filtered_df['구매자']]).dropna().unique() if str(p).strip() != ""])
            selected_person = st.sidebar.selectbox(f"👤 고객 선택 ({len(participants)}명)", ["선택하세요"] + participants)

        # --- 메인 요약 모드 ---
        if selected_person == "SUMMARY_MODE":
            st.title(date_title)
            if not filtered_df.empty:
                # 데이터 집계
                total_sales = filtered_df['가격'].sum()
                all_p = sorted(list(set(filtered_df['판매자'].unique()) | set(filtered_df['구매자'].unique())))
                pay_in, pay_out, total_buy_fees = [], [], 0
                for p in all_p:
                    s_amt = int(filtered_df[filtered_df['판매자'] == p]['가격'].sum())
                    s_net = s_amt - int(s_amt * SELL_FEE_RATE)
                    is_ex = not df_members[df_members['닉네임'] == p].empty and str(df_members[df_members['닉네임'] == p].iloc[0]['수수료면제여부']).strip() == "면제"
                    b_raw = int(filtered_df[filtered_df['구매자'] == p]['가격'].sum())
                    b_f = 0 if is_ex else int(b_raw * DEFAULT_BUY_FEE_RATE)
                    total_buy_fees += b_f
                    bal = s_net - (b_raw + b_f)
                    if bal > 0: pay_out.append({"고객명": p, "금액": bal})
                    elif bal < 0: pay_in.append({"고객명": p, "금액": abs(bal)})

                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div class='summary-box'><h3>💰 총 매출</h3><h2>{total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='summary-box'><h3>📉 예상 수익</h3><h2>{int(total_sales * SELL_FEE_RATE) + total_buy_fees:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='summary-box'><h3>📦 낙찰 건수</h3><h2>{len(filtered_df)}건</h2></div>", unsafe_allow_html=True)
                st.write("---")

                # --- 딜레이 해결을 위한 프래그먼트 영역 ---
                @st.fragment
                def show_settlement_tables():
                    col_l, col_r = st.columns(2)
                    
                    with col_l:
                        st.subheader("📩 입금 받을 돈 (구매자)")
                        # 실시간 합계 계산
                        current_in_sum = sum(i['금액'] for i in pay_in if f"in_{selected_date}_{i['고객명']}" not in st.session_state.done_keys)
                        st.markdown(f"<div class='total-highlight'>남은 미입금 합계: {current_in_sum:,.0f}원</div>", unsafe_allow_html=True)
                        
                        st.markdown("<table><tr><th width='25%'>상태</th><th width='40%'>닉네임</th><th width='35%'>금액</th></tr></table>", unsafe_allow_html=True)
                        for i in sorted(pay_in, key=lambda x: x['고객명']):
                            key = f"in_{selected_date}_{i['고객명']}"
                            is_done = key in st.session_state.done_keys
                            t_style = "text-decoration:line-through; color:#adb5bd;" if is_done else "font-weight:bold; color:black;"
                            
                            c = st.columns([1, 1.5, 1.5])
                            if c[0].button("취소" if is_done else "완료", key=f"btn_{key}"):
                                if is_done: st.session_state.done_keys.remove(key)
                                else: st.session_state.done_keys.add(key)
                                st.rerun() # 프래그먼트 내부에서만 rerun
                            c[1].markdown(f"<div style='text-align:center; padding:6px; font-size:15px; {t_style}'>{i['고객명']}</div>", unsafe_allow_html=True)
                            c[2].markdown(f"<div style='text-align:center; padding:6px; font-size:15px; {t_style}'>{i['금액']:,.0f}원</div>", unsafe_allow_html=True)

                    with col_r:
                        st.subheader("💵 정산 드릴 돈 (판매자)")
                        current_out_sum = sum(i['금액'] for i in pay_out if f"out_{selected_date}_{i['고객명']}" not in st.session_state.done_keys)
                        st.markdown(f"<div class='total-highlight'>남은 미정산 합계: {current_out_sum:,.0f}원</div>", unsafe_allow_html=True)
                        
                        st.markdown("<table><tr><th width='25%'>상태</th><th width='40%'>닉네임</th><th width='35%'>금액</th></tr></table>", unsafe_allow_html=True)
                        for i in sorted(pay_out, key=lambda x: x['고객명']):
                            key = f"out_{selected_date}_{i['고객명']}"
                            is_done = key in st.session_state.done_keys
                            t_style = "text-decoration:line-through; color:#adb5bd;" if is_done else "font-weight:bold; color:black;"
                            
                            c = st.columns([1, 1.5, 1.5])
                            if c[0].button("취소" if is_done else "완료", key=f"btn_{key}"):
                                if is_done: st.session_state.done_keys.remove(key)
                                else: st.session_state.done_keys.add(key)
                                st.rerun()
                            c[1].markdown(f"<div style='text-align:center; padding:6px; font-size:15px; {t_style}'>{i['고객명']}</div>", unsafe_allow_html=True)
                            c[2].markdown(f"<div style='text-align:center; padding:6px; font-size:15px; {t_style}'>{i['금액']:,.0f}원</div>", unsafe_allow_html=True)

                show_settlement_tables() # 프래그먼트 실행

                st.write("---")
                # 하단 랭킹 (여기는 정산과 상관없이 고정)
                rank_l, rank_r = st.columns(2)
                with rank_l:
                    st.subheader("🏆 오늘자 구매왕")
                    rb = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(5).reset_index()
                    rb.columns = ['고객명', '구매금액']; rb.index += 1; rb['구매금액'] = rb['구매금액'].map('{:,.0f}원'.format); st.table(rb)
                with rank_r:
                    st.subheader("🔝 최고가 낙찰품")
                    rt = filtered_df.sort_values(by='가격', ascending=False).head(5)[['품목', '가격', '구매자']].reset_index(drop=True)
                    rt.index += 1; rt['가격'] = rt['가격'].map('{:,.0f}원'.format); st.table(rt)
            else: st.info("데이터가 없습니다.")
        
        # --- 고객 상세 조회 모드 ---
        elif selected_person != "선택하세요":
            member_row = df_members[df_members['닉네임'] == selected_person]
            is_ex = not member_row.empty and str(member_row.iloc[0]['수수료면제여부']).strip() == "면제"
            st.title(f"📜 {selected_person} 경매내역서")
            # 상세 내용 생략 (기존과 동일)
            st.info("고객 상세 내역 출력 중...")
            # (중략 - 기존 상세 코드 유지)
            
        else:
            st.info("👈 왼쪽에서 날짜와 고객을 선택해 주세요.")
