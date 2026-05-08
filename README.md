# ultracognia-pesquisaapi-green

API de pesquisa construída com **FastAPI** com suporte a integração assíncrona com **NotebookLM** para geração de relatórios, áudio e slide deck.

## Visão Geral

O repositório possui dois blocos principais:

1. **API HTTP (`main.py`)**
   - Serviço mock `brain_mock`
   - Endpoints:
     - `GET /health`
     - `POST /chat`
2. **Runner NotebookLM (`notebooklm/primeira_fase/notebook_runner.py`)**
   - Criação de notebooks dinâmica
   - Injeção de prompt proprietário como fonte oculta
   - Adição de fontes de usuário (`url`, `file`, `text`)
   - Geração de artefatos (slides e, opcionalmente, áudio)
   - Cleanup opcional de notebook

## Arquitetura (Resumo)

```text
Cliente -> FastAPI (main.py)
              |
              | (orquestração assíncrona)
              v
      notebook_runner.generate_report()
              |
              v
      NotebookLMClient (SDK notebooklm-py)
          |- notebooks.create
          |- sources.add_text/add_url/add_file
          |- artifacts.generate_slide_deck / generate_audio
          |- artifacts.download_*
```

Documentação detalhada em [ARCHITECTURE.md](./ARCHITECTURE.md).

## Setup Local

### Pré-requisitos

- Python 3.12+
- `pip`
- Autenticação NotebookLM já realizada (`notebooklm login`)

### Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install notebooklm-py python-dotenv
```

> `requirements.txt` cobre o runtime da API. O runner NotebookLM também requer `notebooklm-py` e `python-dotenv`.

### Variáveis de ambiente

Crie `.env` na raiz:

```env
SECRET_PROMPT=Analise os materiais com profundidade e estruture as respostas de forma clara.
OUTPUT_DIR=./outputs
```

- `SECRET_PROMPT`: prompt proprietário injetado como fonte oculta.
- `OUTPUT_DIR`: diretório onde artefatos gerados serão salvos.

## Executando a API

```bash
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### Exemplos de uso da API

#### Health check

```bash
curl -s http://localhost:8004/health
```

Resposta:

```json
{"status":"ok","service":"brain_mock"}
```

#### Chat mock

```bash
curl -s -X POST http://localhost:8004/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Olá"}'
```

Resposta:

```json
{"response":"[MOCK] Olá"}
```

## Uso da integração NotebookLM

Exemplo via script:

```bash
python notebooklm/primeira_fase/notebook_runner.py
```

Exemplo programático:

```python
import asyncio
from notebooklm.primeira_fase.notebook_runner import generate_report

async def run():
    result = await generate_report(
        sources=[
            {"type": "url", "value": "https://arxiv.org/abs/2303.08774"},
            {"type": "text", "value": "Notas internas", "title": "Contexto"},
        ],
        notebook_title="Relatorio_LLM",
        user_context="Foco em aplicações empresariais",
        generate_audio=False,
        generate_slides=True,
        cleanup_notebook=False,
    )
    print(result)

asyncio.run(run())
```

Guia completo em [NOTEBOOKLM_INTEGRATION.md](./NOTEBOOKLM_INTEGRATION.md).

## Docker e Deployment

Build:

```bash
docker build -t ultracognia-pesquisaapi-green:latest .
```

Run:

```bash
docker run --rm -p 8004:8004 ultracognia-pesquisaapi-green:latest
```

Mais detalhes em [DEPLOYMENT.md](./DEPLOYMENT.md).

## Troubleshooting

- **`ModuleNotFoundError: notebooklm`**
  - Instale `notebooklm-py` no ambiente ativo.
- **Falha de autenticação NotebookLM**
  - Execute `notebooklm login` antes de rodar o runner.
- **Slides demorando/falhando**
  - O timeout configurado para conclusão é de `1200s`; valide conectividade e fontes.
- **Sem arquivos gerados**
  - Verifique permissões de escrita em `OUTPUT_DIR`.

## Documentação complementar

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- [NOTEBOOKLM_INTEGRATION.md](./NOTEBOOKLM_INTEGRATION.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
