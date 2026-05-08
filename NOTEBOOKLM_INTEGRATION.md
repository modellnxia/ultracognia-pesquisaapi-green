# NOTEBOOKLM_INTEGRATION

## Como funciona

A integração está centralizada em `notebooklm/primeira_fase/notebook_runner.py` via `generate_report(...)`, com execução assíncrona.

Fluxo:
1. Abre sessão autenticada (`NotebookLMClient.from_storage`).
2. Cria notebook temporário.
3. Injeta prompt proprietário oculto (`SECRET_PROMPT`).
4. Adiciona fontes de usuário.
5. Gera artefatos (slides e opcionalmente áudio).
6. Faz download dos arquivos para `OUTPUT_DIR`.
7. Remove fonte oculta e opcionalmente remove notebook.

## Setup e autenticação

```bash
pip install notebooklm-py python-dotenv
notebooklm login
```

Crie `.env`:

```env
SECRET_PROMPT=Instruções proprietárias
OUTPUT_DIR=./outputs
```

## Fluxo de geração de relatórios

### Assinatura principal

```python
async def generate_report(
    sources: list[dict],
    notebook_title: str = "Relatório Gerado",
    user_context: str = "",
    generate_audio: bool = False,
    generate_slides: bool = True,
    cleanup_notebook: bool = False,
) -> dict
```

### Tipos de fonte suportados

- `{"type": "url", "value": "https://..."}`
- `{"type": "file", "value": "/caminho/arquivo.pdf"}`
- `{"type": "text", "value": "conteúdo", "title": "Opcional"}`

## Injeção de prompts proprietários

- A função `build_hidden_prompt_text` combina:
  - `SECRET_PROMPT` (sistema)
  - `user_context` (contexto de execução)
- O conteúdo é enviado como `source` de texto com título neutro `[config]`.
- Objetivo: controlar instruções sem expor prompt no payload do usuário.

## Geração de artefatos

### Slides
- API usada: `client.artifacts.generate_slide_deck(...)`
- Formato: `PRESENTER_SLIDES`
- Comprimento: `DEFAULT`
- Timeout de espera: `1200` segundos
- Download: `{notebook_title}_slides.pdf`

### Áudio (opcional)
- API usada: `client.artifacts.generate_audio(...)`
- Download: `{notebook_title}_podcast.mp3`

## Tratamento de erros (recomendado)

O código atual delega exceções para o chamador. Em produção:

- Encapsular chamadas NotebookLM com `try/except`.
- Registrar falhas por etapa (`create`, `add_source`, `generate`, `download`).
- Retornar estado parcial com mensagens de erro consumíveis pela API.
- Aplicar retentativas em falhas transitórias de rede.

## Exemplo prático

```python
import asyncio
from notebooklm.primeira_fase.notebook_runner import generate_report

async def run_example():
    data = await generate_report(
        sources=[
            {"type": "url", "value": "https://example.com"},
            {"type": "text", "value": "Contexto complementar", "title": "Interno"},
        ],
        notebook_title="Relatorio_Produto",
        user_context="Foco em visão executiva",
        generate_audio=False,
        generate_slides=True,
        cleanup_notebook=False,
    )
    print(data)

asyncio.run(run_example())
```
