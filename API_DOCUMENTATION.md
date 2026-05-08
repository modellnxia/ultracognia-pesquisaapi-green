# API_DOCUMENTATION

## Base URL

- Local: `http://localhost:8004`

## Autenticação e autorização

- Atualmente, os endpoints não exigem autenticação.
- Para produção, recomenda-se gateway/API key/JWT na borda.

## Modelos de dados

### `ChatRequest`

```json
{
  "message": "string"
}
```

Campos:
- `message` (`str`, obrigatório): texto enviado ao chat mock.

## Endpoints

### `GET /health`

Verifica disponibilidade do serviço.

#### Request
- Sem body.

#### Response `200 OK`

```json
{
  "status": "ok",
  "service": "brain_mock"
}
```

#### Códigos HTTP
- `200`: serviço operacional.

---

### `POST /chat`

Endpoint mock de resposta textual.

#### Request

`Content-Type: application/json`

```json
{
  "message": "Olá, serviço"
}
```

#### Response `200 OK`

```json
{
  "response": "[MOCK] Olá, serviço"
}
```

#### Códigos HTTP
- `200`: resposta gerada.
- `422`: payload inválido (schema Pydantic/FastAPI).

## OpenAPI / Swagger

Com a API em execução:
- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`
- OpenAPI JSON: `http://localhost:8004/openapi.json`

## Exemplos com `curl`

```bash
curl -s http://localhost:8004/health

curl -s -X POST http://localhost:8004/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"teste"}'
```
