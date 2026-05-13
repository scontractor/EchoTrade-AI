"""Registry of celebrity investors with their SEC EDGAR CIK numbers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InvestorMeta:
    id: str
    cik: str
    name: str
    style: str
    description: str


INVESTORS: dict[str, InvestorMeta] = {
    m.id: m
    for m in [
        InvestorMeta("berkshire", "1067983", "Berkshire Hathaway (Warren Buffett)", "Concentrated Value", "Long-horizon value investing with moat focus"),
        InvestorMeta("ark_invest", "1649339", "ARK Invest (Cathie Wood)", "Disruptive Innovation", "High-conviction bets on emerging tech platforms"),
        InvestorMeta("pershing_square", "1336528", "Pershing Square (Bill Ackman)", "Concentrated Activist", "Activist positions in high-quality franchises"),
        InvestorMeta("third_point", "1040273", "Third Point (Dan Loeb)", "Event-Driven Activist", "Special situations, spinoffs, and activist campaigns"),
        InvestorMeta("appaloosa", "1418819", "Appaloosa Management (David Tepper)", "Macro/Value", "Macro-driven rotation with distressed expertise"),
        InvestorMeta("soros_fund", "1029160", "Soros Fund Management (George Soros)", "Global Macro", "Reflexivity-based macro positioning"),
        InvestorMeta("baupost", "1061768", "Baupost Group (Seth Klarman)", "Deep Value", "Margin-of-safety deep value and special situations"),
        InvestorMeta("tiger_global", "1167483", "Tiger Global Management (Chase Coleman)", "Growth Equity", "Secular growth compounders globally"),
        InvestorMeta("druckenmiller", "1383312", "Duquesne Family Office (Stanley Druckenmiller)", "Macro/Growth", "Concentrated macro and growth theses"),
        InvestorMeta("renaissance", "1037389", "Renaissance Technologies (Jim Simons)", "Quantitative", "Systematic quant strategies"),
    ]
}
