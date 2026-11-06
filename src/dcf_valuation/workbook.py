"""Seven-sheet editable Excel model. Excel/LibreOffice performs recalculation."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .model import Assumptions, load_data

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


def build_workbook(output: str | Path, assumptions: Assumptions | None = None) -> Path:
    a = assumptions or Assumptions()
    data = load_data()
    book = Workbook()
    book.remove(book.active)
    for title in (
        "Assumptions",
        "Historical",
        "Projections",
        "DCF",
        "WACC",
        "Sensitivity",
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
        sheet["C3"] = "Base 31/12/2024 • R$ milhões • modelo retrospectivo ilustrativo"
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
    for column, year in enumerate(range(2025, 2030), 4):
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
        ("Caixa e aplicações", a.cash, "DFP24 p. 6; exclui derivativos"),
        ("Dívida financeira", a.debt, "DFP24 p. 6; não inclui outros direitos"),
        (
            "Outros direitos / minoritários",
            a.other_claims,
            "Hipótese de R$500 mi; estimativa a revisar",
        ),
        ("Ações emitidas (milhões)", a.shares, "DFP24 p. 7; proxy, sem ajuste de tesouraria"),
        ("NWC inicial / receita 2024", a.opening_nwc_ratio, "Hipótese: 20%; não é saldo divulgado"),
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
    s["C6"] = "Histórico reportado • DFP24"
    for column, period in enumerate(data["historical"], 4):
        letter = get_column_letter(column)
        s.cell(6, column, period["year"])
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
        "DFP24 p. 5, tabela 1. Valores divulgados em R$ mil convertidos para R$ milhões. "
        "Receita, EBITDA e D&A são reportados; EBIT e margem são calculados."
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
        revenue_base = "'Historical'!F7" if column == 4 else f"{previous}7"
        nwc_base = "'Historical'!F7*'Assumptions'!$D$28" if column == 4 else f"{previous}15"
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
        (23, "Ações emitidas (milhões)", "='Assumptions'!D27"),
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
        "Data-base 31/12/2024; fluxos anuais ao fim de 2025–29. "
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
    s.merge_cells("C12:H12")
    s["C12"] = f"Conferência das fontes: {data['reviewed_on']}. Dados embutidos, sem coleta em CI."

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
        sheet.print_area = f"C2:H{sheet.max_row}"
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
