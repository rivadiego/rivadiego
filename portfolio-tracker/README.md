# Investment Portfolio Tracker

A professional, lightweight, fully automated Excel workbook for tracking investment portfolio performance across multiple accounts.

**Requirements:** Microsoft 365 (Excel with dynamic arrays: `LET`, `FILTER`, `BYROW`, `LAMBDA`, `SWITCH`).

## Files

| File | Purpose |
|------|---------|
| `Portfolio_Tracker.xlsx` | Ready-to-use workbook |
| `build_workbook.py` | Regenerates the workbook (requires Python 3 + openpyxl) |

## Workbook Structure

| Sheet | Role |
|-------|------|
| **Config** (hidden) | Master list of account names; validation lists; setup instructions |
| **Summary** | Portfolio-wide KPIs — no manual investment data |
| **ISP**, **Barclays**, **Interactive Brokers** | One sheet per account (identical layout) |

## Design Principles

- **Single Master Investment Table** per account (`tbl_<AccountName>`) — one row per investment
- **Common columns first**, then bond-, stock-, ETF-, and cash-specific fields (leave unused fields blank)
- **Config-driven aggregation** — Summary formulas read account names from `tblAccounts` on the hidden Config sheet
- **No VBA, macros, Power Query, pivot tables, or charts**

## Daily Use

1. **Update prices** — change `Current Price` on open positions
2. **Add investments** — insert a new row in the account's Master Investment Table (the table expands automatically)
3. **Close positions** — fill in `Sale Date`, `Sale Price`, and `Sale Fees`
4. **Record income** — enter coupon/dividend/interest amounts and the `Income Date` for period filtering

All KPIs on the account sheet and Summary refresh automatically.

## Filters

Both Summary and each account sheet include two dropdown selectors:

| Selector | Options |
|----------|---------|
| **Period** | Current Month, Current Quarter, Current Year, Previous Year, Since Inception, Custom |
| **Asset Class** | All, Bonds, Stocks, ETFs, Funds, Cash, Other |

When **Custom** is selected, use **Custom Start** and **Custom End** (cells B7 and B8).

### How period filtering works

| KPI | Logic |
|-----|-------|
| Portfolio / account value, unrealized P/L | Positions held at period end (purchased on or before end date; not sold before end date) |
| Invested capital | Purchases with `Purchase Date` in the selected period |
| Realized P/L | Sales with `Sale Date` in the selected period |
| Coupons / dividends / interest | Amounts with `Income Date` in the period (all cumulative amounts included for *Since Inception*) |
| Cash balance | Current market value of rows with `Asset Class = Cash` |

## Adding a New Account

1. Open the **Config** sheet (unhide via *Format → Sheet → Unhide*)
2. Add the new account name as a row in `tblAccounts`
3. Duplicate any existing account worksheet
4. Rename the duplicate to **exactly** match the new account name in Config
5. Clear sample data in the Master Investment Table (keep formula rows)
6. The Summary sheet aggregates the new account automatically — no formula changes required

Table naming convention: `tbl_<AccountName>` with spaces replaced by underscores (e.g. `Fineco` → `tbl_Fineco`, `Interactive Brokers` → `tbl_Interactive_Brokers`).

## Master Investment Table Columns

**Common:** Asset Class, ISIN, Ticker, Security Name, Issuer, Currency, Purchase Date, Purchase Price, Quantity / Nominal, Purchase Fees, Other Purchase Costs, Total Cost Basis*, Current Price, Current Market Value*, Unrealized P/L (€)*, Unrealized P/L (%)*, Sale Date, Sale Price, Sale Fees, Net Sale Proceeds*, Realized P/L (€)*, Realized P/L (%)*, Status*, Notes, Income Date

**Bond:** Coupon %, Coupon Frequency, Coupon Payment Dates, Coupons Received, Maturity Date, Yield to Maturity, Duration

**Stock:** Dividend Yield, Dividends Received, Exchange

**ETF:** Distribution Type, TER, Benchmark Index

**Cash:** Interest Rate, Interest Received

\*Calculated automatically — do not overwrite.

## Regenerating the Workbook

```bash
pip install openpyxl
python build_workbook.py
```

Edit `ACCOUNTS` and `sample_rows()` in `build_workbook.py` to customise default accounts and sample data.

## Notes

- All P/L KPIs are denominated in **EUR**. Enter prices and amounts in EUR (or convert manually before entry).
- Conditional formatting: green = positive P/L, red = negative P/L.
- The workbook includes illustrative sample positions — replace with your own data.
