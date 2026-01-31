# 🗄️ MongoDB - Guia Rápido

## ⚡ Passo 1: Instalar MongoDB

### Opção A: Local (Windows/Mac/Linux)

```bash
# Download: https://www.mongodb.com/try/download/community

# Ou via Chocolatey (Windows)
choco install mongodb-community

# Ou via Homebrew (Mac)
brew tap mongodb/brew
brew install mongodb-community

# Verificar instalação
mongod --version
```

### Opção B: Docker (Recomendado)

```bash
# Baixar imagem
docker pull mongo:latest

# Iniciar container
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verificar se está rodando
docker ps
```

## ⚡ Passo 2: Configurar Variável de Ambiente

### Criar arquivo `.env` na raiz do projeto:

```
# Para MongoDB local:
DATABASE_URL=mongodb://localhost:27017/whatsapp_logs

# Ou para MongoDB Atlas (cloud):
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name
```

> Copie do `.env.example` se não souber os valores

## ⚡ Passo 3: Ativar MongoDB na Automação

### Opção A: Via Código Python

```python
from src.services.application_service import ApplicationService, AutomationMode

app = ApplicationService(
    mode=AutomationMode.FULL,
    include_mongodb=True  # ← Ativa MongoDB
)
app.run_sync()
```

### Opção B: Editar `src/main.py`

```python
# Linha 13 - mude:
application = ApplicationService(mode=AutomationMode.FULL, include_mongodb=True)
```

## ⚡ Passo 4: Ver Logs no MongoDB

### Via MongoDB Compass (GUI)

1. Download: https://www.mongodb.com/products/compass
2. Conectar em: `mongodb://localhost:27017`
3. Banco: `whatsapp_logs` → Coleção: `log`

### Via Terminal

```bash
# Entrar no MongoDB
mongosh

# Listar logs
use whatsapp_logs
db.log.find()

# Últimos 5 logs
db.log.find().sort({ time: -1 }).limit(5)

# Contar erros
db.log.countDocuments({ level: "ERROR" })
```

## 📊 Estrutura do Log

```json
{
  "_id": ObjectId("..."),
  "level": "SUCCESS",
  "message": "✅ Mensagem enviada para 5543998377239",
  "time": ISODate("2026-01-25T14:30:00.000Z"),
  "context": {
    "location": "sender.py:250",
    "function": "enviar_mensagens"
  }
}
```

## 🔍 Exemplos de Consultas

```bash
# Todos os logs
db.log.find()

# Apenas erros
db.log.find({ level: "ERROR" })

# Apenas sucessos
db.log.find({ level: "SUCCESS" })

# Mensagens contendo "Mensagem enviada"
db.log.find({ message: /Mensagem enviada/ })

# Logs do último dia
db.log.find({
  time: { $gte: ISODate("2026-01-24T00:00:00Z") }
})

# Contar por nível
db.log.countDocuments({ level: "ERROR" })
db.log.countDocuments({ level: "SUCCESS" })

# Apagar todos os logs (cuidado!)
db.log.deleteMany({})
```

## ❌ Solução de Problemas

| Erro                   | Solução                                              |
| ---------------------- | ---------------------------------------------------- |
| `connection refused`   | MongoDB não está rodando - execute `mongod`          |
| `DATABASE_URL not set` | Crie arquivo `.env` com DATABASE_URL                 |
| `Logs não são salvos`  | Verifique se `include_mongodb=True` está configurado |
| `Timeout`              | Verifique conexão MongoDB e permissões               |

## 📚 Documentação Adicional

- [Prisma + MongoDB](https://www.prisma.io/docs/concepts/database-connectors/mongodb)
- [MongoDB Compass](https://www.mongodb.com/products/compass)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
