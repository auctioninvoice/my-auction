import streamlit as st
            with c1: st.markdown(f"<div class='summary-box'><h3>📦 누적 낙찰</h3><h2>{len(p_buy)}건</h2></div>", unsafe_allow_html=True)
            with c2: 
                st.markdown(f"""
                <div class='summary-box'>
                    <h3>💰 누적 구매금액</h3>
                    <h2>{total_buy_with_fee:,.0f}원</h2>
                    <div style='font-size:0.85em; color:gray; line-height:1.4; margin-top:5px;'>
                        총 낙찰금액: {raw_buy:,.0f}원<br>
                        + 수수료({buy_rate_txt}): {buy_fee:,.0f}원
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c3: 
                st.markdown(f"""
                <div class='summary-box'>
                    <h3>📤 누적 판매금액</h3>
                    <h2>{total_sell_net:,.0f}원</h2>
                    <div style='font-size:0.85em; color:gray; line-height:1.4; margin-top:5px;'>
                        총 낙찰금액: {raw_sell:,.0f}원<br>
                        - 수수료({sell_rate_txt}): {sell_fee:,.0f}원
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.write("---")
            t1, t2 = st.tabs(["🛍️ 전체 구매 내역", "📦 전체 판매 내역"])
            with t1:
                if not p_buy.empty:
                    p_buy_disp = p_buy[['경매일자', '품목', '가격', '판매자']].sort_values('경매일자', ascending=False).reset_index(drop=True)
                    p_buy_disp.index += 1; p_buy_disp['경매일자'] = p_buy_disp['경매일자'].apply(get_ko_date)
                    p_buy_disp['가격'] = p_buy_disp['가격'].map('{:,.0f}'.format); st.table(p_buy_disp)
                else: st.info("구매 내역이 없습니다.")
            with t2:
                if not p_sell.empty:
                    p_sell_disp = p_sell[['경매일자', '품목', '가격', '구매자']].sort_values('경매일자', ascending=False).reset_index(drop=True)
                    p_sell_disp.index += 1; p_sell_disp['경매일자'] = p_sell_disp['경매일자'].apply(get_ko_date)
                    p_sell_disp['가격'] = p_sell_disp['가격'].map('{:,.0f}'.format); st.table(p_sell_disp)
                else: st.info("판매 내역이 없습니다.")
            selected_person = "MEMBER_DETAIL_VIEW"

        # ---------------------------------------------------------
        # [기존] 일별 요약 및 조회
        # ---------------------------------------------------------
        elif view_mode == "일별 요약":
            selected_date = st.sidebar.selectbox("📅 요약 날짜 선택", available_dates) if available_dates else None
            filtered_df = df[df['경매일자'] == selected_date] if selected_date else pd.DataFrame()
            date_title = f"📊 {get_ko_date(selected_date) if selected_date else ''} 판매 요약 보고서"
            selected_person = "SUMMARY_MODE"
        elif view_mode == "일별 조회":
            selected_date = st.sidebar.selectbox("📅 날짜 선택", available_dates) if available_dates else None
            filtered_df = df[df['경매일자'] == selected_date] if selected_date else pd.DataFrame()
            date_title = f"📅 경매일자: {get_ko_date(selected_date) if selected_date else ''}"
        elif view_mode == "기간별 조회": # 기간별
            c1, c2 = st.sidebar.columns(2)
            start_date = c1.date_input("시작일", datetime.now().date() - timedelta(days=7))
            end_date = c2.date_input("종료일", datetime.now().date())
            filtered_df = df[(df['경매일자'] >= start_date) & (df['경매일자'] <= end_date)]
            date_title = f"🗓️ 기간: {get_ko_date(start_date)} ~ {get_ko_date(end_date)}"
        elif view_mode == "연간 요약":
            df['연도'] = df['경매일자_dt'].dt.year
            available_years = sorted(df['연도'].unique(), reverse=True)
            selected_year = st.sidebar.selectbox("📅 연도 선택", available_years)
            filtered_df = df[df['연도'] == selected_year]
            selected_person = "YEARLY_SUMMARY"
        elif view_mode == "월별 요약":
            df['연월'] = df['경매일자_dt'].dt.strftime('%Y-%m')
            available_months = sorted(df['연월'].unique(), reverse=True)
