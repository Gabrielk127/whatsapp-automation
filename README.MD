# Base Starter para Automação Python

Este repositório serve como uma base inicial para projetos de automação utilizando Python. Ele fornece uma estrutura organizada e exemplos básicos para facilitar o desenvolvimento de automações personalizadas.

## Estrutura do Projeto

Abaixo está a descrição de cada diretório e sua finalidade:

- **`assets/`**: Contém arquivos de mídia, como imagens, que podem ser utilizados nas automações.
- **`config/`**: Scripts de configuração do projeto.
- **`prisma/`**: Configuração do Prisma ORM, incluindo o arquivo `schema.prisma` para modelagem de dados.
- **`src/`**: Diretório principal do código-fonte.
  - **`src/config/`**: Configurações específicas do projeto, como integração com o Prisma e manipuladores de logs.
  - **`src/enums/`**: Definições de enums para uso no projeto.
  - **`src/examples/`**: Scripts de exemplo para testar funcionalidades isoladas.
  - **`src/repositories/`**: Repositórios para gerenciar dados, como o `log_repository.py` para logs.
   <!-- Removido: src/robot/ (implementações PyAutoGUI) -->
  - **`src/services/`**: Lógica de negócios e serviços do projeto.
  - **`src/types/`**: Definições de tipos utilizados no projeto.
  - **`src/utils/`**: Utilitários gerais, como funções para manipulação de imagens e sincronização de métodos assíncronos.

## Como Usar

1. Clone o repositório:

   ```bash
   git clone https://link-para-o-projeto
   cd nome-do-projeto
   ```

2. Crie e ative o ambiente virtual:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

   nas próximas execuções, você pode simplesmente usar:
   ```bash
   make install
   ```

4. Execute o projeto:

   - **Execução Local Direta:**
     ```bash
     make start
     ```

   - **Execução como Servidor Flask:**
     ```bash
     make server
     ```

     Após iniciar o servidor, acesse `http://localhost:5000` no navegador ou utilize a API diretamente.

## Comandos Disponíveis

- `make start` - Configura permissões e executa o programa principal.
- `make server` - Inicia o servidor Flask.
- `make setup` - Configura permissões X11 no Linux.
- `make install` - Instala dependências do `requirements.txt`.
- `make clean` - Remove arquivos de cache Python.
- `make help` - Mostra ajuda dos comandos disponíveis.
