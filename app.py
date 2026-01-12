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

# --- 스타일 설정 (표 테두리 및 버튼 디자인) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: white !important; }
    .stButton button { width: 100%; padding: 2px !important; height: 30px !important; font-size: 12px !important; }
    .total-highlight { background-color: #f8f9fa; padding: 15px; border-radius: 10px; text-align: right; font-weight: bold; font-size: 1.3em; color: #d32f2f; margin-bottom: 10px; border: 1px solid #dee2e6; border-right: 8px solid #d32f2f; }
    .summary-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 10px; }
    .vvip-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 8px; border-left: 5px solid #ffc107; }
    .benefit-tag { background-color: #d1ecf1; color: #0c5460; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }
    /* 표 스타일 강제 적용 */
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #f1f3f5 !important; color: black !important; border: 1px solid #dee2e6 !important; text-align: center !important; padding: 10px !important; }
    td { border: 1px solid #dee2e6 !important; padding: 8px !important; text-align: center !important; color: black !important; }
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

# 세션 상태 초기화 (입금/정산 체크용)
if 'done_list' not in st.session_state:
    st.session_state.done_list = set()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

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

        # 사이드바 이벤트 명단
        st.sidebar.write("---")
        st.sidebar.subheader("💎 배송비 이벤트 명단")
        def get_event_total(nickname):
            row = df_members[df_members['닉네임'] == nickname]
            if row.empty: return 0
            lb = row.iloc[0]['마지막혜택일'] if '마지막혜택일' in row.columns else pd.NA
            ud = df[df['구매자'] == nickname]
            if not pd.isna(lb): ud = ud[ud['경매일자'] > lb]
            return ud['가격'].sum()

        all_buyers = df['구매자'].dropna().unique()
        vvip = sorted([{'nick': b, 'amt': get_event_total(b)} for b in all_buyers if get_event_total(b) >= 3000000], key=lambda x: x['amt'], reverse=True)
        for v in vvip:
            tag = "30% 지원" if v['amt'] < 5000000 else "50% 지원" if v['amt'] < 10000000 else "🔥 전액지원"
            st.sidebar.markdown(f'<div class="vvip-box"><strong>{v["nick"]}</strong> <span class="benefit-tag">{tag}</span><br>누적: {v["amt"]:,.0f}원</div>', unsafe_allow_html=True)

        if selected_person == "SUMMARY_MODE":
            st.title(date_title)
            if not filtered_df.empty:
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
                
                col_in, col_out = st.columns(2)
                
                with col_in:
                    st.subheader("📩 입금 받을 돈 (구매자)")
                    remain_in_val = sum(i['금액'] for i in pay_in if f"in_{selected_date}_{i['고객명']}" not in st.session_state.done_list)
                    st.markdown(f"<div class='total-highlight'>남은 미입금 합계: {remain_in_val:,.0f}원</div>", unsafe_allow_html=True)
                    
                    # 수동 표 생성
                    st.markdown("<table><tr><th style='width:20%'>상태</th><th style='width:40%'>닉네임</th><th style='width:40%'>금액</th></tr>", unsafe_allow_html=True)
                    for i in sorted(pay_in, key=lambda x: x['고객명']):
                        key = f"in_{selected_date}_{i['고객명']}"
                        is_done = key in st.session_state.done_list
                        bg_color = "#f1f3f5" if is_done else "white"
                        text_style = "text-decoration: line-through; color: #adb5bd;" if is_done else "font-weight: bold;"
                        btn_label = "취소" if is_done else "입금완료"
                        
                        cols = st.columns([1, 2, 2])
                        if cols[0].button(btn_label, key=f"btn_{key}"):
                            if is_done: st.session_state.done_list.remove(key)
                            else: st.session_state.done_list.add(key)
                            st.rerun()
                        cols[1].markdown(f"<div style='text-align:center; padding:5px; {text_style}'>{i['고객명']}</div>", unsafe_allow_html=True)
                        cols[2].markdown(f"<div style='text-align:center; padding:5px; {text_style}'>{i['금액']:,.0f}원</div>", unsafe_allow_html=True)
                    st.markdown("</table>", unsafe_allow_html=True)

                with col_out:
                    st.subheader("💵 정산 드릴 돈 (판매자)")
                    remain_out_val = sum(i['금액'] for i in pay_out if f"out_{selected_date}_{i['고객명']}" not in st.session_state.done_list)
                    st.markdown(f"<div class='total-highlight'>남은 미정산 합계: {remain_out_val:,.0f}원</div>", unsafe_allow_html=True)
                    
                    st.markdown("<table><tr><th style='width:20%'>상태</th><th style='width:40%'>닉네임</th><th style='width:40%'>금액</th></tr>", unsafe_allow_html=True)
                    for i in sorted(pay_out, key=lambda x: x['고객명']):
                        key = f"out_{selected_date}_{i['고객명']}"
                        is_done = key in st.session_state.done_list
                        bg_color = "#f1f3f5" if is_done else "white"
                        text_style = "text-decoration: line-through; color: #adb5bd;" if is_done else "font-weight: bold;"
                        btn_label = "취소" if is_done else "정산완료"
                        
                        cols = st.columns([1, 2, 2])
                        if cols[0].button(btn_label, key=f"btn_{key}"):
                            if is_done: st.session_state.done_list.remove(key)
                            else: st.session_state.done_list.add(key)
                            st.rerun()
                        cols[1].markdown(f"<div style='text-align:center; padding:5px; {text_style}'>{i['고객명']}</div>", unsafe_allow_html=True)
                        cols[2].markdown(f"<div style='text-align:center; padding:5px; {text_style}'>{i['금액']:,.0f}원</div>", unsafe_allow_html=True)
                    st.markdown("</table>", unsafe_allow_html=True)

                st.write("---")
                # 랭킹 분석
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

        elif selected_person != "선택하세요":
            member_row = df_members[df_members['닉네임'] == selected_person]
            is_ex = not member_row.empty and str(member_row.iloc[0]['수수료면제여부']).strip() == "면제"
            st.title(f"📜 {selected_person} 경매내역서")
            info_col1, info_col2, info_col3 = st.columns([1, 1.2, 2.5])
            with info_col1: st.markdown(f"**🏷️ 성함**\n{member_row.iloc[0]['이름'] if not member_row.empty else '미등록'}")
            with info_col2: st.markdown(f"**📞 연락처**\n{member_row.iloc[0]['전화번호'] if not member_row.empty else '미등록'}")
            with info_col3: st.markdown(f"**🏠 주소**\n{member_row.iloc[0]['주소'] if not member_row.empty else '미등록'}")
            if is_ex: st.success("✨ 수수료 면제 대상 회원입니다")
            st.write("---")
            sell_data = filtered_df[filtered_df['판매자'] == selected_person].copy()
            buy_data = filtered_df[filtered_df['구매자'] == selected_person].copy()
            s_total = int(sell_data['가격'].sum()); s_fee = int(s_total * SELL_FEE_RATE); s_net = s_total - s_fee
            b_total_raw = int(buy_data['가격'].sum()); b_fee = 0 if is_ex else int(b_total_raw * DEFAULT_BUY_FEE_RATE); b_total_final = b_total_raw + b_fee
            final_balance = s_net - b_total_final
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("📤 판매 정산금", f"{s_net:,.0f}원"); st.caption(f"판매:{s_total:,.0f}/수수료:-{s_fee:,.0f}")
            with c2: st.metric("📥 구매 청구금", f"{b_total_final:,.0f}원"); st.caption(f"구매:{b_total_raw:,.0f}/수수료:+{b_fee:,.0f}")
            with c3: st.metric("💵 결과", f"{abs(final_balance):,.0f}원"); st.caption("정산드릴돈" if final_balance > 0 else "입금받을돈")
            st.write("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("[판매 내역]")
                if not sell_data.empty:
                    disp_s = sell_data[['품목', '가격', '구매자']].reset_index(drop=True); disp_s.index += 1
                    disp_s['가격'] = disp_s['가격'].map('{:,.0f}원'.format); st.table(disp_s)
            with col2:
                st.subheader("[구매 내역]")
                if not buy_data.empty:
                    disp_b = buy_data[['품목', '가격', '판매자']].reset_index(drop=True); disp_b.index += 1
                    disp_b['가격'] = disp_b['가격'].map('{:,.0f}원'.format); st.table(disp_b)
        else:
            st.info("👈 왼쪽에서 날짜와 고객을 선택해 주세요.")
