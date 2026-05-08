# CONTRIBUTING

## Padrões de código

- Python com tipagem e docstrings em funções públicas.
- Alterações devem ser pequenas, focadas e com impacto mínimo fora do escopo.
- Evite expor conteúdo sensível (ex.: `SECRET_PROMPT`) em logs ou responses.

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install notebooklm-py python-dotenv
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

## Como adicionar novos endpoints

1. Defina modelo Pydantic em `main.py` (ou módulo dedicado).
2. Adicione rota com verbo HTTP apropriado.
3. Garanta resposta serializável e códigos HTTP consistentes.
4. Atualize `API_DOCUMENTATION.md` e, se necessário, `README.md`.

## Testes

No estado atual do repositório não há suíte de testes automatizada.

Recomendado para novas contribuições:
- adicionar testes de endpoint (ex.: `fastapi.testclient`);
- validar contratos de request/response;
- cobrir cenários de erro (payload inválido, falhas de integração).

## Processo de contribuição

1. Crie branch de trabalho.
2. Faça commits pequenos e descritivos.
3. Execute validações locais disponíveis.
4. Abra PR com contexto, escopo e evidências de validação.
