# Metodologia: WEG, DCF e incerteza dos drivers

Data da avaliação: **06/11/2026**. Base operacional: **TTM encerrado em 30/09/2026**.
Os cinco fluxos representam períodos sucessivos de 12 meses desde a avaliação
(Y1–Y5), pagos no fim de cada período. Não são previsões dos anos fiscais 2025–29.
Valores financeiros e ações em milhões; taxas e fluxos nominais em BRL.

## Fonte, unidade e reconciliação

O [fixture](../src/dcf_valuation/data/weg_research.json) registra fontes, datas,
hashes SHA-256 dos ZIPs consultados e a cotação observada. Os
[dados DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) e
[dados ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) são da CVM.
Selecionamos CNPJ `84.429.695/0001-11`, demonstrações consolidadas, versão 1,
DFP 31/12/2025 e ITR 30/09/2026. DRE e DFC usam períodos acumulados iniciados em
janeiro, evitando somar o trimestre isolado aos nove meses. R$ mil / 1.000 = R$ mi.

| R$ milhões | FY2025 | 9M2026 | 9M2025 | TTM = FY25 + 9M26 − 9M25 |
| --- | ---: | ---: | ---: | ---: |
| Receita (DRE 3.01) | 40.804,110 | 30.472,677 | 30.557,320 | 40.719,467 |
| EBIT (DRE 3.05) | 7.998,741 | 5.887,920 | 6.002,174 | 7.884,487 |
| D&A (DFC 6.01.01.02) | 1.001,296 | 772,679 | 705,858 | 1.068,117 |

EBITDA deste estudo = EBIT + D&A: R$8.952,604 milhões TTM. Não é uma série de
EBITDA ajustado. As linhas originais estão em
[cvm_weg.csv](../src/dcf_valuation/data/cvm_weg.csv); a composição do capital em
[capital_weg.json](../src/dcf_valuation/data/capital_weg.json). Testes reconciliam
TTM e ponte patrimonial com essas linhas. O antigo `weg_2024.json` é preservado
como referência histórica; não é a base padrão do research atualizado.

## Fluxo operacional

```text
Receita[t] = Receita[t−1] × (1 + crescimento[t])
EBIT[t] = Receita[t] × margem[t]
NOPAT[t] = EBIT[t] − max(EBIT[t], 0) × imposto
NWC[t] = Receita[t] × razão NWC
FCFF[t] = NOPAT[t] + D&A[t] − Capex[t] − (NWC[t] − NWC[t−1])
```

Crescimento Y1–Y5 de 12%, 11%, 10%, 9%, 8%; margem EBIT 20%; imposto 34%;
D&A 2,5%, capex 4,5% e NWC 20% da receita são **premissas do autor**, não guidance,
consenso, estimativas inferidas das demonstrações ou distribuições ajustadas a dados.
O NWC inicial também é 20% da receita-base. O cenário assume aceleração sobre o
histórico recente: é uma hipótese a defender, não extrapolação automática.
Não há crédito fiscal imediato se EBIT for negativo. A interface de cenários
limita margens a 0–100%. Aquisições e segmentos não são modelados separadamente.

## Desconto e terminal

```text
Ke = 10% + 0,90 × 6% = 15,4%
WACC = Ke × 90% + 12% × (1 − 34%) × 10% = 14,652%
TV[5] = FCFF[5] × (1 + g) / (WACC − g), com g = 4%
EV = Σ FCFF[t] / (1 + WACC)^t + TV[5] / (1 + WACC)^5
```

CAPM e peso-alvo da dívida são hipóteses nominais em reais. Não estimamos beta nem
prêmio de risco a partir da cotação. `numpy-financial.npv` desconta a série iniciada
com zero em t=0. Validações rejeitam WACC ≤ g, denominadores nulos e valores não
finitos. A sensibilidade WACC × g redesconta todos os fluxos e o terminal.

Gordon cresce o FCFF final como um bloco: não há sexto ano normalizado nem ROIC
terminal independente. A coerência entre crescimento, reinvestimento e retorno
precisa ser testada antes de usar o estudo numa decisão de investimento.

## Ponte patrimonial em 30/09/2026

| Componente | R$ milhões |
| --- | ---: |
| Caixa e equivalentes + aplicações circulantes | 5.484,016 + 855,431 = 6.339,447 |
| Empréstimos e financiamentos circulantes + não circulantes | 1.917,755 + 1.836,690 = 3.754,445 |
| Arrendamentos circulantes + não circulantes | 193,101 + 598,991 = 792,092 |
| Participações não controladoras, saldo contábil | 1.410,309 |
| Outros direitos deduzidos: arrendamentos + não controladores | 2.202,401 |

Equity = EV + caixa − dívida − outros direitos. Ações = 4.197,317998 milhões
emitidas − 1,488307 milhões em tesouraria = **4.195,829691 milhões**. As contas
BPA/BPP e composição do capital estão no extrato CVM citado acima.

**Simplificações materiais:** NCI contábil é proxy, não valor justo. Arrendamentos
são tratados como financiamento; não há ajuste separado da despesa de aluguel no
EBIT, além do tratamento contábil já reportado. Não são incluídos derivativos,
ativos não operacionais adicionais, diluição futura ou alterações patrimoniais
entre 30/09 e 06/11. A base TTM é usada como ritmo inicial na data da avaliação,
sem estimar o mês intermediário. Equity negativo não é truncado para zero.

## Monte Carlo reproduzível

10.000 trajetórias, `numpy.random.default_rng(seed=42)` e sorteios triangulares
simétricos via `scipy.stats.triang`. Cada distribuição tem moda no cenário base:

| Driver | Suporte da distribuição |
| --- | --- |
| Crescimento | deslocamento entre −5 e +5 pontos percentuais, somado a cada ano |
| Margem EBIT | deslocamento entre −4 e +4 pp, somado a cada ano |
| WACC | 12,152% a 17,152%, moda 14,652% |
| Crescimento terminal | 2,5% a 5,5%, moda 4% |

Os quatro sorteios são independentes entre si. Crescimento e margem têm um único
deslocamento persistente por trajetória, criando correlação perfeita dos choques
entre os cinco anos. WACC e g permanecem constantes dentro de cada trajetória.
Capex, D&A, NWC, impostos e ponte patrimonial ficam fixos. Validamos o suporte
inteiro antes de sortear: não há truncamento silencioso nem descarte seletivo de
cenários. Todo cenário executa o mesmo núcleo do DCF determinístico.

Essas distribuições limitadas excluem crises, mudanças de regime e dependências
entre crescimento, margens e juros. O intervalo P5–P95 é uma faixa **condicional às
hipóteses**, não intervalo de confiança empírico. A fração acima da cotação não é
probabilidade de a ação subir. Mais sorteios reduzem ruído numérico, não erro de modelo.

O histograma mostra fair value/ação; o fan chart mostra receita, não preço futuro.
O tornado altera um driver de cada vez entre seus P10/P90, mantendo os outros na
moda; é sensibilidade local, não atribuição causal nem decomposição de variância.
O quarto gráfico coloca a cotação no mesmo eixo dos intervalos de percentis do fair value.

## Cotação, Excel e atualização

`get_quote()` usa o snapshot versionado. `get_quote(live=True)` e `dcf --live`
consultam `regularMarketPrice` e `regularMarketTime` do Yahoo Finance via yfinance,
com moeda BRL e ticker WEGE3.SA validados. A cotação pode ter atraso. Data de mercado
e instante de coleta são distintos; falha de rede não vira fallback silencioso.
Uma nova cotação não atualiza os fundamentos nem muda automaticamente a data da
avaliação. Se as datas se afastarem, atualize a pesquisa antes de interpretar o spread.

As seis abas de cálculo preservam fórmulas editáveis e `Sources` é só texto. `MonteCarlo`
contém parâmetros, seed, resumo, cotação e amostras calculadas em Python. Ela é um
**snapshot**, não uma simulação dinâmica do Excel: sua única fórmula marca o estado
como desatualizado; após editar premissas, execute o Python novamente.
openpyxl não calcula caches das fórmulas; Excel/LibreOffice precisa recalculá-las.
O notebook e a CLI funcionam sem rede no modo padrão. Testes de rede usam mocks;
a coleta real da cotação na preparação foi verificada separadamente.
