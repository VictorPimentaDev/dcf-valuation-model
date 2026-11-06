# Equipamentos elétricos no Brasil: da expansão da rede ao caixa

Recorte: motores, automação e equipamentos de geração, transmissão e distribuição.
Estudo qualitativo preparado em 06/11/2026, com documentos setoriais de 2024–25 e demonstrações da WEG até setembro de 2026.
As relações econômicas abaixo são análise do autor, não projeções oficiais de receita.

## Onde a demanda começa

Uma fábrica compra um motor para expandir capacidade ou substituir um equipamento.
Uma concessionária encomenda um transformador para ligar nova geração, atender
demanda ou renovar a rede. A aplicação final importa: reposição industrial tem um
ciclo diferente de uma subestação que depende de licenciamento, financiamento e obras.

A WEG descreve essas famílias de produtos e seus ciclos nas
[demonstrações de 2024, pp. 3–4](https://api.mziq.com/mzfilemanager/v2/d/50c1bd3e-8ac6-42d9-884f-b9d69f690602/f2b70b43-c767-ec6f-c3a5-a3da6aecf962?origin=1).
O [PDE 2034 da EPE](https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-804/topico-758/PDE2034_Aprovado.pdf)
é uma referência para a expansão energética brasileira. O plano foi
[aprovado pelo MME em abril de 2025](https://www.gov.br/mme/pt-br/assuntos/noticias/2023-2026/mme-aprova-plano-decenal-de-expansao-de-energia-2034).
Planejamento setorial sinaliza necessidades de infraestrutura; não é uma carteira
de pedidos de um fabricante e não garante sua participação em contratos.

O MME associa ao PDE 2034 cerca de R$3,2 trilhões de investimentos e crescimento
de aproximadamente 25% da oferta interna de energia em dez anos. Esse agregado
inclui petróleo, gás e outras fontes: **não é o mercado endereçável de equipamentos
elétricos**, nem pode ser multiplicado pela participação da WEG para projetar vendas.
A leitura útil é localizar o gargalo de cada projeto: geração, conexão, transmissão,
distribuição ou consumo industrial. Fonte: comunicado do MME citado acima.

## Cadeia de valor e disputa comercial

| Elo | O que o cliente compara | Efeito econômico a investigar |
| --- | --- | --- |
| Materiais e componentes | Prazo, especificação, disponibilidade | Cobre, aço e componentes podem pressionar custo e estoques |
| Projeto e fabricação | Eficiência, confiabilidade, prazo de entrega | Engenharia e escala podem sustentar margem; capacidade ociosa pode reduzi-la |
| Integração e instalação | Compatibilidade, execução, garantia | Projetos maiores alongam recebimento e expõem multas |
| Reposição e manutenção | Base instalada, assistência, tempo de parada | Atendimento local pode favorecer recorrência |

Compararia fabricantes locais, multinacionais com produção regional e importadores
por aplicação e custo total de propriedade. Preço de compra é só uma parte: consumo
de energia, manutenção e parada operacional também entram na decisão. Isso não
permite assumir poder de preço uniforme em todas as linhas de produto.

## O ciclo aparece primeiro no capital de giro

Uma encomenda pode exigir compra de materiais meses antes da entrega. Se o cliente
não adianta recursos, o fornecedor financia estoque e produção em andamento. A receita
pode crescer junto com o lucro e, ainda assim, o fluxo de caixa cair temporariamente.
Esse é o motivo para modelar variação de NWC separadamente do EBIT.

Expandir uma fábrica também demanda desembolso antes da nova receita. No DCF deste
repositório, capex supera D&A: há reinvestimento líquido. As razões constantes são
um ponto de partida didático; uma projeção detalhada precisaria de projetos,
cronograma de entrada em operação e utilização de capacidade.

## Como levar a análise ao modelo

| Questão de pesquisa | Evidência necessária | Driver do DCF |
| --- | --- | --- |
| Pedidos viram entregas no prazo? | Carteira, cancelamentos, prazos | Crescimento da receita por ano |
| Há repasse de custo ou ganho de mix? | Margem por negócio e região | Margem EBIT |
| A expansão cabe na capacidade? | Investimentos e utilização | Capex, D&A e crescimento |
| Quanto caixa fica preso no ciclo? | Estoques, recebíveis e fornecedores | NWC e sua variação |
| O retorno suporta o crescimento terminal? | Capital empregado e retorno incremental | Reinvestimento e perpetuidade |

## O contraste com os números da companhia

A receita consolidada da WEG cresceu de R$37,99 bilhões em FY2024 para R$40,80
bilhões em FY2025 (+7,4%). No TTM até setembro de 2026 ficou em R$40,72 bilhões:
praticamente estável contra FY2025, embora os períodos se sobreponham e não sejam
uma comparação anual independente. A margem EBIT passou de 20,25% em FY2024
para 19,60% em FY2025 e 19,36% no TTM. Cálculos sobre
[DFP/ITR da CVM reconciliados na metodologia](methodology.md#fonte-unidade-e-reconciliação).

Isso impede transformar a tese de eletrificação em crescimento linear de lucro.
Uma tendência estrutural pode conviver com mix pior, custo maior e adiamento de
entregas. A WEG consolidada tem exposição internacional; sua receita não mede o
crescimento do mercado brasileiro de equipamentos. Não inferimos market share
nem tamanho do setor a partir desses números.

## Quatro mecanismos que podem mudar o retorno

| Mecanismo | Hipótese favorável | Evidência contrária | Como entra no modelo |
| --- | --- | --- | --- |
| Eficiência energética | Economia de energia justifica troca de motores | Cliente posterga capex por financiamento caro | Crescimento menor e WACC maior |
| Redes e conexão | Obras liberam pedidos de equipamentos | Licenciamento e conexão atrasam projetos | Receita adiada, NWC mais alto |
| Competição e materiais | Escala e serviço sustentam preço | Importações ou insumos comprimem rentabilidade | Margem EBIT menor |
| Expansão de capacidade | Mais entregas absorvem custos fixos | Capacidade entra antes da demanda | Capex alto com margem e giro piores |

Essa matriz é análise econômica do autor. Ela mostra uma limitação da simulação:
os choques podem ocorrer juntos, enquanto os quatro drivers sorteados são
independentes e NWC/capex ficam fixos. Para investigar um estresse setorial,
substitua o cenário inteiro, em vez de tratar P5 como limite de perda.

## Cenários e limites

Um cenário favorável combinaria execução da expansão de redes, demanda industrial e
entregas sem deterioração do capital de giro. Um cenário adverso reuniria adiamentos
de projetos, competição por preço e capacidade nova entrando antes da demanda.
Câmbio afeta tradução de receita e custos de maneiras diferentes; tratá-lo como
benefício automático seria um erro.

O modelo consolida todos os negócios em uma receita e uma margem. Não estima
participação de mercado, tamanho de mercado ou valor dos contratos da EPE para a WEG.
O estudo também não cobre a indústria elétrica brasileira inteira. Para aprofundar,
separaria primeiro os negócios de ciclo curto dos projetos de rede, mantendo os
mesmos vínculos entre receita, margem, reinvestimento e caixa.

Fontes consultadas em 06/11/2026. O documento de planejamento citado é o PDE 2034;
não há alegação de que seja a edição mais recente disponível.
