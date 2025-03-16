from typing import List, Dict

class TokenSummary:
    """Stores processed token data for analysis & reporting."""
    
    def __init__(
        self,
        token_address: str,
        token_name: str,
        token_symbol: str,
        token_decimal: int,
        total_supply: float,
        market_cap_usd: float,
        clog: float,
        clog_percent: float,
        b_count: int,
        s_count: int,
        total_recivedB: float,
        total_recivedS: float,
        total_bundle_balance: float,
        total_sniper_balance: float,
        unsold: float,
        total_ethb: float,
        total_eths: float,
        links: List[str],
        tax: Dict[str, float],
        pairA: str,
        reserveUSD: float,
        tx_count: float,
        totalVolumen: float,
        combined_data: List[List],
        totalVolumen1: str,
        bundle_arrow: str,
        sniper_arrow: str,
        market_cap_arrow: str
    ):
        self.token_address = token_address
        self.token_name = token_name
        self.token_symbol = token_symbol
        self.token_decimal = token_decimal
        self.total_supply = total_supply
        self.market_cap_usd = market_cap_usd
        self.clog = clog
        self.clog_percent = clog_percent
        self.b_count = b_count
        self.s_count = s_count
        self.total_recivedB = total_recivedB
        self.total_recivedS = total_recivedS
        self.total_bundle_balance = total_bundle_balance
        self.total_sniper_balance = total_sniper_balance
        self.unsold = unsold
        self.total_ethb = total_ethb
        self.total_eths = total_eths
        self.links = links
        self.tax = tax
        self.pairA = pairA
        self.reserveUSD = reserveUSD
        self.tx_count = tx_count
        self.totalVolumen = totalVolumen
        self.combined_data = combined_data
        self.totalVolumen1 = totalVolumen1
        self.bundle_arrow = bundle_arrow
        self.sniper_arrow = sniper_arrow
        self.market_cap_arrow = market_cap_arrow

    def __repr__(self):
        """Returns a readable representation of the TokenSummary."""
        return f"TokenSummary({self.token_symbol} | Market Cap: ${self.market_cap_usd:.2f})"
