# 📡 MONITORING-NOTEBOOKLM-PY.md
## Documento Arquitetural — Sistema de Monitoramento da Biblioteca `notebooklm-py`

**Repositório:** `modellnxia/ultracognia-pesquisaapi-green`
**Versão:** 1.0
**Atualizado:** 2026-04-23
**Responsável:** modellnxia / Ramon Turbay Muliterno

---

## 1. Visão Geral

### O que é `notebooklm-py`?

`notebooklm-py` é uma biblioteca Python não-oficial que expõe a API interna do **Google NotebookLM** para uso programático. Ela permite:

- Criar e gerenciar notebooks no NotebookLM via código
- Adicionar fontes (URLs, arquivos PDF, textos)
- Gerar artefatos: podcast (áudio), slide decks e resumos
- Enviar perguntas via chat sobre o conteúdo dos notebooks

**Instalação:**
```bash
pip install notebooklm-py
notebooklm login  # autenticação via Google OAuth
```

**Uso neste projeto (`notebook_runner.py`):**
```python
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength, SlideDeckFormat

async with await NotebookLMClient.from_storage() as client:
    nb = await client.notebooks.create(nome)
    await client.sources.add_url(nb.id, url, wait=True)
    await client.artifacts.generate_slide_deck(nb.id, ...)
    await client.sources.delete(nb.id, source_id)
    await client.notebooks.delete(nb.id)
```

### Por que monitorar?

| Risco | Impacto | Probabilidade |
|-------|---------|---------------|
| Google muda API interna do NotebookLM | Quebra total do sistema | Alta |
| `notebooklm-py` lança breaking change | Quebra de integração | Média |
| Deprecação de endpoints RPC | Falha silenciosa | Média |
| Vulnerabilidade de segurança na lib | Exposição de credenciais | Baixa |
| Mudança no fluxo de autenticação OAuth | Login inoperante | Média |

### Riscos de Mudanças Não Detectadas

```
Sem monitoramento ativo:
├── Deploy passa, mas notebook_runner.py falha em produção
├── Slides/podcasts não são gerados sem aviso
├── Credenciais OAuth expiram sem notificação
├── Bug silencioso injeta prompt oculto em notebooks errados
└── Dados de usuários podem vazar se a lib mudar o comportamento de delete
```

---

## 2. Pontos Críticos da Biblioteca

### APIs de Maior Risco

| Módulo | Função | Risco | Crítico |
|--------|--------|-------|---------|
| `client.notebooks` | `create()`, `delete()` | Mudança de parâmetros | ⚠️ Alto |
| `client.sources` | `add_url()`, `add_file()`, `add_text()`, `delete()` | Renomeação / novo campo obrigatório | ⚠️ Alto |
| `client.artifacts` | `generate_audio()`, `generate_slide_deck()`, `download_audio()`, `download_slide_deck()`, `wait_for_completion()` | Task ID / timeout / formato de retorno | 🔴 Crítico |
| `client.chat` | `ask()` | Estrutura da resposta | ⚠️ Alto |
| `NotebookLMClient` | `from_storage()` | Fluxo de autenticação | 🔴 Crítico |
| `notebooklm.rpc.types` | `SlideDeckLength`, `SlideDeckFormat` | Valores de enum removidos/renomeados | ⚠️ Alto |

### Pontos de Atenção no `notebook_runner.py`

```python
# LINHA 91 — from_storage() depende do arquivo de sessão OAuth
async with await NotebookLMClient.from_storage() as client:

# LINHAS 184-191 — Enums de RPC podem mudar entre versões
slide_status = await client.artifacts.generate_slide_deck(
    nb.id,
    slide_format=SlideDeckFormat.PRESENTER_SLIDES,   # ← enum crítico
    slide_length=SlideDeckLength.DEFAULT,              # ← enum crítico
    instructions="...",
)

# LINHA 191 — timeout hardcoded pode ser insuficiente com nova versão
await client.artifacts.wait_for_completion(nb.id, slide_status.task_id, timeout=1200)
```

### Versões & EOL (End of Life)

```
notebooklm-py segue versionamento semver (MAJOR.MINOR.PATCH)
MAJOR → Breaking changes garantidos
MINOR → Novas features, possível deprecação
PATCH → Bug fixes (geralmente seguro)

Verificar versão atual:
pip show notebooklm-py
```

---

## 3. Arquitetura de Monitoramento

### Fluxo: Detecção → Análise → Alerta → Ação

```
┌─────────────────────────────────────────────────────────────┐
│                   FONTES DE MONITORAMENTO                   │
│                                                             │
│  PyPI API              GitHub Releases       RSS/Atom       │
│  (versão atual)        (notebooklm-py repo)  (changelog)   │
└────────────┬───────────────┬──────────────────┬────────────┘
             │               │                  │
             ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│           SCRIPT: check_notebooklm_updates.py              │
│                                                             │
│  1. Consulta PyPI para versão mais recente                  │
│  2. Compara com versão instalada em requirements.txt        │
│  3. Busca releases no GitHub da biblioteca                  │
│  4. Analisa changelog para breaking changes                 │
│  5. Classifica o tipo de atualização                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CLASSIFICAÇÃO DA MUDANÇA                       │
│                                                             │
│  PATCH (x.x.N) → 🟢 Info — Baixo risco                     │
│  MINOR (x.N.x) → 🟡 Warning — Testar antes                 │
│  MAJOR (N.x.x) → 🔴 Critical — Breaking change provável    │
│  Vuln detectada → 🚨 Security Alert                         │
└────────────────────────┬────────────────────────────────────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │  Slack   │ │  GitHub  │ │  Log     │
      │  Alert   │ │  Issue   │ │  File    │
      └──────────┘ └──────────┘ └──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  RUNBOOK ACIONADO   │
              │  (ALERT-RUNBOOK.md) │
              └─────────────────────┘
```

### Integrações

| Integração | Propósito | Quando |
|------------|-----------|--------|
| PyPI JSON API | Obter versão mais recente | A cada execução |
| GitHub API (releases) | Ler changelog | A cada execução |
| Slack Webhook | Notificação imediata | Quando há update |
| GitHub Issues | Rastreamento | Quando há major/minor update |
| GitHub Actions | Agendamento automático | Segunda-feira 9h |

---

## 4. Ferramentas & Integração

### Dependabot (GitHub)

Adicione ao `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    labels:
      - "dependencies"
      - "notebooklm"
    reviewers:
      - "modellnxia"
```

**Prós:** Automático, cria PR com diff  
**Contras:** Não analisa breaking changes de API interna

### Renovate

```json
{
  "extends": ["config:base"],
  "packageRules": [
    {
      "matchPackageNames": ["notebooklm-py"],
      "automerge": false,
      "labels": ["notebooklm-update"],
      "assignees": ["modellnxia"]
    }
  ]
}
```

**Prós:** Flexível, suporte a rollback automático  
**Contras:** Requer configuração adicional

### Snyk

```bash
pip install snyk
snyk test --file=requirements.txt
snyk monitor --file=requirements.txt
```

**Prós:** Detecta vulnerabilidades de segurança  
**Contras:** Plano pago para recursos avançados

### Script Customizado (Recomendado para este projeto)

```bash
python scripts/check_notebooklm_updates.py
```

**Prós:** Controle total, análise de breaking changes customizada, sem custo  
**Contras:** Requer manutenção

### Estratégia Recomendada

```
Para o ultracognia-pesquisaapi-green:

1. PRIMARY:   Script customizado (check_notebooklm_updates.py)
              └── Rodado via GitHub Actions toda segunda-feira

2. SECONDARY: Dependabot
              └── Cria PRs automáticos de atualização

3. SECURITY:  Snyk (opcional, plano free)
              └── Scan de vulnerabilidades em dependencies
```

---

## 5. Tipos de Alertas

### Matriz de Alertas

| Tipo | Trigger | Severidade | Canal | Ação |
|------|---------|------------|-------|------|
| 🟢 Nova versão (patch) | `x.x.N+1` disponível | Info | Log + Slack info | Testar e atualizar |
| 🟡 Nova versão (minor) | `x.N+1.x` disponível | Warning | Slack + Issue | Revisar changelog, testar |
| 🔴 Breaking change (major) | `N+1.x.x` disponível | Critical | Slack urgente + Issue + Email | Runbook completo |
| 🚨 Vulnerabilidade | CVE detectada | Security | Slack + Issue imediato | Patch urgente |
| ⚠️ Deprecação de API | Aviso no changelog | High | Slack + Issue | Planejar migração |
| 💀 EOL anunciado | Versão sem suporte | Critical | Slack + Issue | Planejar substituição |

### Formato dos Alertas Slack

**Patch update:**
```
[INFO] notebooklm-py: Nova versão patch disponível
Atual: 0.3.1 → Nova: 0.3.2
Risco: 🟢 Baixo
Ação: Testar localmente antes de atualizar
```

**Major update:**
```
🚨 [CRITICAL] notebooklm-py: MAJOR VERSION UPDATE
Atual: 0.3.1 → Nova: 1.0.0
Risco: 🔴 BREAKING CHANGES PROVÁVEIS
Ação: CONSULTAR RUNBOOK IMEDIATAMENTE
Link: https://github.com/modellnxia/ultracognia-pesquisaapi-green/blob/main/ALERT-RUNBOOK.md
```

---

## 6. Runbook para Desenvolvedores

> Para o guia completo passo a passo, consulte: **[ALERT-RUNBOOK.md](./ALERT-RUNBOOK.md)**

### Resumo Rápido

```
1. Recebeu alerta → Leia o ALERT-RUNBOOK.md
2. Crie uma branch: git checkout -b fix/update-notebooklm-vX.Y.Z
3. Atualize requirements.txt
4. Teste localmente: python notebooklm/primeira_fase/notebook_runner.py
5. Abra PR com label "notebooklm-update"
6. modellnxia faz review + merge
```

### Como Testar Localmente

```bash
# 1. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# 2. Instale nova versão
pip install notebooklm-py==X.Y.Z

# 3. Autentique
notebooklm login

# 4. Rode o script
python notebooklm/primeira_fase/notebook_runner.py

# 5. Verifique os outputs
ls outputs/
```

### Rollback de Emergência

```bash
# Volte para versão anterior no requirements.txt
# Ex: notebooklm-py==0.3.1 (versão estável conhecida)

git checkout -b hotfix/rollback-notebooklm
# edite requirements.txt
git commit -m "hotfix: rollback notebooklm-py para versão estável"
git push origin hotfix/rollback-notebooklm
# Abra PR urgente para modellnxia
```

---

## 7. Automação GitHub Actions

> Arquivo completo: **[.github/workflows/monitor-notebooklm.yml](.github/workflows/monitor-notebooklm.yml)**

### Agendamento

```
Toda segunda-feira às 9h UTC
Cron: 0 9 * * MON
```

### Jobs do Workflow

```yaml
jobs:
  check-updates:      # Verifica versões no PyPI e GitHub
  analyze-changes:    # Analisa tipo de mudança (patch/minor/major)
  notify:             # Envia alertas para Slack
  create-issue:       # Cria issue no repo se major/minor
```

### Secrets Necessários

Configure em `Settings → Secrets → Actions`:

| Secret | Descrição | Obrigatório |
|--------|-----------|-------------|
| `SLACK_WEBHOOK_URL` | URL do webhook do Slack | Sim (para alertas) |
| `GH_TOKEN` | Token GitHub para criar issues | Sim (para issues) |
| `PYPI_NOTEBOOKLM_PACKAGE` | Nome do pacote (default: notebooklm-py) | Não |

---

## 8. Métricas & Dashboard

### KPIs de Monitoramento

| Métrica | Descrição | Meta |
|---------|-----------|------|
| Tempo de detecção | De release → alerta recebido | < 7 dias |
| Tempo de resposta | De alerta → PR criado | < 3 dias úteis |
| Tempo de adoção | De PR → deploy em produção | < 5 dias úteis |
| Taxa de atualização | % de patches aplicados dentro do SLA | > 90% |
| Cobertura de testes | % de funcionalidades testadas | > 80% |

### Histórico de Updates

Crie uma tabela em `docs/notebooklm-update-history.md` (opcional):

```markdown
| Data       | Versão Anterior | Versão Nova | Tipo   | Responsável | PR    | Notas |
|------------|----------------|-------------|--------|-------------|-------|-------|
| 2026-04-23 | 0.3.0          | 0.3.1       | patch  | Ramon       | #12   | OK    |
```

### Dashboard (Futuro)

Para evolução futura, considere integrar com:
- **Grafana + Prometheus** — métricas de latência da API NotebookLM
- **GitHub Insights** — frequência de atualizações
- **Datadog / New Relic** — monitoramento de erros em produção

---

## Apêndice: Estrutura de Arquivos Adicionados

```
ultracognia-pesquisaapi-green/
├── MONITORING-NOTEBOOKLM-PY.md      ← Este documento
├── ALERT-RUNBOOK.md                  ← Guia de ação para alertas
├── scripts/
│   └── check_notebooklm_updates.py  ← Script de verificação
└── .github/
    └── workflows/
        └── monitor-notebooklm.yml   ← GitHub Actions workflow
```

---

*Documento mantido por: modellnxia | Ramon Turbay Muliterno*
*Próxima revisão: Trimestral ou após qualquer major update*
