import streamlit as st
import requests
from datetime import datetime
import config
import utils


def render_portfolio_page(current_user):
    """Render the full Portfolio Health Analyzer page."""

    # ── HERO BANNER ──
    st.markdown('<div class="glass-panel" style="text-align: center; padding: 60px 40px; margin-bottom: 40px;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 3.5rem; margin-bottom: 20px;">📊</div>
    <div style="font-size: 2rem; font-weight: 700; margin-bottom: 16px; background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Portfolio Health Analyzer
    </div>
    <div style="font-size: 1rem; color: #9ca3af; max-width: 700px; margin: 0 auto; line-height: 1.7;">
        Comprehensive analysis of your entire investment portfolio. Upload screenshots or PDFs, get detailed risk assessment, concentration analysis, and restructuring recommendations.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── UPLOAD SECTION ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📂 Upload Portfolio Data</div>', unsafe_allow_html=True)

    col_upload_left, col_upload_right = st.columns([1.2, 1])

    with col_upload_left:
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <div style="font-size: 1.1rem; font-weight: 600; color: #e5e7eb; margin-bottom: 12px;">📸 Upload Portfolio Screenshot or PDF</div>
            <div style="font-size: 0.9rem; color: #9ca3af; line-height: 1.6;">
                Upload screenshots from your broker app, portfolio tracker, or export PDFs. We support all major brokers including Zerodha, Groww, Upstox, Angel One, etc.
            </div>
        </div>
        """, unsafe_allow_html=True)

        portfolio_file = st.file_uploader(
            "Upload Portfolio Screenshot or PDF",
            type=["png", "jpg", "jpeg", "pdf"],
            label_visibility="collapsed",
            key="portfolio_upload_main",
            help="Upload your full portfolio view showing all positions and P&L"
        )

        if portfolio_file:
            if portfolio_file.type == "application/pdf":
                st.success("✅ PDF uploaded successfully!")
                st.info("📄 PDF analysis extracts: Total P&L, Position count, Individual holdings")
            else:
                st.success("✅ Image uploaded successfully!")
                st.markdown('<div style="margin-top: 20px; border-radius: 12px; overflow: hidden; border: 2px solid rgba(16, 185, 129, 0.3);">', unsafe_allow_html=True)
                st.image(portfolio_file, use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    with col_upload_right:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0; margin-bottom: 20px;">
            <div style="font-size: 1rem; font-weight: 600; color: #10b981; margin-bottom: 12px;">💡 What We Analyze</div>
            <div style="font-size: 0.85rem; color: #d1d5db; line-height: 1.7;">
                • Overall portfolio P&L and drawdown<br>
                • Position sizing discipline<br>
                • Diversification vs concentration<br>
                • Stop loss implementation<br>
                • Leverage/margin risks<br>
                • Sector exposure analysis<br>
                • Crisis position identification<br>
                • Recovery timeline estimation
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 20px; border-radius: 0 12px 12px 0;">
            <div style="font-size: 1rem; font-weight: 600; color: #f59e0b; margin-bottom: 12px;">⚠️ Manual Input Recommended</div>
            <div style="font-size: 0.85rem; color: #d1d5db; line-height: 1.7;">
                For best accuracy, provide your portfolio data manually below. AI image analysis can miss details in complex portfolio views.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── MANUAL INPUT FORM ──
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 Manual Portfolio Data (Highly Recommended)</div>', unsafe_allow_html=True)

    with st.form("portfolio_input_form"):
        st.markdown("**Core Portfolio Metrics**")
        col_m1, col_m2, col_m3 = st.columns(3)

        with col_m1:
            portfolio_total_invested = st.number_input("Total Invested (₹)", min_value=0.0, step=10000.0, format="%.2f", help="Total capital you've invested across all positions")
        with col_m2:
            portfolio_current_value = st.number_input("Current Value (₹)", min_value=0.0, step=10000.0, format="%.2f", help="Current market value of your entire portfolio")
        with col_m3:
            portfolio_num_positions = st.number_input("Number of Positions", min_value=1, max_value=500, value=10, help="How many different stocks/assets you hold")

        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        st.markdown("**Position Details (Optional but Helpful)**")

        col_m4, col_m5 = st.columns(2)
        with col_m4:
            portfolio_largest_loss = st.text_input("Worst Position", placeholder="e.g., ADANIPOWER -₹45,000 (-277%)", help="Your biggest losing position with amount and %")
            portfolio_largest_gain = st.text_input("Best Position", placeholder="e.g., TCS +₹85,000 (+35%)", help="Your biggest winning position with amount and %")
        with col_m5:
            portfolio_crisis_stocks = st.text_input("Crisis Positions (>30% loss)", placeholder="e.g., ADANIPOWER, AARTIIND, YESBANK", help="List stocks with major losses, comma-separated")
            portfolio_top_holdings = st.text_input("Top 3 Holdings by %", placeholder="e.g., RELIANCE 15%, INFY 12%, TCS 10%", help="Your largest positions by portfolio weight")

        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        st.markdown("**Additional Context**")

        col_m6, col_m7 = st.columns(2)
        with col_m6:
            portfolio_sectors = st.text_input("Main Sectors", placeholder="e.g., IT 40%, Banking 25%, Pharma 15%", help="Your sector allocation if known")
            portfolio_strategy = st.selectbox("Investment Approach", ["Long-term investing", "Swing trading", "Day trading", "Mixed approach", "No clear strategy"], help="How do you approach the market?")
        with col_m7:
            portfolio_time_horizon = st.selectbox("Time Horizon", ["< 6 months", "6-12 months", "1-2 years", "2-5 years", "5+ years", "No specific timeline"], help="How long do you plan to hold?")
            portfolio_leverage = st.selectbox("Leverage/Margin Usage", ["No leverage (cash only)", "Margin < 25%", "Margin 25-50%", "Margin > 50%", "Futures/Options", "Not sure"], help="Are you trading with borrowed money?")

        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

        portfolio_description = st.text_area(
            "Additional Context (Very Important!)",
            height=120,
            placeholder="""Describe your situation:
• How did you build this portfolio?
• Any specific problems you're facing?
• Previous trading experience?
• Risk management practices?
• Stop loss usage?
• Why are you seeking analysis?""",
            help="More context = better, more personalized analysis"
        )

        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("🔬 RUN COMPREHENSIVE PORTFOLIO ANALYSIS", type="primary", use_container_width=True)

        if submitted:
            if portfolio_total_invested == 0 or portfolio_current_value == 0:
                st.error("⚠️ Please enter both Total Invested and Current Value for analysis.")
            else:
                _run_portfolio_analysis(
                    current_user, portfolio_file,
                    portfolio_total_invested, portfolio_current_value, portfolio_num_positions,
                    portfolio_largest_loss, portfolio_largest_gain, portfolio_crisis_stocks,
                    portfolio_top_holdings, portfolio_sectors, portfolio_strategy,
                    portfolio_time_horizon, portfolio_leverage, portfolio_description
                )

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────
# INTERNAL: run the analysis + display results
# ─────────────────────────────────────────────────────

def _run_portfolio_analysis(
    current_user, portfolio_file,
    total_invested, current_value, num_positions,
    largest_loss, largest_gain, crisis_stocks,
    top_holdings, sectors, strategy, time_horizon, leverage, description
):
    total_pnl = current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # ── Prepare image ──
    img_b64 = None
    stored_portfolio_image_url = None
    if portfolio_file and portfolio_file.type != "application/pdf":
        try:
            with st.spinner("Uploading portfolio evidence to secure vault..."):
                stored_portfolio_image_url = utils.upload_image_to_supabase(portfolio_file)
            img_b64 = utils.prepare_image_b64(portfolio_file)
        except:
            st.warning("Could not process image, using manual data only")

    # ── Build prompt ──
    portfolio_context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPREHENSIVE PORTFOLIO DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PORTFOLIO OVERVIEW:
Total Invested: ₹{total_invested:,.2f}
Current Value: ₹{current_value:,.2f}
Total P&L: ₹{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)
Number of Positions: {num_positions}

POSITION DETAILS:
Worst Position: {largest_loss if largest_loss else "Not provided"}
Best Position: {largest_gain if largest_gain else "Not provided"}
Crisis Stocks: {crisis_stocks if crisis_stocks else "None listed"}
Top Holdings: {top_holdings if top_holdings else "Not provided"}

PORTFOLIO STRUCTURE:
Sector Allocation: {sectors if sectors else "Not provided"}
Strategy: {strategy}
Time Horizon: {time_horizon}
Leverage Usage: {leverage}

TRADER CONTEXT:
{description if description else "No additional context provided"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THIS IS GROUND TRUTH DATA. Analyze based on these exact values.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    portfolio_prompt = f"""You are a Senior Portfolio Manager with 30+ years experience managing institutional portfolios. You specialize in retail portfolio risk assessment and restructuring.

{portfolio_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPREHENSIVE PORTFOLIO ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PORTFOLIO HEALTH ASSESSMENT:
   Analyze the overall portfolio drawdown of {total_pnl_pct:.2f}%
   - Is this acceptable, concerning, or catastrophic?
   - Current value vs invested (recovery difficulty)
   - Number of positions ({num_positions}) - over/under diversified?
   - Win/loss distribution based on provided positions

2. RISK MANAGEMENT DEEP DIVE:
   - Position sizing: With {num_positions} positions, average should be ~{100/num_positions if num_positions > 0 else 0:.1f}% each
   - Concentration risk: Top holdings analysis
   - Stop loss discipline: Evidence from crisis positions
   - Leverage assessment: {leverage} - flag if dangerous
   - Sector concentration: {sectors if sectors else "Unknown"} - any overexposure?

3. CRISIS IDENTIFICATION:
   Crisis Positions: {crisis_stocks if crisis_stocks else "None specified"}
   Worst Position: {largest_loss if largest_loss else "Not provided"}
   - Any positions >100% loss? (leverage emergency)
   - Multiple positions >50% loss? (exit discipline failure)
   - Recovery likelihood for crisis positions

4. BEHAVIORAL PATTERN ANALYSIS:
   Strategy: {strategy}
   Time Horizon: {time_horizon}
   Context: {description[:200] if description else "Minimal"}
   - Holding losers too long?
   - FOMO buying at peaks?
   - Averaging down mistakes?
   - Emotional vs. systematic approach?

5. PORTFOLIO STRUCTURE EVALUATION:
   - {num_positions} positions: Is this manageable?
   - Sector allocation quality
   - Market cap diversification
   - Correlation risks
   - Appropriate for stated time horizon?

SEVERITY CLASSIFICATION (CRITICAL):

Drawdown >50%: CATASTROPHIC EMERGENCY (Score: 0-5, Grade: F)
Drawdown 30-50%: SEVERE CRISIS (Score: 5-15, Grade: F)
Drawdown 20-30%: MAJOR PROBLEM (Score: 15-30, Grade: D)
Drawdown 10-20%: CONCERNING (Score: 30-50, Grade: C)
Drawdown 5-10%: MINOR ISSUE (Score: 50-70, Grade: B)
Drawdown 0-5%: ACCEPTABLE (Score: 70-85, Grade: A)
Profit >0%: GOOD (Score: 85-100, Grade: A/S-Tier)

SPECIAL CONSIDERATIONS:
- Leverage usage increases severity by one level
- >20 positions increases severity (over-diversification)
- Multiple crisis stocks increases severity
- No clear strategy increases severity

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <0-100 based on drawdown and risk factors>

[OVERALL_GRADE] <F/D/C/B/A/S-Tier based on severity table>

[ENTRY_QUALITY] <0-100: Average entry timing quality across portfolio>

[EXIT_QUALITY] <0-100: Exit discipline - stop loss usage, holding losers?>

[RISK_SCORE] <0-100: Portfolio risk management quality - MUST be 0-10 if crisis>

[TAGS] <Choose 5-8 relevant tags: Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Over_Diversified, Sector_Concentration, Multiple_Losers, Exit_Failure, Hope_Trading, Good_Diversification, Disciplined_Stops, etc.>

[TECH] PORTFOLIO STRUCTURE ANALYSIS:

Portfolio Metrics: ₹{total_invested:,.0f} invested → ₹{current_value:,.0f} current = ₹{total_pnl:,.0f} ({total_pnl_pct:+.2f}%)

Position Count Analysis: {num_positions} positions. [Is this optimal? Too many to manage? Too few for diversification?]

Top Holdings Impact: {top_holdings if top_holdings else "Not provided"}. [Concentration risk assessment]

Sector Exposure: {sectors if sectors else "Unknown"}. [Any dangerous concentration?]

Crisis Positions: {crisis_stocks if crisis_stocks else "None listed"}. [Recovery likelihood? Should close?]

[Provide specific technical commentary on portfolio construction, position sizing, diversification quality, and structural issues]

[PSYCH] BEHAVIORAL PORTFOLIO PSYCHOLOGY:

Trading Approach: {strategy} with {time_horizon} horizon. [Is behavior aligned with stated goals?]

Decision-Making Patterns: [Based on crisis positions, worst loss, and description, analyze: Are they holding losers too long? Cutting winners early? FOMO buying? Revenge trading? Averaging down? Emotional attachment?]

Discipline Assessment: [Evidence of trading plan? Stop loss usage? Position sizing rules? Or hope-based investing?]

{leverage} - [If using leverage, address the psychological impact and risk]

[Analyze the trader's MINDSET and behavioral patterns visible in portfolio structure]

[RISK] COMPREHENSIVE RISK ASSESSMENT:

Portfolio Drawdown: {total_pnl_pct:.2f}% = [CATASTROPHIC/SEVERE/MAJOR/CONCERNING/MINOR/ACCEPTABLE]

Position Sizing: Avg {100/num_positions if num_positions > 0 else 0:.1f}% per position with {num_positions} holdings. [Assessment of sizing discipline]

Leverage Risk: {leverage}. [If using margin/futures/options, this is RED FLAG - quantify danger]

Concentration Risk: [Based on top holdings and sector allocation, assess if too concentrated]

Stop Loss Implementation: [Based on crisis positions and description, are stops used? If not, bleeding continues]

Recovery Mathematics: To recover {abs(total_pnl_pct):.1f}% loss requires {abs(total_pnl_pct)/(100+total_pnl_pct)*100 if total_pnl_pct < 0 else 0:.1f}% gain. Timeline: [Estimate 6mo/12mo/18mo/24mo+]

[Provide specific risk metrics and quantified danger assessment]

[FIX] PORTFOLIO RESTRUCTURING ROADMAP:

IMMEDIATE (Next 24-48 hours):
1. [Most urgent action - usually investigate leverage, close worst positions, or stop new trades]
2. [Second priority - typically implement stops or hedge risks]
3. [Third priority - usually calculate actual losses and set recovery plan]

SHORT TERM (1-4 weeks):
1. [Position reduction/consolidation - specific numbers]
2. [Stop loss implementation - specific % levels]
3. [Sector rebalancing if needed]
4. [Close beyond-recovery positions]

LONG TERM (1-6 months):
1. [Complete portfolio restructuring strategy]
2. [Education/skill development needs]
3. [New risk management framework]
4. [Psychology reset and habit building]

Position Sizing Rule Going Forward: Risk no more than 1-2% per position (₹{total_invested*0.02:,.0f} max per trade)

[STRENGTH] [Find something positive even in disaster: diversification across sectors? at least some winners? closed positions before -100%? still has capital to recover?]

[CRITICAL_ERROR] [The single biggest portfolio-level mistake: usually no stops, concentration, leverage, or holding losers. Be specific with numbers/names]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES:
- If drawdown >30%, score MUST be 0-15, grade F
- If leverage + crisis, increase severity dramatically
- Be specific with numbers from provided data
- Recovery timeline must be realistic based on drawdown
- If crisis positions listed, address them specifically by name
- Focus on PORTFOLIO MANAGEMENT not stock picking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # ── Call AI ──
    with st.spinner("🔬 Running Deep Portfolio Analysis... This may take 30-60 seconds..."):
        try:
            if img_b64:
                messages = [{"role": "user", "content": [{"type": "text", "text": portfolio_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}]}]
            else:
                messages = [{"role": "user", "content": [{"type": "text", "text": portfolio_prompt}]}]

            payload = {
                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.3
            }
            headers = {
                "Authorization": f"Bearer {config.HF_TOKEN}",
                "Content-Type": "application/json"
            }

            res = requests.post(config.API_URL, headers=headers, json=payload, timeout=90)

            if res.status_code == 200:
                raw_response = res.json()["choices"][0]["message"]["content"]
                report = utils.parse_report(raw_response)
                utils.save_analysis(current_user, report, "PORTFOLIO", stored_portfolio_image_url)
                _display_portfolio_results(report, total_pnl_pct)
                st.success("✅ Portfolio analysis complete! Review recommendations above.")
            else:
                st.error(f"API Error: {res.status_code} - {res.text[:200]}")

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.info("Try providing more manual data or uploading a clearer screenshot.")


def _display_portfolio_results(report, total_pnl_pct):
    """Render the animated results cards for a portfolio analysis."""

    # Determine theme colors from score
    if report['score'] >= 80:
        score_color = "#10b981"
        grade_color = "rgba(16, 185, 129, 0.2)"
    elif report['score'] >= 60:
        score_color = "#3b82f6"
        grade_color = "rgba(59, 130, 246, 0.2)"
    elif report['score'] >= 40:
        score_color = "#f59e0b"
        grade_color = "rgba(245, 158, 11, 0.2)"
    else:
        score_color = "#ef4444"
        grade_color = "rgba(239, 68, 68, 0.2)"

    # ── HEADER ──
    st.markdown(f"""
    <div class="glass-panel animate-scale-in" style="border-top: 3px solid {score_color}; margin-top: 32px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
            <div>
                <div style="color:#6b7280; letter-spacing:3px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 10px; font-weight: 600;">PORTFOLIO ANALYSIS COMPLETE</div>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="score-value" style="color:{score_color}">{report['score']}</div>
                    <div class="grade-badge" style="background:{grade_color}; color:{score_color};">
                        GRADE: {report.get('overall_grade', 'C')}
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <div class="ticker-badge">PORTFOLIO</div>
                <div style="color:#6b7280; font-size:0.85rem; margin-top: 8px;">{datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
                <div style="color: {score_color}; font-size:1.1rem; font-weight: 700; margin-top: 8px; font-family: 'JetBrains Mono', monospace;">
                    {total_pnl_pct:+.2f}%
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── METRICS ROW ──
    st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Portfolio Health Metrics</div>', unsafe_allow_html=True)

    met_col1, met_col2, met_col3 = st.columns(3)
    metrics_data = [
        ("Position Entry Quality", report.get('entry_quality', 50), met_col1),
        ("Exit Discipline", report.get('exit_quality', 50), met_col2),
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
        st.markdown('<div class="section-title">🏷️ Portfolio Risk Factors</div>', unsafe_allow_html=True)

        tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px;">'
        for tag in report['tags']:
            if any(w in tag.lower() for w in ['crisis', 'catastrophic', 'emergency', 'overleveraged', 'failure']):
                tag_color, tag_bg = "#ef4444", "rgba(239, 68, 68, 0.15)"
            elif any(w in tag.lower() for w in ['good', 'disciplined', 'strong', 'excellent']):
                tag_color, tag_bg = "#10b981", "rgba(16, 185, 129, 0.15)"
            else:
                tag_color, tag_bg = "#f59e0b", "rgba(245, 158, 11, 0.15)"
            tags_html += f'<div style="background: {tag_bg}; border: 1px solid {tag_color}40; padding: 10px 18px; border-radius: 10px; color: {tag_color}; font-weight: 600; font-size: 0.85rem; letter-spacing: 0.5px;">{tag}</div>'
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── DETAILED ANALYSIS (2-col) ──
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.4s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">📊</div><div style="font-size: 1rem; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;">Portfolio Structure</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["tech"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.6s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">⚠️</div><div style="font-size: 1rem; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 1px;">Risk Analysis</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["risk"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.5s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">🧠</div><div style="font-size: 1rem; font-weight: 700; color: #8b5cf6; text-transform: uppercase; letter-spacing: 1px;">Behavioral Analysis</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["psych"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.7s;">', unsafe_allow_html=True)
        st.markdown('<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="font-size: 1.8rem;">🎯</div><div style="font-size: 1rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">Recovery Roadmap</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">{report["fix"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── STRENGTH / CRITICAL ERROR ──
    if report.get('strength') or report.get('critical_error'):
        st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.8s;">', unsafe_allow_html=True)
        ins_col1, ins_col2 = st.columns(2)

        with ins_col1:
            if report.get('strength'):
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                        <div style="font-size: 1.5rem;">💪</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">What's Working</div>
                    </div>
                    <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">{report['strength']}</div>
                </div>
                """, unsafe_allow_html=True)

        with ins_col2:
            if report.get('critical_error'):
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 20px; border-radius: 0 12px 12px 0;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                        <div style="font-size: 1.5rem;">⛔</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #ef4444; text-transform: uppercase; letter-spacing: 1px;">Biggest Problem</div>
                    </div>
                    <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">{report['critical_error']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
