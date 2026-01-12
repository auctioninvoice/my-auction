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
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: white !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: black !important; }
    .stTable { width: 100% !important; border-collapse: collapse; }
    .stTable th { text-align: center !important; background-color: #f0f2f6 !important; color: black !important; }
    .stTable td { background-color: white !important; color: black !important; border-bottom: 1px solid #ddd !important; }
    .vvip-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 8px; border-left: 5px solid #ffc107; }
    .benefit-tag { background-color: #d1ecf1; color: #0c5460; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }
    .summary-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 10px; }
    .total-highlight { background-color: #e9ecef; padding: 10px; border-radius: 5px; text-align: right; font-weight: bold; font-size: 1.1em; color: #212529; margin-bottom: 10px; border-right: 5px solid #6c757d; }
    @media print {
        [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, button, header { display: none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
    }
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
        if len(df_m.columns) >= 8:
            df_m = df_m.iloc[:, :8]
            df_m.columns = member_cols + ['마지막혜택일']
        else:
            df_m.columns = member_cols
            df_m['마지막혜택일'] = pd.NA
        df_m['마지막혜택일'] = pd.to_datetime(df_m['마지막혜택일'], errors='coerce').dt.date
        return df_a, df_m
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}"); return None, None

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
        # --- [1. 사이드바 상단: 조회 설정] ---
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

        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False; st.rerun()

        # --- [2. 사이드바 하단: 이벤트 명단] ---
        st.sidebar.write("---")
        st.sidebar.subheader("💎 배송비 이벤트 명단")
        def get_event_total(nickname):
            row = df_members[df_members['닉네임'] == nickname]
            if row.empty: return 0
            last_benefit = row.iloc[0]['마지막혜택일']
            user_data = df[df['구매자'] == nickname]
            if not pd.isna(last_benefit):
                user_data = user_data[user_data['경매일자'] > last_benefit]
            return user_data['가격'].sum()

        all_buyers = df['구매자'].dropna().unique()
        vvip_results = []
        for b in all_buyers:
            amt = get_event_total(b)
            if amt >= 3000000: vvip_results.append({'nick': b, 'amt': amt})
        if vvip_results:
            vvip_results = sorted(vvip_results, key=lambda x: x['amt'], reverse=True)
            for v in vvip_results:
                tag = "30% 지원" if v['amt'] < 5000000 else "50% 지원" if v['amt'] < 10000000 else "🔥 전액지원"
                st.sidebar.markdown(f'<div class="vvip-box"><strong>{v["nick"]}</strong> <span class="benefit-tag">{tag}</span><br>누적: {v["amt"]:,.0f}원</div>', unsafe_allow_html=True)
        else: st.sidebar.write("대상자 없음")

        # --- [3. 메인 화면 출력] ---
        if selected_person == "SUMMARY_MODE":
            st.title(date_title)
            if not filtered_df.empty:
                total_sales = filtered_df['가격'].sum()
                sell_fees = int(total_sales * SELL_FEE_RATE)
                all_p = sorted(list(set(filtered_df['판매자'].unique()) | set(filtered_df['구매자'].unique())))
                pay_in, pay_out, total_buy_fees = [], [], 0
                for p in all_p:
                    s_amt = int(filtered_df[filtered_df['판매자'] == p]['가격'].sum())
                    s_net = s_amt - int(s_amt * SELL_FEE_RATE)
                    is_exempt = not df_members[df_members['닉네임'] == p].empty and str(df_members[df_members['닉네임'] == p].iloc[0]['수수료면제여부']).strip() == "면제"
                    b_raw = int(filtered_df[filtered_df['구매자'] == p]['가격'].sum())
                    b_f = 0 if is_exempt else int(b_raw * DEFAULT_BUY_FEE_RATE)
                    total_buy_fees += b_f
                    bal = s_net - (b_raw + b_f)
                    if bal > 0: pay_out.append({"고객명": p, "금액": bal})
                    elif bal < 0: pay_in.append({"고객명": p, "금액": abs(bal)})

                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div class='summary-box'><h3>💰 총 매출</h3><h2>{total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='summary-box'><h3>📉 예상 수익(수수료)</h3><h2>{sell_fees + total_buy_fees:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='summary-box'><h3>📦 낙찰 건수</h3><h2>{len(filtered_df)}건</h2></div>", unsafe_allow_html=True)
                st.write("---")
                
                col_in, col_out = st.columns(2)
                with col_in:
                    st.subheader("📩 입금 받을 돈 (구매자)")
                    in_remain_placeholder = st.empty()
                    total_in_remain = 0
                    for item in sorted(pay_in, key=lambda x: x['금액'], reverse=True):
                        c_chk, c_name, c_amt = st.columns([1, 4, 4])
                        is_checked = c_chk.checkbox("", key=f"in_{selected_date}_{item['고객명']}")
                        c_name.markdown(f"**{item['고객명']}**")
                        c_amt.markdown(f"{item['금액']:,.0f}원")
                        if not is_checked: total_in_remain += item['금액']
                    in_remain_placeholder.markdown(f"<div class='total-highlight'>남은 미입금 합계: {total_in_remain:,.0f}원</div>", unsafe_allow_html=True)
                with col_out:
                    st.subheader("💵 정산 드릴 돈 (판매자)")
                    out_remain_placeholder = st.empty()
                    total_out_remain = 0
                    for item in sorted(pay_out, key=lambda x: x['금액'], reverse=True):
                        c_chk, c_name, c_amt = st.columns([1, 4, 4])
                        is_checked = c_chk.checkbox("", key=f"out_{selected_date}_{item['고객명']}")
                        c_name.markdown(f"**{item['고객명']}**")
                        c_amt.markdown(f"{item['금액']:,.0f}원")
                        if not is_checked: total_out_remain += item['금액']
                    out_remain_placeholder.markdown(f"<div class='total-highlight'>남은 미정산 합계: {total_out_remain:,.0f}원</div>", unsafe_allow_html=True)

                st.write("---")
                rank_l, rank_r = st.columns(2)
                with rank_l:
                    st.subheader("🏆 오늘자 구매왕")
                    rb = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(5).reset_index()
                    rb.index += 1; rb.columns = ['고객명', '구매금액']
                    rb['구매금액'] = rb['구매금액'].map('{:,.0f}원'.format); st.table(rb)
                with rank_r:
                    st.subheader("🔝 최고가 낙찰품")
                    rt = filtered_df.sort_values(by='가격', ascending=False).head(5)[['품목', '가격', '구매자']].reset_index(drop=True)
                    rt.index += 1; rt['가격'] = rt['가격'].map('{:,.0f}원'.format); st.table(rt)
            else: st.info("데이터가 없습니다.")

        elif selected_person != "선택하세요":
            member_row = df_members[df_members['닉네임'] == selected_person]
            is_exempt = not member_row.empty and str(member_row.iloc[0]['수수료면제여부']).strip() == "면제"
            st.title("📜 경매내역서 조회")
            st.markdown(f"### {date_title}")
            st.markdown(f"## 👤 {selected_person} 님의 상세 정보")
            
            info_col1, info_col2, info_col3 = st.columns([1, 1.2, 2.5])
            with info_col1: st.markdown(f"**🏷️ 성함**\n{member_row.iloc[0]['이름'] if not member_row.empty else '미등록'}")
            with info_col2: st.markdown(f"**📞 연락처**\n{member_row.iloc[0]['전화번호'] if not member_row.empty else '미등록'}")
            with info_col3: st.markdown(f"**🏠 주소**\n{member_row.iloc[0]['주소'] if not member_row.empty else '미등록'}")
            if is_exempt: st.success("✨ 수수료 면제 대상 회원입니다")
            st.write("---")

            sell_data = filtered_df[filtered_df['판매자'] == selected_person].copy()
            buy_data = filtered_df[filtered_df['구매자'] == selected_person].copy()
            s_total = int(sell_data['가격'].sum()); s_fee = int(s_total * SELL_FEE_RATE); s_net = s_total - s_fee
            b_total_raw = int(buy_data['가격'].sum()); b_fee = 0 if is_exempt else int(b_total_raw * DEFAULT_BUY_FEE_RATE); b_total_final = b_total_raw + b_fee
            final_balance = s_net - b_total_final

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("📤 판매 정산금", f"{s_net:,.0f}원"); st.caption(f"판매:{s_total:,.0f} / 수수료:-{s_fee:,.0f}")
            with c2: st.metric("📥 구매 청구금", f"{b_total_final:,.0f}원"); st.caption(f"구매:{b_total_raw:,.0f} / 수수료:+{b_fee:,.0f}")
            with c3:
                label = "💵 입금해드릴 돈" if final_balance > 0 else "📩 입금받을 돈"
                st.metric(label, f"{abs(final_balance):,.0f}원")

            st.write("---")
            col1, col2 = st.columns(2)
            s_cols, b_cols = (['품목', '가격', '구매자'], ['품목', '가격', '판매자']) if view_mode == "일별 조회" else (['경매일자', '품목', '가격'], ['경매일자', '품목', '가격'])
            with col1:
                st.markdown("### [판매 내역]")
                if not sell_data.empty:
                    disp_s = sell_data[s_cols].reset_index(drop=True); disp_s.index += 1
                    disp_s['가격'] = disp_s['가격'].map('{:,.0f}'.format); st.table(disp_s)
                else: st.write("판매 내역 없음")
            with col2:
                st.markdown("### [구매 내역]")
                if not buy_data.empty:
                    disp_b = buy_data[b_cols].reset_index(drop=True); disp_b.index += 1
                    disp_b['가격'] = disp_b['가격'].map('{:,.0f}'.format); st.table(disp_b)
                else: st.write("구매 내역 없음")
        
        # --- [마지막 안내 문구 추가] ---
        else:
            st.info("👈 왼쪽에서 날짜와 고객을 선택해 주세요.")
 이 코드가 내가 저장해노라고한 코드야!
