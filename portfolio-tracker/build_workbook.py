#!/usr/bin/env python3
"""Build a professional Excel investment portfolio tracker workbook."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

OUTPUT = Path(__file__).resolve().parent / "Portfolio_Tracker.xlsx"

ACCOUNTS = ["ISP", "Barclays", "Interactive Brokers"]

PERIOD_OPTIONS = [
    "Current Month",
    "Current Quarter",
    "Current Year",
    "Previous Year",
    "Since Inception",
    "Custom",
]

ASSET_CLASS_OPTIONS = ["All", "Bonds", "Stocks", "ETFs", "Funds", "Cash", "Other"]

# Master Investment Table columns (single source of truth per account sheet)
MASTER_COLUMNS = [
    # Common
    "Asset Class",
    "ISIN",
    "Ticker",
    "Security Name",
    "Issuer",
    "Currency",
    "Purchase Date",
    "Purchase Price",
    "Quantity / Nominal",
    "Purchase Fees",
    "Other Purchase Costs",
    "Total Cost Basis",
    "Current Price",
    "Current Market Value",
    "Unrealized P/L (€)",
    "Unrealized P/L (%)",
    "Sale Date",
    "Sale Price",
    "Sale Fees",
    "Net Sale Proceeds",
    "Realized P/L (€)",
    "Realized P/L (%)",
    "Status",
    "Notes",
    "Income Date",
    # Bond
    "Coupon %",
    "Coupon Frequency",
    "Coupon Payment Dates",
    "Coupons Received",
    "Maturity Date",
    "Yield to Maturity",
    "Duration",
    # Stock
    "Dividend Yield",
    "Dividends Received",
    "Exchange",
    # ETF
    "Distribution Type",
    "TER",
    "Benchmark Index",
    # Cash
    "Interest Rate",
    "Interest Received",
]

CONFIG_TABLE = "tblAccounts"


def table_name(account: str) -> str:
    """Workbook-unique Excel Table name derived from the account name."""
    return "tbl_" + account.replace(" ", "_")

# Layout constants (shared across Summary and account sheets)
SEL_PERIOD = "B5"
SEL_ASSET = "B6"
SEL_CUSTOM_START = "B7"
SEL_CUSTOM_END = "B8"

KPI_START_ROW = 11
TABLE_HEADER_ROW = 24
TABLE_DATA_START = 25

# Styling
FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="1F3864")
FONT_SECTION = Font(name="Calibri", size=11, bold=True, color="1F3864")
FONT_LABEL = Font(name="Calibri", size=10, color="404040")
FONT_VALUE = Font(name="Calibri", size=10, bold=True, color="1F3864")
FONT_KPI_LABEL = Font(name="Calibri", size=10, color="595959")
FONT_TABLE_HEADER = Font(name="Calibri", size=9, bold=True, color="FFFFFF")

FILL_HEADER = PatternFill("solid", fgColor="1F3864")
FILL_SECTION = PatternFill("solid", fgColor="EEF2F7")
FILL_INPUT = PatternFill("solid", fgColor="FFFDF5")

BORDER_THIN = Border(
    left=Side(style="thin", color="D0D7DE"),
    right=Side(style="thin", color="D0D7DE"),
    top=Side(style="thin", color="D0D7DE"),
    bottom=Side(style="thin", color="D0D7DE"),
)

EUR_FORMAT = '#,##0.00" €"'
PCT_FORMAT = "0.00%"
DATE_FORMAT = "dd/mm/yyyy"
INT_FORMAT = "#,##0"

KPI_DEFS = [
    ("Current Portfolio Value", "value", EUR_FORMAT),
    ("Total Invested Capital", "value", EUR_FORMAT),
    ("Unrealized P/L (€)", "signed", EUR_FORMAT),
    ("Unrealized P/L (%)", "signed_pct", PCT_FORMAT),
    ("Realized P/L (€)", "signed", EUR_FORMAT),
    ("Realized P/L (%)", "signed_pct", PCT_FORMAT),
    ("Total Cash", "value", EUR_FORMAT),
    ("Coupons Received", "value", EUR_FORMAT),
    ("Dividends Received", "value", EUR_FORMAT),
    ("Number of Open Positions", "count", INT_FORMAT),
    ("Number of Closed Positions", "count", INT_FORMAT),
]

ACCOUNT_KPI_LABELS = [
    ("Current Account Value", "portfolio_value"),
    ("Invested Capital", "invested_capital"),
    ("Unrealized P/L (€)", "unrealized_eur"),
    ("Unrealized P/L (%)", "unrealized_pct"),
    ("Realized P/L (€)", "realized_eur"),
    ("Realized P/L (%)", "realized_pct"),
    ("Cash Balance", "cash_balance"),
    ("Coupons Received", "coupons"),
    ("Dividends Received", "dividends"),
    ("Open Positions", "open_count"),
    ("Closed Positions", "closed_count"),
]


def col_letter(index: int) -> str:
    return get_column_letter(index)


def table_col(account: str, name: str) -> str:
    return f"{table_name(account)}[{name}]"


def period_bounds_let(prefix: str = "") -> str:
    """Period and asset-class selector bindings shared by summary formulas."""
    p = prefix
    return (
        f"pSel,{p}${SEL_PERIOD},"
        f"acSel,{p}${SEL_ASSET},"
        f"cStart,{p}${SEL_CUSTOM_START},"
        f"cEnd,{p}${SEL_CUSTOM_END},"
        f"pStart,SWITCH(pSel,\"Current Month\",DATE(YEAR(TODAY()),MONTH(TODAY()),1),"
        f"\"Current Quarter\",DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+1,1),"
        f"\"Current Year\",DATE(YEAR(TODAY()),1,1),"
        f"\"Previous Year\",DATE(YEAR(TODAY())-1,1,1),"
        f"\"Since Inception\",DATE(1900,1,1),"
        f"\"Custom\",cStart,DATE(1900,1,1)),"
        f"pEnd,SWITCH(pSel,\"Current Month\",EOMONTH(TODAY(),0),"
        f"\"Current Quarter\",EOMONTH(DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+3,1),0),"
        f"\"Current Year\",DATE(YEAR(TODAY()),12,31),"
        f"\"Previous Year\",DATE(YEAR(TODAY())-1,12,31),"
        f"\"Since Inception\",DATE(9999,12,31),"
        f"\"Custom\",cEnd,DATE(9999,12,31))"
    )


def period_let(table: str, prefix: str = "") -> str:
    """Return LET bindings for period boundaries referencing selector cells."""
    return (
        f"{period_bounds_let(prefix)},"
        f"acOK,LAMBDA(c,OR(acSel=\"All\",acSel=c)),"
        f"heldAtEnd,LAMBDA(pd,sd,(pd<>\"\")*(pd<=pEnd)*((sd=\"\")+(sd>pEnd))),"
        f"inPeriod,LAMBDA(dt,(dt<>\"\")*(dt>=pStart)*(dt<=pEnd)),"
        f"incomeInPeriod,LAMBDA(amtCol,IF(pSel=\"Since Inception\","
        f"SUM(FILTER(amtCol,(acSel=\"All\")+({table}[Asset Class]=acSel))),"
        f"SUM(FILTER(amtCol,((acSel=\"All\")+({table}[Asset Class]=acSel))*"
        f"({table}[Income Date]>=pStart)*({table}[Income Date]<=pEnd)*"
        f"({table}[Income Date]<>\"\")))))"
    )


def account_kpi_formula(account: str, metric: str) -> str:
    """Build LET formula for a single account KPI referencing the local master table."""
    t = table_name(account)
    p = period_let(t)

    formulas = {
        "portfolio_value": (
            f"IFERROR(SUM(FILTER({t}[Current Market Value],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)"
        ),
        "invested_capital": (
            f"IFERROR(SUM(FILTER({t}[Total Cost Basis],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"inPeriod({t}[Purchase Date]))),0)"
        ),
        "unrealized_eur": (
            f"IFERROR(SUM(FILTER({t}[Unrealized P/L (€)],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)"
        ),
        "unrealized_pct": (
            f"IFERROR(IF(SUM(FILTER({t}[Total Cost Basis],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date])))=0,0,"
            f"SUM(FILTER({t}[Unrealized P/L (€)],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date])))"
            f"/SUM(FILTER({t}[Total Cost Basis],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date])))),0)"
        ),
        "realized_eur": (
            f"IFERROR(SUM(FILTER({t}[Realized P/L (€)],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"inPeriod({t}[Sale Date]))),0)"
        ),
        "realized_pct": (
            f"IFERROR(IF(SUM(FILTER({t}[Total Cost Basis],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"inPeriod({t}[Sale Date])))=0,0,"
            f"SUM(FILTER({t}[Realized P/L (€)],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"inPeriod({t}[Sale Date])))"
            f"/SUM(FILTER({t}[Total Cost Basis],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"inPeriod({t}[Sale Date])))),0)"
        ),
        "cash_balance": (
            f"IFERROR(SUM(FILTER({t}[Current Market Value],"
            f"({t}[Asset Class]=\"Cash\")*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date])),0)"
        ),
        "coupons": f"IFERROR(incomeInPeriod({t}[Coupons Received]),0)",
        "dividends": (
            f"IFERROR(incomeInPeriod({t}[Dividends Received])"
            f"+incomeInPeriod({t}[Interest Received]),0)"
        ),
        "open_count": (
            f"IFERROR(ROWS(FILTER({t}[Asset Class],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"({t}[Status]=\"Open\")*"
            f"heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)"
        ),
        "closed_count": (
            f"IFERROR(ROWS(FILTER({t}[Asset Class],"
            f"((acSel=\"All\")+({t}[Asset Class]=acSel))*"
            f"({t}[Status]=\"Closed\")*"
            f"inPeriod({t}[Sale Date]))),0)"
        ),
    }
    body = formulas[metric]
    return f"=LET({p},{body})"


def summary_kpi_formula(metric: str) -> str:
    """Build LET formula aggregating KPIs across accounts listed in Config."""
    acct_range = f"{CONFIG_TABLE}[Account Name]"

    def tbl_ref(col: str) -> str:
        return f"INDIRECT(\"'\"&acct&\"'!tbl_\"&SUBSTITUTE(acct,\" \",\"_\")&\"[{col}]\")"

    def acct_sum(range_suffix: str, extra_filter: str) -> str:
        return (
            f"SUM(BYROW({acct_range},LAMBDA(acct,"
            f"IFERROR(SUM(FILTER({tbl_ref(range_suffix)},{extra_filter})),0))))"
        )

    def acct_rows(range_suffix: str, extra_filter: str) -> str:
        return (
            f"SUM(BYROW({acct_range},LAMBDA(acct,"
            f"IFERROR(ROWS(FILTER({tbl_ref(range_suffix)},{extra_filter})),0))))"
        )

    ac = f"((acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))"
    held = (
        f"({tbl_ref('Purchase Date')}<>\"\")*({tbl_ref('Purchase Date')}<=pEnd)*"
        f"(({tbl_ref('Sale Date')}=\"\")+({tbl_ref('Sale Date')}>pEnd))"
    )
    in_p = (
        f"({tbl_ref('Purchase Date')}>=pStart)*({tbl_ref('Purchase Date')}<=pEnd)"
    )
    sale_p = (
        f"({tbl_ref('Sale Date')}>=pStart)*({tbl_ref('Sale Date')}<=pEnd)*"
        f"({tbl_ref('Sale Date')}<>\"\")"
    )
    status_open = f"{tbl_ref('Status')}=\"Open\""
    status_closed = f"{tbl_ref('Status')}=\"Closed\""
    cash = f"{tbl_ref('Asset Class')}=\"Cash\""

    income = (
        f"SUM(BYROW({acct_range},LAMBDA(acct,IFERROR("
        f"IF(pSel=\"Since Inception\","
        f"SUM(FILTER({tbl_ref('Coupons Received')},"
        f"(acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))),"
        f"SUM(FILTER({tbl_ref('Coupons Received')},"
        f"((acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\")))),0))))"
    )

    income_div = (
        f"SUM(BYROW({acct_range},LAMBDA(acct,IFERROR("
        f"IF(pSel=\"Since Inception\","
        f"SUM(FILTER({tbl_ref('Dividends Received')},"
        f"(acSel=\"All\")+({tbl_ref('Asset Class')}=acSel)))"
        f"+SUM(FILTER({tbl_ref('Interest Received')},"
        f"(acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))),"
        f"SUM(FILTER({tbl_ref('Dividends Received')},"
        f"((acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\")))"
        f"+SUM(FILTER({tbl_ref('Interest Received')},"
        f"((acSel=\"All\")+({tbl_ref('Asset Class')}=acSel))*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\")))),0))))"
    )

    pv = acct_sum("Current Market Value", f"{ac}*{held}")
    ic = acct_sum("Total Cost Basis", f"{ac}*{in_p}")
    ur_e = acct_sum("Unrealized P/L (€)", f"{ac}*{held}")
    ur_d = acct_sum("Unrealized P/L (€)", f"{ac}*{held}")
    ur_b = acct_sum("Total Cost Basis", f"{ac}*{held}")
    rl_e = acct_sum("Realized P/L (€)", f"{ac}*{sale_p}")
    rl_b = acct_sum("Total Cost Basis", f"{ac}*{sale_p}")
    cash_f = acct_sum("Current Market Value", f"{cash}*{held}")

    formulas = {
        "portfolio_value": f"IFERROR({pv},0)",
        "invested_capital": f"IFERROR({ic},0)",
        "unrealized_eur": f"IFERROR({ur_e},0)",
        "unrealized_pct": f"IFERROR(IF({ur_b}=0,0,{ur_d}/{ur_b}),0)",
        "realized_eur": f"IFERROR({rl_e},0)",
        "realized_pct": f"IFERROR(IF({rl_b}=0,0,{rl_e}/{rl_b}),0)",
        "cash_balance": f"IFERROR({cash_f},0)",
        "coupons": f"IFERROR({income},0)",
        "dividends": f"IFERROR({income_div},0)",
        "open_count": f"IFERROR({acct_rows('Asset Class', f'{ac}*{status_open}*{held}')},0)",
        "closed_count": f"IFERROR({acct_rows('Asset Class', f'{ac}*{status_closed}*{sale_p}')},0)",
    }

    metric_map = {
        "Current Portfolio Value": "portfolio_value",
        "Total Invested Capital": "invested_capital",
        "Unrealized P/L (€)": "unrealized_eur",
        "Unrealized P/L (%)": "unrealized_pct",
        "Realized P/L (€)": "realized_eur",
        "Realized P/L (%)": "realized_pct",
        "Total Cash": "cash_balance",
        "Coupons Received": "coupons",
        "Dividends Received": "dividends",
        "Number of Open Positions": "open_count",
        "Number of Closed Positions": "closed_count",
    }
    body = formulas[metric_map[metric]]
    return f"=LET({period_bounds_let()},{body})"


def calc_column_formula(col_name: str) -> str:
    mapping = {
        "Total Cost Basis": (
            "=[@[Quantity / Nominal]]*[@[Purchase Price]]"
            "+[@[Purchase Fees]]+[@[Other Purchase Costs]]"
        ),
        "Status": '=IF([@[Sale Date]]="","Open","Closed")',
        "Current Market Value": (
            '=IF([@Status]="Open",[@[Quantity / Nominal]]*[@[Current Price]],0)'
        ),
        "Unrealized P/L (€)": (
            '=IF([@Status]="Open",[@[Current Market Value]]-[@[Total Cost Basis]],0)'
        ),
        "Unrealized P/L (%)": (
            "=IF([@[Total Cost Basis]]=0,0,"
            'IF([@Status]="Open",[@[Unrealized P/L (€)]]/[@[Total Cost Basis]],0))'
        ),
        "Net Sale Proceeds": (
            '=IF([@Status]="Closed",'
            "[@[Quantity / Nominal]]*[@[Sale Price]]-[@[Sale Fees]],0)"
        ),
        "Realized P/L (€)": (
            '=IF([@Status]="Closed",[@[Net Sale Proceeds]]-[@[Total Cost Basis]],0)'
        ),
        "Realized P/L (%)": (
            "=IF([@[Total Cost Basis]]=0,0,"
            'IF([@Status]="Closed",[@[Realized P/L (€)]]/[@[Total Cost Basis]],0))'
        ),
    }
    return mapping[col_name]


def style_cell(ws, coord, font=None, fill=None, border=None, alignment=None, fmt=None):
    cell = ws[coord]
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    if border:
        cell.border = border
    if alignment:
        cell.alignment = alignment
    if fmt:
        cell.number_format = fmt


def apply_kpi_signed_format(ws, cell_ref: str, kind: str):
    if kind == "signed":
        ws.conditional_formatting.add(
            cell_ref,
            CellIsRule(operator="greaterThan", formula=["0"], font=Font(color="006100")),
        )
        ws.conditional_formatting.add(
            cell_ref,
            CellIsRule(operator="lessThan", formula=["0"], font=Font(color="9C0006")),
        )
    elif kind == "signed_pct":
        ws.conditional_formatting.add(
            cell_ref,
            CellIsRule(operator="greaterThan", formula=["0"], font=Font(color="006100")),
        )
        ws.conditional_formatting.add(
            cell_ref,
            CellIsRule(operator="lessThan", formula=["0"], font=Font(color="9C0006")),
        )


def add_validations(ws):
    dv_period = DataValidation(
        type="list",
        formula1=f"={PERIOD_LIST_RANGE}",
        allow_blank=False,
    )
    dv_period.error = "Select a valid period."
    dv_period.prompt = "Filter KPIs by reporting period."
    ws.add_data_validation(dv_period)
    dv_period.add(ws[SEL_PERIOD])

    dv_asset = DataValidation(
        type="list",
        formula1=f"={ASSET_LIST_RANGE}",
        allow_blank=False,
    )
    dv_asset.error = "Select a valid asset class."
    ws.add_data_validation(dv_asset)
    dv_asset.add(ws[SEL_ASSET])

    dv_ac = DataValidation(
        type="list",
        formula1=f"={ASSET_INPUT_RANGE}",
        allow_blank=True,
    )
    ws.add_data_validation(dv_ac)


def build_config_sheet(wb: Workbook):
    ws = wb.create_sheet("Config", 0)
    ws.sheet_state = "hidden"

    ws["A1"] = "Account Name"
    ws["A1"].font = FONT_SECTION
    for idx, name in enumerate(ACCOUNTS, start=2):
        ws[f"A{idx}"] = name

    last_acct_row = 1 + len(ACCOUNTS)
    tbl = Table(
        displayName=CONFIG_TABLE,
        ref=f"A1:A{last_acct_row}",
    )
    tbl.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tbl)

    ws["C1"] = "Period Options"
    ws["C1"].font = FONT_SECTION
    for idx, opt in enumerate(PERIOD_OPTIONS, start=2):
        ws[f"C{idx}"] = opt
    global PERIOD_LIST_RANGE
    PERIOD_LIST_RANGE = f"Config!$C$2:$C${1 + len(PERIOD_OPTIONS)}"

    ws["E1"] = "Asset Class Options"
    ws["E1"].font = FONT_SECTION
    ws["E2"] = "All"
    for idx, opt in enumerate(ASSET_CLASS_OPTIONS[1:], start=3):
        ws[f"E{idx}"] = opt
    global ASSET_LIST_RANGE, ASSET_INPUT_RANGE
    ASSET_LIST_RANGE = f"Config!$E$2:$E${1 + len(ASSET_CLASS_OPTIONS)}"
    ASSET_INPUT_RANGE = f"Config!$E$3:$E${1 + len(ASSET_CLASS_OPTIONS)}"

    ws["G1"] = "Instructions"
    ws["G1"].font = FONT_SECTION
    instructions = [
        "1. Add a new account name to tblAccounts, then duplicate any account sheet.",
        "2. Rename the duplicated sheet to match the new account name exactly.",
        "3. Update the sheet title — all Summary formulas read account names from tblAccounts.",
        "4. Enter investments in each account's Master Investment Table only.",
        "5. Update Current Price periodically — all KPIs refresh automatically.",
        "6. Use Income Date when recording coupons, dividends, or interest for period filters.",
    ]
    for i, line in enumerate(instructions, start=2):
        ws[f"G{i}"] = line
        ws[f"G{i}"].font = FONT_LABEL

    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["G"].width = 72


def build_summary_sheet(wb: Workbook):
    ws = wb.create_sheet("Summary", 1)
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:D1")
    ws["A1"] = "Portfolio Summary"
    ws["A1"].font = FONT_TITLE

    ws["A3"] = "Filters"
    ws["A3"].font = FONT_SECTION
    for r, (label, default) in enumerate(
        [
            ("Period", "Since Inception"),
            ("Asset Class", "All"),
            ("Custom Start", ""),
            ("Custom End", ""),
        ],
        start=4,
    ):
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = FONT_LABEL
        ws[f"B{r}"] = default
        ws[f"B{r}"].fill = FILL_INPUT
        ws[f"B{r}"].border = BORDER_THIN
        if "Date" in label or label.startswith("Custom"):
            ws[f"B{r}"].number_format = DATE_FORMAT

    ws["A9"] = "Portfolio KPIs"
    ws["A9"].font = FONT_SECTION
    ws["A9"].fill = FILL_SECTION
    ws["B9"].fill = FILL_SECTION
    ws.merge_cells("A9:B9")

    metric_keys = [
        "Current Portfolio Value",
        "Total Invested Capital",
        "Unrealized P/L (€)",
        "Unrealized P/L (%)",
        "Realized P/L (€)",
        "Realized P/L (%)",
        "Total Cash",
        "Coupons Received",
        "Dividends Received",
        "Number of Open Positions",
        "Number of Closed Positions",
    ]

    for i, (label, kind, fmt) in enumerate(KPI_DEFS):
        row = KPI_START_ROW + i
        ws[f"A{row}"] = label
        ws[f"A{row}"].font = FONT_KPI_LABEL
        ws[f"B{row}"] = summary_kpi_formula(metric_keys[i])
        ws[f"B{row}"].font = FONT_VALUE
        ws[f"B{row}"].number_format = fmt
        ws[f"A{row}"].border = BORDER_THIN
        ws[f"B{row}"].border = BORDER_THIN
        if kind in {"signed", "signed_pct"}:
            apply_kpi_signed_format(ws, f"B{row}", kind)

    add_validations(ws)

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 18
    ws.freeze_panes = "A10"


def sample_rows(account: str) -> list[dict]:
    """Return illustrative sample investments per account."""
    samples = {
        "ISP": [
            {
                "Asset Class": "ETFs",
                "ISIN": "IE00B4L5Y983",
                "Ticker": "IWDA",
                "Security Name": "iShares Core MSCI World",
                "Issuer": "iShares",
                "Currency": "EUR",
                "Purchase Date": "2022-03-15",
                "Purchase Price": 72.5,
                "Quantity / Nominal": 120,
                "Purchase Fees": 8.95,
                "Other Purchase Costs": 0,
                "Current Price": 88.2,
                "Distribution Type": "Accumulating",
                "TER": 0.002,
                "Benchmark Index": "MSCI World",
            },
            {
                "Asset Class": "Bonds",
                "ISIN": "IT0005437146",
                "Ticker": "BTPS",
                "Security Name": "BTP 3.5% 2028",
                "Issuer": "Republic of Italy",
                "Currency": "EUR",
                "Purchase Date": "2023-01-10",
                "Purchase Price": 98.4,
                "Quantity / Nominal": 10000,
                "Purchase Fees": 12,
                "Other Purchase Costs": 0,
                "Current Price": 96.8,
                "Coupon %": 0.035,
                "Coupon Frequency": "Semi-Annual",
                "Coupons Received": 350,
                "Income Date": "2025-07-15",
                "Maturity Date": "2028-02-01",
                "Yield to Maturity": 0.038,
                "Duration": 2.8,
            },
        ],
        "Barclays": [
            {
                "Asset Class": "Stocks",
                "ISIN": "US0378331005",
                "Ticker": "AAPL",
                "Security Name": "Apple Inc.",
                "Issuer": "Apple Inc.",
                "Currency": "USD",
                "Purchase Date": "2021-06-01",
                "Purchase Price": 124.5,
                "Quantity / Nominal": 50,
                "Purchase Fees": 5,
                "Other Purchase Costs": 0,
                "Current Price": 195.3,
                "Dividend Yield": 0.005,
                "Dividends Received": 42.5,
                "Income Date": "2025-05-15",
                "Exchange": "NASDAQ",
            },
            {
                "Asset Class": "Cash",
                "ISIN": "",
                "Ticker": "",
                "Security Name": "EUR Cash Balance",
                "Issuer": "Barclays",
                "Currency": "EUR",
                "Purchase Date": "2020-01-01",
                "Purchase Price": 1,
                "Quantity / Nominal": 12500,
                "Purchase Fees": 0,
                "Other Purchase Costs": 0,
                "Current Price": 1,
                "Interest Rate": 0.0125,
                "Interest Received": 156.25,
                "Income Date": "2025-06-30",
            },
        ],
        "Interactive Brokers": [
            {
                "Asset Class": "Funds",
                "ISIN": "LU1781541179",
                "Ticker": "VWCE",
                "Security Name": "Vanguard FTSE All-World",
                "Issuer": "Vanguard",
                "Currency": "EUR",
                "Purchase Date": "2024-02-20",
                "Purchase Price": 102.3,
                "Quantity / Nominal": 80,
                "Purchase Fees": 3.5,
                "Other Purchase Costs": 0,
                "Current Price": 118.7,
            },
            {
                "Asset Class": "Stocks",
                "ISIN": "NL0010273215",
                "Ticker": "ASML",
                "Security Name": "ASML Holding",
                "Issuer": "ASML",
                "Currency": "EUR",
                "Purchase Date": "2023-09-05",
                "Purchase Price": 620,
                "Quantity / Nominal": 10,
                "Purchase Fees": 4,
                "Other Purchase Costs": 0,
                "Current Price": 710,
                "Sale Date": "2025-04-10",
                "Sale Price": 705,
                "Sale Fees": 4,
                "Exchange": "Euronext Amsterdam",
            },
        ],
    }
    return samples.get(account, [])


def build_account_sheet(wb: Workbook, account: str):
    ws = wb.create_sheet(account)
    ws.sheet_view.showGridLines = False

    num_cols = len(MASTER_COLUMNS)
    last_col = col_letter(num_cols)

    ws.merge_cells(f"A1:D1")
    ws["A1"] = f"Account Summary — {account}"
    ws["A1"].font = FONT_TITLE

    ws["A3"] = "Filters"
    ws["A3"].font = FONT_SECTION
    filter_rows = [
        ("Period", "Since Inception"),
        ("Asset Class", "All"),
        ("Custom Start", ""),
        ("Custom End", ""),
    ]
    for r, (label, default) in enumerate(filter_rows, start=4):
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = FONT_LABEL
        ws[f"B{r}"] = default
        ws[f"B{r}"].fill = FILL_INPUT
        ws[f"B{r}"].border = BORDER_THIN
        if "Custom" in label:
            ws[f"B{r}"].number_format = DATE_FORMAT

    ws["A9"] = "Account KPIs"
    ws["A9"].font = FONT_SECTION
    ws["A9"].fill = FILL_SECTION
    ws["B9"].fill = FILL_SECTION
    ws.merge_cells("A9:B9")

    for i, (label, metric) in enumerate(ACCOUNT_KPI_LABELS):
        row = KPI_START_ROW + i
        ws[f"A{row}"] = label
        ws[f"A{row}"].font = FONT_KPI_LABEL
        ws[f"B{row}"] = account_kpi_formula(account, metric)
        ws[f"B{row}"].font = FONT_VALUE
        ws[f"A{row}"].border = BORDER_THIN
        ws[f"B{row}"].border = BORDER_THIN
        if "P/L" in label and "%" in label:
            ws[f"B{row}"].number_format = PCT_FORMAT
            apply_kpi_signed_format(ws, f"B{row}", "signed_pct")
        elif "P/L" in label:
            ws[f"B{row}"].number_format = EUR_FORMAT
            apply_kpi_signed_format(ws, f"B{row}", "signed")
        elif "Positions" in label:
            ws[f"B{row}"].number_format = INT_FORMAT
        else:
            ws[f"B{row}"].number_format = EUR_FORMAT

    ws[f"A{TABLE_HEADER_ROW - 1}"] = "Master Investment Table"
    ws[f"A{TABLE_HEADER_ROW - 1}"].font = FONT_SECTION

    for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
        cell = ws.cell(row=TABLE_HEADER_ROW, column=col_idx, value=header)
        cell.font = FONT_TABLE_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER_THIN

    rows = sample_rows(account)
    data_end_row = TABLE_DATA_START + max(len(rows), 4) - 1

    editable_cols = {
        "Asset Class",
        "ISIN",
        "Ticker",
        "Security Name",
        "Issuer",
        "Currency",
        "Purchase Date",
        "Purchase Price",
        "Quantity / Nominal",
        "Purchase Fees",
        "Other Purchase Costs",
        "Current Price",
        "Sale Date",
        "Sale Price",
        "Sale Fees",
        "Notes",
        "Income Date",
        "Coupon %",
        "Coupon Frequency",
        "Coupon Payment Dates",
        "Coupons Received",
        "Maturity Date",
        "Yield to Maturity",
        "Duration",
        "Dividend Yield",
        "Dividends Received",
        "Exchange",
        "Distribution Type",
        "TER",
        "Benchmark Index",
        "Interest Rate",
        "Interest Received",
    }

    calc_cols = {
        "Total Cost Basis",
        "Current Market Value",
        "Unrealized P/L (€)",
        "Unrealized P/L (%)",
        "Net Sale Proceeds",
        "Realized P/L (€)",
        "Realized P/L (%)",
        "Status",
    }

    for row_offset, row_data in enumerate(rows):
        row_num = TABLE_DATA_START + row_offset
        for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
            cell = ws.cell(row=row_num, column=col_idx)
            if header in calc_cols:
                cell.value = calc_column_formula(header)
            elif header in row_data:
                cell.value = row_data[header]
            if header in {"Purchase Date", "Sale Date", "Maturity Date", "Income Date"}:
                cell.number_format = DATE_FORMAT
            elif header in {
                "Purchase Price",
                "Current Price",
                "Sale Price",
                "Purchase Fees",
                "Other Purchase Costs",
                "Total Cost Basis",
                "Current Market Value",
                "Unrealized P/L (€)",
                "Net Sale Proceeds",
                "Realized P/L (€)",
                "Coupons Received",
                "Dividends Received",
                "Interest Received",
            }:
                cell.number_format = EUR_FORMAT
            elif header in {
                "Unrealized P/L (%)",
                "Realized P/L (%)",
                "Coupon %",
                "Dividend Yield",
                "Yield to Maturity",
                "TER",
                "Interest Rate",
            }:
                cell.number_format = PCT_FORMAT

    # Blank template rows with formulas
    for row_num in range(TABLE_DATA_START + len(rows), data_end_row + 1):
        for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
            cell = ws.cell(row=row_num, column=col_idx)
            if header in calc_cols:
                cell.value = calc_column_formula(header)

    table_ref = f"A{TABLE_HEADER_ROW}:{last_col}{data_end_row}"
    tbl = Table(displayName=table_name(account), ref=table_ref)
    tbl.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tbl)

    add_validations(ws)

    # Conditional formatting on calculated P/L columns
    for header in ("Unrealized P/L (€)", "Unrealized P/L (%)", "Realized P/L (€)", "Realized P/L (%)"):
        col = col_letter(MASTER_COLUMNS.index(header) + 1)
        rng = f"{col}{TABLE_DATA_START}:{col}{data_end_row}"
        ws.conditional_formatting.add(
            rng,
            CellIsRule(operator="greaterThan", formula=["0"], font=Font(color="006100")),
        )
        ws.conditional_formatting.add(
            rng,
            CellIsRule(operator="lessThan", formula=["0"], font=Font(color="9C0006")),
        )

    # Asset class input validation on table column
    ac_col = col_letter(MASTER_COLUMNS.index("Asset Class") + 1)
    dv_asset_input = DataValidation(type="list", formula1=f"={ASSET_INPUT_RANGE}", allow_blank=True)
    ws.add_data_validation(dv_asset_input)
    dv_asset_input.add(f"{ac_col}{TABLE_DATA_START}:{ac_col}{data_end_row}")

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 18
    for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
        letter = col_letter(col_idx)
        width = max(12, min(22, len(header) + 2))
        ws.column_dimensions[letter].width = width

    ws.freeze_panes = f"A{TABLE_HEADER_ROW + 1}"


def build_workbook() -> Path:
    global PERIOD_LIST_RANGE, ASSET_LIST_RANGE, ASSET_INPUT_RANGE

    wb = Workbook()
    default = wb.active
    wb.remove(default)

    build_config_sheet(wb)
    build_summary_sheet(wb)
    for account in ACCOUNTS:
        build_account_sheet(wb, account)

    wb.properties.title = "Investment Portfolio Tracker"
    wb.properties.subject = "Automated portfolio and account performance tracker"
    wb.properties.creator = "Portfolio Tracker Builder"
    wb.properties.description = (
        "Formula-driven investment portfolio tracker using Excel Tables and dynamic arrays."
    )

    wb.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    path = build_workbook()
    print(f"Created {path}")
