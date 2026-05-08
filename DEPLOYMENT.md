# DEPLOYMENT

## Docker

### Build

```bash
docker build -t ultracognia-pesquisaapi-green:latest .
```

### Run

```bash
docker run --rm \
  -p 8004:8004 \
  --env-file .env \
  ultracognia-pesquisaapi-green:latest
```

## Variáveis de ambiente

- `SECRET_PROMPT`: instruções proprietárias para o runner NotebookLM.
- `OUTPUT_DIR`: diretório de saída de artefatos.

## Health checks

Endpoint de prontidão:

```bash
curl -f http://localhost:8004/health
```

Sugestão de healthcheck no Docker (exemplo operacional):

```text
CMD curl -f http://localhost:8004/health || exit 1
```

## Logging e monitoramento

- API FastAPI/Uvicorn: logs padrão de acesso e erro.
- Runner NotebookLM: logs de progresso por etapa (`[1/6]`, `[2/6]`, etc.).
- Recomendações:
  - Centralizar logs (ELK, Cloud Logging, Datadog).
  - Criar métricas de tempo por etapa da geração.
  - Alertar para falhas repetidas de autenticação NotebookLM.

## Escalabilidade

- API mock é stateless e escalável horizontalmente.
- Geração NotebookLM é operação potencialmente longa e assíncrona.
- Para maior escala:
  - mover `generate_report` para workers/background queue;
  - impor limites de concorrência por tenant;
  - persistir metadados de execução e status para acompanhamento.

## Checklist de produção

- [ ] Variáveis sensíveis em secret manager
- [ ] `notebooklm login` provisionado no ambiente de execução
- [ ] `OUTPUT_DIR` persistente e com permissões corretas
- [ ] Monitoramento de healthcheck e latência
