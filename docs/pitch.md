# WEG: qualidade operacional ainda precisa caber no preço

**Estudo retrospectivo em 31/12/2024, preparado em 06/11/2026.** Os anos
2025–29 são cenários ilustrativos: este exercício não incorpora os resultados
posteriormente publicados nem uma cotação atual. Não é recomendação de investimento.

Escolhi a WEG (WEGE3) porque motores, automação e equipamentos para redes elétricas
permitem conectar demanda, capacidade instalada e reinvestimento à geração de caixa.
O objetivo do pitch é testar quanto se paga pelo crescimento, com a conta aberta.

## A tese

A WEG combina produtos de reposição e ciclo curto com projetos de maior duração em
geração, transmissão e distribuição. A exposição a diferentes mercados pode reduzir
a dependência de um único ciclo, mas não elimina risco cambial nem execução de
aquisições. Esse é o ponto de partida qualitativo; a diversificação não vira um
prêmio automático no valuation.

Em 2024, a receita foi de R$37.986,9 milhões e o EBITDA de R$8.503,0 milhões,
com margem de 22,4%. São dados reportados, não premissas. A fonte é a
[DFP 2024, tabela 1, p. 5](https://api.mziq.com/mzfilemanager/v2/d/50c1bd3e-8ac6-42d9-884f-b9d69f690602/f2b70b43-c767-ec6f-c3a5-a3da6aecf962?origin=1).

## Quanto o cenário paga

| Variável | Cenário ilustrativo |
| --- | ---: |
| Crescimento da receita em 2025–29 | 12%, 11%, 10%, 9%, 8% |
| Margem EBIT / alíquota operacional | 20% / 34% |
| D&A / capex / NWC, como % da receita | 2,5% / 4,5% / 20% |
| WACC nominal em reais | 14,652% |
| Crescimento nominal na perpetuidade | 4,0% |
| Enterprise value | R$45.324,9 milhões |
| Equity value | R$49.242,9 milhões |
| Valor por ação | **R$11,73** |
| Parcela do EV atribuída ao valor terminal descontado | 64,6% |

Os valores são reproduzíveis com `dcf`. A ponte para equity soma caixa e aplicações,
deduz dívida financeira e uma **hipótese de R$500 milhões** de outros direitos,
incluindo minoritários. Usa ações emitidas como aproximação das ações em circulação.
São simplificações materiais, descritas na [metodologia](methodology.md).

Não comparo R$11,73 a um preço de tela atual. A conclusão deste exercício é mais
restrita: estas premissas sustentam esse valor. Uma tese de preço maior precisa
explicitar margem, crescimento, reinvestimento ou custo de capital diferentes.

## O que mudaria minha avaliação

No lado operacional, acompanharia pedidos convertidos em receita, margem EBIT e
retorno dos investimentos em capacidade. No caixa, olharia especialmente estoques,
recebíveis e capex: crescimento pode consumir recursos antes de remunerar o acionista.

Na sensibilidade, o valor vai de aproximadamente R$9,51 a R$15,67 por ação para
WACC entre 12,652% e 16,652% e crescimento terminal entre 3% e 5%. É uma grade de
hipóteses, não um intervalo estatístico nem preços-alvo. Como quase dois terços do EV
vêm do terminal, pequenos ajustes nessa etapa têm peso relevante.

## Riscos que o modelo simplifica

- Mix de produtos e câmbio: uma margem consolidada fixa não captura mudanças por região.
- Aquisições: integração, desembolsos futuros e sinergias exigiriam modelagem separada.
- Capital de giro: a razão fixa de 20% pode esconder sazonalidade e atrasos de recebimento.
- Perpetuidade: crescer o FCFF final mantém implicitamente sua estrutura de reinvestimento;
  não há uma estimativa independente de ROIC terminal.
- Ponte patrimonial: derivativos, arrendamentos, minoritários e ações em tesouraria precisam
  de uma revisão específica antes de usar a conta numa decisão real.

O próximo teste econômico seria reconstruir o reinvestimento por segmento e comparar
o crescimento projetado com a capacidade financiada. Atualizar os dados de base é
necessário antes de discutir valor presente hoje.

Veja o [estudo setorial](industry-deep-dive.md), a [metodologia](methodology.md) e a
versão de leitura do [pitch em HTML](pitch.html). Fontes consultadas em 06/11/2026.
