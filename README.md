# DCF da WEG

**English summary:** A small Python valuation package that builds an editable,
formula-driven Excel DCF for WEG. Public historical figures, explicit illustrative
assumptions, and reproducible tests. This is a retrospective educational model.

Modelo de fluxo de caixa descontado da WEG (WEGE3), com base em 31/12/2024.
O objetivo é deixar a conta aberta: da receita ao valor por ação.

Escolhi a WEG porque sua operação industrial permite discutir margem,
reinvestimento e capital de giro sem o tratamento específico que um banco exigiria.
O histórico 2022–2024 vem da DFP; as projeções 2025–2029 são **ilustrativas**.
O modelo foi preparado em novembro de 2026, mas não incorpora os resultados de
2025–2026 nem representa um valuation atualizado. Não é recomendação de investimento.

## Rodar

Python 3.11 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
dcf --output outputs/weg-dcf.xlsx
# Alternativa equivalente:
python -m dcf_valuation --output outputs/weg-dcf.xlsx
```

O comando não usa a rede. Gera o Excel e imprime os resultados do cálculo Python:

| Métrica | Padrão ilustrativo |
| --- | ---: |
| WACC nominal em reais | 14,652% |
| Enterprise value | R$ 45.324,89 milhões |
| Equity value | R$ 49.242,86 milhões |
| Valor por ação | R$ 11,73 |

O Excel contém fórmulas e solicita recálculo automático ao abrir. **openpyxl não
calcula nem salva resultados em cache**: leitores que exibem apenas valores
armazenados podem mostrar células vazias até o recálculo em Excel/LibreOffice.
O resumo do terminal é calculado em Python e funciona sem aplicativo de planilha.

## Alterar premissas

Edite as células azuis da aba `Assumptions`, ou passe um JSON com os campos que
quiser substituir. Taxas usam frações: `0.10` significa 10%. Valores financeiros
estão em R$ milhões; ações, em milhões de ações.

```json
{
  "growth": [0.10, 0.09, 0.08, 0.07, 0.06],
  "ebit_margin": [0.20, 0.20, 0.21, 0.21, 0.21],
  "terminal_growth": 0.035
}
```

Salve como `scenario.json` e execute:

```bash
dcf --assumptions scenario.json --output outputs/scenario.xlsx
```

Os drivers anuais exigem cinco valores. Entradas não finitas, ações nulas,
proporções fora de faixa e crescimento terminal maior ou igual ao WACC são
rejeitados pela CLI. O Excel tem validação de entrada e uma checagem que também
detecta vários valores inválidos colados diretamente. A planilha não é protegida:
fórmulas podem ser editadas, e isso exige revisão de quem as altera. O JSON não é
atualizado quando você edita o Excel. O destino indicado é sobrescrito ao gerar.

## O que há no arquivo

| Aba | Conteúdo |
| --- | --- |
| Assumptions | Drivers anuais, custo de capital e ponte para o acionista |
| Historical | Receita, EBITDA e D&A de 2022–2024, EBIT e margem calculados |
| Projections | Receita, EBIT, impostos, NOPAT, D&A, capex, NWC e FCFF |
| DCF | Desconto ao fim do ano, perpetuidade, EV, equity e valor por ação |
| WACC | CAPM e estrutura-alvo de capital |
| Sensitivity | Valor por ação por WACC × crescimento terminal |
| Sources | Links, localização, unidades, data de conferência e ressalvas |

A sensibilidade redesconta cada fluxo e o valor terminal. Seu centro reproduz o
DCF base. Pares inválidos, como WACC ≤ g, ficam em `#N/A` de propósito.

## Dados e leitura

O [fixture versionado](src/dcf_valuation/data/weg_2024.json) guarda números,
unidades e referências. A fonte financeira é a
[DFP WEG 2024](https://api.mziq.com/mzfilemanager/v2/d/50c1bd3e-8ac6-42d9-884f-b9d69f690602/f2b70b43-c767-ec6f-c3a5-a3da6aecf962?origin=1):
relatório da administração, páginas 5–7. Não há scraping nem dependência de
disponibilidade do RI durante os testes.

- [Metodologia e limitações](docs/methodology.md)
- [Pitch da ação](docs/pitch.md), também em [HTML para leitura e impressão](docs/pitch.html)
- [Deep dive: equipamentos elétricos no Brasil](docs/industry-deep-dive.md)

Caixa, dívida e ações emitidas têm fonte pública. O ajuste de outros direitos de
R$ 500 milhões, inclusive minoritários, é uma **hipótese**, não uma avaliação
observada. Derivativos não entram no caixa. Ações emitidas são uma aproximação
das ações diluídas em circulação. A metodologia detalha essas escolhas e o
tratamento da reinversão terminal.

## Verificar

```bash
pytest -q
ruff check .
python -m build
```

Os testes confrontam o DCF com uma conta independente em `Decimal`, verificam
WACC, perpetuidade, sensibilidade, entradas inválidas, CLI e as fórmulas gravadas
no Excel. Alterar um driver de 2029 deve mudar o valuation sem mudar 2025.
O avaliador de fórmulas dos testes cobre somente o subconjunto usado aqui; não é
um substituto para testes de compatibilidade do Excel.

Na entrega inicial, as sete abas também foram renderizadas e recalculadas por
um motor independente. Não foi executado Excel/LibreOffice nativo. O workflow
executa pytest e ruff em Python 3.11 e 3.13, além de construir o pacote e gerar
um Excel de exemplo.

Código sob [licença MIT](LICENSE). Documentos de terceiros continuam sujeitos
às condições dos seus respectivos autores.
