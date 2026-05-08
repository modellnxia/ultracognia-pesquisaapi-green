# ARCHITECTURE

## Diagrama de fluxo (ASCII)

```text
+-------------------+
| Client / Consumer |
+---------+---------+
          |
          | HTTP
          v
+-------------------------+
| FastAPI app (main.py)   |
| - GET /health           |
| - POST /chat            |
+------------+------------+
             |
             | integração interna assíncrona
             v
+----------------------------------------------+
| notebook_runner.generate_report()            |
| - cria notebook                              |
| - injeta prompt oculto                       |
| - adiciona fontes do usuário                 |
| - gera artefatos (slides/áudio)              |
| - faz download para OUTPUT_DIR               |
+------------------+---------------------------+
                   |
                   v
+----------------------------------------------+
| NotebookLM SDK (notebooklm-py)               |
| notebooks / sources / chat / artifacts       |
+----------------------------------------------+
```

## Componentes e responsabilidades

### 1) `main.py`
- Disponibiliza API HTTP minimalista para mock de brain.
- Define modelo `ChatRequest`.
- Expõe endpoint de saúde para operações e monitoramento.

### 2) `notebooklm/primeira_fase/notebook_runner.py`
- Orquestra ciclo completo de geração de relatório/artefatos.
- Controla política de injeção de prompt proprietário em fonte oculta.
- Normaliza saída local em estrutura de diretórios configurável.

### 3) Dependências externas
- `FastAPI` e `Uvicorn` para API.
- `notebooklm-py` para operações NotebookLM.
- `python-dotenv` para configuração por ambiente.

## Fluxo de dados

1. Aplicação define lista de fontes (`url`, `file`, `text`).
2. Runner cria notebook com nome timestampado.
3. Runner injeta `SECRET_PROMPT` + `user_context` como fonte oculta.
4. Runner adiciona fontes de usuário.
5. Runner solicita geração de artefatos (slides e opcionalmente áudio).
6. Runner aguarda conclusão (timeout de slides: 1200s).
7. Runner baixa artefatos em `OUTPUT_DIR`.
8. Runner remove fonte oculta e opcionalmente remove notebook inteiro.

## Integração NotebookLM

Pontos de integração usados:
- `NotebookLMClient.from_storage()` para sessão autenticada.
- `client.notebooks.create/delete`.
- `client.sources.add_text/add_url/add_file/delete`.
- `client.artifacts.generate_slide_deck/generate_audio`.
- `client.artifacts.wait_for_completion`.
- `client.artifacts.download_slide_deck/download_audio`.

## Padrões de design

- **Orquestrador assíncrono**: `generate_report` concentra o workflow transacional.
- **Configuração por ambiente**: `SECRET_PROMPT` e `OUTPUT_DIR` externos.
- **Nomeação idempotente temporal**: evita colisão com `timestamped_name`.
- **Resultado estruturado**: retorno em dicionário com caminhos para consumo posterior.

## Segurança e prompt injection prevention

- O prompt proprietário não é enviado pelo usuário final; é carregado de ambiente.
- Injeção ocorre como fonte oculta com título neutro (`[config]`).
- Fonte oculta é removida após geração de slides, reduzindo exposição residual.
- Recomendações adicionais:
  - Armazenar `SECRET_PROMPT` em secret manager.
  - Validar/limitar fontes de entrada para reduzir risco de conteúdo malicioso.
  - Sanitizar logs para não persistir conteúdo sensível.
