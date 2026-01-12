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
    .stTable td { text-align: center !important; background-color: white !important; color: black !important; border-bottom: 1px solid #ddd !important; }
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
        df_a['경매일자_dt'] = pd.to_datetime(df_a['경매일자'], errors='coerce')
        df_a = df_a.dropna(subset=['경매일자_dt']) 
        df_a['경매일자'] = df_a['경매일자_dt'].dt.date
        
        df_m = pd.read_csv(URL_MEMBERS)
        member_cols = ['닉네임', '이름', '전화번호', '주소', '수수료면제여부', '전미수', '금액']
        if len(df_m.columns) >= 8:
            df_m = df_m.iloc[:, :8]; df_m.columns = member_cols + ['마지막혜택일']
        else:
            df_m.columns = member_cols; df_m['마지막혜택일'] = pd.NA
        df_m['마지막혜택일'] = pd.to_datetime(df_m['마지막혜택일'], errors='coerce').dt.date
        return df_a, df_m
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}"); return None, None

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

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
        view_mode = st.sidebar.radio("모드 선택", ["일별 조회", "기간별 조회", "일별 요약", "월별 요약", "연간 요약"])
        available_dates = sorted(df['경매일자'].unique(), reverse=True)
        
        if view_mode == "월별 요약":
            df['연월'] = df['경매일자_dt'].dt.strftime('%Y-%m')
            available_months = sorted(df['연월'].unique(), reverse=True)
            selected_month = st.sidebar.selectbox("📅 월 선택", available_months)
            filtered_df = df[df['연월'] == selected_month]
            selected_person = "MONTHLY_SUMMARY"
        elif view_mode == "연간 요약":
            df['연도'] = df['경매일자_dt'].dt.year
            available_years = sorted(df['연도'].unique(), reverse=True)
            selected_year = st.sidebar.selectbox("📅 연도 선택", available_years)
            filtered_df = df[df['연도'] == selected_year]
            selected_person = "YEARLY_SUMMARY"
        elif view_mode == "일별 요약":
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

        if st.sidebar.button("로그아웃"): st.session_state['logged_in'] = False; st.rerun()

        # --- [사이드바 이벤트 명단 로직 생략(기존과 동일)] ---
        st.sidebar.write("---")
        st.sidebar.subheader("💎 배송비 이벤트 명단")
        def get_event_total(nickname):
            row = df_members[df_members['닉네임'] == nickname]
            if row.empty: return 0
            last_benefit = row.iloc[0]['마지막혜택일']
            user_data = df[df['구매자'] == nickname]
            if not pd.isna(last_benefit): user_data = user_data[user_data['경매일자_dt'].dt.date > last_benefit]
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

        # --- [메인 화면 출력] ---

        if selected_person == "SUMMARY_MODE":
            st.title(date_title)
            if not filtered_df.empty:
                # --- [수정] 한글 오전/오후 시간 파싱 및 그래프 로직 ---
                st.subheader("📈 시간대별 매출 및 낙찰 건수 흐름 (오후 2시 시작)")
                def parse_korean_time_to_sort(time_val):
                    try:
                        t_str = str(time_val).strip()
                        if not t_str or t_str == 'nan': return None
                        t_str = t_str.replace("오후", "PM").replace("오전", "AM")
                        for fmt in ("%p %I:%M:%S", "%p %I:%M", "%H:%M:%S", "%H:%M"):
                            try:
                                dt_obj = datetime.strptime(t_str, fmt)
                                h = dt_obj.hour
                                return h if h >= 14 else h + 24
                            except: continue
                        return None
                    except: return None

                chart_df = filtered_df.copy()
                chart_df['정렬시간'] = chart_df['낙찰시간'].apply(parse_korean_time_to_sort)
                valid_chart_df = chart_df.dropna(subset=['정렬시간'])
                
                if not valid_chart_df.empty:
                    time_agg = valid_chart_df.groupby('정렬시간').agg(매출금액=('가격', 'sum'), 낙찰건수=('가격', 'count')).reset_index()
                    all_h = range(14, int(time_agg['정렬시간'].max()) + 1)
                    time_agg = pd.merge(pd.DataFrame({'정렬시간': list(all_h)}), time_agg, on='정렬시간', how='left').fillna(0)
                    def fmt_label(h):
                        act_h = int(h) if h < 24 else int(h) - 24
                        p = "오후" if 12 <= act_h < 24 else "오전"
                        disp = act_h if act_h <= 12 else act_h - 12
                        if disp == 0: disp = 12
                        return f"{p} {disp}시"
                    time_agg['시간대'] = time_agg['정렬시간'].apply(fmt_label)
                    g1, g2 = st.columns(2)
                    with g1: st.write("💰 시간대별 매출"); st.line_chart(time_agg.set_index('시간대')['매출금액'])
                    with g2: st.write("📦 시간대별 건수"); st.line_chart(time_agg.set_index('시간대')['낙찰건수'])
                else: st.warning("시간 데이터를 인식할 수 없습니다.")
                
                st.write("---")
                total_sales = filtered_df['가격'].sum()
                sell_fees = int(total_sales * SELL_FEE_RATE)
                all_p = sorted(list(set(filtered_df['판매자'].unique()) | set(filtered_df['구매자'].unique())))
                pay_in, pay_out, total_buy_fees = [], [], 0
                for p in all_p:
                    s_amt = int(filtered_df[filtered_df['판매자'] == p]['가격'].sum())
                    s_net = s_amt - int(s_amt * SELL_FEE_RATE)
                    is_ex = not df_members[df_members['닉네임'] == p].empty and str(df_members[df_members['닉네임'] == p].iloc[0]['수수료면제여부']).strip() == "면제"
                    b_raw = int(filtered_df[filtered_df['구매자'] == p]['가격'].sum())
                    b_f = 0 if is_ex else int(b_raw * DEFAULT_BUY_FEE_RATE)
                    total_buy_fees += b_f; bal = s_net - (b_raw + b_f)
                    if bal > 0: pay_out.append({"고객명": p, "금액": bal})
                    elif bal < 0: pay_in.append({"고객명": p, "금액": abs(bal)})

                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div class='summary-box'><h3>💰 총 매출</h3><h2>{total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='summary-box'><h3>📉 예상 수익</h3><h2>{sell_fees + total_buy_fees:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='summary-box'><h3>📦 낙찰 건수</h3><h2>{len(filtered_df)}건</h2></div>", unsafe_allow_html=True)
                
                st.write("---")
                r1, r2 = st.columns(2)
                with r1:
                    st.subheader("🏆 오늘 구매 TOP 10")
                    rb = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    rb.index += 1; rb.columns=['고객명','구매금액']; rb['구매금액']=rb['구매금액'].map('{:,.0f}원'.format); st.table(rb)
                with r2:
                    st.subheader("💰 오늘 판매 TOP 10")
                    rs = filtered_df.groupby('판매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    rs.index += 1; rs.columns=['고객명','판매금액']; rs['판매금액']=rs['판매금액'].map('{:,.0f}원'.format); st.table(rs)
                
                st.subheader("🔝 오늘 최고가 낙찰품 TOP 10")
                rt = filtered_df.sort_values(by='가격', ascending=False).head(10)[['품목', '가격', '구매자', '판매자']].reset_index(drop=True)
                rt.index += 1; rt['가격'] = rt['가격'].map('{:,.0f}원'.format); st.table(rt)

                st.write("---")
                ci, co = st.columns(2)
                with ci:
                    st.subheader("📩 입금 받을 돈")
                    rip = st.empty(); tri = 0
                    for item in sorted(pay_in, key=lambda x: x['금액'], reverse=True):
                        chk, nm, am = st.columns([1, 4, 4])
                        is_c = chk.checkbox("", key=f"in_{selected_date}_{item['고객명']}")
                        nm.markdown(f"**{item['고객명']}**")
                        am.markdown(f"{item['금액']:,.0f}원")
                        if not is_c: tri += item['금액']
                    rip.markdown(f"<div class='total-highlight'>남은 미입금: {tri:,.0f}원</div>", unsafe_allow_html=True)
                with co:
                    st.subheader("💵 정산 드릴 돈")
                    rop = st.empty(); tro = 0
                    for item in sorted(pay_out, key=lambda x: x['금액'], reverse=True):
                        chk, nm, am = st.columns([1, 4, 4])
                        is_c = chk.checkbox("", key=f"out_{selected_date}_{item['고객명']}")
                        nm.markdown(f"**{item['고객명']}**")
                        am.markdown(f"{item['금액']:,.0f}원")
                        if not is_c: tro += item['금액']
                    rop.markdown(f"<div class='total-highlight'>남은 미정산: {tro:,.0f}원</div>", unsafe_allow_html=True)
            else: st.info("데이터가 없습니다.")

        elif selected_person == "MONTHLY_SUMMARY":
            st.title(f"📅 {selected_month} 월간 실적 요약")
            if not filtered_df.empty:
                total_sales = filtered_df['가격'].sum()
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div class='summary-box'><h3>💰 월 매출</h3><h2>{total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='summary-box'><h3>📈 낙찰 건수</h3><h2>{len(filtered_df)}건</h2></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='summary-box'><h3>🤝 고객수</h3><h2>{filtered_df['구매자'].nunique()}명</h2></div>", unsafe_allow_html=True)
                st.write("---")
                cl, cr = st.columns(2)
                with cl:
                    st.subheader("🏆 이달의 구매 TOP 10")
                    mb = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    mb.index += 1; mb.columns=['고객명','구매금액']; mb['구매금액']=mb['구매금액'].map('{:,.0f}원'.format); st.table(mb)
                with cr:
                    st.subheader("💰 이달의 판매 TOP 10")
                    ms = filtered_df.groupby('판매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    ms.index += 1; ms.columns=['고객명','판매금액']; ms['판매금액']=ms['판매금액'].map('{:,.0f}원'.format); st.table(ms)

        elif selected_person == "YEARLY_SUMMARY":
            st.title(f"🏢 {selected_year}년 연간 경영 요약")
            if not filtered_df.empty:
                total_sales = filtered_df['가격'].sum()
                st.markdown(f"<div class='summary-box'><h2>{selected_year}년 누적 매출: {total_sales:,.0f}원</h2></div>", unsafe_allow_html=True)
                filtered_df['월'] = filtered_df['경매일자_dt'].dt.month
                mc = filtered_df.groupby('월')['가격'].sum().reset_index()
                st.subheader("📊 월별 매출 흐름")
                st.line_chart(mc.set_index('월'))
                col_l, col_r = st.columns(2)
                with col_l:
                    st.subheader("🥇 연간 구매 왕 TOP 10")
                    yb = filtered_df.groupby('구매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    yb.index+=1; yb.columns=['고객명','구매금액']; yb['구매금액']=yb['구매금액'].map('{:,.0f}원'.format); st.table(yb)
                with col_r:
                    st.subheader("💰 연간 판매 왕 TOP 10")
                    ys = filtered_df.groupby('판매자')['가격'].sum().sort_values(ascending=False).head(10).reset_index()
                    ys.index+=1; ys.columns=['고객명','판매금액']; ys['판매금액']=ys['판매금액'].map('{:,.0f}원'.format); st.table(ys)
                st.write("---")
                st.subheader("🔝 연간 최고가 낙찰품 TOP 10")
                yt = filtered_df.sort_values(by='가격', ascending=False).head(10)[['경매일자', '품목', '가격', '구매자', '판매자']].reset_index(drop=True)
                yt.index+=1; yt['가격']=yt['가격'].map('{:,.0f}원'.format); st.table(yt)

        elif selected_person != "선택하세요":
            member_row = df_members[df_members['닉네임'] == selected_person]
            is_exempt = not member_row.empty and str(member_row.iloc[0]['수수료면제여부']).strip() == "면제"
            st.title("📜 경매내역서 조회")
            st.markdown(f"## 👤 {selected_person} 님의 상세 정보")
            i1, i2, i3 = st.columns([1, 1.2, 2.5])
            i1.markdown(f"**🏷️ 성함**\n{member_row.iloc[0]['이름'] if not member_row.empty else '미등록'}")
            i2.markdown(f"**📞 연락처**\n{member_row.iloc[0]['전화번호'] if not member_row.empty else '미등록'}")
            i3.markdown(f"**🏠 주소**\n{member_row.iloc[0]['주소'] if not member_row.empty else '미등록'}")
            if is_exempt: st.success("✨ 수수료 면제 대상 회원입니다")
            st.write("---")
            sd = filtered_df[filtered_df['판매자'] == selected_person].copy()
            bd = filtered_df[filtered_df['구매자'] == selected_person].copy()
            st_raw = int(sd['가격'].sum()); sf = int(st_raw * SELL_FEE_RATE); sn = st_raw - sf
            bt_raw = int(bd['가격'].sum()); bf = 0 if is_exempt else int(bt_raw * DEFAULT_BUY_FEE_RATE); bt_f = bt_raw + bf
            bal = sn - bt_f
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("📤 판매 정산금", f"{sn:,.0f}원")
            with c2: st.metric("📥 구매 청구금", f"{bt_f:,.0f}원")
            with c3: st.metric("💵 최종 정산액" if bal > 0 else "📩 최종 입금액", f"{abs(bal):,.0f}원")
            st.write("---")
            l, r = st.columns(2)
            scs, bcs = (['품목','가격','구매자'],['품목','가격','판매자']) if view_mode=="일별 조회" else (['경매일자','품목','가격'],['경매일자','품목','가격'])
            with l:
                st.markdown("### [판매 내역]")
                if not sd.empty: dps=sd[scs].reset_index(drop=True); dps.index+=1; dps['가격']=dps['가격'].map('{:,.0f}'.format); st.table(dps)
            with r:
                st.markdown("### [구매 내역]")
                if not bd.empty: dpb=bd[bcs].reset_index(drop=True); dpb.index+=1; dpb['가격']=dpb['가격'].map('{:,.0f}'.format); st.table(dpb)
        else: st.info("👈 왼쪽에서 날짜와 고객을 선택해 주세요.")
