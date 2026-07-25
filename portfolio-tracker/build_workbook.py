#!/usr/bin/env python3
"""Build a professional Excel investment portfolio tracker workbook."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

OUTPUT = Path(__file__).resolve().parent / "Portfolio_Tracker.xlsx"

# Accounts derived from uploaded statements (Barclays ISA + Intesa Sanpaolo)
ACCOUNTS = ["Barclays ISA", "Intesa Sanpaolo"]

PERIOD_OPTIONS = [
    "Current Month",
    "Current Quarter",
    "Current Year",
    "Previous Year",
    "Since Inception",
    "Custom",
]

PERIOD_SHORT = ["Current Month", "Current Quarter", "Current Year", "Previous Year", "Since Inception"]

ASSET_CLASS_OPTIONS = ["All", "Bonds", "Stocks", "ETFs", "Funds", "Cash", "Other"]
ASSET_BREAKDOWN = ["Bonds", "Stocks", "ETFs", "Funds", "Cash", "Other"]

MASTER_COLUMNS = [
    "Asset Class",
    "ISIN",
    "Ticker",
    "Security Name",
    "Issuer",
    "Currency",
    "FX to EUR",
    "Purchase Date",
    "Purchase Price",
    "Quantity / Nominal",
    "Purchase Fees",
    "Other Purchase Costs",
    "Total Cost Basis",
    "Current Price",
    "Current Market Value",
    "Value (EUR)",
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
]

CONFIG_TABLE = "tblAccounts"

# Selectors (column C on dashboard sheets)
SEL_PERIOD = "C5"
SEL_ASSET = "C6"
SEL_CUSTOM_START = "C7"
SEL_CUSTOM_END = "C8"

TABLE_HEADER_ROW = 48
TABLE_DATA_START = 49

# Barclays-inspired palette
C_NAVY = "002B5C"
C_BLUE = "0076B6"
C_LIGHT = "F4F6F8"
C_WHITE = "FFFFFF"
C_GREY = "6B7280"
C_LINE = "D1D5DB"
C_GREEN = "1B7742"
C_RED = "B91C1C"

FONT_BRAND = Font(name="Calibri", size=16, bold=True, color=C_WHITE)
FONT_SUB = Font(name="Calibri", size=9, color=C_GREY)
FONT_SECTION = Font(name="Calibri", size=10, bold=True, color=C_NAVY)
FONT_LABEL = Font(name="Calibri", size=9, color=C_GREY)
FONT_KPI = Font(name="Calibri", size=9, color=C_GREY)
FONT_KPI_VAL = Font(name="Calibri", size=11, bold=True, color=C_NAVY)
FONT_TABLE = Font(name="Calibri", size=9, bold=True, color=C_WHITE)
FONT_TOTAL = Font(name="Calibri", size=9, bold=True, color=C_NAVY)

FILL_NAVY = PatternFill("solid", fgColor=C_NAVY)
FILL_BLUE = PatternFill("solid", fgColor=C_BLUE)
FILL_LIGHT = PatternFill("solid", fgColor=C_LIGHT)
FILL_WHITE = PatternFill("solid", fgColor=C_WHITE)
FILL_INPUT = PatternFill("solid", fgColor="FFFEF8")

BORDER_HAIR = Border(bottom=Side(style="thin", color=C_LINE))
BORDER_BOX = Border(
    left=Side(style="thin", color=C_LINE),
    right=Side(style="thin", color=C_LINE),
    top=Side(style="thin", color=C_LINE),
    bottom=Side(style="thin", color=C_LINE),
)

EUR = '#,##0.00" €"'
PCT = "0.00%"
DATE = "dd/mm/yyyy"
INT = "#,##0"

PERIOD_LIST_RANGE = ""
ASSET_LIST_RANGE = ""
ASSET_INPUT_RANGE = ""


def table_name(account: str) -> str:
    return "tbl_" + account.replace(" ", "_")


def col_letter(index: int) -> str:
    return get_column_letter(index)


def period_switch(prefix: str, var: str) -> str:
    p = prefix
    return (
        f'SWITCH({var},"Current Month",DATE(YEAR(TODAY()),MONTH(TODAY()),1),'
        f'"Current Quarter",DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+1,1),'
        f'"Current Year",DATE(YEAR(TODAY()),1,1),'
        f'"Previous Year",DATE(YEAR(TODAY())-1,1,1),'
        f'"Since Inception",DATE(1900,1,1),'
        f'"Custom",{p}${SEL_CUSTOM_START},DATE(1900,1,1))'
    )


def period_end_switch(prefix: str, var: str) -> str:
    p = prefix
    return (
        f'SWITCH({var},"Current Month",EOMONTH(TODAY(),0),'
        f'"Current Quarter",EOMONTH(DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+3,1),0),'
        f'"Current Year",DATE(YEAR(TODAY()),12,31),'
        f'"Previous Year",DATE(YEAR(TODAY())-1,12,31),'
        f'"Since Inception",DATE(9999,12,31),'
        f'"Custom",{p}${SEL_CUSTOM_END},DATE(9999,12,31))'
    )


def period_bounds_literal(period_name: str) -> tuple[str, str]:
    ps = (
        f'SWITCH("{period_name}","Current Month",DATE(YEAR(TODAY()),MONTH(TODAY()),1),'
        f'"Current Quarter",DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+1,1),'
        f'"Current Year",DATE(YEAR(TODAY()),1,1),'
        f'"Previous Year",DATE(YEAR(TODAY())-1,1,1),'
        f'"Since Inception",DATE(1900,1,1),DATE(1900,1,1))'
    )
    pe = (
        f'SWITCH("{period_name}","Current Month",EOMONTH(TODAY(),0),'
        f'"Current Quarter",EOMONTH(DATE(YEAR(TODAY()),INT((MONTH(TODAY())-1)/3)*3+3,1),0),'
        f'"Current Year",DATE(YEAR(TODAY()),12,31),'
        f'"Previous Year",DATE(YEAR(TODAY())-1,12,31),'
        f'"Since Inception",DATE(9999,12,31),DATE(9999,12,31))'
    )
    return ps, pe


def tbl_ref(col: str) -> str:
    return f'INDIRECT("\'"&acct&"\'!tbl_"&SUBSTITUTE(acct," ","_")&"[{col}]")'


def agg_sum(value_col: str, filter_expr: str, period_mode: str = "selector") -> str:
    acct_range = f"{CONFIG_TABLE}[Account Name]"
    if period_mode == "selector":
        bounds = (
            f"pSel,{SEL_PERIOD},acSel,{SEL_ASSET},"
            f"pStart,{period_switch('', 'pSel')},"
            f"pEnd,{period_end_switch('', 'pSel')}"
        )
    else:
        ps, pe = period_bounds_literal(period_mode)
        bounds = f"pStart,{ps},pEnd,{pe},acSel,{SEL_ASSET}"
    return (
        f"SUM(BYROW({acct_range},LAMBDA(acct,IFERROR("
        f"SUM(FILTER({tbl_ref(value_col)},{filter_expr})),0))))"
    )


def agg_rows(value_col: str, filter_expr: str, period_mode: str = "selector") -> str:
    acct_range = f"{CONFIG_TABLE}[Account Name]"
    return (
        f"SUM(BYROW({acct_range},LAMBDA(acct,IFERROR("
        f"ROWS(FILTER({tbl_ref(value_col)},{filter_expr})),0))))"
    )


def portfolio_filters(asset_class: str | None = None, period_mode: str = "selector") -> str:
    ac = f'({tbl_ref("Asset Class")}="{asset_class}")' if asset_class else '(acSel="All")+(INDIRECT("\'"&acct&"\'!tbl_"&SUBSTITUTE(acct," ","_")&"[Asset Class]")=acSel)'
    if asset_class:
        ac = f'({tbl_ref("Asset Class")}="{asset_class}")'
    else:
        ac = '((acSel="All")+(INDIRECT("\'"&acct&"\'!tbl_"&SUBSTITUTE(acct," ","_")&"[Asset Class]")=acSel))'
    held = (
        f'({tbl_ref("Purchase Date")}<>"")*({tbl_ref("Purchase Date")}<=pEnd)*'
        f'(({tbl_ref("Sale Date")}="")+({tbl_ref("Sale Date")}>pEnd))'
    )
    in_p = f'({tbl_ref("Purchase Date")}>=pStart)*({tbl_ref("Purchase Date")}<=pEnd)'
    sale_p = (
        f'({tbl_ref("Sale Date")}>=pStart)*({tbl_ref("Sale Date")}<=pEnd)*'
        f'({tbl_ref("Sale Date")}<>"")'
    )
    return ac, held, in_p, sale_p


def portfolio_metric_formula(metric: str, asset_class: str | None = None, period_mode: str = "selector") -> str:
    ac, held, in_p, sale_p = portfolio_filters(asset_class, period_mode)
    if period_mode == "selector":
        header = (
            f"pSel,{SEL_PERIOD},acSel,{SEL_ASSET},"
            f"pStart,{period_switch('', 'pSel')},"
            f"pEnd,{period_end_switch('', 'pSel')},"
        )
    else:
        ps, pe = period_bounds_literal(period_mode)
        header = f"pStart,{ps},pEnd,{pe},acSel,{SEL_ASSET},"

    income_since = (
        f"SUM(BYROW({CONFIG_TABLE}[Account Name],LAMBDA(acct,IFERROR("
        f"SUM(FILTER({tbl_ref('Coupons Received')},{ac})),0))))"
    )
    income_period = (
        f"SUM(BYROW({CONFIG_TABLE}[Account Name],LAMBDA(acct,IFERROR("
        f"SUM(FILTER({tbl_ref('Coupons Received')},{ac}*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\"))),0))))"
    )
    div_since = (
        f"SUM(BYROW({CONFIG_TABLE}[Account Name],LAMBDA(acct,IFERROR("
        f"SUM(FILTER({tbl_ref('Dividends Received')},{ac}))+"
        f"SUM(FILTER({tbl_ref('Interest Received')},{ac})),0))))"
    )
    div_period = (
        f"SUM(BYROW({CONFIG_TABLE}[Account Name],LAMBDA(acct,IFERROR("
        f"SUM(FILTER({tbl_ref('Dividends Received')},{ac}*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\")))+"
        f"SUM(FILTER({tbl_ref('Interest Received')},{ac}*"
        f"({tbl_ref('Income Date')}>=pStart)*({tbl_ref('Income Date')}<=pEnd)*"
        f"({tbl_ref('Income Date')}<>\"\"))),0))))"
    )

    m = {
        "nav": agg_sum("Value (EUR)", f"{ac}*{held}", period_mode),
        "invested": agg_sum("Total Cost Basis", f"{ac}*{in_p}", period_mode),
        "unrealized": agg_sum("Unrealized P/L (€)", f"{ac}*{held}", period_mode),
        "realized": agg_sum("Realized P/L (€)", f"{ac}*{sale_p}", period_mode),
        "cash": agg_sum("Value (EUR)", f'({tbl_ref("Asset Class")}="Cash")*{held}', period_mode),
        "coupons": (
            f'IF(pSel="Since Inception",{income_since},{income_period})'
            if period_mode == "selector"
            else (income_since if period_mode == "Since Inception" else income_period)
        ),
        "dividends": (
            f'IF(pSel="Since Inception",{div_since},{div_period})'
            if period_mode == "selector"
            else (div_since if period_mode == "Since Inception" else div_period)
        ),
        "open": agg_rows("Asset Class", f'{ac}*({tbl_ref("Status")}="Open")*{held}', period_mode),
        "closed": agg_rows("Asset Class", f'{ac}*({tbl_ref("Status")}="Closed")*{sale_p}', period_mode),
    }

    body = m[metric]
    return f"=LET({header}IFERROR({body},0))"


def account_metric_formula(account: str, metric: str, asset_class: str | None = None, period_mode: str = "selector") -> str:
    t = table_name(account)
    if period_mode == "selector":
        header = (
            f"pSel,{SEL_PERIOD},acSel,{SEL_ASSET},"
            f"pStart,{period_switch('', 'pSel')},"
            f"pEnd,{period_end_switch('', 'pSel')},"
            f"heldAtEnd,LAMBDA(pd,sd,(pd<>\"\")*(pd<=pEnd)*((sd=\"\")+(sd>pEnd))),"
            f"inPeriod,LAMBDA(dt,(dt<>\"\")*(dt>=pStart)*(dt<=pEnd)),"
            f"acMatch,LAMBDA(c,(acSel=\"All\")+(acSel=c)),"
        )
        psel_var = "pSel"
    else:
        ps, pe = period_bounds_literal(period_mode)
        header = (
            f"pStart,{ps},pEnd,{pe},acSel,{SEL_ASSET},"
            f"heldAtEnd,LAMBDA(pd,sd,(pd<>\"\")*(pd<=pEnd)*((sd=\"\")+(sd>pEnd))),"
            f"inPeriod,LAMBDA(dt,(dt<>\"\")*(dt>=pStart)*(dt<=pEnd)),"
        )
        psel_var = f'"{period_mode}"'

    if asset_class:
        ac_filter = f'({t}[Asset Class]="{asset_class}")'
    else:
        ac_filter = f'((acSel="All")+({t}[Asset Class]=acSel))'

    formulas = {
        "nav": f"IFERROR(SUM(FILTER({t}[Value (EUR)],{ac_filter}*heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)",
        "invested": f"IFERROR(SUM(FILTER({t}[Total Cost Basis],{ac_filter}*inPeriod({t}[Purchase Date]))),0)",
        "unrealized": f"IFERROR(SUM(FILTER({t}[Unrealized P/L (€)],{ac_filter}*heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)",
        "realized": f"IFERROR(SUM(FILTER({t}[Realized P/L (€)],{ac_filter}*inPeriod({t}[Sale Date]))),0)",
        "cash": f'IFERROR(SUM(FILTER({t}[Value (EUR)],({t}[Asset Class]="Cash")*heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)',
        "coupons": (
            f"IFERROR(IF({psel_var}=\"Since Inception\",SUM(FILTER({t}[Coupons Received],{ac_filter})),"
            f"SUM(FILTER({t}[Coupons Received],{ac_filter}*({t}[Income Date]>=pStart)*"
            f"({t}[Income Date]<=pEnd)*({t}[Income Date]<>\"\")))),0)"
        ),
        "dividends": (
            f"IFERROR(IF({psel_var}=\"Since Inception\","
            f"SUM(FILTER({t}[Dividends Received],{ac_filter}))+SUM(FILTER({t}[Interest Received],{ac_filter})),"
            f"SUM(FILTER({t}[Dividends Received],{ac_filter}*({t}[Income Date]>=pStart)*({t}[Income Date]<=pEnd)*({t}[Income Date]<>\"\")))+"
            f"SUM(FILTER({t}[Interest Received],{ac_filter}*({t}[Income Date]>=pStart)*({t}[Income Date]<=pEnd)*({t}[Income Date]<>\"\")))),0)"
        ),
        "open": f"IFERROR(ROWS(FILTER({t}[Asset Class],{ac_filter}*({t}[Status]=\"Open\")*heldAtEnd({t}[Purchase Date],{t}[Sale Date]))),0)",
        "closed": f"IFERROR(ROWS(FILTER({t}[Asset Class],{ac_filter}*({t}[Status]=\"Closed\")*inPeriod({t}[Sale Date]))),0)",
    }
    return f"=LET({header}{formulas[metric]})"


def calc_column_formula(col_name: str) -> str:
    bond_px = '[@Asset Class]="Bonds"'
    px = f"IF({bond_px},[@[Quantity / Nominal]]*[@[Purchase Price]]/100,[@[Quantity / Nominal]]*[@[Purchase Price]])"
    sale_px = f"IF({bond_px},[@[Quantity / Nominal]]*[@[Sale Price]]/100,[@[Quantity / Nominal]]*[@[Sale Price]])"
    mapping = {
        "Total Cost Basis": f"={px}+[@[Purchase Fees]]+[@[Other Purchase Costs]]",
        "Status": '=IF([@[Sale Date]]="","Open","Closed")',
        "Current Market Value": f'=IF([@Status]="Open",IF({bond_px},[@[Quantity / Nominal]]*[@[Current Price]]/100,[@[Quantity / Nominal]]*[@[Current Price]]),0)',
        "Value (EUR)": (
            '=IF([@Status]="Open",[@[Current Market Value]]*IF([@[FX to EUR]]="",1,[@[FX to EUR]]),0)'
        ),
        "Unrealized P/L (€)": (
            '=IF([@Status]="Open",[@[Value (EUR)]]-[@[Total Cost Basis]]*IF([@[FX to EUR]]="",1,[@[FX to EUR]]),0)'
        ),
        "Unrealized P/L (%)": (
            "=IF([@[Total Cost Basis]]=0,0,"
            'IF([@Status]="Open",[@[Unrealized P/L (€)]]/([@[Total Cost Basis]]*IF([@[FX to EUR]]="",1,[@[FX to EUR]])),0))'
        ),
        "Net Sale Proceeds": f'=IF([@Status]="Closed",{sale_px}-[@[Sale Fees]],0)',
        "Realized P/L (€)": (
            '=IF([@Status]="Closed",[@[Net Sale Proceeds]]-[@[Total Cost Basis]]*IF([@[FX to EUR]]="",1,[@[FX to EUR]]),0)'
        ),
        "Realized P/L (%)": (
            "=IF([@[Total Cost Basis]]=0,0,"
            'IF([@Status]="Closed",[@[Realized P/L (€)]]/([@[Total Cost Basis]]*IF([@[FX to EUR]]="",1,[@[FX to EUR]])),0))'
        ),
    }
    return mapping[col_name]


def apply_signed(ws, ref: str):
    ws.conditional_formatting.add(ref, CellIsRule(operator="greaterThan", formula=["0"], font=Font(color=C_GREEN)))
    ws.conditional_formatting.add(ref, CellIsRule(operator="lessThan", formula=["0"], font=Font(color=C_RED)))


def style_header_band(ws, row: int, last_col: str, title: str, subtitle: str = ""):
    ws.merge_cells(f"A{row}:{last_col}{row}")
    c = ws[f"A{row}"]
    c.value = title
    c.font = FONT_BRAND
    c.fill = FILL_NAVY
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[row].height = 28
    if subtitle:
        ws.merge_cells(f"A{row + 1}:F{row + 1}")
        s = ws[f"A{row + 1}"]
        s.value = subtitle
        s.font = FONT_SUB
        s.fill = FILL_LIGHT
        s.alignment = Alignment(horizontal="left", vertical="center", indent=1)


def write_section_title(ws, row: int, col: str, text: str, span: str):
    ws.merge_cells(f"{col}{row}:{span}{row}")
    c = ws[f"{col}{row}"]
    c.value = text.upper()
    c.font = FONT_SECTION
    c.fill = FILL_LIGHT
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)


def write_table_header(ws, row: int, headers: list[str], start_col: int = 1):
    for i, h in enumerate(headers):
        cell = ws.cell(row=row, column=start_col + i, value=h)
        cell.font = FONT_TABLE
        cell.fill = FILL_NAVY
        cell.alignment = Alignment(horizontal="center" if i else "left", vertical="center")
        cell.border = BORDER_BOX


def add_validations(ws):
    dv_period = DataValidation(type="list", formula1=f"={PERIOD_LIST_RANGE}", allow_blank=False)
    ws.add_data_validation(dv_period)
    dv_period.add(ws[SEL_PERIOD])
    dv_asset = DataValidation(type="list", formula1=f"={ASSET_LIST_RANGE}", allow_blank=False)
    ws.add_data_validation(dv_asset)
    dv_asset.add(ws[SEL_ASSET])


def build_config_sheet(wb: Workbook):
    ws = wb.create_sheet("Config", 0)
    ws.sheet_state = "hidden"
    ws["A1"] = "Account Name"
    for i, name in enumerate(ACCOUNTS, start=2):
        ws[f"A{i}"] = name
    ws.add_table(Table(displayName=CONFIG_TABLE, ref=f"A1:A{1 + len(ACCOUNTS)}"))
    ws.tables[CONFIG_TABLE].tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

    for i, opt in enumerate(PERIOD_OPTIONS, start=2):
        ws[f"C{i}"] = opt
    global PERIOD_LIST_RANGE
    PERIOD_LIST_RANGE = f"Config!$C$2:$C${1 + len(PERIOD_OPTIONS)}"

    ws["E2"] = "All"
    for i, opt in enumerate(ASSET_CLASS_OPTIONS[1:], start=3):
        ws[f"E{i}"] = opt
    global ASSET_LIST_RANGE, ASSET_INPUT_RANGE
    ASSET_LIST_RANGE = f"Config!$E$2:$E${1 + len(ASSET_CLASS_OPTIONS)}"
    ASSET_INPUT_RANGE = f"Config!$E$3:$E${1 + len(ASSET_CLASS_OPTIONS)}"


def build_filter_panel(ws, start_row: int = 4):
    labels = [("Reporting Period", "Since Inception"), ("Asset Class", "All"), ("Custom Start", ""), ("Custom End", "")]
    for i, (label, default) in enumerate(labels):
        r = start_row + i
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = FONT_LABEL
        ws[f"B{r}"] = ""
        ws[f"C{r}"] = default
        ws[f"C{r}"].fill = FILL_INPUT
        ws[f"C{r}"].border = BORDER_BOX
        ws[f"C{r}"].font = FONT_KPI_VAL
        if "Custom" in label:
            ws[f"C{r}"].number_format = DATE
    ws.merge_cells(f"A{start_row - 1}:C{start_row - 1}")
    ws[f"A{start_row - 1}"] = "REPORTING FILTERS"
    ws[f"A{start_row - 1}"].font = FONT_SECTION


def build_kpi_strip(ws, row: int):
    kpis = [
        ("Net Asset Value", "nav", EUR),
        ("Invested Capital", "invested", EUR),
        ("Unrealized P/L", "unrealized", EUR),
        ("Realized P/L", "realized", EUR),
        ("Cash", "cash", EUR),
        ("Income", "dividends", EUR),
    ]
    col = 1
    for label, metric, fmt in kpis:
        lcell = ws.cell(row=row, column=col, value=label)
        lcell.font = FONT_KPI
        lcell.fill = FILL_WHITE
        vcell = ws.cell(row=row + 1, column=col, value=portfolio_metric_formula(metric))
        vcell.font = FONT_KPI_VAL
        vcell.number_format = fmt
        vcell.fill = FILL_WHITE
        vcell.border = BORDER_HAIR
        if metric in {"unrealized", "realized"}:
            apply_signed(ws, vcell.coordinate)
        col += 1


def build_asset_breakdown(ws, start_row: int, scope: str, account: str | None = None):
    headers = [
        "Asset Class", "Market Value", "Weight", "Cost Basis", "Unrealized", "Unrealized %",
        "Realized", "Income", "Open Pos.",
    ]
    write_section_title(ws, start_row, "A", "Performance Breakdown by Asset Class", "J")
    write_table_header(ws, start_row + 1, headers)

    total_nav_ref = f"B{start_row + 8}"  # total row market value
    for i, cls in enumerate(ASSET_BREAKDOWN + ["TOTAL"]):
        r = start_row + 2 + i
        ws.cell(row=r, column=1, value=cls).font = FONT_TOTAL if cls == "TOTAL" else FONT_LABEL
        if scope == "portfolio":
            if cls == "TOTAL":
                ws.cell(row=r, column=2, value=portfolio_metric_formula("nav")).number_format = EUR
                ws.cell(row=r, column=3, value=1).number_format = PCT
                ws.cell(row=r, column=4, value=portfolio_metric_formula("invested")).number_format = EUR
                ws.cell(row=r, column=5, value=portfolio_metric_formula("unrealized")).number_format = EUR
                ws.cell(row=r, column=6, value=f"=IFERROR(IF(D{r}=0,0,E{r}/D{r}),0)").number_format = PCT
                ws.cell(row=r, column=7, value=portfolio_metric_formula("realized")).number_format = EUR
                ws.cell(row=r, column=8, value=portfolio_metric_formula("dividends")).number_format = EUR
                ws.cell(row=r, column=9, value=portfolio_metric_formula("open")).number_format = INT
            else:
                ws.cell(row=r, column=2, value=portfolio_metric_formula("nav", cls)).number_format = EUR
                ws.cell(row=r, column=3, value=f"=IFERROR(IF({total_nav_ref}=0,0,B{r}/{total_nav_ref}),0)").number_format = PCT
                ws.cell(row=r, column=4, value=portfolio_metric_formula("invested", cls)).number_format = EUR
                ws.cell(row=r, column=5, value=portfolio_metric_formula("unrealized", cls)).number_format = EUR
                ws.cell(row=r, column=6, value=f"=IFERROR(IF(D{r}=0,0,E{r}/D{r}),0)").number_format = PCT
                ws.cell(row=r, column=7, value=portfolio_metric_formula("realized", cls)).number_format = EUR
                ws.cell(row=r, column=8, value=portfolio_metric_formula("dividends", cls)).number_format = EUR
                ws.cell(row=r, column=9, value=portfolio_metric_formula("open", cls)).number_format = INT
        else:
            assert account
            if cls == "TOTAL":
                ws.cell(row=r, column=2, value=account_metric_formula(account, "nav")).number_format = EUR
                ws.cell(row=r, column=3, value=1).number_format = PCT
                ws.cell(row=r, column=4, value=account_metric_formula(account, "invested")).number_format = EUR
                ws.cell(row=r, column=5, value=account_metric_formula(account, "unrealized")).number_format = EUR
                ws.cell(row=r, column=6, value=f"=IFERROR(IF(D{r}=0,0,E{r}/D{r}),0)").number_format = PCT
                ws.cell(row=r, column=7, value=account_metric_formula(account, "realized")).number_format = EUR
                ws.cell(row=r, column=8, value=account_metric_formula(account, "dividends")).number_format = EUR
                ws.cell(row=r, column=9, value=account_metric_formula(account, "open")).number_format = INT
            else:
                ws.cell(row=r, column=2, value=account_metric_formula(account, "nav", cls)).number_format = EUR
                ws.cell(row=r, column=3, value=f"=IFERROR(IF({total_nav_ref}=0,0,B{r}/{total_nav_ref}),0)").number_format = PCT
                ws.cell(row=r, column=4, value=account_metric_formula(account, "invested", cls)).number_format = EUR
                ws.cell(row=r, column=5, value=account_metric_formula(account, "unrealized", cls)).number_format = EUR
                ws.cell(row=r, column=6, value=f"=IFERROR(IF(D{r}=0,0,E{r}/D{r}),0)").number_format = PCT
                ws.cell(row=r, column=7, value=account_metric_formula(account, "realized", cls)).number_format = EUR
                ws.cell(row=r, column=8, value=account_metric_formula(account, "dividends", cls)).number_format = EUR
                ws.cell(row=r, column=9, value=account_metric_formula(account, "open", cls)).number_format = INT
        for c in range(1, 10):
            ws.cell(row=r, column=c).border = BORDER_BOX
            if c in {5, 6, 7}:
                apply_signed(ws, ws.cell(row=r, column=c).coordinate)


def build_period_matrix(ws, start_row: int, scope: str, account: str | None = None):
    headers = ["Metric"] + PERIOD_SHORT
    write_section_title(ws, start_row, "A", "Performance by Reporting Period", "F")
    write_table_header(ws, start_row + 1, headers)
    metrics = [
        ("Net Asset Value", "nav", EUR),
        ("Invested Capital", "invested", EUR),
        ("Unrealized P/L", "unrealized", EUR),
        ("Realized P/L", "realized", EUR),
        ("Total Return %", "return", PCT),
    ]
    for i, (label, metric, fmt) in enumerate(metrics):
        r = start_row + 2 + i
        ws.cell(row=r, column=1, value=label).font = FONT_LABEL
        for j, period in enumerate(PERIOD_SHORT):
            c = j + 2
            if metric == "return":
                if scope == "portfolio":
                    u = portfolio_metric_formula("unrealized", period_mode=period)[1:]
                    rl = portfolio_metric_formula("realized", period_mode=period)[1:]
                    d = portfolio_metric_formula("invested", period_mode=period)[1:]
                    ws.cell(row=r, column=c, value=f"=LET(u,{u},rl,{rl},d,{d},IFERROR(IF(d=0,0,(u+rl)/d),0))")
                else:
                    u = account_metric_formula(account, "unrealized", period_mode=period)[1:]
                    rl = account_metric_formula(account, "realized", period_mode=period)[1:]
                    d = account_metric_formula(account, "invested", period_mode=period)[1:]
                    ws.cell(row=r, column=c, value=f"=LET(u,{u},rl,{rl},d,{d},IFERROR(IF(d=0,0,(u+rl)/d),0))")
            elif scope == "portfolio":
                ws.cell(row=r, column=c, value=portfolio_metric_formula(metric, period_mode=period))
            else:
                ws.cell(row=r, column=c, value=account_metric_formula(account, metric, period_mode=period))
            ws.cell(row=r, column=c).number_format = fmt
            ws.cell(row=r, column=c).border = BORDER_BOX
            if metric in {"unrealized", "realized", "return"}:
                apply_signed(ws, ws.cell(row=r, column=c).coordinate)
        ws.cell(row=r, column=1).border = BORDER_BOX


def build_account_overview(ws, start_row: int):
    headers = ["Account", "Market Value", "Weight", "Unrealized", "Realized", "Income", "Open Pos."]
    write_section_title(ws, start_row, "A", "Account Overview", "G")
    write_table_header(ws, start_row + 1, headers)
    for i, account in enumerate(ACCOUNTS):
        r = start_row + 2 + i
        ws.cell(row=r, column=1, value=account).font = FONT_LABEL
        ws.cell(row=r, column=2, value=account_metric_formula(account, "nav")).number_format = EUR
        total_row = start_row + 2 + len(ACCOUNTS)
        ws.cell(row=r, column=3, value=f"=IFERROR(IF(B{total_row}=0,0,B{r}/B{total_row}),0)").number_format = PCT
        ws.cell(row=r, column=4, value=account_metric_formula(account, "unrealized")).number_format = EUR
        ws.cell(row=r, column=5, value=account_metric_formula(account, "realized")).number_format = EUR
        ws.cell(row=r, column=6, value=account_metric_formula(account, "dividends")).number_format = EUR
        ws.cell(row=r, column=7, value=account_metric_formula(account, "open")).number_format = INT
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = BORDER_BOX
            if c in {4, 5}:
                apply_signed(ws, ws.cell(row=r, column=c).coordinate)
    tr = start_row + 2 + len(ACCOUNTS)
    ws.cell(row=tr, column=1, value="TOTAL").font = FONT_TOTAL
    ws.cell(row=tr, column=2, value=portfolio_metric_formula("nav")).number_format = EUR
    ws.cell(row=tr, column=3, value=1).number_format = PCT
    ws.cell(row=tr, column=4, value=portfolio_metric_formula("unrealized")).number_format = EUR
    ws.cell(row=tr, column=5, value=portfolio_metric_formula("realized")).number_format = EUR
    ws.cell(row=tr, column=6, value=portfolio_metric_formula("dividends")).number_format = EUR
    ws.cell(row=tr, column=7, value=portfolio_metric_formula("open")).number_format = INT
    for c in range(1, 8):
        ws.cell(row=tr, column=c).border = BORDER_BOX


def build_summary_sheet(wb: Workbook):
    ws = wb.create_sheet("Summary", 1)
    ws.sheet_view.showGridLines = False
    style_header_band(ws, 1, "J", "PORTFOLIO PERFORMANCE REPORT", "Consolidated view | All accounts | EUR reporting currency")
    ws["H2"] = "As of"
    ws["H2"].font = FONT_LABEL
    ws["I2"] = "=TODAY()"
    ws["I2"].number_format = DATE
    ws["I2"].font = FONT_KPI_VAL

    build_filter_panel(ws, 4)
    write_section_title(ws, 9, "A", "Portfolio Snapshot", "J")
    build_kpi_strip(ws, 10)
    build_asset_breakdown(ws, 13, "portfolio")
    build_period_matrix(ws, 23, "portfolio")
    build_account_overview(ws, 31)
    add_validations(ws)

    widths = {"A": 18, "B": 14, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12, "H": 10, "I": 12, "J": 10}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"


def sample_rows(account: str) -> list[dict]:
    data = {
        "Barclays ISA": [
            {
                "Asset Class": "Bonds",
                "ISIN": "GB00B3KJDS62",
                "Ticker": "GILT 39",
                "Security Name": "UK (GOVT OF) 4.25% Gilt 07/09/39",
                "Issuer": "UK Government",
                "Currency": "GBP",
                "FX to EUR": 1.17,
                "Purchase Date": "2024-11-12",
                "Purchase Price": 92.5,
                "Quantity / Nominal": 10000,
                "Purchase Fees": 12.5,
                "Other Purchase Costs": 0,
                "Current Price": 93.8,
                "Maturity Date": "2039-09-07",
                "Coupon %": 0.0425,
                "Coupon Frequency": "Semi-Annual",
                "Notes": "Da estratto Barclays ISA ID1901366-001 — aggiornare prezzo/FX",
            },
            {
                "Asset Class": "Funds",
                "ISIN": "LU1829219392",
                "Ticker": "LUXG",
                "Security Name": "Amundi S&P Global Luxury",
                "Issuer": "Amundi",
                "Currency": "EUR",
                "FX to EUR": 1,
                "Purchase Date": "2023-05-18",
                "Purchase Price": 118.4,
                "Quantity / Nominal": 45,
                "Purchase Fees": 0,
                "Other Purchase Costs": 0,
                "Current Price": 132.6,
                "Notes": "Da estratto Barclays ISA",
            },
            {
                "Asset Class": "Funds",
                "ISIN": "LU1931974630",
                "Ticker": "PRAN",
                "Security Name": "Amundi Prime Emerging Markets Acc",
                "Issuer": "Amundi",
                "Currency": "EUR",
                "FX to EUR": 1,
                "Purchase Date": "2024-01-22",
                "Purchase Price": 102.1,
                "Quantity / Nominal": 60,
                "Purchase Fees": 0,
                "Other Purchase Costs": 0,
                "Current Price": 108.3,
                "Notes": "Da estratto Barclays ISA",
            },
            {
                "Asset Class": "ETFs",
                "ISIN": "IE00BFMXYP42",
                "Ticker": "VUAG",
                "Security Name": "Vanguard S&P 500 UCITS ETF Acc",
                "Issuer": "Vanguard",
                "Currency": "GBP",
                "FX to EUR": 1.17,
                "Purchase Date": "2022-08-03",
                "Purchase Price": 68.2,
                "Quantity / Nominal": 250,
                "Purchase Fees": 3.95,
                "Other Purchase Costs": 0,
                "Current Price": 89.4,
                "Distribution Type": "Accumulating",
                "TER": 0.0007,
                "Benchmark Index": "S&P 500",
                "Notes": "Da estratto Barclays ISA",
            },
            {
                "Asset Class": "Cash",
                "ISIN": "",
                "Ticker": "",
                "Security Name": "Cash GBP/EUR",
                "Issuer": "Barclays",
                "Currency": "GBP",
                "FX to EUR": 1.17,
                "Purchase Date": "2025-01-01",
                "Purchase Price": 1,
                "Quantity / Nominal": 4100,
                "Purchase Fees": 0,
                "Other Purchase Costs": 0,
                "Current Price": 1,
                "Notes": "Saldo cash — aggiornare da estratto",
            },
        ],
        "Intesa Sanpaolo": [
            {
                "Asset Class": "Bonds",
                "ISIN": "XS2829810923",
                "Ticker": "ROMANIA 37",
                "Security Name": "Romania 5.625% 24/37",
                "Issuer": "Romania",
                "Currency": "EUR",
                "FX to EUR": 1,
                "Purchase Date": "2026-07-14",
                "Purchase Price": 97.0,
                "Quantity / Nominal": 15000,
                "Purchase Fees": 38.42,
                "Other Purchase Costs": 93.38,
                "Current Price": 97.0,
                "Maturity Date": "2037-02-24",
                "Coupon %": 0.05625,
                "Coupon Frequency": "Annual",
                "Yield to Maturity": 0.059,
                "Duration": 8.5,
                "Notes": "Conferma operazioni 14/07/2026 — Dep. 06793 3100 03022395",
            },
        ],
    }
    return data.get(account, [])


def build_account_sheet(wb: Workbook, account: str):
    ws = wb.create_sheet(account)
    ws.sheet_view.showGridLines = False
    style_header_band(ws, 1, "J", f"ACCOUNT REPORT — {account.upper()}", "Single-account performance | Master table is the source of truth")
    ws["H2"] = "As of"
    ws["I2"] = "=TODAY()"
    ws["I2"].number_format = DATE

    build_filter_panel(ws, 4)
    write_section_title(ws, 9, "A", "Account Snapshot", "J")
    kpis = [
        ("Net Asset Value", "nav", EUR),
        ("Invested Capital", "invested", EUR),
        ("Unrealized P/L", "unrealized", EUR),
        ("Realized P/L", "realized", EUR),
        ("Cash", "cash", EUR),
        ("Income", "dividends", EUR),
    ]
    col = 1
    for label, metric, fmt in kpis:
        ws.cell(row=10, column=col, value=label).font = FONT_KPI
        ws.cell(row=11, column=col, value=account_metric_formula(account, metric)).font = FONT_KPI_VAL
        ws.cell(row=11, column=col).number_format = fmt
        if metric in {"unrealized", "realized"}:
            apply_signed(ws, ws.cell(row=11, column=col).coordinate)
        col += 1

    build_asset_breakdown(ws, 13, "account", account)
    build_period_matrix(ws, 23, "account", account)

    ws[f"A{TABLE_HEADER_ROW - 2}"] = "MASTER INVESTMENT TABLE"
    ws[f"A{TABLE_HEADER_ROW - 2}"].font = FONT_SECTION
    ws[f"A{TABLE_HEADER_ROW - 1}"] = "Single source of truth for this account — all metrics above are formula-linked to this table."
    ws[f"A{TABLE_HEADER_ROW - 1}"].font = FONT_SUB

    rows = sample_rows(account)
    data_end = TABLE_DATA_START + max(len(rows), 5) - 1
    calc_cols = {
        "Total Cost Basis", "Current Market Value", "Value (EUR)", "Unrealized P/L (€)",
        "Unrealized P/L (%)", "Net Sale Proceeds", "Realized P/L (€)", "Realized P/L (%)", "Status",
    }

    for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
        cell = ws.cell(row=TABLE_HEADER_ROW, column=col_idx, value=header)
        cell.font = FONT_TABLE
        cell.fill = FILL_NAVY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER_BOX

    for offset, row_data in enumerate(rows):
        rn = TABLE_DATA_START + offset
        for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
            cell = ws.cell(row=rn, column=col_idx)
            if header in calc_cols:
                cell.value = calc_column_formula(header)
            elif header in row_data:
                cell.value = row_data[header]
            if "Date" in header:
                cell.number_format = DATE
            elif header in {"Coupon %", "Dividend Yield", "Yield to Maturity", "TER", "Interest Rate", "Unrealized P/L (%)", "Realized P/L (%)"}:
                cell.number_format = PCT
            elif header not in {"Asset Class", "ISIN", "Ticker", "Security Name", "Issuer", "Currency", "Status", "Notes", "Coupon Frequency", "Coupon Payment Dates", "Exchange", "Distribution Type", "Benchmark Index", "FX to EUR"}:
                cell.number_format = EUR

    for rn in range(TABLE_DATA_START + len(rows), data_end + 1):
        for col_idx, header in enumerate(MASTER_COLUMNS, start=1):
            if header in calc_cols:
                ws.cell(row=rn, column=col_idx, value=calc_column_formula(header))

    last_col = col_letter(len(MASTER_COLUMNS))
    tbl = Table(displayName=table_name(account), ref=f"A{TABLE_HEADER_ROW}:{last_col}{data_end}")
    tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tbl)

    add_validations(ws)
    ac_col = col_letter(MASTER_COLUMNS.index("Asset Class") + 1)
    dv = DataValidation(type="list", formula1=f"={ASSET_INPUT_RANGE}", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{ac_col}{TABLE_DATA_START}:{ac_col}{data_end}")

    for header in ("Unrealized P/L (€)", "Unrealized P/L (%)", "Realized P/L (€)", "Realized P/L (%)"):
        c = col_letter(MASTER_COLUMNS.index(header) + 1)
        apply_signed(ws, f"{c}{TABLE_DATA_START}:{c}{data_end}")

    ws.column_dimensions["A"].width = 14
    for i, header in enumerate(MASTER_COLUMNS, start=1):
        ws.column_dimensions[col_letter(i)].width = max(11, min(24, len(header) + 1))
    ws.freeze_panes = f"A{TABLE_HEADER_ROW + 1}"


def build_workbook() -> Path:
    global PERIOD_LIST_RANGE, ASSET_LIST_RANGE, ASSET_INPUT_RANGE
    wb = Workbook()
    wb.remove(wb.active)
    build_config_sheet(wb)
    build_summary_sheet(wb)
    for account in ACCOUNTS:
        build_account_sheet(wb, account)
    wb.properties.title = "Investment Portfolio Tracker"
    wb.properties.creator = "Portfolio Tracker"
    wb.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(f"Created {build_workbook()}")
