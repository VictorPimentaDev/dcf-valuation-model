# Metodologia do DCF

Data-base econômica: **31/12/2024**. Preparado em **06/11/2026**. O período
explícito cobre os anos completos de 2025 a 2029. São projeções didáticas, não
uma reconstrução de consenso daquela data nem uma análise atualizada.

Todos os fluxos e taxas são nominais em reais. Contas financeiras usam R$
milhões e ações usam milhões; a divisão retorna reais por ação. A moeda de
apresentação consolidada não remove a exposição cambial da operação.

## Histórico e ajustes

A [DFP 2024 da WEG](https://api.mziq.com/mzfilemanager/v2/d/50c1bd3e-8ac6-42d9-884f-b9d69f690602/f2b70b43-c767-ec6f-c3a5-a3da6aecf962?origin=1)
é a fonte dos dados no fixture. O relatório da administração traz receita,
EBITDA e D&A na tabela 1 da página 5, dívida e caixa na tabela 2 da página 6
e ações emitidas na página 7. A conversão de R$ mil para R$ milhões divide
por 1.000. A conversão das ações divide por 1.000.000.

EBIT histórico é EBITDA menos D&A. Não modelamos ajustes não recorrentes,
segmentos, aquisições futuras ou três demonstrações completas. Os dados
históricos servem de base e comparação, sem insinuar que todo crescimento
reportado foi orgânico.

## Receita e fluxo de caixa

Para cada ano, os drivers editáveis são crescimento, margem EBIT, D&A/receita,
capex/receita e NWC/receita. As relações são:

```text
Receita[t] = Receita[t−1] × (1 + crescimento[t])
EBIT[t] = Receita[t] × margem EBIT[t]
Imposto[t] = max(EBIT[t], 0) × alíquota
NOPAT[t] = EBIT[t] − Imposto[t]
NWC[t] = Receita[t] × NWC/receita[t]
ΔNWC[t] = NWC[t] − NWC[t−1]
FCFF[t] = NOPAT[t] + D&A[t] − Capex[t] − ΔNWC[t]
```

Capex e D&A são entradas positivas. Aumento de NWC consome caixa. O saldo
inicial de NWC equivale, por hipótese, a 20% da receita de 2024; não foi
extraído do balanço. A alíquota de 34% é uma simplificação uniforme, sem
jurisdições, incentivos, impostos diferidos ou uso de prejuízos fiscais.
Os helpers aceitam EBIT negativo, mas não geram crédito fiscal imediato.
O cenário padrão e a interface de premissas limitam margens a 0–100%.

Os crescimentos de 12%, 11%, 10%, 9% e 8% são escolhas do exercício. Margem
EBIT de 20%, D&A de 2,5%, capex de 4,5% e NWC de 20% da receita são hipóteses,
não guidance da WEG. A última margem histórica calculada fica próxima de
20,25%, tornando visível a mudança para 20% na projeção.

## WACC e perpetuidade

```text
Ke = taxa livre de risco + beta × prêmio de risco de ações
WACC = Ke × (1 − peso da dívida) + Kd × (1 − imposto) × peso da dívida
TV[2029] = FCFF[2029] × (1 + g) / (WACC − g)
EV = soma(FCFF[t] / (1 + WACC)^t) + TV[2029] / (1 + WACC)^5
```

O CAPM usa taxa livre de risco de 10%, beta alavancado de 0,90 e prêmio de 6%,
todos hipotéticos em BRL. Não adicionamos outro prêmio país. O custo da
dívida é 12% e o peso-alvo da dívida a valor de mercado é 10%; esse peso não
é calculado a partir dos saldos contábeis. O WACC resultante é 14,652%.

Os fluxos ocorrem ao fim do ano. Não há desconto de meio de ano. O valor
terminal usa g nominal de 4%; a matemática exige WACC > g e g > −100%.
A sensibilidade varia WACC em ±1/±2 pontos percentuais e g em ±0,5/±1 ponto.
Cada célula redesconta os cinco fluxos e o terminal.

**Limite material:** Gordon cresce o FCFF final como um bloco. O modelo não
estima um ROIC terminal independente nem normaliza capex e NWC em um sexto
ano. Logo, a reinversão implícita no último FCFF é carregada para a
perpetuidade. Para uma avaliação de investimento, seria necessário confrontar
essa reinversão com `g = taxa de reinvestimento × ROIC` e a capacidade
produtiva requerida. Aproximadamente 64,6% do EV padrão vem do terminal.

## Ponte para o acionista

```text
Equity = EV + caixa e aplicações − dívida financeira − outros direitos
Valor por ação = Equity / ações (milhões)
```

Caixa e aplicações de R$ 8.013,210 milhões e dívida de R$ 3.595,237 milhões
produzem caixa líquido de R$ 4.417,973 milhões. O caixa líquido divulgado
inclui também derivativos líquidos de R$ 190,678 milhões, excluídos deste
exercício. Essa diferença é intencional.

O FCFF é consolidado. Deduzimos R$ 500 milhões **hipotéticos** em outros
direitos para tornar explícita a necessidade de avaliar participações de
não controladores e outras obrigações. Esse número não é saldo contábil
nem valor justo reportado; arrendamentos, ativos não operacionais e direitos
de terceiros exigiriam análise própria antes de usar o valor por ação.

As 4.197,317998 milhões de ações são o total emitido ao fim de 2024,
aproximação do denominador econômico. Não há ajuste de ações em tesouraria,
diluição, recompras futuras ou eventos societários posteriores. Equity
negativo não é truncado para zero.

## Reprodução e verificação

A CLI aceita somente campos de `Assumptions`, exige valores finitos e
cinco períodos e valida os denominadores. O fixture é distribuído dentro
do pacote, sem downloads. No Excel, todas as saídas dependem das entradas
e a aba DCF bloqueia os principais resultados quando o check de validade
falha. As validações não protegem contra exclusão ou alteração de fórmulas.

Os testes usam contas independentes em Decimal e avaliam o subconjunto de
fórmulas gravadas. Foram verificados o centro da sensibilidade, o efeito de
alterações em 2029 e entradas inválidas. O arquivo inicial também passou por
recálculo e renderização em motor independente; Excel/LibreOffice nativo não
foi executado. openpyxl grava fórmulas sem cache de resultados.
