# MMM System - Plano de Implementacao

## Contexto e Objetivo

Construir um sistema auto-alimentado de Marketing Mix Modeling (MMM) que:
- Conecta-se continuamente as fontes de dados
- Produz recomendacoes actionable de alocacao de investimento
- Identifica levers subutilizadas
- Roda com cadencia recorrente (mensal com data pipeline semanal)
- Oferece multiplos modelos (Meridian + PyMC-Marketing) para comparacao

---

## Decisoes Arquiteturais

### Por que NAO Robyn como opcao principal?
- A versao madura e em R (nao Python) - dificulta integracao
- A versao Python esta em beta, traduzida via LLM, nao production-ready
- Abordagem frequentista (Ridge Regression) - nao produz intervalos de confianca reais
- Sem suporte nativo a modelagem geo-level hierarquica

### Por que Meridian + PyMC-Marketing?
| Aspecto | Meridian (Google) | PyMC-Marketing |
|---|---|---|
| Abordagem | Bayesiana hierarquica (NUTS/MCMC) | Bayesiana (MCMC via PyMC) |
| Linguagem | Python | Python |
| Incerteza | Distribuicoes posteriores completas | Distribuicoes posteriores completas |
| Geo-level | Suporte nativo hierarquico | Suportado |
| Calibracao | Priors de experimentos | Priors de lift test/geo-lift |
| Efeitos temporais | Limitado | Gaussian Processes (TV effects) |
| Memoria | Alta (5GB+) | Baixa (900MB-2.5GB) |
| Ecossistema | Inclinacao Google/YouTube | Neutro |
| Budget Optimizer | Built-in + Scenario Planner | Built-in |

**Resultado**: Rodar ambos e comparar outputs permite:
1. Cross-validar resultados (se ambos concordam, mais confianca)
2. Explorar forcas de cada um (Meridian para reach/frequency de video, PyMC para efeitos temporais)
3. Escolher o melhor modelo para cada contexto

---

## Arquitetura do Sistema

```
                    FONTE DE DADOS
                    [Google Sheets]
      (4 tabs: media_spend, kpi, external_factors, channel_config)
                           |
                     gspread (API v4)
                           |
                    [Sheets Connector]  ← modulo unico
                           |
                    [Validacao de Dados]
                           |
                    DATA WAREHOUSE
                    [PostgreSQL (daily) + DuckDB (analytics)]
                           |
                    [Agregacao Diaria → Semanal]
                           |
              +------------+------------+
              |                         |
        MODEL ENGINE 1            MODEL ENGINE 2
        [PyMC-Marketing]         [Google Meridian]
              |                         |
              +------------+------------+
                           |
                    MODEL REGISTRY
                    [MLflow / custom]
                           |
                    BUDGET OPTIMIZER
                    [Scenario Planner]
                           |
                    OUTPUT LAYER
                    [Dashboard Web App]
                           |
              +------------+------------+
              |            |            |
         Weekly       Saturation    Underused
         Report       Curves        Levers Alert
```

---

## Template Google Sheets

Workbook com 4 tabs. O pipeline descobre canais dinamicamente escaneando colunas `*_spend`.

### Tab 1: `media_spend` — Investimento Diario por Canal

Todos os canais (digital, offline, influenciadores, eventos) ficam nesta tab.
Cada canal tem coluna `{canal}_spend` (obrigatoria) e opcionalmente uma segunda metrica.

| Coluna | Tipo | Obrigatorio | Descricao |
|---|---|---|---|
| `date` | DATE (YYYY-MM-DD) | Sim | Data diaria |
| `google_ads_spend` | NUMBER (BRL) | Sim | Spend diario |
| `google_ads_impressions` | NUMBER | Nao | Impressoes |
| `meta_ads_spend` | NUMBER (BRL) | Sim | Spend diario |
| `meta_ads_impressions` | NUMBER | Nao | Impressoes |
| `tiktok_spend` | NUMBER (BRL) | Sim | Spend diario |
| `tiktok_impressions` | NUMBER | Nao | Impressoes |
| `programmatic_spend` | NUMBER (BRL) | Sim | Spend diario |
| `programmatic_impressions` | NUMBER | Nao | Impressoes |
| `tv_spend` | NUMBER (BRL) | Sim | Spend diario |
| `tv_grps` | NUMBER | Nao | Gross Rating Points |
| `radio_spend` | NUMBER (BRL) | Sim | Spend diario |
| `radio_spots` | NUMBER | Nao | Numero de spots veiculados |
| `ooh_spend` | NUMBER (BRL) | Sim | Spend diario |
| `ooh_faces` | NUMBER | Nao | Numero de faces/paineis ativos |
| `influencer_spend` | NUMBER (BRL) | Sim | Spend diario |
| `influencer_impressions` | NUMBER | Nao | Alcance estimado |
| `events_spend` | NUMBER (BRL) | Sim | Spend diario |
| `sponsorship_spend` | NUMBER (BRL) | Sim | Spend diario |
| `trade_actions_spend` | NUMBER (BRL) | Sim | Trade marketing spend |

**Regras**:
- Dias com zero spend: preencher com `0`, nao deixar em branco
- Impressoes/metricas secundarias sem dado: deixar em branco
- Adicionar novo canal: criar `{novo_canal}_spend` (e opcionalmente `{novo_canal}_impressions`)
- Valores em BRL, sem simbolo de moeda

### Tab 2: `kpi` — Metricas de Negocio Diarias

| Coluna | Tipo | Obrigatorio | Descricao |
|---|---|---|---|
| `date` | DATE (YYYY-MM-DD) | Sim | Data diaria |
| `revenue` | NUMBER (BRL) | Sim | Receita bruta diaria (KPI principal) |
| `transactions` | NUMBER | Nao | Numero de transacoes |
| `leads` | NUMBER | Nao | Leads gerados |
| `sessions` | NUMBER | Nao | Sessoes do site (GA4) |
| `conversions` | NUMBER | Nao | Conversoes online |

### Tab 3: `external_factors` — Variaveis de Controle

| Coluna | Tipo | Obrigatorio | Descricao |
|---|---|---|---|
| `date` | DATE (YYYY-MM-DD) | Sim | Data diaria |
| `ipca_monthly` | NUMBER (%) | Nao | Taxa IPCA (repetida para cada dia do mes) |
| `usd_brl` | NUMBER | Nao | Cotacao dolar |
| `selic_rate` | NUMBER (%) | Nao | Taxa SELIC |
| `promotion` | 0/1 | Nao | Promocao ativa? |
| `promotion_discount_pct` | NUMBER (%) | Nao | Percentual de desconto |
| `black_friday` | 0/1 | Nao | Periodo Black Friday |
| `christmas` | 0/1 | Nao | Periodo Natal |
| `carnival` | 0/1 | Nao | Periodo Carnaval |
| `mothers_day` | 0/1 | Nao | Periodo Dia das Maes |
| `competitor_major_campaign` | 0/1 | Nao | Campanha grande de concorrente |
| `price_index` | NUMBER | Nao | Indice medio de precos |

### Tab 4: `channel_config` — Configuracao por Canal

Tab de referencia (nao e serie temporal). O pipeline usa para configurar o modelo.

| Coluna | Tipo | Descricao |
|---|---|---|
| `channel_name` | TEXT | Deve corresponder ao prefixo em `media_spend` (ex: `google_ads`) |
| `channel_type` | TEXT | `digital`, `offline_tv`, `offline_radio`, `offline_ooh`, `influencer`, `events`, `sponsorship`, `trade` |
| `has_impressions` | TRUE/FALSE | Canal tem dados de impressoes/alcance? |
| `adstock_l_max_weeks` | NUMBER | Lag maximo em semanas (ver defaults abaixo) |
| `adstock_decay_prior_mu` | NUMBER | Prior mean do decay rate |
| `adstock_decay_prior_sigma` | NUMBER | Prior std do decay rate (default: 0.10) |
| `saturation_type` | TEXT | `logistic` (default) ou `hill` |
| `roi_prior_mu` | NUMBER | Prior mean do ROI esperado |
| `roi_prior_sigma` | NUMBER | Incerteza do prior de ROI |
| `min_budget_weekly` | NUMBER (BRL) | Budget minimo semanal (para otimizador) |
| `max_budget_weekly` | NUMBER (BRL) | Budget maximo semanal (para otimizador) |

---

## Defaults de Adstock por Tipo de Canal

| Tipo | l_max (semanas) | Decay Prior (mu) | Decay Prior (sigma) | Racional |
|---|---|---|---|---|
| Digital (Google, Meta, TikTok) | 4 | 0.30 | 0.10 | Efeito rapido, 1-2 semanas |
| Programatica (Display) | 4 | 0.35 | 0.10 | Ligeiramente mais persistente que search |
| TV | 8 | 0.60 | 0.15 | Efeito de marca longo, 4-8 semanas carryover |
| Radio | 6 | 0.50 | 0.12 | Persistencia media, 2-4 semanas |
| OOH | 8 | 0.55 | 0.15 | Exposicao longa, similar a TV |
| Influenciador | 4 | 0.35 | 0.15 | Alta variancia; conteudo pode viralizar ou morrer rapido |
| Eventos | 2 | 0.20 | 0.10 | Impacto imediato, pouco carryover |
| Patrocinio | 6 | 0.45 | 0.15 | Brand building, persistencia moderada |
| Trade Actions | 2 | 0.15 | 0.10 | Lift imediato de vendas, curta duracao |

Esses defaults sao pre-populados na tab `channel_config` mas podem ser ajustados com base no conhecimento do negocio ou benchmarks do Uncover.

---

## Modulos e Fases de Implementacao

### FASE 1: Fundacao (Semanas 1-3)
**Objetivo**: Infraestrutura base, data pipeline, e primeiro modelo rodando

#### 1.1 Setup do Projeto
- Estrutura monorepo Python com Poetry/uv
- Docker Compose para servicos locais (DB, dashboards)
- CI/CD basico

#### 1.2 Data Pipeline (Google Sheets)
- **Conector unico**: `sheets_connector.py` usando `gspread` + Google Sheets API v4
  - Autenticacao via Service Account (JSON key, env var `GOOGLE_SHEETS_CREDENTIALS_PATH`)
  - Funcoes: `fetch_media_spend()`, `fetch_kpi()`, `fetch_external_factors()`, `fetch_channel_config()`
  - `discover_channels()` — escaneia `*_spend` columns dinamicamente (nao precisa hardcodar canais)
  - Cache em Parquet (`data/raw/`) a cada sync para recovery e auditoria
- **Channel Registry**: `channel_registry.py` — ponte entre sheet e modelos
  - Le tab `channel_config` e gera configs para PyMC-Marketing e Meridian
  - `get_pymc_model_config()`: priors de adstock/saturacao por canal
  - `get_meridian_coord_to_columns()`: mapeamento de colunas para Meridian
  - `get_optimizer_constraints()`: min/max budget por canal
- **Validacao**:
  - Schema: `date` existe e e YYYY-MM-DD, `*_spend` e numerico e >= 0
  - Cross-tab: datas alinhadas entre as 3 tabs de serie temporal
  - Cross-ref: todo `*_spend` tem entrada correspondente em `channel_config`
  - Qualidade: null checks, outlier detection (> 3 std), gaps de datas
  - Output: `ValidationReport` com `errors` (bloqueante) e `warnings` (log)
- **Agregacao diaria → semanal**: `aggregator.py`
  - Spend: SUM por ISO week (segunda a domingo)
  - Flags booleanos (promocao, feriados): MAX por semana
  - Macro vars (IPCA, SELIC, USD/BRL): MEAN por semana
  - Impressoes/GRPs: SUM por semana
- **Storage**: PostgreSQL (formato long/melted) + DuckDB (analytics) + Parquet (snapshots)

#### 1.3 Primeiro Modelo (PyMC-Marketing)
- Comecar com PyMC-Marketing por ser mais leve e rapido
- Configurar modelo dinamicamente via `ChannelRegistry`:
  - KPI: receita (configuravel)
  - Media channels: todos os canais da sheet (digital + offline + influenciadores + eventos)
  - Controles: variaveis da tab `external_factors` (IPCA, promocoes, feriados, etc.)
  - Adstock: geometric decay com `l_max` = maximo entre todos os canais (8 semanas para TV)
  - Priors por canal: decay e ROI definidos na tab `channel_config`
  - Saturacao: Hill function
- Rodar primeiro modelo com dados historicos (minimo 2 anos)
- Validar resultados contra conhecimento do negocio e benchmarks do Uncover

### FASE 2: Multi-Model e Otimizacao (Semanas 4-6)
**Objetivo**: Segundo modelo, comparacao, e budget optimizer

#### 2.1 Segundo Modelo (Google Meridian)
- Instalar Meridian com suporte GPU (se disponivel)
- Configurar modelo com mesmos dados
- Adicionar reach/frequency data para canais de video (se aplicavel)
- Comparar outputs com PyMC-Marketing

#### 2.2 Model Comparison Framework
- Dashboard de comparacao lado a lado:
  - ROI por canal (ambos modelos)
  - Intervalos de confianca
  - Curvas de saturacao
  - Decomposicao de contribuicao
- Metricas de qualidade do modelo:
  - MAPE (Mean Absolute Percentage Error)
  - R-squared
  - Out-of-sample prediction accuracy
- Sistema de scoring para recomendar qual modelo confiar mais

#### 2.3 Budget Optimizer
- Otimizacao de alocacao com restricoes:
  - Budget total fixo OU flexivel
  - Minimos/maximos por canal
  - Target ROI ou target ROAS
- Cenarios what-if:
  - "E se eu aumentar Meta em 20%?"
  - "E se eu cortar TV?"
  - "Qual o budget otimo total?"
- Output: tabela de alocacao recomendada vs. atual

### FASE 3: Automacao e Dashboard (Semanas 7-10)
**Objetivo**: Sistema auto-alimentado com dashboard interativo

#### 3.1 Pipeline Automatizado
- **Cadencia**:
  - Diario: ingestao e validacao de dados
  - Semanal: validacao de data quality + alertas
  - Mensal: retrain completo dos modelos
  - Trimestral: revisao profunda da arquitetura do modelo
- Orquestracao via Prefect ou Airflow
- Alertas de anomalias nos dados (Slack/email)
- Model drift detection automatico

#### 3.2 Dashboard Web (inspirado no Uncover)
**Stack**: Next.js + Python API (FastAPI)

**Telas principais** (inspiradas no Uncover):

1. **ROI 360** - Visao geral
   - ROI/ROAS por canal com intervalos de confianca
   - Contribuicao de cada canal para o KPI
   - Waterfall chart de decomposicao (baseline + canais + fatores externos)
   - Comparacao entre modelos (Meridian vs PyMC)

2. **Media Optimizer** - Alocacao de budget
   - Alocacao atual vs. recomendada (bar chart comparativo)
   - Saturation curves interativas por canal
   - Simulador de cenarios (sliders para ajustar budget)
   - Underused levers highlight (canais com alto ROI marginal)

3. **Metrics Manager** - Dados em tempo real
   - KPIs diarios (spend, conversoes, receita)
   - Tracking de budget executado vs. planejado
   - Alertas de desvio

4. **Forecasting**
   - Projecao de receita baseada no plano de midia
   - Sensibilidade a mudancas de budget
   - Cenarios otimista/pessimista/base

5. **Insights Semanais** (feature diferencial)
   - Report automatico semanal com:
     - Top 3 recomendacoes actionable
     - Canais com maior oportunidade de melhoria
     - Alertas de saturacao (canal X atingiu ponto de retornos decrescentes)
     - Comparacao semana vs. semana
   - Envio automatico por email/Slack

### FASE 4: Calibracao e Feedback Loop (Semanas 11-14)
**Objetivo**: Loop de aprendizado continuo

#### 4.1 Integracao com Experimentos
- Framework para rodar geo-lift tests
- Integracao de resultados de incrementality tests como priors
- Calibracao automatica: resultados de experimentos alimentam a proxima rodada do modelo
- PyMC-Marketing tem suporte nativo para isso

#### 4.2 Feedback Loop Completo
```
Modelo atual --> Recomendacao de alocacao
       |
       v
  Implementacao pelo time de midia
       |
       v
  Dados reais de performance
       |
       v
  Validacao modelo vs. realidade
       |
       v
  Ajuste de priors + retrain
       |
       v
  Modelo atualizado (proximo ciclo)
```

#### 4.3 Historico e Auditoria
- Log de todas as recomendacoes feitas
- Tracking de quais recomendacoes foram implementadas
- Medicao de impacto: "seguimos a recomendacao X, resultado foi Y"
- Melhoria continua do modelo baseada em resultados reais

---

## Stack Tecnologico

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+ | Unica linguagem para todo o stack |
| Modelos MMM | PyMC-Marketing + Meridian | Bayesianos, Python-native, complementares |
| Data Pipeline | Prefect | Mais simples que Airflow, Python-native |
| Banco de Dados | PostgreSQL + DuckDB | PostgreSQL (formato long/melted) para app, DuckDB para analytics |
| API Backend | FastAPI | Async, rapido, Python-native |
| Frontend | Next.js (React) | Dashboards interativos, SSR |
| Visualizacao | Plotly / Recharts | Graficos interativos (Python + JS) |
| Model Registry | MLflow | Versionamento de modelos e artefatos |
| Containerizacao | Docker Compose | Desenvolvimento local + deploy |
| Scheduling | Prefect (built-in) | Orquestracao + scheduling integrados |

---

## Estrutura de Diretorios

```
mmm-system/
├── docker-compose.yml
├── pyproject.toml
├── .env.example                    # GOOGLE_SHEETS_CREDENTIALS_PATH, DB_URL, etc.
│
├── src/
│   ├── pipeline/                   # Data pipeline
│   │   ├── connectors/
│   │   │   └── sheets_connector.py # UNICO conector (substitui todos os API connectors)
│   │   ├── transformers/
│   │   │   ├── aggregator.py       # Agregacao diaria → semanal
│   │   │   └── preprocessor.py     # Scaling, encoding, trend
│   │   ├── validators/
│   │   │   └── data_validator.py   # Schema + qualidade + cross-tab
│   │   ├── storage/
│   │   │   ├── postgres.py         # PostgreSQL read/write (formato long)
│   │   │   └── duckdb_analytics.py # DuckDB queries analiticas
│   │   └── orchestrator.py         # Prefect flows
│   │
│   ├── models/                     # MMM Models
│   │   ├── base.py                 # Abstract ModelWrapper + ModelResult
│   │   ├── channel_registry.py     # ChannelSpec + ChannelRegistry (ponte sheet→modelo)
│   │   ├── pymc_model.py           # PyMC-Marketing wrapper
│   │   ├── meridian_model.py       # Meridian wrapper
│   │   └── comparison.py           # Model comparison framework
│   │
│   ├── optimizer/                  # Budget optimization
│   │   ├── allocator.py            # Budget allocation engine
│   │   ├── scenarios.py            # What-if scenario engine
│   │   └── constraints.py          # Business constraints (da tab channel_config)
│   │
│   ├── insights/                   # Automated insights
│   │   ├── weekly_report.py
│   │   ├── alerts.py
│   │   └── recommendations.py
│   │
│   ├── api/                        # FastAPI backend
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── sync.py             # POST /api/sync (trigger sheets sync)
│   │   │   ├── channels.py         # GET /api/channels (canais descobertos)
│   │   │   ├── models.py           # GET /api/model/results/{model_type}
│   │   │   └── optimizer.py        # POST /api/optimizer/allocate
│   │   └── schemas/
│   │
│   └── calibration/
│       ├── geo_lift.py
│       └── priors.py
│
├── frontend/                       # Next.js dashboard
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
│
├── data/
│   ├── raw/                        # Parquet snapshots de cada sync
│   ├── processed/                  # Dados semanais agregados
│   └── models/                     # Artefatos de modelos treinados
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_pymc_model.ipynb
│   ├── 03_meridian_model.ipynb
│   └── 04_sheets_template_test.ipynb  # Teste de integracao com sheets
│
└── tests/
    ├── test_pipeline/
    │   ├── test_sheets_connector.py
    │   ├── test_validator.py
    │   └── test_aggregator.py
    ├── test_models/
    │   ├── test_channel_registry.py
    │   ├── test_pymc_model.py
    │   └── test_meridian_model.py
    └── test_optimizer/
```

---

## Features Inspiradas no Uncover (para replicar)

1. **"PlayStation for media professionals"** - UX interativa e gamificada para exploracao de dados
2. **Real-time model updates** - Modelos que se recalibram continuamente (nao reports estaticos)
3. **Triangulo de medicao integrado** - MMM + atribuicao last-click + testes de incrementalidade
4. **Marketing Data Hub** - Consolidacao automatica de dados fragmentados
5. **Self-service scenario simulation** - Simulador drag-and-drop de cenarios de budget
6. **Weekly insights automaticos** - Report semanal com top 3 acoes recomendadas
7. **Saturation alerts** - Alertas quando um canal atinge ponto de retornos decrescentes
8. **Underused levers detection** - Identificacao automatica de canais subutilizados com alto ROI marginal

---

## Cadencia Operacional Recomendada

| Frequencia | Acao |
|---|---|
| Diaria | Ingestao de dados, validacao basica |
| Semanal | Report de insights, validacao de data quality, alertas |
| Mensal | Retrain completo dos modelos, nova otimizacao de budget |
| Trimestral | Revisao da arquitetura do modelo, geo-lift tests, calibracao |
| Semestral | Avaliacao de novos canais, reavaliacao de priors |

**Por que mensal e nao semanal para o modelo?**
- Adicionar 1 semana a 2+ anos de dados representa < 1% de dados novos
- Efeitos de adstock levam ~3 meses para serem totalmente incorporados
- Mensal equilibra frescor com custo computacional e revisao humana
- O report semanal usa o modelo mais recente + dados frescos para gerar insights

---

## Riscos e Mitigacoes

| Risco | Mitigacao |
|---|---|
| Dados insuficientes (< 2 anos) | Comecar com dados disponiveis, usar priors informativos |
| Pouca variacao de spend entre canais | Recomendar testes deliberados de variacao |
| Modelo sugere alocacao errada | Calibracao com experimentos, nunca confiar cegamente |
| Custo computacional alto (GPU) | PyMC-Marketing como modelo primario (mais leve) |
| Complexidade de manutencao | Automacao maxima, alertas de drift |
| Dificuldade de interpretacao | Dashboard claro, insights em linguagem natural |
| Usuario corrompe dados na Sheet | Snapshots Parquet a cada sync para point-in-time recovery |
| Estrutura da sheet muda | Validacao de schema detecta mudancas imediatamente com erro claro |
| Canal adicionado sem config | Validacao cruzada: erro se `*_spend` nao tem entrada em `channel_config` |
| Google Sheets API rate limits | 4 reads por sync (bem dentro do limite de 300/min); backoff exponencial |

---

## Proximos Passos Imediatos

1. Criar o workbook Google Sheets com as 4 tabs conforme template acima
2. Preencher tab `channel_config` com todos os canais ativos e ajustar defaults
3. Popular as tabs `media_spend`, `kpi` e `external_factors` com dados historicos (ideal: 2+ anos diarios)
4. Definir o KPI principal (receita, conversoes, leads?)
5. Criar Service Account no Google Cloud e compartilhar a sheet com o email da service account
6. Comecar pela Fase 1: setup do projeto + sheets connector + primeiro modelo PyMC-Marketing
