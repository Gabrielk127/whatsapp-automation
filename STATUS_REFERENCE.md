"""
Guia de Status de Mensagens - SentMessage

Este arquivo documenta todos os status possíveis que podem ser salvos no banco de dados
para cada contato após a tentativa de envio de mensagens.

=== STATUS DE SUCESSO ===

- SENT: Todas as 3 mensagens foram enviadas com sucesso
- PARTIAL_1/3: 1 mensagem foi enviada
- PARTIAL_2/3: 2 mensagens foram enviadas

=== STATUS DE ERRO - NÚMERO NÃO ESTÁ NO WHATSAPP ===

- INVALID_Número_não_está_no_WhatsApp: Número não tem WhatsApp ativo
- INVALID_Número_não_tem_WhatsApp: Variação da mesma situação
- NOT_FOUND: Campo de mensagem não foi encontrado (provável que não tenha WhatsApp)

=== STATUS DE ERRO - NÚMERO INVÁLIDO ===

- INVALID_Número_inválido: Número não passou na validação do WhatsApp
- INVALID_Alerta_geral: Algum alerta foi exibido na página

=== STATUS DE ERRO - ENVIO ===

- ERROR_1/3: Erro ao enviar (1 mensagem foi enviada antes do erro)
- ERROR_2/3: Erro ao enviar (2 mensagens foram enviadas antes do erro)

=== COMO LER OS DADOS ===
Você pode consultar os dados no MongoDB:

db.sentmessage.find({}) # Buscar todas as mensagens

Ou filtrar por status:
db.sentmessage.find({ "status": "SENT" }) # Apenas sucessos
db.sentmessage.find({ "status": { $regex: "INVALID" } }) # Todos os inválidos
db.sentmessage.find({ "status": { $regex: "ERROR" } }) # Todos com erro

=== ANÁLISE ===
Com esses status você pode:

1. Identificar quais números não têm WhatsApp
2. Saber quantas mensagens foram enviadas antes de cada erro
3. Fazer retry apenas dos números com erro (não dos inválidos)
4. Gerar relatórios de taxa de sucesso
   """
