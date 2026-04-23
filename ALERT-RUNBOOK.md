# 🚨 ALERT-RUNBOOK.md
## Guia de Ação para Alertas — `notebooklm-py`

**Repositório:** `modellnxia/ultracognia-pesquisaapi-green`
**Versão:** 1.0
**Atualizado:** 2026-04-23

> Este documento é acionado quando o workflow `monitor-notebooklm.yml` detecta uma atualização
> ou quando qualquer membro da equipe recebe um alerta de mudança na biblioteca `notebooklm-py`.

---

## ⚡ Início Rápido (TL;DR)

```
Recebeu alerta?
├── 🟢 PATCH  → Seção 2 (processo padrão)
├── 🟡 MINOR  → Seção 3 (processo cauteloso)
└── 🔴 MAJOR  → Seção 4 (processo completo + aprovação)
```

---

## 1. Pré-Requisitos

Antes de iniciar qualquer atualização, confirme que você tem:

- [ ] Python 3.12+ instalado
- [ ] Git configurado com acesso ao repositório
- [ ] Ambiente virtual disponível (`venv/`)
- [ ] Arquivo `.env` com `SECRET_PROMPT` e credenciais Google configurados
- [ ] Acesso autenticado ao NotebookLM: `notebooklm login`
- [ ] Permissão para criar branches e PRs

---

## 2. Processo Padrão — Patch Update 🟢

> **Quando:** `notebooklm-py x.x.N+1` (ex: 0.3.1 → 0.3.2)
> **Risco:** Baixo — apenas bug fixes

### Passo a Passo

```bash
# 1. Clone / atualize o repositório local
git clone https://github.com/modellnxia/ultracognia-pesquisaapi-green.git
cd ultracognia-pesquisaapi-green
git pull origin main

# 2. Crie uma branch de atualização
git checkout -b fix/update-notebooklm-X.Y.Z
# Substitua X.Y.Z pela versão nova (ex: 0.3.2)

# 3. Crie e ative ambiente virtual
python -m venv venv
source venv/bin/activate          # Linux/Mac
# ou: venv\Scripts\activate       # Windows

# 4. Instale a nova versão
pip install notebooklm-py==X.Y.Z
pip install -r requirements.txt

# 5. Atualize requirements.txt
# Edite a linha: notebooklm-py==X.Y.Z

# 6. Autentique no NotebookLM
notebooklm login

# 7. Teste o script principal
python notebooklm/primeira_fase/notebook_runner.py

# 8. Verifique os outputs gerados
ls outputs/

# 9. Commit e push
git add requirements.txt
git commit -m "chore: bump notebooklm-py to X.Y.Z (patch)"
git push origin fix/update-notebooklm-X.Y.Z

# 10. Abra PR no GitHub com label 'notebooklm-update'
```

### Critérios de Aprovação (Patch)

- [ ] Script `notebook_runner.py` executa sem erros
- [ ] Pelo menos 1 slide deck gerado com sucesso
- [ ] Prompt oculto injetado e removido corretamente
- [ ] `requirements.txt` atualizado

---

## 3. Processo Cauteloso — Minor Update 🟡

> **Quando:** `notebooklm-py x.N+1.x` (ex: 0.3.x → 0.4.0)
> **Risco:** Médio — possíveis novas features ou deprecações

### Antes de Começar

1. **Leia o changelog completo:**
   - PyPI: `https://pypi.org/project/notebooklm-py/#history`
   - GitHub Releases: `https://github.com/jvnkr/notebooklm-py/releases`

2. **Identifique APIs afetadas** (checar especificamente):

```python
# Arquivos críticos a verificar:
# notebooklm/primeira_fase/notebook_runner.py

# Imports de risco:
from notebooklm import NotebookLMClient           # linha 17
from notebooklm.rpc.types import SlideDeckLength  # linha 18
from notebooklm.rpc.types import SlideDeckFormat  # linha 18

# Chamadas de risco (verificar assinatura):
NotebookLMClient.from_storage()                   # linha 91
client.notebooks.create(name)                     # linha 96
client.sources.add_text(id, content, title, wait) # linha 106
client.sources.add_url(id, url, wait)             # linha 122
client.sources.add_file(id, path, wait)           # linha 126
client.artifacts.generate_slide_deck(...)         # linha 184
client.artifacts.wait_for_completion(id, task_id, timeout) # linha 190
client.artifacts.download_slide_deck(id, path)   # linha 194
client.sources.delete(id, source_id)             # linha 198
client.notebooks.delete(id)                       # linha 204
```

### Teste de Compatibilidade

```bash
# 1. Instale em ambiente isolado (não afete o principal)
python -m venv venv_test
source venv_test/bin/activate
pip install notebooklm-py==X.Y.Z

# 2. Rode verificação de imports
python -c "
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength, SlideDeckFormat
print('Imports OK:', SlideDeckLength.__members__, SlideDeckFormat.__members__)
"

# 3. Teste completo
python notebooklm/primeira_fase/notebook_runner.py

# 4. Se tudo OK, siga o Processo Padrão (Seção 2)
```

### Comunicação com Equipe

Antes de fazer o PR, comunique no canal do projeto:
```
📢 [notebooklm-py minor update]
Versão: X.Y → X.Y+1
Status: Testado localmente ✅
PR: [link]
Próximo passo: Review de modellnxia
```

---

## 4. Processo Completo — Major Update 🔴

> **Quando:** `notebooklm-py N+1.x.x` (ex: 0.x.x → 1.0.0)
> **Risco:** Alto — breaking changes quase certos

### ⚠️ NÃO atualize sem seguir TODO este processo

### Fase 1: Análise (Antes de qualquer código)

```bash
# 1. Leia TODAS as release notes
# GitHub: https://github.com/jvnkr/notebooklm-py/releases

# 2. Identifique breaking changes
# Procure por: "breaking", "removed", "deprecated", "migration guide"

# 3. Faça inventário das chamadas afetadas
grep -rn "notebooklm" notebooklm/primeira_fase/notebook_runner.py

# 4. Estime impacto:
# - Quantas linhas precisam mudar?
# - Há mudança no fluxo de autenticação?
# - Enums SlideDeckLength/SlideDeckFormat existem ainda?
```

### Fase 2: Ambiente de Teste

```bash
# 1. Crie branch específica
git checkout -b fix/major-update-notebooklm-vN

# 2. Ambiente completamente isolado
python -m venv venv_major_test
source venv_major_test/bin/activate
pip install notebooklm-py==N.0.0

# 3. Teste de imports (vai falhar se houver breaking changes)
python -c "
import notebooklm
print(dir(notebooklm))
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength, SlideDeckFormat
"

# 4. Documente o que mudou
```

### Fase 3: Adaptação do Código

Para cada breaking change identificado, adapte `notebook_runner.py`:

**Exemplo — Mudança de import:**
```python
# Antes (versão antiga):
from notebooklm.rpc.types import SlideDeckLength

# Depois (verificar na nova versão):
from notebooklm.types import SlideDeckLength  # se o módulo mudou
```

**Exemplo — Mudança de assinatura:**
```python
# Antes:
await client.sources.add_text(nb.id, content=texto, title="[config]", wait=True)

# Depois (verificar na nova API):
await client.sources.add_text(nb.id, text=texto, title="[config]", wait_for_processing=True)
```

### Fase 4: Testes

```bash
# 1. Teste unitário do módulo de imports
python -c "
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength, SlideDeckFormat
print('✅ Imports OK')
"

# 2. Teste de autenticação
notebooklm login

# 3. Teste completo do workflow
python notebooklm/primeira_fase/notebook_runner.py

# 4. Verifique outputs
ls outputs/
cat outputs/*_relatorio.md  # se gerado
```

### Fase 5: PR e Aprovação

```bash
# Commit com mensagem descritiva
git add .
git commit -m "feat!: upgrade notebooklm-py to vN.0.0 (BREAKING CHANGES)

- [descreva o que mudou]
- [descreva adaptações no notebook_runner.py]
- [descreva qualquer mudança de comportamento]

Closes #[número da issue de tracking]"

git push origin fix/major-update-notebooklm-vN
```

**O PR deve incluir:**
- [ ] Descrição detalhada dos breaking changes
- [ ] Lista de adaptações feitas no código
- [ ] Resultado dos testes (com screenshot ou log)
- [ ] Impacto no comportamento do usuário final

**Aprovação obrigatória de:** `@modellnxia`

---

## 5. Rollback de Emergência 🆘

Se a atualização quebrou produção:

```bash
# 1. Identifique a última versão estável
# Consulte o histórico do requirements.txt:
git log --oneline requirements.txt

# 2. Reverta para versão anterior
git checkout -b hotfix/rollback-notebooklm
# Edite requirements.txt: notebooklm-py==VERSAO_ESTAVEL

# 3. Instale e teste rapidamente
pip install notebooklm-py==VERSAO_ESTAVEL
python notebooklm/primeira_fase/notebook_runner.py

# 4. Push urgente
git add requirements.txt
git commit -m "hotfix: rollback notebooklm-py to VERSAO_ESTAVEL"
git push origin hotfix/rollback-notebooklm

# 5. Abra PR urgente (marque como HOTFIX)
# Notifique @modellnxia imediatamente
```

---

## 6. Verificação Pós-Update ✅

Após qualquer atualização, confirme:

```bash
# Checklist de verificação

# 1. Versão instalada está correta
pip show notebooklm-py | grep Version

# 2. Imports funcionam
python -c "
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength, SlideDeckFormat
print('Imports OK')
print('SlideDeckLength values:', list(SlideDeckLength))
print('SlideDeckFormat values:', list(SlideDeckFormat))
"

# 3. Script principal não tem erros de sintaxe
python -m py_compile notebooklm/primeira_fase/notebook_runner.py
echo "Syntax OK"

# 4. Variáveis de ambiente carregam
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SECRET_PROMPT:', 'OK' if os.getenv('SECRET_PROMPT') else 'AUSENTE')
print('OUTPUT_DIR:', os.getenv('OUTPUT_DIR', './outputs'))
"

# 5. Autenticação NotebookLM válida
notebooklm login --check 2>/dev/null && echo "Auth OK" || echo "Auth necessária"
```

---

## 7. Comunicação com a Equipe

### Quando Notificar

| Situação | Canal | Urgência |
|----------|-------|---------|
| Patch update disponível | Slack #dev | Normal |
| Minor update disponível | Slack #dev + Issue | Normal |
| Major update disponível | Slack #dev + Issue + menção @Ramon | Alta |
| Vulnerabilidade detectada | Slack #alertas-segurança + Issue | Urgente |
| Produção quebrada | Slack #incidentes + menção @modellnxia | Crítica |

### Template de Mensagem Slack

```
📦 [notebooklm-py] Update {TIPO}
Versão: {ATUAL} → {NOVA}
Risco: {EMOJI} {NÍVEL}
Arquivo afetado: notebooklm/primeira_fase/notebook_runner.py
Issue: #{NÚMERO}
Responsável: @{DESENVOLVEDOR}
```

---

## 8. Histórico de Incidentes

Registre aqui incidentes relacionados a updates (atualize manualmente):

| Data | Versão | Incidente | Resolução | Tempo |
|------|--------|-----------|-----------|-------|
| — | — | — | — | — |

---

## 9. Contatos

| Papel | Pessoa | Responsabilidade |
|-------|--------|-----------------|
| DevOps / Validador | modellnxia | Merge, deploy, aprovação final |
| Backend Developer | Ramon Turbay Muliterno | notebook_runner.py, APIs |

---

*Runbook mantido por: modellnxia | Ramon Turbay Muliterno*
*Vinculado ao workflow: `.github/workflows/monitor-notebooklm.yml`*
