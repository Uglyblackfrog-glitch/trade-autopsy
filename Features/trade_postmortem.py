def analyze_trade(trade):
    """
    Analyze a trade and return the most likely mistake.

    Expected trade format:
    {
        "entry_price": float,
        "exit_price": float,
        "trade_type": "breakout" | "reversal" | "trend"
    }
    """

    entry_price = trade.get("entry_price")
    exit_price = trade.get("exit_price")
    trade_type = trade.get("trade_type")

    # Default response
    result = {
        "mistake": "Unknown",
        "reason": "Insufficient data to analyze the trade."
    }

    # Rule 1: Late Entry (common breakout mistake)
    if trade_type == "breakout" and exit_price < entry_price:
        result["mistake"] = "Late Entry"
        result["reason"] = (
            "The trade appears to be entered late in a breakout. "
            "Late entries often fail because most of the momentum is already exhausted."
        )

    # Rule 2: Poor Risk–Reward
    elif exit_price < entry_price:
        result["mistake"] = "Poor Risk–Reward"
        result["reason"] = (
            "The trade had an unfavorable risk-to-reward ratio, "
            "where the potential loss was larger than the expected gain."
        )

    # Rule 3: Wrong Market Regime
    elif trade_type == "reversal":
        result["mistake"] = "Wrong Market Regime"
        result["reason"] = (
            "Reversal strategies usually perform poorly in strongly trending markets."
        )

    return result
