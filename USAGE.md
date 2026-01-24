# 🤖 WhatsApp Automation - Guia de Uso

## 📋 Estrutura

```
src/
├── main.py                      ← Entry point principal
├── app_server.py                ← Servidor Flask
├── config/                      ← Configurações
├── services/
│   └── application_service.py   ← ⭐ Orquestrador da automação
└── whatsapp/                    ← ⭐ Módulo de automação WhatsApp
    ├── config.py                (configurações)
    ├── config_logger.py         (logging com loguru)
    ├── examples.py              (exemplos de uso)
    ├── utils/                   (utilities)
    │   ├── phone_formatter.py
    │   └── text_formatter.py
    └── robot/                   (scripts de automação)
        ├── auth.py              (autenticação)
        └── sender.py            (envio de mensagens)
```

## 🚀 Como Usar

### **Opção 1: Linha de Comando (Recomendado)**

```bash
# Automação completa (autenticação + envio)
python src/main.py full

# Apenas autenticação (QR Code)
python src/main.py auth

# Apenas envio de mensagens
python src/main.py send

# Com logging em MongoDB
python src/main.py full --mongodb
```

### **Opção 2: Código Python**

```python
from src.services.application_service import ApplicationService, AutomationMode

# Automação completa
app = ApplicationService(mode=AutomationMode.FULL)
app.run_sync()

# Apenas autenticação
app = ApplicationService(mode=AutomationMode.AUTHENTICATE)
app.run_sync()

# Apenas envio
app = ApplicationService(mode=AutomationMode.SEND)
app.run_sync()

# Com MongoDB
app = ApplicationService(mode=AutomationMode.FULL, include_mongodb=True)
app.run_sync()
```

### **Opção 3: Importação Direta**

```python
from src.whatsapp import save_session, enviar_mensagens

# Autenticar
save_session()

# Enviar
enviar_mensagens()
```

## 📝 Configuração

Edite as constantes em `src/whatsapp/config.py`:

```python
# Arquivo Excel com contatos
ARQUIVO_EXCEL = 'contatos.xlsx'

# Mensagens
MENSAGEM_BASE = "Olá {nome}, tudo bem?"
MENSAGEM_BASE_2 = "Tem interesse em saber mais?"

# Colunas de telefone no Excel
COLUNAS_TELEFONE = ['Tel1', 'Tel2', 'Tel3', 'Tel4', 'Tel5']

# Delays (segundos)
DELAY_MIN = 20
DELAY_MAX = 45
DELAY_ENTRE_MENSAGENS = 5
```

## 📊 Logs

### Local dos Logs

- **Console**: Colorido em tempo real
- **Arquivo JSON**: `src/whatsapp/logs/whatsapp.json`
- **Arquivo TXT**: `src/whatsapp/logs/whatsapp.log`
- **MongoDB**: Se `--mongodb` for usado

### Exemplos

```bash
# Ver logs em tempo real
tail -f src/whatsapp/logs/whatsapp.log

# Contar mensagens enviadas
grep "✅ Mensagem" src/whatsapp/logs/whatsapp.log | wc -l

# Ver apenas erros
grep "❌" src/whatsapp/logs/whatsapp.log
```

## 🔐 Autenticação

1. Execute `python src/main.py auth`
2. Navegador abre automaticamente
3. Escaneie o QR Code com seu telefone
4. `state.json` é criado automaticamente
5. Na próxima execução, usa a sessão salva

## 📱 Formato do Excel (contatos.xlsx)

| Nome    | Tel1        | Tel2       | Tel3 |
| ------- | ----------- | ---------- | ---- |
| Gabriel | 43998716601 |            |      |
| João    | 4398377239  | 4399999999 |      |
| Maria   | 4398888888  |            |      |

**Regras:**

- `Nome`: Será formatado para Title Case com primeiro nome
- `Tel1-Tel5`: Números sem formatação, será adicionado DDI 55

## ⚙️ Modo de Operação

### **AUTHENTICATE** 🔐

- Abre navegador com WhatsApp Web
- Você escaneia o QR Code
- Salva a sessão em `state.json`
- Não envia mensagens

### **SEND** 📤

- Usa sessão salva de `state.json`
- Lê contatos do Excel
- Envia 2 mensagens por contato
- Com delays aleatórios

### **FULL** 🚀 (Padrão)

- Executa AUTHENTICATE
- Depois executa SEND
- Pipeline completo

## 🐛 Troubleshooting

### "Arquivo não encontrado"

```bash
# Certifique-se que contatos.xlsx está na raiz do projeto
ls contatos.xlsx
```

### "QR Code não aparece"

- Verifique se você tem Firefox/Chrome instalado
- Pode ser necessário instalar playwright browsers:
  ```bash
  playwright install
  ```

### "Mensagens não estão sendo enviadas"

- Verifique os logs: `src/whatsapp/logs/whatsapp.log`
- Certifique-se de que WhatsApp está funcionando em `web.whatsapp.com`
- Tente aumentar os delays em `config.py`

## 📚 Documentação Adicional

- [Logging com Loguru](src/whatsapp/LOGGING.md)
- [Exemplos de Uso](src/whatsapp/examples.py)

## 🔄 Fluxo de Execução

```
main.py
  ↓
ApplicationService
  ├─ setup_loguru()
  ├─ setup_whatsapp_logger()
  └─ Modo selecionado:
      ├─ AUTHENTICATE → save_session()
      ├─ SEND → enviar_mensagens()
      └─ FULL → save_session() → enviar_mensagens()
```

---

**Last Updated:** 22 de janeiro de 2026
