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
- **MongoDB**: Opcional (veja seção abaixo)

### Exemplos

```bash
# Ver logs em tempo real
tail -f src/whatsapp/logs/whatsapp.log

# Contar mensagens enviadas
grep "✅ Mensagem" src/whatsapp/logs/whatsapp.log | wc -l

# Ver apenas erros
grep "❌" src/whatsapp/logs/whatsapp.log
```

## 🗄️ Salvando Logs no MongoDB

### Pré-requisitos

1. **MongoDB instalado e rodando:**

   ```bash
   # Windows (se instalado via Chocolatey)
   mongod

   # Ou via Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. **Variável de ambiente configurada:**
   - Copie `.env.example` para `.env`
   - Edite com sua URL do MongoDB:

   ```bash
   # Para MongoDB local:
   DATABASE_URL=mongodb://localhost:27017/whatsapp_logs

   # Para MongoDB Atlas (cloud):
   DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority
   ```

### Como Usar

#### **Opção 1: Código Python**

```python
from src.services.application_service import ApplicationService, AutomationMode
from src.repositories.log_repository import LogRepository

# Criar instância do repositório
log_repo = LogRepository()

# Executar com MongoDB ativado
app = ApplicationService(
    mode=AutomationMode.FULL,
    include_mongodb=True  # ← Ativa MongoDB
)
app.run_sync()
```

#### **Opção 2: Editar `src/main.py`**

```python
# Antes:
application = ApplicationService(mode=AutomationMode.FULL, include_mongodb=False)

# Depois:
application = ApplicationService(mode=AutomationMode.FULL, include_mongodb=True)
```

### O que é Salvo no MongoDB

Cada log contém:

```json
{
  "_id": "ObjectId",
  "level": "INFO", // Nível do log (INFO, SUCCESS, WARNING, ERROR)
  "message": "✅ Mensagem enviada",
  "time": "2026-01-25T14:30:00.000Z",
  "context": {
    "location": "sender.py:250",
    "function": "enviar_mensagens"
  }
}
```

### Consultando Logs no MongoDB

#### **Via MongoDB Compass (GUI):**

1. Abra MongoDB Compass
2. Conecte em `mongodb://localhost:27017`
3. Banco: `whatsapp_logs`
4. Coleção: `log`

#### **Via Terminal (mongosh):**

```bash
# Conectar ao MongoDB
mongosh

# Listar logs
use whatsapp_logs
db.log.find()

# Contar mensagens enviadas
db.log.countDocuments({ message: /Mensagem.*enviada/ })

# Ver apenas erros
db.log.find({ level: "ERROR" })

# Últimos 10 logs
db.log.find().sort({ time: -1 }).limit(10)

# Logs de um intervalo de tempo
db.log.find({
  time: {
    $gte: ISODate("2026-01-25T00:00:00Z"),
    $lte: ISODate("2026-01-25T23:59:59Z")
  }
})
```

#### **Via Python:**

```python
from src.repositories.log_repository import LogRepository
import asyncio

async def listar_logs():
    repo = LogRepository()

    # Todos os logs
    logs = await repo.get_all_logs()
    print(f"Total de logs: {len(logs)}")

    # Últimos 10 logs
    for log in logs[-10:]:
        print(f"{log.level} | {log.message} | {log.time}")

# Executar
asyncio.run(listar_logs())
```

### Solução de Problemas

**Erro: "Failed to connect to MongoDB"**

- Certifique-se que MongoDB está rodando: `mongod` ou `docker ps`
- Verifique a URL em `.env` - padrão é `mongodb://localhost:27017`

**Erro: "DATABASE_URL not set"**

- Crie arquivo `.env` (copie de `.env.example`)
- Adicione: `DATABASE_URL=mongodb://localhost:27017/whatsapp_logs`

**Logs não estão sendo salvos**

- Verifique se `include_mongodb=True` está configurado
- Verifique os logs do console para erros de conexão

## 🔐 Autenticação

1. Execute `python src/main.py auth`
2. Navegador abre automaticamente
3. Escaneie o QR Code com seu telefone
4. `state.json` é criado automaticamente
5. Na próxima execução, usa a sessão salva

## � Formato do Excel (contatos.xlsx)

| Nome    | Tel1        | Tel2       | Tel3 |
| ------- | ----------- | ---------- | ---- |
| Gabriel | 43998716601 |            |      |
| João    | 4398377239  | 4399999999 |      |
| Maria   | 4398888888  |            |      |

**Regras:**

- `Nome`: Será formatado para Title Case com primeiro nome
- `Tel1-Tel5`: Números sem formatação, será adicionado DDI 55

## 📞 Validação de Telefones

### Números em Formato Incorreto

Se um número está em formato inválido (muito curto, sem dígitos suficientes):

```
⚠️ Telefone inválido para João: 123
   (Número muito curto ou sem dígitos - pode ser telefone fixo ou formato incorreto)
```

**O que é considerado inválido:**

- ❌ Menos de 10 dígitos (ex: 123, 98765432)
- ❌ Números vazios ou nulos
- ❌ Apenas caracteres especiais (ex: ----, ( ))

**O que é considerado válido:**

- ✅ 10 dígitos (ex: 4333333333 → 554333333333)
- ✅ 11 dígitos (ex: 43998377239 → 5543998377239)
- ✅ Com formatação (ex: (43) 99837-7239 → 5543998377239)

### Números Sem WhatsApp

Se o número é válido **mas não tem WhatsApp ativo**:

```
📱 Processando João - 5543998377239... (Mensagem 1/2)
⚠️ WhatsApp rejeitou o número 5543998377239
   Mensagem: 'O número de telefone compartilhado por url é inválido'
   Possível causa: Número não tem WhatsApp ou é inválido
```

Ou quando não encontra o campo de mensagem:

```
⚠️ Não foi possível enviar para 5543998377239
   Possível causa:
   • Este número não tem WhatsApp ativo
   • Ou o número está bloqueado
   • Ou houve timeout na página
```

**Por que isso acontece:**

- Telefones fixos (TIM, Claro, Vivo fixo) geralmente **não têm WhatsApp**
- Números antigos ou desativados não têm WhatsApp
- Números bloqueados pelo WhatsApp
- Números que o remetente está bloqueado

**Solução:**

- ✅ Remova esses números da planilha
- ✅ Ou deixe as colunas vazias se não tiver móvel
- ✅ O script pulará automaticamente com uma mensagem clara no log

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
