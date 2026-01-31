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
# INITIALIZATION (CRITICAL FIX)
# ==========================================
# This ensures "authenticated" key exists before we check it
if hasattr(config, 'init_session'):
    config.init_session()
else:
    # Fallback if config.py wasn't updated
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.session_state["current_page"] = "analyze"

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

    base = alt.Chart(chart_data).encode(x=alt.X('index', title='Trade Sequence'))
    line = base.mark_line(color='#10b981', strokeWidth=3).encode(y=alt.Y('score', title='Score', scale=alt.Scale(domain=[0, 100])))
    points = base.mark_circle(color='white', size=60, opacity=1).encode(y='score', tooltip=['created_at', 'score'])
    
    st.altair_chart((line + points).properties(height=300), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────
# HELPER: PROMPT BUILDERS (Restored for completeness)
# ─────────────────────────────────────────────────────

def _build_chart_vision_prompt(manual_context):
    return f"""
    You are a professional trading psychology coach and technical analyst.
    Analyze this trading chart image.
    {manual_context}
    
    Provide a JSON response with these keys:
    - score (0-100)
    - tags (list of strings like "FOMO", "Impulse", "Good Entry")
    - tech (technical analysis summary)
    - psych (psychological state analysis)
    - risk (risk management analysis)
    - fix (how to improve)
    - strength (what went well)
    - critical_error (fatal mistake if any)
    """

def _build_portfolio_context(inv, curr, pnl, pnl_pct, num, l_loss, l_gain, crisis, desc):
    return f"""
    Portfolio Data:
    - Invested: {inv}
    - Current Value: {curr}
    - P&L: {pnl} ({pnl_pct:.2f}%)
    - Positions: {num}
    - Largest Loss: {l_loss}
    - Largest Gain: {l_gain}
    - Crisis Stocks: {crisis}
    - Description: {desc}
    """

def _build_inline_portfolio_prompt(ctx, pnl, pnl_pct, num, l_loss, l_gain, crisis, desc, inv):
    return f"""
    Analyze this portfolio health based on the image and data provided.
    {ctx}
    
    Provide a JSON response in the same format as a trade audit, but adapted for portfolio health:
    - score (0-100 health score)
    - tags (risk factors like "Over-concentrated", "High Drawdown")
    - tech (structural analysis of portfolio)
    - psych (investor psychology assessment based on holding losers/winners)
    - risk (exposure analysis)
    - fix (restructuring recommendations)
    - strength (what is working)
    """

def _build_text_param_prompt(ticker, setup, emotion, entry, exit_p, stop, notes):
    return f"""
    Analyze this trade:
    Ticker: {ticker}
    Setup: {setup}
    Emotion: {emotion}
    Entry: {entry}
    Exit: {exit_p}
    Stop: {stop}
    Notes: {notes}
    
    Provide JSON response with standard keys (score, tags, tech, psych, risk, fix, strength, critical_error).
    """

def _display_audit_results(report, ticker_val):
    st.markdown(f"### Analysis Result for {ticker_val}")
    st.json(report)
