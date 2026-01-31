import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# ── Local module imports ──
import config
from config import check_login
from styles import inject_css
import utils
from pages_portfolio import render_portfolio_page

# ==========================================
# INJECT THEME (must run before anything renders)
# ==========================================
inject_css()

# ==========================================
# LOGIN GATE
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🩸</div>
        <h1 style="margin: 0 0 10px 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; position: relative; z-index: 1;">StockPostmortem</h1>
        <p style="color: #6b7280; font-size: 0.8rem; margin-bottom: 48px; letter-spacing: 3px; text-transform: uppercase; position: relative; z-index: 1;">Algorithmic Behavioral Forensics</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login_form"):
            st.text_input("Operator ID", key="username_input", placeholder="Enter your ID")
            st.text_input("Access Key", type="password", key="password_input", placeholder="Enter your key")
            submitted = st.form_submit_button("INITIALIZE TERMINAL", type="primary", use_container_width=True)
            if submitted:
                check_login(st.session_state.username_input, st.session_state.password_input)

# ==========================================
# AUTHENTICATED DASHBOARD
# ==========================================
else:
    # One-time DB/API init per session
    if "db_initialized" not in st.session_state:
        config.init_db_and_api()
        st.session_state["db_initialized"] = True

    current_user = st.session_state["user"]

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "analyze"

    current_page = st.session_state.get("current_page", "analyze")

    # ── NAVBAR ──
    st.markdown(f"""
    <div class="premium-navbar">
        <div class="nav-brand">
            <div class="nav-logo">🩸</div>
            <div><div class="nav-title">Trade Autopsy</div></div>
        </div>
        <div class="nav-menu">
            <span class="nav-link {'active' if current_page == 'analyze' else ''}" id="nav_analyze">Analyze</span>
            <span class="nav-link {'active' if current_page == 'portfolio' else ''}" id="nav_portfolio">Portfolio</span>
            <span class="nav-link {'active' if current_page == 'data_vault' else ''}" id="nav_vault">Data Vault</span>
            <span class="nav-link {'active' if current_page == 'pricing' else ''}" id="nav_pricing">Pricing</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: rgba(16, 185, 129, 0.15); padding: 8px 16px; border-radius: 10px; font-size: 0.85rem; font-weight: 600; color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3);">
                {current_user}
            </div>
        </div>
    </div>
    <script>
    document.getElementById('nav_analyze').onclick = function() {{ window.location.href = '?page=analyze'; }};
    document.getElementById('nav_portfolio').onclick = function() {{ window.location.href = '?page=portfolio'; }};
    document.getElementById('nav_vault').onclick = function() {{ window.location.href = '?page=data_vault'; }};
    document.getElementById('nav_pricing').onclick = function() {{ window.location.href = '?page=pricing'; }};
    </script>
    """, unsafe_allow_html=True)

    # ==========================================
    # PAGE ROUTING
    # ==========================================

    if current_page == "portfolio":
        render_portfolio_page(current_user)

    elif current_page == "data_vault":
        _render_data_vault(current_user)

    elif current_page == "pricing":
        _render_pricing()

    else:  # "analyze"
        _render_analyze_page(current_user)


# ============================================================
# PAGE: DATA VAULT
# ============================================================
def _render_data_vault(current_user):
    if not config.supabase:
        st.warning("Database not configured.")
        return

    hist = config.supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()

    if hist.data:
        df = pd.DataFrame(hist.data)
        df['created_at'] = pd.to_datetime(df['created_at'])

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">Complete Audit History ({len(df)} records)</div>', unsafe_allow_html=True)

        col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
        with col_search1:
            search_ticker = st.text_input("Search by Ticker", placeholder="e.g., SPY, AAPL", label_visibility="collapsed")
        with col_search2:
            score_filter = st.selectbox("Score Filter", ["All", "Excellent (80+)", "Good (60-80)", "Fair (40-60)", "Poor (<40)"], label_visibility="collapsed")
        with col_search3:
            sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Score", "Lowest Score"], label_visibility="collapsed")

        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

        filtered_df = df.copy()
        if search_ticker:
            filtered_df = filtered_df[filtered_df['ticker'].str.contains(search_ticker, case=False, na=False)]
        if score_filter == "Excellent (80+)":
            filtered_df = filtered_df[filtered_df['score'] >= 80]
        elif score_filter == "Good (60-80)":
            filtered_df = filtered_df[(filtered_df['score'] >= 60) & (filtered_df['score'] < 80)]
        elif score_filter == "Fair (40-60)":
            filtered_df = filtered_df[(filtered_df['score'] >= 40) & (filtered_df['score'] < 60)]
        elif score_filter == "Poor (<40)":
            filtered_df = filtered_df[filtered_df['score'] < 40]

        if sort_order == "Oldest First":
            filtered_df = filtered_df.sort_values('created_at', ascending=True)
        elif sort_order == "Highest Score":
            filtered_df = filtered_df.sort_values('score', ascending=False)
        elif sort_order == "Lowest Score":
            filtered_df = filtered_df.sort_values('score', ascending=True)
        else:
            filtered_df = filtered_df.sort_values('created_at', ascending=False)

        table_df = filtered_df[['created_at', 'ticker', 'score', 'mistake_tags', 'technical_analysis', 'psych_analysis']].copy()
        table_df.columns = ['Date', 'Ticker', 'Score', 'Error Tags', 'Technical Notes', 'Psychology Notes']
        table_df['Error Tags'] = table_df['Error Tags'].apply(lambda x: ', '.join(x[:3]) if len(x) > 0 else 'None')
        table_df['Technical Notes'] = table_df['Technical Notes'].apply(lambda x: (x[:80] + '...') if len(str(x)) > 80 else x)
        table_df['Psychology Notes'] = table_df['Psychology Notes'].apply(lambda x: (x[:80] + '...') if len(str(x)) > 80 else x)

        st.dataframe(
            table_df, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                "Date": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY HH:mm"),
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Error Tags": st.column_config.TextColumn("Error Tags", width="medium"),
                "Technical Notes": st.column_config.TextColumn("Technical", width="large"),
                "Psychology Notes": st.column_config.TextColumn("Psychology", width="large")
            },
            height=600
        )

        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"stockpostmortem_data_{current_user}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=False
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">🗄️</div>
        <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Data Vault Empty</div>
        <div style="font-size: 0.95rem; color: #6b7280;">Your audit history will appear here once you start analyzing trades.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE: PRICING
# ============================================================
def _render_pricing():
    st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">💳</div>
    <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Pricing Information</div>
    <div style="font-size: 0.95rem; color: #6b7280;">Pricing details coming soon.</div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE: ANALYZE  (Forensic Audit + Performance Metrics tabs)
# ============================================================
def _render_analyze_page(current_user):
    main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

    with main_tab1:
        _render_forensic_audit(current_user)

    with main_tab2:
        _render_performance_metrics(current_user)


# ─────────────────────────────────────────────────────
# TAB 1: FORENSIC AUDIT  (3 input modes)
# ─────────────────────────────────────────────────────
def _render_forensic_audit(current_user):
    c_mode = st.radio("Input Vector", ["Text Parameters", "Chart Vision", "Portfolio Analysis"], horizontal=True, label_visibility="collapsed")

    prompt = ""
    img_b64 = None
    ticker_val = "IMG"
    ready_to_run = False
    stored_image_url = None

    # ── MODE: Chart Vision ──
    if c_mode == "Chart Vision":
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Quantitative Chart Analysis</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div class="upload-icon">📊</div>
            <div class="upload-text">Upload Trading Chart for Deep Analysis</div>
            <div class="upload-subtext">Supports PNG, JPG (Max 10MB). Our AI analyzes price action, risk metrics, and behavioral patterns.</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="chart_upload")

        if uploaded_file:
            st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
            st.image(uploaded_file, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
            with st.expander("📝 Optional: Help AI Read Your Chart (if it struggles)"):
                st.markdown("If the AI generates wrong prices, you can provide key info to help:")
                manual_ticker = st.text_input("Ticker Symbol (e.g., GLIT, AAPL)", "", placeholder="Leave blank for auto-detect")
                manual_pnl = st.text_input("Your P&L shown (e.g., -$18,500 or +$2,340)", "", placeholder="Leave blank for auto-detect")
                manual_pnl_pct = st.text_input("Your P&L % shown (e.g., -66.2% or +15.3%)", "", placeholder="Leave blank for auto-detect")
                manual_price_range = st.text_input("Price range on chart (e.g., $200 to $290)", "", placeholder="Leave blank for auto-detect")

            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

            if st.button("🧬 RUN QUANTITATIVE ANALYSIS", type="primary", use_container_width=True):
                with st.spinner("Uploading evidence to secure vault..."):
                    stored_image_url = utils.upload_image_to_supabase(uploaded_file)

                img_b64 = utils.prepare_image_b64(uploaded_file)

                # Build manual override context
                manual_context = ""
                if manual_ticker or manual_pnl or manual_pnl_pct or manual_price_range:
                    manual_context = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    manual_context += "USER PROVIDED THIS INFORMATION FROM THE CHART:\n"
                    if manual_ticker:  manual_context += f"- Ticker: {manual_ticker}\n"
                    if manual_pnl:     manual_context += f"- P&L: {manual_pnl}\n"
                    if manual_pnl_pct: manual_context += f"- P&L Percentage: {manual_pnl_pct}\n"
                    if manual_price_range: manual_context += f"- Price Range: {manual_price_range}\n"
                    manual_context += "USE THIS INFORMATION - IT IS CORRECT. Analyze based on these real values.\n"
                    manual_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

                prompt = _build_chart_vision_prompt(manual_context)
                ready_to_run = True

        st.markdown('</div>', unsafe_allow_html=True)

    # ── MODE: Portfolio Analysis (inline on Analyze tab) ──
    elif c_mode == "Portfolio Analysis":
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Portfolio Health Analysis</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div class="upload-icon">📂</div>
            <div class="upload-text">Upload Your Portfolio Screenshot or PDF</div>
            <div class="upload-subtext">Supports PNG, JPG, PDF. We'll analyze your entire portfolio health, risk metrics, and provide restructuring recommendations.</div>
        </div>
        """, unsafe_allow_html=True)

        portfolio_file = st.file_uploader("Upload Portfolio Screenshot or PDF", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed", key="portfolio_upload")

        if portfolio_file:
            if portfolio_file.type == "application/pdf":
                st.info("📄 PDF uploaded. Analysis will extract portfolio data from PDF.")
            else:
                st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
                st.image(portfolio_file, use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
            with st.expander("📝 Manual Portfolio Data (Recommended for Best Results)", expanded=True):
                st.markdown("**Provide your portfolio details for most accurate analysis:**")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    portfolio_total_invested = st.number_input("Total Invested Amount", min_value=0.0, step=1000.0, format="%.2f", help="Total capital invested")
                    portfolio_current_value = st.number_input("Current Portfolio Value", min_value=0.0, step=1000.0, format="%.2f", help="Current market value")
                    portfolio_num_positions = st.number_input("Number of Positions", min_value=1, max_value=200, value=10, help="How many stocks/assets in portfolio")
                with col_p2:
                    portfolio_largest_loss = st.text_input("Largest Single Loss", placeholder="e.g., AAPL -₹50,000 (-45%)", help="Your worst performing position")
                    portfolio_largest_gain = st.text_input("Largest Single Gain", placeholder="e.g., TSLA +₹30,000 (+60%)", help="Your best performing position")
                    portfolio_crisis_stocks = st.text_input("Stocks in Crisis (>30% loss)", placeholder="e.g., ADANIPOWER, AARTIIND", help="Comma-separated list")

                portfolio_description = st.text_area("Additional Portfolio Context", height=100, placeholder="Describe your portfolio: sectors, strategy, time horizon, any leveraged positions, margin usage, etc.", help="More context = better analysis")

            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

            if st.button("🔬 ANALYZE PORTFOLIO HEALTH", type="primary", use_container_width=True):
                total_pnl = portfolio_current_value - portfolio_total_invested if portfolio_total_invested > 0 else 0
                total_pnl_pct = (total_pnl / portfolio_total_invested * 100) if portfolio_total_invested > 0 else 0

                img_b64 = None
                if portfolio_file.type != "application/pdf":
                    img_b64 = utils.prepare_image_b64(portfolio_file)

                portfolio_context = _build_portfolio_context(
                    portfolio_total_invested, portfolio_current_value, total_pnl, total_pnl_pct,
                    portfolio_num_positions, portfolio_largest_loss, portfolio_largest_gain,
                    portfolio_crisis_stocks, portfolio_description
                )
                prompt = _build_inline_portfolio_prompt(portfolio_context, total_pnl, total_pnl_pct, portfolio_num_positions,
                                                        portfolio_largest_loss, portfolio_largest_gain, portfolio_crisis_stocks,
                                                        portfolio_description, portfolio_total_invested)
                ticker_val = "PORTFOLIO"
                ready_to_run = True

        st.markdown('</div>', unsafe_allow_html=True)

    # ── MODE: Text Parameters ──
    else:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Case Data Input</div>', unsafe_allow_html=True)
        with st.form("audit_form"):
            col_a, col_b, col_c = st.columns(3)
            with col_a: ticker = st.text_input("Ticker", "SPY")
            with col_b: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
            with col_c: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Tilt"])

            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

            col_d, col_e, col_f = st.columns(3)
            with col_d: entry = st.number_input("Entry", 0.0, step=0.01)
            with col_e: exit_price = st.number_input("Exit", 0.0, step=0.01)
            with col_f: stop = st.number_input("Stop", 0.0, step=0.01)

            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
            notes = st.text_area("Execution Notes", height=120, placeholder="Describe your decision-making process, entry hesitation, stop management...")
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

            if st.form_submit_button("EXECUTE AUDIT", type="primary", use_container_width=True):
                ticker_val = ticker
                prompt = _build_text_param_prompt(ticker, setup_type, emotion, entry, exit_price, stop, notes)
                ready_to_run = True

        st.markdown('</div>', unsafe_allow_html=True)

    # ── EXECUTE + DISPLAY RESULTS ──
    if ready_to_run and config.supabase:
        with st.spinner("🧠 Running Deep Quantitative Analysis..."):
            try:
                if img_b64:
                    raw_response = utils.call_vision_api(prompt, img_b64)
                else:
                    raw_response = utils.call_text_api(prompt)

                report = utils.parse_report(raw_response)

                # ── Hallucination / sanity checks ──
                warning_messages = []
                hallucinated_prices = ['$445', '$435', '$451', '$458', '$440', '$437']
                if any(p in report.get('tech', '') for p in hallucinated_prices):
                    warning_messages.append("⚠️ AI may have hallucinated prices from examples rather than analyzing your actual chart")

                if 'catastrophic' in raw_response.lower() or 'emergency' in raw_response.lower():
                    if report['score'] > 20:
                        report['score'] = max(10, report['score'] // 5)
                        report['overall_grade'] = 'F'
                        report['risk_score'] = min(20, report['risk_score'])
                        warning_messages.append("🚨 Score adjusted for catastrophic loss detected in analysis")

                if report['score'] == 50 and report['entry_quality'] == 50 and report['exit_quality'] == 50:
                    warning_messages.append("⚠️ Analysis may be incomplete. Try a clearer image with visible price levels.")

                for msg in warning_messages:
                    st.warning(msg)

                utils.save_analysis(current_user, report, ticker_val, stored_image_url)
                _display_audit_results(report, ticker_val)

            except Exception as e:
                st.error(f"⚠️ Analysis Failed: {str(e)}")
                st.info("""
                💡 **Troubleshooting Tips:**
                - Ensure chart image is clear with visible price levels
                - Check that the image shows actual trading activity
                - Try a different screenshot with better contrast
                - If problem persists, try the Text Parameters mode instead
                """)


# ─────────────────────────────────────────────────────
# TAB 2: PERFORMANCE METRICS
# ─────────────────────────────────────────────────────
def _render_performance_metrics(current_user):
    if not config.supabase:
        st.warning("Database not configured.")
        return

    hist = config.supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()

    if not hist.data:
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">📊</div>
        <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">No Performance Data Yet</div>
        <div style="font-size: 0.95rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(hist.data)
    df['created_at'] = pd.to_datetime(df['created_at'])

    avg_score = df['score'].mean()
    total_trades = len(df)
    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    top_mistake = pd.Series(all_tags).mode()[0] if all_tags else "None"
    win_rate = len(df[df['score'] > 60]) / len(df) * 100 if len(df) > 0 else 0

    recent_avg = df.head(5)['score'].mean() if len(df) >= 5 else avg_score
    prev_avg = df.iloc[5:10]['score'].mean() if len(df) >= 10 else avg_score
    trend = "↗" if recent_avg > prev_avg else "↘" if recent_avg < prev_avg else "→"

    # ── KPI ROW ──
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card"><div class="kpi-val">{int(avg_score)}</div><div class="kpi-label">Avg Quality Score</div></div>
        <div class="kpi-card"><div class="kpi-val">{int(win_rate)}%</div><div class="kpi-label">Quality Rate</div></div>
        <div class="kpi-card"><div class="kpi-val">{total_trades}</div><div class="kpi-label">Total Audits</div></div>
        <div class="kpi-card"><div class="kpi-val" style="font-size:2.5rem;">{trend}</div><div class="kpi-label">Recent Trend</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── PERFORMANCE EVOLUTION CHART ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Performance Evolution</div>', unsafe_allow_html=True)

    chart_data = df[['created_at', 'score']].sort_values('created_at').reset_index(drop=True)
    chart_data['index'] = range(len(chart_data))

    base = alt.Chart(chart_data).encode(
        x=alt.X('index:Q', axis=alt.Axis(title='Trade Sequence', grid=False, labelColor='#6b7280', titleColor='#9ca3af', labelFontSize=11, titleFontSize=12))
    )

    good_line = alt.Chart(pd.DataFrame({'y': [70]})).mark_rule(strokeDash=[5, 5], color='#10b981', opacity=0.3).encode(y='y:Q')
    bad_line  = alt.Chart(pd.DataFrame({'y': [40]})).mark_rule(strokeDash=[5, 5], color='#ef4444', opacity=0.3).encode(y='y:Q')

    line = base.mark_line(
        color='#3b82f6', strokeWidth=3,
        point=alt.OverlayMarkDef(filled=True, size=80, color='#3b82f6', strokeWidth=2, stroke='#1e40af')
    ).encode(
        y=alt.Y('score:Q', scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(title='Quality Score', grid=True, gridColor='rgba(255,255,255,0.04)', labelColor='#6b7280', titleColor='#9ca3af', labelFontSize=11, titleFontSize=12)),
        tooltip=[alt.Tooltip('index:Q', title='Trade #'), alt.Tooltip('score:Q', title='Score'), alt.Tooltip('created_at:T', title='Date', format='%b %d, %Y')]
    )

    area = base.mark_area(color='#3b82f6', opacity=0.1, line=False).encode(y='score:Q')

    chart = (good_line + bad_line + area + line).properties(height=320).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── TWO-COL: Error Patterns + AI Insights ──
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Error Pattern Analysis</div>', unsafe_allow_html=True)

        if all_tags:
            tag_counts = pd.Series(all_tags).value_counts().head(6).reset_index()
            tag_counts.columns = ['Mistake', 'Count']

            bar_chart = alt.Chart(tag_counts).mark_bar(cornerRadiusEnd=6, height=28).encode(
                x=alt.X('Count:Q', axis=alt.Axis(title=None, grid=False, labelColor='#6b7280', labelFontSize=11)),
                y=alt.Y('Mistake:N', sort='-x', axis=alt.Axis(title=None, labelColor='#e5e7eb', labelFontSize=12, labelPadding=10)),
                color=alt.Color('Count:Q', scale=alt.Scale(scheme='redyellowblue', reverse=True), legend=None),
                tooltip=[alt.Tooltip('Mistake:N', title='Error Type'), alt.Tooltip('Count:Q', title='Occurrences')]
            ).properties(height=280).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')

            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("No error patterns detected yet.")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # AI Insights
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)

        insights = utils.generate_insights(df)
        for insight in insights:
            parts = insight.split(' ', 1)
            emoji   = parts[0] if len(parts) > 0 else ''
            content = parts[1] if len(parts) > 1 else insight

            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.03); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0; margin-bottom: 18px; transition: all 0.3s ease;'>
                <div style='font-size: 1.6rem; margin-bottom: 10px;'>{emoji}</div>
                <div style='font-size: 0.92rem; line-height: 1.7; color: #d1d5db;'>{content}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Score Distribution
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Score Distribution</div>', unsafe_allow_html=True)

        score_ranges = pd.cut(df['score'], bins=[0, 40, 60, 80, 100], labels=['Poor (0-40)', 'Fair (40-60)', 'Good (60-80)', 'Excellent (80-100)'])
        dist_data = score_ranges.value_counts().reset_index()
        dist_data.columns = ['Range', 'Count']

        color_map = {'Poor (0-40)': '#ef4444', 'Fair (40-60)': '#f59e0b', 'Good (60-80)': '#3b82f6', 'Excellent (80-100)': '#10b981'}

        for _, row in dist_data.iterrows():
            range_name = row['Range']
            count = row['Count']
            percentage = (count / len(df)) * 100
            color = color_map.get(range_name, '#6b7280')

            st.markdown(f"""
            <div style='margin-bottom: 22px;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                    <span style='font-size: 0.88rem; color: #9ca3af; font-weight: 600;'>{range_name}</span>
                    <span style='font-size: 0.88rem; color: #e5e7eb; font-family: "JetBrains Mono", monospace;'>{count} ({int(percentage)}%)</span>
                </div>
                <div style='width: 100%; height: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 5px; overflow: hidden;'>
                    <div style='width: {percentage}%; height: 100%; background: {color}; border-radius: 5px; transition: width 0.6s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── RECENT TRADES TABLE ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recent Activity</div>', unsafe_allow_html=True)

    table_df = df.head(10)[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
    table_df.columns = ['Time', 'Asset', 'Score', 'Primary Errors']
    table_df['Primary Errors'] = table_df['Primary Errors'].apply(lambda x: ', '.join(x[:2]) if len(x) > 0 else 'None')

    st.dataframe(
        table_df, use_container_width=True, hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Quality Score", min_value=0, max_value=100, format="%d"),
            "Time": st.column_config.DatetimeColumn("Time", format="MMM DD, HH:mm"),
            "Asset": st.column_config.TextColumn("Asset", width="small")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── DETAILED TRADE HISTORY WITH IMAGES ──
    st.markdown('<div class="glass-panel" style="margin-top: 32px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📜 Trade History Details</div>', unsafe_allow_html=True)

    for i, row in df.head(20).iterrows():
        with st.expander(f"📊 {row['created_at'].strftime('%Y-%m-%d %H:%M')} | {row['ticker']} | Score: {row['score']}/100"):
            if row.get('image_url'):
                st.image(row['image_url'], caption="Original Trade Evidence", width=600)
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Quality Grade:** {row.get('overall_grade', 'N/A')}")
                st.markdown(f"**Entry Quality:** {row.get('entry_quality', 'N/A')}/100")
                st.markdown(f"**Exit Quality:** {row.get('exit_quality', 'N/A')}/100")
                st.markdown(f"**Risk Score:** {row.get('risk_score', 'N/A')}/100")
            with col2:
                tags = row.get('mistake_tags', [])
                st.markdown(f"**Error Tags:** {', '.join(tags)}" if tags else "**Error Tags:** None")

            st.markdown("---")
            if row.get('technical_analysis'):
                st.markdown("**📈 Technical Analysis:**")
                st.write(row['technical_analysis'])
            if row.get('psych_analysis'):
                st.markdown("**🧠 Psychological Analysis:**")
                st.write(row['psych_analysis'])
            if row.get('risk_analysis'):
                st.markdown("**⚠️ Risk Analysis:**")
                st.write(row['risk_analysis'])
            if row.get('fix_action'):
                st.markdown("**🔧 Recommended Fixes:**")
                st.write(row['fix_action'])
            if row.get('strength'):
                st.markdown("**💪 Strengths:**")
                st.write(row['strength'])
            if row.get('critical_error'):
                st.markdown("**🚨 Critical Error:**")
                st.write(row['critical_error'])

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PROMPT BUILDERS  (pure functions — no side effects)
# ============================================================

def _build_chart_vision_prompt(manual_context=""):
    return f"""CRITICAL INSTRUCTIONS: Analyze this trading/portfolio screenshot.

FIRST: IDENTIFY WHAT YOU'RE LOOKING AT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Look carefully at the image and determine:

1. Is this a PORTFOLIO view (multiple stocks listed) or SINGLE CHART?
2. If portfolio: How many stocks/positions are visible?
3. If portfolio: What is the TOTAL P&L shown at top?
4. If portfolio: What is the TOTAL percentage gain/loss?
5. If single chart: Proceed with normal chart analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF THIS IS A PORTFOLIO SCREENSHOT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read the TOTAL/OVERALL P&L at the top (usually labeled "Total P/L", "Unrealised P/L", "Portfolio Value", etc.)

Analyze the PORTFOLIO as a whole, not individual stocks.

Identify:
- Total number of positions
- Largest losses (list top 3-5 by % or amount)
- Any position showing >100% loss (red flag for leverage/options/error)
- Overall portfolio drawdown percentage
- Risk concentration issues

PORTFOLIO OUTPUT FORMAT:

[SCORE] <0-100 based on OVERALL portfolio health>
[OVERALL_GRADE] <F if total loss>20%, D if >10%, C if >5%, etc.>
[ENTRY_QUALITY] <Average entry quality across visible positions>
[EXIT_QUALITY] <Exit discipline assessment based on how losses were managed>
[RISK_SCORE] <0-100 based on PORTFOLIO-LEVEL risk management>
[TAGS] <Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Multiple_Catastrophic_Positions, etc.>

[TECH] PORTFOLIO ANALYSIS: Total P/L: [EXACT total P/L] ([EXACT %]). Number of positions: [count]. Current value: [amount]. Invested: [amount]. Top losses: [list 3-5 worst positions with their %]. Critical observations about portfolio structure and risk concentration.

[PSYCH] PORTFOLIO PSYCHOLOGY: [Analyze the decision-making that led to multiple simultaneous losses. Look for patterns: averaging down? holding losers? FOMO buying? lack of selling discipline?]

[RISK] PORTFOLIO RISK ASSESSMENT: [Analyze diversification, position sizing across portfolio, stop loss discipline, drawdown management, any positions >100% loss (leverage red flags)]

[FIX] PORTFOLIO RECOVERY PLAN:
1. [Immediate crisis management - which positions to close NOW]
2. [Risk reduction strategy - position sizing going forward]
3. [Rehabilitation timeline and rules]

[STRENGTH] [What's working in the portfolio, if anything]
[CRITICAL_ERROR] [The biggest portfolio-level mistake - usually lack of risk management, no stops, or concentration]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF THIS IS A SINGLE CHART (not portfolio):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manual_context}

Look at the TOP RIGHT corner of the trading interface. You will see:
- "P/L: [some amount]" - This is the profit/loss. READ IT EXACTLY.
- "([some percentage])" - This is the percentage. READ IT EXACTLY.

The P/L text is usually in RED (loss) or GREEN (profit). What do you see?

Look at the TOP LEFT. You will see the ticker symbol (e.g., "AAPL", "GLIT", "SPY", etc.). What is it?

Look at the RIGHT SIDE Y-AXIS. You will see price levels. What are the numbers? (e.g., $100, $200, $300?)

SEVERITY ASSESSMENT:

Based on the P/L you read:

IF loss > 50% of account → CATASTROPHIC EMERGENCY (Score: 0-5)
IF loss > 30% of account → SEVERE CRISIS (Score: 5-15)
IF loss > 10% of account → MAJOR PROBLEM (Score: 15-30)
IF loss < 5% of account → Poor trade (Score: 30-50)
IF profit > 0% → Grade normally (Score: 50-100)

SINGLE TRADE OUTPUT FORMAT:

[SCORE] <Use severity guide above>
[OVERALL_GRADE] <F if loss>50%, D if loss>30%, C if loss>10%, etc.>
[ENTRY_QUALITY] <0-100>
[EXIT_QUALITY] <0-100>
[RISK_SCORE] <0-100>
[TAGS] <Based on single trade behavior>

[TECH] Ticker: [EXACT ticker]. P&L: [EXACT P&L] ([EXACT %]). Chart price range: [ACTUAL prices on Y-axis]. [Analysis of price action]
[PSYCH] [Single trade psychology analysis]
[RISK] [Single trade risk analysis]
[FIX] [Specific improvements for this trade]
[STRENGTH] [What went well]
[CRITICAL_ERROR] [Biggest mistake in this trade]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL REMINDERS:
1. FIRST determine if this is PORTFOLIO or SINGLE TRADE
2. If portfolio with multiple losses, this is likely a SEVERE crisis
3. Any position showing >100% loss needs immediate investigation
4. Portfolio losses of >20% = catastrophic failure
5. Use EXACT numbers you see on screen, no hallucinations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def _build_text_param_prompt(ticker, setup_type, emotion, entry, exit_price, stop, notes):
    pnl = exit_price - entry if exit_price > 0 and entry > 0 else 0
    pnl_pct = (pnl / entry * 100) if entry > 0 else 0
    risk = abs(entry - stop) if stop > 0 and entry > 0 else 0
    risk_pct = (risk / entry * 100) if entry > 0 else 0
    reward = abs(exit_price - entry) if exit_price > 0 and entry > 0 else 0
    rr_ratio = (reward / risk) if risk > 0 else 0

    return f"""You are Dr. Michael Steinhardt, legendary hedge fund manager with 45 years experience. Analyze this trade with brutal institutional honesty.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADE DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker: {ticker}
Setup: {setup_type}
Emotional State: {emotion}
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
Stop: ${stop:.2f}

METRICS:
PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)
Risk: ${risk:.2f} ({risk_pct:.2f}%)
R:R Ratio: {rr_ratio:.2f}:1

NOTES: {notes if notes else "No notes"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (EXACT):

[SCORE] <0-100>
[OVERALL_GRADE] <F/D/C/B/A/S-Tier>
[ENTRY_QUALITY] <0-100>
[EXIT_QUALITY] <0-100>
[RISK_SCORE] <0-100>
[TAGS] <comma-separated, 3-5 tags>

[TECH] <3-5 sentences with NUMBERS: entry timing, stop placement, R:R analysis, setup quality>
[PSYCH] <2-4 sentences: emotional state impact, biases detected, discipline assessment>
[RISK] <3-4 sentences with PERCENTAGES: account risk, position size, stop effectiveness>
[FIX] <Exactly 3 improvements:
1. [Specific technical fix]
2. [Specific psychological fix]
3. [Specific risk fix]>
[STRENGTH] <1-2 sentences on what was good>
[CRITICAL_ERROR] <Single biggest mistake>

BE HARSH. USE NUMBERS. BE SPECIFIC."""


def _build_portfolio_context(total_invested, current_value, total_pnl, total_pnl_pct,
                             num_positions, largest_loss, largest_gain, crisis_stocks, description):
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO DATA PROVIDED BY USER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Invested: {total_invested:,.2f}
Current Value: {current_value:,.2f}
Total P&L: {total_pnl:,.2f} ({total_pnl_pct:+.2f}%)
Number of Positions: {num_positions}
Largest Loss: {largest_loss if largest_loss else "Not specified"}
Largest Gain: {largest_gain if largest_gain else "Not specified"}
Crisis Stocks (>30% loss): {crisis_stocks if crisis_stocks else "None specified"}

Additional Context:
{description if description else "No additional context provided"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USE THIS INFORMATION AS GROUND TRUTH. Analyze based on these provided values.
"""


def _build_inline_portfolio_prompt(portfolio_context, total_pnl, total_pnl_pct, num_positions,
                                   largest_loss, largest_gain, crisis_stocks, description, total_invested):
    return f"""You are analyzing a COMPLETE INVESTMENT PORTFOLIO. This is NOT a single trade - this is portfolio-level risk assessment.

{portfolio_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PORTFOLIO HEALTH ASSESSMENT:
   - Overall portfolio P&L and percentage
   - Drawdown severity (current loss from peak)
   - Number of positions (diversification vs. over-diversification)
   - Win/loss ratio across portfolio
   - Concentration risk (any position >10% of portfolio?)

2. RISK MANAGEMENT EVALUATION:
   - Are stop losses in place across positions?
   - Position sizing discipline (should be 1-5% per position)
   - Correlation risk (positions moving together?)
   - Sector concentration
   - Any leveraged/margin positions (red flag)
   - Positions with >50% losses (likely beyond recovery)

3. PORTFOLIO STRUCTURE ANALYSIS:
   - Too many positions? (>20 = likely over-diversified)
   - Too few? (<5 = concentration risk)
   - Balance between growth/value/defensive
   - Sector diversification
   - Market cap diversification

4. CRISIS IDENTIFICATION:
   - Any positions showing >100% loss (leverage/margin emergency)
   - Multiple positions >50% down (poor exit discipline)
   - Portfolio drawdown >30% (severe crisis)
   - Evidence of averaging down into losers
   - Revenge trading patterns

5. PSYCHOLOGICAL ASSESSMENT:
   - Holding losers, cutting winners?
   - Evidence of FOMO buying at tops
   - Lack of selling discipline
   - Emotional attachment to positions
   - Hope-based investing vs. risk management

SEVERITY LEVELS FOR PORTFOLIOS:

Portfolio Drawdown >50%: CATASTROPHIC (Score 0-5)
Portfolio Drawdown 30-50%: SEVERE CRISIS (Score 5-15)
Portfolio Drawdown 20-30%: MAJOR PROBLEM (Score 15-30)
Portfolio Drawdown 10-20%: CONCERNING (Score 30-50)
Portfolio Drawdown 5-10%: MINOR ISSUE (Score 50-70)
Portfolio Drawdown <5%: ACCEPTABLE (Score 70-100)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <0-100 based on portfolio drawdown severity>
[OVERALL_GRADE] <F if >30% loss, D if 20-30%, C if 10-20%, B if 5-10%, A if <5%>
[ENTRY_QUALITY] <Average entry quality across portfolio>
[EXIT_QUALITY] <Exit discipline - are stop losses used? Or holding losers?>
[RISK_SCORE] <0-100 portfolio-level risk management quality>
[TAGS] <Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Too_Many_Positions, Sector_Concentration, Multiple_Losers, No_Exit_Plan, Hope_Based_Investing, etc.>

[TECH] PORTFOLIO TECHNICAL ANALYSIS: Total P&L: {total_pnl:,.2f} ({total_pnl_pct:+.2f}%). Portfolio has {num_positions} positions. [Analyze diversification, concentration, position sizing. List top 3-5 problem positions. Identify sector exposure risks. Comment on portfolio structure.]

[PSYCH] PORTFOLIO PSYCHOLOGY PROFILE: [Analyze the decision-making patterns across the portfolio. Are they holding losers and cutting winners? Evidence of FOMO? Revenge trading? Lack of selling discipline? Emotional attachment to positions? This should be behavioral analysis of their OVERALL trading psychology based on portfolio patterns.]

[RISK] PORTFOLIO RISK ASSESSMENT: [Analyze portfolio-level risk: position sizing discipline, stop loss usage across positions, concentration risk, correlation risk, drawdown management, any leverage/margin red flags. If portfolio loss >30%, this is CATASTROPHIC. If any position shows >100% loss, this is margin/leverage emergency.]

[FIX] PORTFOLIO RESTRUCTURING PLAN:
1. IMMEDIATE ACTIONS: [What needs to happen in next 24-48 hours]
2. SHORT TERM (1-4 weeks): [Which positions to close/reduce, how to implement stops, position sizing rules]
3. LONG TERM (1-6 months): [Portfolio rebuild strategy, education needs, risk management framework, psychological reset]

[STRENGTH] [What's working in the portfolio, if anything]
[CRITICAL_ERROR] [The biggest portfolio-level mistake]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL PORTFOLIO-SPECIFIC RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. If portfolio drawdown >30%: This is CATASTROPHIC portfolio failure, score MUST be 0-10
2. If any position shows >100% loss: LEVERAGE/MARGIN EMERGENCY - flag immediately
3. If >20 positions: Likely over-diversification
4. If multiple positions >50% loss: Exit discipline failure
5. Portfolio analysis is about RISK MANAGEMENT, not individual stock picking
6. Focus on position sizing, diversification, stop losses, and exit discipline
7. Recovery from >30% drawdown typically takes 12-24+ months minimum

REMEMBER: This is PORTFOLIO analysis. Focus on overall risk management, diversification, position sizing discipline, and exit strategy across ALL positions.
"""


# ============================================================
# RESULT DISPLAY HELPERS
# ============================================================

def _display_audit_results(report, ticker_val):
    """Render the animated forensic-audit result cards (shared by all 3 input modes)."""

    if report['score'] >= 80:
        score_color, grade_color = "#10b981", "rgba(16, 185, 129, 0.2)"
    elif report['score'] >= 60:
        score_color, grade_color = "#3b82f6", "rgba(59, 130, 246, 0.2)"
    elif report['score'] >= 40:
        score_color, grade_color = "#f59e0b", "rgba(245, 158, 11, 0.2)"
    else:
        score_color, grade_color = "#ef4444", "rgba(239, 68, 68, 0.2)"

    # ── HEADER ──
    st.markdown(f"""
    <div class="glass-panel animate-scale-in" style="border-top: 3px solid {score_color}; margin-top: 32px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
            <div>
                <div style="color:#6b7280; letter-spacing:3px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 10px; font-weight: 600;">FORENSIC ANALYSIS COMPLETE</div>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="score-value" style="color:{score_color}">{report['score']}</div>
                    <div class="grade-badge" style="background:{grade_color}; color:{score_color};">GRADE: {report.get('overall_grade', 'C')}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div class="ticker-badge">{ticker_val}</div>
                <div style="color:#6b7280; font-size:0.85rem; margin-top: 8px;">{datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── METRICS ──
    st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Performance Breakdown</div>', unsafe_allow_html=True)

    met_col1, met_col2, met_col3 = st.columns(3)
    metrics_data = [
        ("Entry Quality", report.get('entry_quality', 50), met_col1),
        ("Exit Quality", report.get('exit_quality', 50), met_col2),
        ("Risk Management", report.get('risk_score', 50), met_col3)
    ]

    for metric_name, metric_value, col in metrics_data:
        with col:
            met_color = "#10b981" if metric_value >= 80 else "#3b82f6" if metric_value >= 60 else "#f59e0b" if metric_value >= 40 else "#ef4444"
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <div class="metric-circle" style="background: rgba(255,255,255,0.03);">
                    <div style="font-size: 2rem; font-weight: 700; color: {met_color}; font-family: 'JetBrains Mono', monospace;">{metric_value}</div>
                    <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 1px;">/100</div>
                </div>
                <div style="margin-top: 16px; font-size: 0.9rem; font-weight: 600; color: #e5e7eb;">{metric_name}</div>
                <div class="progress-bar-container" style="margin-top: 12px;">
                    <div class="progress-bar" style="width: {metric_value}%; background: linear-gradient(90deg, {met_color}, {met_color}80);"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── TAGS ──
    if report.get('tags'):
        st.markdown('<div class="glass-panel animate-slide-right" style="animation-delay: 0.2s;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏷️ Behavioral Patterns Detected</div>', unsafe_allow_html=True)

        tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px;">'
        for tag in report['tags']:
            if any(w in tag.lower() for w in ['fomo', 'revenge', 'emotional', 'panic', 'tilt']):
                tag_color, tag_bg = "#ef4444", "rgba(239, 68, 68, 0.15)"
            elif any(w in tag.lower() for w in ['disciplined', 'good', 'excellent', 'strong']):
                tag_color, tag_bg = "#10b981", "rgba(16, 185, 129, 0.15)"
            else:
                tag_color, tag_bg = "#f59e0b", "rgba(245, 158, 11, 0.15)"
            tags_html += f'<div style="background: {tag_bg}; border: 1px solid {tag_color}40; padding: 10px 18px; border-radius: 10px; color: {tag_color}; font-weight: 600; font-size: 0.85rem; letter-spacing: 0.5px;">{tag}</div>'
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── RADAR CHART ──
    st.markdown('<div class="glass-panel animate-fade-in" style="animation-delay: 0.3s;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Performance Radar</div>', unsafe_allow_html=True)

    chart_data = pd.DataFrame({
        'Metric': ['Entry\nQuality', 'Exit\nQuality', 'Risk\nManagement', 'Overall\nScore'],
        'Score': [report.get('entry_quality', 50), report.get('exit_quality', 50), report.get('risk_score', 50), report['score']]
    })

    bars = alt.Chart(chart_data).mark_bar(cornerRadiusEnd=8, size=40).encode(
        x=alt.X('Metric:N', axis=alt.Axis(title=None, labelColor='#e5e7eb', labelFontSize=12, labelAngle=0)),
        y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(title='Score', titleColor='#9ca3af', labelColor='#9ca3af', grid=True, gridColor='#ffffff10')),
        color=alt.Color('Score:Q', scale=alt.Scale(domain=[0, 40, 60, 80, 100], range=['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#10b981']), legend=None),
        tooltip=[alt.Tooltip('Metric:N', title='Category'), alt.Tooltip('Score:Q', title='Score')]
    ).properties(height=300).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')

    st.altair_chart(bars, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2-COL DETAIL CARDS ──
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.4s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">⚙️</div><div style="font-size: 1rem; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;">Technical Analysis</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["tech"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.6s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">⚠️</div><div style="font-size: 1rem; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 1px;">Risk Assessment</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["risk"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.5s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">🧠</div><div style="font-size: 1rem; font-weight: 700; color: #8b5cf6; text-transform: uppercase; letter-spacing: 1px;">Psychology Profile</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["psych"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.7s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">🎯</div><div style="font-size: 1rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">Action Plan</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["fix"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── STRENGTH / CRITICAL ERROR ──
    if report.get('strength') != 'N/A' and report.get('strength') != 'Analyzing...':
        st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.8s;">', unsafe_allow_html=True)
        ins_col1, ins_col2 = st.columns(2)

        with ins_col1:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <div style="font-size: 1.5rem;">💪</div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">What Went Well</div>
                </div>
                <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">{report['strength']}</div>
            </div>
            """, unsafe_allow_html=True)

        with ins_col2:
            if report.get('critical_error') != 'N/A' and report.get('critical_error') != 'Analyzing...':
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 20px; border-radius: 0 12px 12px 0;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                        <div style="font-size: 1.5rem;">⛔</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #ef4444; text-transform: uppercase; letter-spacing: 1px;">Critical Error</div>
                    </div>
                    <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">{report['critical_error']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
