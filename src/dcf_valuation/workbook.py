"""Editable DCF plus an explicitly frozen Monte Carlo research snapshot."""

import json
from dataclasses import asdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .model import Assumptions, calculate, load_assumptions, load_data
from .monte_carlo import Simulation, simulate

NUMBER = '#,##0.0;(#,##0.0);"–"'
PERCENT = '0.0%;(0.0%);"–"'
PRICE = '"R$ "0.00;("R$ "0.00);"–"'


def _validation(sheet, cell_range: str, minimum: float, maximum: float) -> None:
    rule = DataValidation(type="decimal", operator="between", formula1=minimum, formula2=maximum)
    rule.showErrorMessage = True
    rule.errorTitle = "Premissa inválida"
    rule.error = f"Informe um número entre {minimum} e {maximum}."
    rule.errorStyle = "stop"
    sheet.add_data_validation(rule)
    rule.add(cell_range)


def build_workbook(
    output: str | Path,
    assumptions: Assumptions | None = None,
    *,
    data: dict | None = None,
    simulation: Simulation | None = None,
    quote: dict | None = None,
) -> Path:
    data = data or load_data()
    a = assumptions or load_assumptions(data)
    simulation = simulation or simulate(a, data=data)
    if (
        asdict(simulation.assumptions) != asdict(a)
        or simulation.valuation_date != data["valuation_date"]
        or simulation.base_revenue != data["historical"][-1]["revenue"]
    ):
        raise ValueError(
            "simulation must match workbook assumptions, valuation date and revenue base"
        )
    quote = quote or data.get("quote")
    projection_dates = [p["period_end"] for p in calculate(a, data)["projections"]]
    historical_column = get_column_letter(3 + len(data["historical"]))
    book = Workbook()
    book.remove(book.active)
    for title in (
        "Assumptions",
        "Historical",
        "Projections",
        "DCF",
        "WACC",
        "Sensitivity",
        "MonteCarlo",
        "Sources",
    ):
        sheet = book.create_sheet(title)
        sheet.sheet_view.showGridLines = False
        sheet.freeze_panes = "D7"
        sheet.column_dimensions["A"].width = 2
        sheet.column_dimensions["B"].width = 2
        sheet.column_dimensions["C"].width = 39
        for column in "DEFGH":
            sheet.column_dimensions[column].width = 19
        sheet.merge_cells("C2:H2")
        sheet["C2"] = f"WEG • {title}"
        sheet.merge_cells("C3:H3")
        sheet["C3"] = f"Valuation {data['valuation_date']} • R$ milhões • premissas ilustrativas"
        sheet.row_dimensions[3].height = 30
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 1

    s = book["Assumptions"]
    s.sheet_properties.tabColor = "EADAC5"
    s["C6"] = "Projeções ilustrativas"
    drivers = [
        ("Crescimento da receita", a.growth),
        ("Margem EBIT", a.ebit_margin),
        ("D&A / receita", a.da_ratio),
        ("Capex / receita", a.capex_ratio),
        ("NWC / receita", a.nwc_ratio),
    ]
    for column, year in enumerate(projection_dates, 4):
        s.cell(6, column, year)
    for row, (label, values) in enumerate(drivers, 7):
        s.cell(row, 3, label)
        for column, value in enumerate(values, 4):
            s.cell(row, column, value).number_format = PERCENT
    _validation(s, "D7:H7", -0.999999, 100)
    _validation(s, "D8:H11", 0, 1)
    s.merge_cells("C13:H13")
    s["C13"] = "Azul: entradas editáveis. Verde: vínculos entre abas. Preto: cálculos."
    s["C16"] = "Capital e ponte para o acionista"
    s["D16"] = "Valor"
    s.merge_cells("E16:H16")
    s["E16"] = "Origem do padrão (valores editáveis)"
    scalars = [
        ("Taxa livre de risco nominal BRL", a.risk_free, "Hipótese: 10%; não é cotação de título"),
        ("Beta alavancado", a.beta, "Hipótese: 0,90; sem regressão"),
        (
            "Prêmio de risco de ações",
            a.equity_risk_premium,
            "Hipótese BRL; sem spread país adicional",
        ),
        ("Custo da dívida antes de impostos", a.debt_cost, "Hipótese nominal BRL"),
        (
            "Dívida / capital (valor de mercado)",
            a.debt_weight,
            "Estrutura-alvo hipotética, não contábil",
        ),
        ("Alíquota sobre EBIT positivo", a.tax_rate, "Hipótese simplificada: 34%"),
        ("Crescimento na perpetuidade", a.terminal_growth, "Hipótese nominal BRL; deve ser < WACC"),
        ("Caixa e aplicações", a.cash, "Fixture versionada; fontes e data na aba Sources"),
        ("Dívida financeira", a.debt, "Fixture versionada; fontes e data na aba Sources"),
        (
            "Outros direitos / minoritários",
            a.other_claims,
            "Fixture versionada; premissa/valor divulgado conforme Sources",
        ),
        ("Ações usadas (milhões)", a.shares, "Fixture versionada; proxy sem diluição futura"),
        ("NWC inicial / receita base", a.opening_nwc_ratio, "Hipótese: 20%; não é saldo divulgado"),
    ]
    for row, (label, value, origin) in enumerate(scalars, 17):
        s.cell(row, 3, label)
        s.cell(row, 4, value)
        s.merge_cells(start_row=row, start_column=5, end_row=row, end_column=8)
        s.cell(row, 5, origin)
        s.cell(row, 4).number_format = PERCENT if row in (17, 19, 20, 21, 22, 23, 28) else NUMBER
    for region in ("D17:D20", "D24:D26"):
        _validation(s, region, 0, 1e12)
    for region in ("D21:D22", "D28"):
        _validation(s, region, 0, 1)
    _validation(s, "D23", -0.999999, 100)
    _validation(s, "D27", 0.000001, 1e12)
    s["C30"] = "Entradas numéricas válidas?"
    s["D30"] = (
        "=AND(COUNT(D7:H11)=25,MIN(D7:H7)>-1,MIN(D8:H11)>=0,MAX(D8:H11)<=1,"
        "COUNT(D17:D28)=12,MIN(D17:D22)>=0,D21<=1,D22<=1,D23>-1,"
        "MIN(D24:D26)>=0,D27>0,D28>=0,D28<=1)"
    )
    s.merge_cells("C32:H33")
    s["C32"] = (
        "Fontes em Sources. Não são previsões atuais nem recomendação. "
        "Alterações manuais no Excel não modificam o JSON nem o resumo Python."
    )

    s = book["Historical"]
    s["C6"] = "Histórico • último período é a base"
    for column, period in enumerate(data["historical"], 4):
        letter = get_column_letter(column)
        s.cell(6, column, period.get("period", period["year"]))
        for row, key in ((7, "revenue"), (8, "ebitda"), (9, "da")):
            s.cell(row, column, period[key])
        s.cell(10, column, f"={letter}8-{letter}9")
        s.cell(11, column, f"={letter}10/{letter}7").number_format = PERCENT
    for row, label in enumerate(
        ("Receita líquida", "EBITDA", "D&A", "EBIT = EBITDA − D&A", "Margem EBIT"), 7
    ):
        s.cell(row, 3, label)
    s.merge_cells("C14:H16")
    s["C14"] = (
        "R$ milhões. Veja períodos, fontes e reconciliação na fixture e em Sources. "
        "TTM, quando indicado, é calculado por FY + 9M atual − 9M anterior. "
        "EBIT = EBITDA − D&A; bases e eventuais aproximações estão identificadas."
    )

    s = book["Projections"]
    labels = {
        7: "Receita líquida",
        8: "Crescimento da receita",
        9: "Margem EBIT",
        10: "EBIT",
        11: "Impostos operacionais",
        12: "NOPAT",
        13: "D&A",
        14: "Capex",
        15: "Capital de giro operacional (NWC)",
        16: "Variação de NWC",
        17: "FCFF",
    }
    for row, label in labels.items():
        s.cell(row, 3, label)
    for column in range(4, 9):
        c = get_column_letter(column)
        previous = get_column_letter(column - 1)
        revenue_base = f"'Historical'!{historical_column}7" if column == 4 else f"{previous}7"
        nwc_base = (
            f"'Historical'!{historical_column}7*'Assumptions'!$D$28"
            if column == 4
            else f"{previous}15"
        )
        formulas = {
            6: f"='Assumptions'!{c}6",
            7: f"={revenue_base}*(1+{c}8)",
            8: f"='Assumptions'!{c}7",
            9: f"='Assumptions'!{c}8",
            10: f"={c}7*{c}9",
            11: f"=MAX({c}10,0)*'Assumptions'!$D$22",
            12: f"={c}10-{c}11",
            13: f"={c}7*'Assumptions'!{c}9",
            14: f"={c}7*'Assumptions'!{c}10",
            15: f"={c}7*'Assumptions'!{c}11",
            16: f"={c}15-({nwc_base})",
            17: f"={c}12+{c}13-{c}14-{c}16",
        }
        for row, formula in formulas.items():
            s.cell(row, column, formula)
        for row in (8, 9):
            s.cell(row, column).number_format = PERCENT
    s.merge_cells("C20:H22")
    s["C20"] = (
        "FCFF sem alavancagem; capex como saída positiva. Impostos sem crédito imediato "
        "sobre prejuízo. NWC inicial hipotético. Não é projeção de balanço completo."
    )

    s = book["WACC"]
    for row, label, formula in (
        (7, "Taxa livre de risco", "='Assumptions'!D17"),
        (8, "Beta alavancado", "='Assumptions'!D18"),
        (9, "Prêmio de risco de ações", "='Assumptions'!D19"),
        (10, "Custo do capital próprio", "=D7+D8*D9"),
        (12, "Custo da dívida", "='Assumptions'!D20"),
        (13, "Alíquota fiscal", "='Assumptions'!D22"),
        (14, "Dívida / capital", "='Assumptions'!D21"),
        (15, "Capital próprio / capital", "=1-D14"),
        (17, "WACC nominal BRL", "=D10*D15+D12*(1-D13)*D14"),
    ):
        s.cell(row, 3, label)
        s.cell(row, 4, formula).number_format = NUMBER if row == 8 else PERCENT
    s.merge_cells("C20:H22")
    s["C20"] = (
        "CAPM simplificado. Todas as taxas são hipóteses em reais nominais. "
        "A taxa livre de risco e o prêmio não são dados correntes de mercado."
    )

    s = book["DCF"]
    for row, label in {
        7: "FCFF",
        8: "Ano de desconto",
        9: "Fator de desconto",
        10: "Valor presente do FCFF",
    }.items():
        s.cell(row, 3, label)
    for column in range(4, 9):
        c = get_column_letter(column)
        s.cell(6, column, f"='Assumptions'!{c}6")
        s.cell(7, column, f"='Projections'!{c}17")
        s.cell(8, column, column - 3).number_format = "0"
        s.cell(9, column, f"=1/(1+'WACC'!$D$17)^{c}8").number_format = '0.000"x"'
        s.cell(10, column, f"={c}7*{c}9")
    summary = [
        (
            12,
            "Entradas e WACC > g válidos?",
            "=AND('Assumptions'!D30,'WACC'!D17>'Assumptions'!D23)",
        ),
        (14, "VP do período explícito", "=IF(D12,SUM(D10:H10),NA())"),
        (15, "FCFF terminal (ano seguinte)", "=IF(D12,H7*(1+'Assumptions'!D23),NA())"),
        (16, "Valor terminal (Gordon)", "=D15/('WACC'!D17-'Assumptions'!D23)"),
        (17, "VP do valor terminal", "=D16*H9"),
        (18, "Enterprise value", "=D14+D17"),
        (19, "Caixa e aplicações", "='Assumptions'!D24"),
        (20, "Dívida financeira", "='Assumptions'!D25"),
        (21, "Outros direitos / minoritários", "='Assumptions'!D26"),
        (22, "Equity value", "=D18+D19-D20-D21"),
        (23, "Ações usadas (milhões)", "='Assumptions'!D27"),
        (24, "Valor ilustrativo por ação (R$)", "=D22/D23"),
        (25, "VP terminal / enterprise value", "=D17/D18"),
    ]
    for row, label, formula in summary:
        s.cell(row, 3, label)
        s.cell(row, 4, formula)
    s["D24"].number_format = PRICE
    s["D25"].number_format = PERCENT
    s.merge_cells("C28:H30")
    s["C28"] = (
        f"Data-base {data['valuation_date']}; cinco fluxos anuais completos a partir desta data. "
        "Gordon cresce o FCFF final como bloco, sem ROIC terminal independente. "
        "O resultado depende da reinversão implícita; consulte metodologia."
    )

    s = book["Sensitivity"]
    s["C6"] = "R$/ação • WACC ↓ / g →"
    for column, offset in enumerate((-0.01, -0.005, 0, 0.005, 0.01), 4):
        c = get_column_letter(column)
        s.cell(6, column, f"='Assumptions'!$D$23+({offset})").number_format = PERCENT
        for row, spread in enumerate((-0.02, -0.01, 0, 0.01, 0.02), 7):
            s.cell(row, 3, f"='WACC'!$D$17+({spread})").number_format = PERCENT
            s.cell(
                row,
                column,
                (
                    f"=IF(AND('Assumptions'!$D$30,$C{row}>=0,{c}$6>-1,$C{row}>{c}$6),"
                    f"(NPV($C{row},'Projections'!$D$17:$H$17)"
                    f"+'Projections'!$H$17*(1+{c}$6)/($C{row}-{c}$6)/(1+$C{row})^5"
                    "+'Assumptions'!$D$24-'Assumptions'!$D$25-'Assumptions'!$D$26)"
                    "/'Assumptions'!$D$27,NA())"
                ),
            ).number_format = PRICE
    s.merge_cells("C14:H16")
    s["C14"] = (
        "Cada célula redesconta todos os FCFFs e a perpetuidade. Centro = DCF base. "
        "Combinações com WACC ≤ g ou taxas inválidas retornam #N/A deliberadamente."
    )

    s = book["Sources"]
    s.freeze_panes = "D7"
    s.column_dimensions["C"].width = 17
    for column, width in (("D", 38), ("E", 50), ("F", 30), ("G", 42), ("H", 56)):
        s.column_dimensions[column].width = width
    for column, label in enumerate(
        ("ID", "Documento", "URL", "Localização", "Abrangência", "Notas"), 3
    ):
        s.cell(6, column, label)
    for row, source in enumerate(data["sources"], 7):
        for column, key in enumerate(("id", "title", "url", "location", "scope", "notes"), 3):
            s.cell(row, column, source[key])
        s.row_dimensions[row].height = 100
    source_footer = 8 + len(data["sources"])
    s.merge_cells(f"C{source_footer}:H{source_footer}")
    s.cell(
        source_footer, 3, f"Fontes: {data['reviewed_on']}. Fixture offline; coleta live opcional."
    )
    if quote:
        s.cell(source_footer + 2, 3, "Cotação usada")
        s.cell(source_footer + 2, 4, quote["price"])
        s.cell(source_footer + 2, 5, quote["source_url"])
        s.cell(source_footer + 2, 6, quote["timestamp"])
        s.cell(source_footer + 2, 7, quote["provider"])

    s = book["MonteCarlo"]
    s["C3"] = f"Valuation {data['valuation_date']} • fair value em R$/ação • snapshot Python"
    s["C6"], s["D6"] = "Snapshot Python • não recalcula no Excel", "Valor"
    s["C7"], s["D7"] = "Seed", simulation.config.seed
    s["C8"], s["D8"] = "Número de trajetórias", simulation.config.samples
    for row, (key, item) in enumerate(simulation.summary.items(), 9):
        s.cell(row, 3, key)
        s.cell(row, 4, item).number_format = PRICE
    s["C17"], s["D17"] = "Cotação de comparação", quote["price"] if quote else "Indisponível"
    s["D17"].number_format = PRICE
    s["D7"].number_format = s["D8"].number_format = "0"
    s["C18"], s["D18"] = "Cotação: timestamp", quote["timestamp"] if quote else "Indisponível"
    s["C19"], s["D19"] = "Cotação: fonte", quote["source_url"] if quote else "Indisponível"
    s["C20"], s["D20"] = "Parâmetros Monte Carlo", json.dumps(
        simulation.config.metadata(), ensure_ascii=False
    )
    s["C21"], s["D21"] = "Premissas congeladas", json.dumps(asdict(a), ensure_ascii=False)
    checks = []
    for row in range(7, 12):
        for column in range(4, 9):
            cell = book["Assumptions"].cell(row, column)
            checks.append(f"'Assumptions'!{cell.coordinate}={cell.value!r}")
    for row in range(17, 29):
        cell = book["Assumptions"].cell(row, 4)
        checks.append(f"'Assumptions'!{cell.coordinate}={cell.value!r}")
    for column, period in enumerate(data["historical"], 4):
        checks.append(f"'Historical'!{get_column_letter(column)}7={period['revenue']!r}")
    s["C22"] = "Estado do snapshot"
    s["D22"] = "=IF(AND(" + ",".join(checks) + '),"CURRENT","STALE — rerun Python")'
    s.merge_cells("C23:I24")
    s["C23"] = (
        "Distribuições triangulares independentes; um spread de crescimento/margem por trajetória. "
        "Todo suporte atende WACC > g, sem clipping. Percentis subjetivos de fair value, "
        "não previsão "
        "de preço. Reexecute Python após editar entradas; fórmulas DCF continuam editáveis."
    )
    for column, label in enumerate(simulation.samples.columns, 3):
        s.cell(26, column, label)
    for row, values in enumerate(simulation.samples.itertuples(index=False, name=None), 27):
        for column, item in enumerate(values, 3):
            s.cell(row, column, item).number_format = PRICE if column == 9 else PERCENT
    s.column_dimensions["I"].width = 22
    s.freeze_panes = "D27"
    for row in (18, 19, 20, 21, 22):
        s.merge_cells(start_row=row, start_column=4, end_row=row, end_column=9)
    s.row_dimensions[20].height = 85
    s.row_dimensions[21].height = 130
    s.row_dimensions[23].height = 70

    for sheet in book:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                is_formula = cell.data_type == "f"
                is_input = (
                    sheet.title == "Assumptions"
                    and isinstance(cell.value, (int, float))
                    and cell.row != 6
                )
                color = (
                    "0000FF"
                    if is_input
                    else "008000"
                    if is_formula and "!" in cell.value
                    else "172B3A"
                )
                cell.font = Font(name="Aptos", size=11, color=color)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if cell.number_format == "General" and (
                    is_formula or isinstance(cell.value, (int, float))
                ):
                    cell.number_format = NUMBER
                if cell.row == 6:
                    cell.fill = PatternFill("solid", fgColor="173B4F")
                    cell.font = Font(name="Aptos", size=11, bold=True, color="FFFFFF")
                    if (
                        sheet.title in ("Assumptions", "Historical", "Projections", "DCF")
                        and cell.column > 3
                    ):
                        cell.number_format = '0"E"' if sheet.title != "Historical" else '0"A"'
                if is_input:
                    cell.fill = PatternFill("solid", fgColor="FFF4CE")
        sheet["C2"].font = Font(name="Aptos", size=20, bold=True, color="173B4F")
        sheet["C3"].font = Font(name="Aptos", size=11, italic=True, color="526574")
        for row in range(7, sheet.max_row + 1):
            if sheet.row_dimensions[row].height is None:
                sheet.row_dimensions[row].height = 29
        sheet.print_options.horizontalCentered = True
        sheet.print_area = "C2:I24" if sheet.title == "MonteCarlo" else f"C2:H{sheet.max_row}"
    for name, rows in (("DCF", (18, 22, 24)), ("Projections", (17,)), ("WACC", (17,))):
        for row in rows:
            for cell in book[name][row][2:8]:
                cell.border = Border(top=Side(style="thin", color="79909E"))
                cell.font = Font(name="Aptos", size=11, bold=True, color="173B4F")
                cell.fill = PatternFill("solid", fgColor="E8F0F4")
    book.calculation.fullCalcOnLoad = True
    book.calculation.forceFullCalc = True
    book.calculation.calcMode = "auto"
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    book.save(destination)
    return destination
