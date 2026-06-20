# 종목 기본정보 스크래핑
import yfinance as yf, pandas as pd

# yahoo finance의 종목정보에서 
# 1. 기본정보
# 2. 재무정보를 추출해서 제공하느 함수를 작성합니다.

class Stock:
    def __init__(self, symbol: str):
        self.ticker = yf.Ticker(symbol)

    def get_basic_info(self) -> str:
        df = pd.DataFrame.from_dict(self.ticker.info, orient='index', columns=['Value'])
        df = df.loc[['longName','industry','sector','marketCap','sharesOutstanding']]
        df = df.rename_axis('항목')
        return df.to_markdown()

    def get_financial_statement(self) -> str:
        inc = self.ticker.quarterly_income_stmt.loc[
            ['Total Revenue','Gross Profit','Operating Income','Net Income']
        ].rename_axis('항목').rename(columns=lambda x: x.strftime("%Y-%m-%d"))
        
        bal = self.ticker.quarterly_balance_sheet.loc[
            ['Total Assets','Total Liabilities Net Minority Interest','Stockholders Equity']
        ].rename_axis('항목').rename(columns=lambda x: x.strftime("%Y-%m-%d"))
        
        cfs = self.ticker.quarterly_cash_flow.loc[
            ['Operating Cash Flow','Investing Cash Flow','Financing Cash Flow']
        ].rename_axis('항목').rename(columns=lambda x: x.strftime("%Y-%m-%d"))

        return (
            "### Quarterly Income Statement\n" + inc.to_markdown() + "\n\n" +
            "### Quarterly Balance Sheet\n"  + bal.to_markdown() + "\n\n" +
            "### Quarterly Cash Flow\n"      + cfs.to_markdown()
        )