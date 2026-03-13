---
description: Como iniciar a automação do WhatsApp
---

# 🤖 Como Iniciar a Automação do WhatsApp

## Pré-requisitos

1. Python 3.9+ instalado
2. Virtual environment (`venv`) criado
3. Arquivo `.env` configurado com `DATABASE_URL`
4. Arquivo `contatos.xlsx` com os contatos na raiz do projeto

## Passo a Passo

### 1. Ativar o ambiente virtual
```bash
source venv/bin/activate
```

### 2. Instalar dependências (se necessário)
```bash
pip install -r requirements.txt
```

### 3. Instalar browsers do Playwright (primeira vez)
```bash
python -m playwright install chromium
```

### 4. Configurar o arquivo `src/whatsapp/config.py`
Edite as variáveis conforme necessidade:
- `CONDOMINIO` - Nome do condomínio alvo
- `MESSAGE_TEMPLATE_1/2/3` - Templates das mensagens
- `BASE_NUMBER` - Número seguro para retorno entre delays
- `MAX_CONTACTS_PER_SESSION` - Limite de contatos por sessão (padrão: 80)
- `DELAY_MIN` / `DELAY_MAX` - Intervalo de delay entre contatos (60-180s)

### 5. Primeira execução: Autenticar no WhatsApp Web
Na primeira vez, execute a autenticação para escanear o QR Code:
```bash
python -m src.main
```
Ou para apenas autenticar (sem enviar mensagens):
Altere `main.py` para usar `AutomationMode.AUTHENTICATE`

### 6. Executar a automação (envio de mensagens)
```bash
python -m src.main
```
O modo padrão é `SEND` com MongoDB habilitado.

### 7. (Opcional) Dashboard de monitoramento
```bash
python run_dashboard.py
```
Acesse em: http://localhost:8000

## Modos de Automação

| Modo | Descrição |
|------|-----------|
| `AUTHENTICATE` | Apenas faz login e salva a sessão |
| `SEND` | Apenas envia mensagens (requer sessão salva) |
| `FULL` | Autenticação + Envio |

## Estrutura do `contatos.xlsx`

| Coluna | Descrição |
|--------|-----------|
| `Nome` | Nome do contato |
| `Telefone 1` a `Telefone 5` | Números de telefone |
