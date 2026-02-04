# 📊 Logging Estruturado - Guia de Uso

## Visão Geral

O sistema de logging foi aprimorado com **logging estruturado** e **métricas de sessão** para melhor análise e monitoramento.

## Novos Componentes

### 1. StructuredLogger (`src/utils/structured_logger.py`)

Logger que gera logs em formato JSON para fácil parsing e análise.

**Métodos disponíveis:**

```python
from src.utils.structured_logger import StructuredLogger

# Log de tentativa de envio de mensagem
StructuredLogger.log_message_attempt(
    contact_name="João Silva",
    phone="5543998377239",
    message_number=1,
    total_messages=3,
    status="success",  # ou "failed", "invalid", "not_found"
    error=None  # opcional
)

# Log de autenticação
StructuredLogger.log_authentication("success")  # ou "failed", "started"

# Log de operação de banco de dados
StructuredLogger.log_database_operation(
    operation="save",
    status="success",
    record_count=1
)

# Log de resumo de sessão
StructuredLogger.log_session_summary(
    total_contacts=50,
    total_phones_processed=75,
    total_messages_sent=120,
    total_failures=5,
    invalid_phones=3,
    not_found_phones=2,
    duration_seconds=1800.0
)
```

### 2. SessionMetrics (`src/utils/metrics.py`)

Classe para rastrear métricas durante a execução.

**Uso:**

```python
from src.utils.metrics import SessionMetrics

# Inicializar no início da sessão
metrics = SessionMetrics()

# Registrar eventos
metrics.record_contact_processed()
metrics.record_phone_processed()
metrics.record_success()
metrics.record_failure("timeout")
metrics.record_invalid_phone()
metrics.record_not_found()

# Finalizar e obter resumo
metrics.finalize()
summary = metrics.get_summary()

print(summary)
# {
#   'duration_seconds': 1800.0,
#   'duration_minutes': 30.0,
#   'total_contacts': 50,
#   'messages_sent': 120,
#   'success_rate_percent': 96.0,
#   ...
# }
```

## Formato dos Logs

### Logs Estruturados (JSON)

Cada log estruturado contém:

```json
{
  "event": "message_attempt",
  "contact_name": "João Silva",
  "phone": "5543998377239",
  "message_number": 1,
  "total_messages": 3,
  "status": "success",
  "timestamp": "2026-02-02T22:55:00.000000"
}
```

### Tipos de Eventos

1. **authentication**: Login no WhatsApp
2. **contact_processing**: Processamento de contato
3. **message_attempt**: Tentativa de envio de mensagem
4. **database_operation**: Operação no banco de dados
5. **session_summary**: Resumo da sessão

## Resumo de Sessão

Ao final de cada execução, você verá:

```
============================================================
📊 SESSION SUMMARY
============================================================
Duration: 30.5 minutes
Contacts processed: 50
Phones processed: 75
Messages sent: 142
Messages failed: 8
Invalid phones: 3
Not found on WhatsApp: 5
Success rate: 94.7%
Messages per minute: 4.7
Errors by type: {'timeout': 3, 'send_error': 5}
============================================================
```

## Análise de Logs

### Filtrar logs estruturados

```bash
# Apenas sucessos
grep '"status": "success"' logs/whatsapp.log

# Apenas falhas
grep '"status": "failed"' logs/whatsapp.log

# Resumos de sessão
grep '"event": "session_summary"' logs/whatsapp.log
```

### Análise com Python

```python
import json

# Ler logs estruturados
with open('logs/whatsapp.log', 'r') as f:
    for line in f:
        if '|' in line:
            # Extrair JSON do log
            json_part = line.split('|', 1)[1].strip()
            try:
                data = json.loads(json_part)
                if data['event'] == 'message_attempt':
                    print(f"{data['contact_name']}: {data['status']}")
            except:
                pass
```

### Análise com MongoDB

Se estiver usando MongoDB, os logs estruturados também são salvos lá:

```javascript
// Contar mensagens por status
db.log.aggregate([
  { $match: { message: /message_attempt/ } },
  { $group: { _id: "$status", count: { $sum: 1 } } }
])

// Taxa de sucesso por dia
db.log.aggregate([
  { $match: { message: /session_summary/ } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$time" } },
      avgSuccessRate: { $avg: "$success_rate_percent" }
  }}
])
```

## Métricas Disponíveis

| Métrica | Descrição |
|---------|-----------|
| `total_contacts` | Total de contatos processados |
| `total_phones_processed` | Total de telefones processados |
| `messages_sent` | Mensagens enviadas com sucesso |
| `messages_failed` | Mensagens que falharam |
| `invalid_phones` | Números inválidos |
| `not_found_phones` | Números não encontrados no WhatsApp |
| `success_rate_percent` | Taxa de sucesso (%) |
| `messages_per_minute` | Velocidade de envio |
| `errors_by_type` | Erros agrupados por tipo |

## Segurança: .env

### ⚠️ IMPORTANTE

O arquivo `.env` contém credenciais sensíveis e **NÃO deve ser commitado** no Git.

### Configuração

1. **Use o template `.env.example`:**
   ```bash
   cp .env.example .env
   ```

2. **Preencha suas credenciais em `.env`:**
   ```bash
   DATABASE_URL=mongodb+srv://seu_usuario:sua_senha@cluster.mongodb.net/database
   ```

3. **Verifique que `.env` está no `.gitignore`:**
   ```bash
   cat .gitignore | grep .env
   # Deve mostrar: .env
   ```

4. **Nunca commite `.env`:**
   ```bash
   git status
   # .env NÃO deve aparecer na lista
   ```

### Se você já commitou .env por engano

```bash
# Remover do histórico do Git
git rm --cached .env
git commit -m "Remove sensitive .env file"

# Rotacionar credenciais (mudar senha do MongoDB)
```

## Próximos Passos

- [ ] Configurar alertas baseados em métricas
- [ ] Criar dashboard de visualização
- [ ] Adicionar exportação de métricas para CSV
- [ ] Integrar com sistema de monitoramento (Prometheus/Grafana)
