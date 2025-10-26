# CLAUDE.md

Este arquivo fornece orientações para Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## Visão Geral do Projeto

**Classifier v2: Motor de Classificação Orientado a Dados**

Um sistema de classificação de produtos orientado a dados que evolui de um classificador simples baseado em NCM para um motor de regras flexível. A inovação central é mover a lógica de classificação de regras Python codificadas para uma arquitetura orientada por banco de dados, armazenada em uma tabela `regras_de_classificacao`.

### Filosofia da Arquitetura

**Princípio-Chave:** A aplicação Python é um motor de regras genérico que lê e aplica regras do banco de dados. A lógica de classificação reside nos dados, não no código.

**Vantagens desta abordagem:**
- **Manutenção Simples:** Modifique classificações editando registros do banco de dados, sem mudanças de código
- **Precisão Aprimorada:** Regras podem segmentar descrições específicas de produtos com correspondência de palavras-chave, tendo prioridade sobre regras NCM genéricas
- **Escalabilidade:** Suporta milhares de regras sem complexidade adicional no código
- **Auditabilidade:** A lógica de negócio é transparente e consultável no banco de dados



### Configuração Inicial do Projeto

O projeto é estruturado usando o framework SpecKit (localizado em `.specify/`) para desenvolvimento orientado por especificação:

### Schema da Tabela de Regras (`regras_de_classificacao`)

Todo o sistema de classificação depende desta tabela. Colunas esperadas incluem:
- Identificador da regra
- Prioridade/precedência
- Critérios de correspondência (palavras-chave, descrições de produtos, padrões NCM,Tamanho,Quantidade)
- Resultados de classificação
- Status (ativo/inativo)

### Estratégia de Prioridade de Regras

Regras de maior prioridade devem ser avaliadas primeiro:
1. Regras específicas de palavras-chave (correspondência de descrição de produto)
2. Regras específicas de categoria
3. Regras genéricas baseadas em NCM
4. Classificações padrão/fallback

## Padrões de Implementação-Chave

- **Design Orientado ao Banco de Dados:** Antes de escrever código Python, as regras devem ser definíveis no banco de dados
- **Sem Classificações Codificadas:** Toda a lógica de classificação deve vir da `regras_de_classificacao`
- **Composição de Regras:** Suportar regras complexas (condições AND/OR) sem mudanças de código
- **Performance:** Projetar consultas para lidar eficientemente com milhares de regras

## Estratégia de Testes

Dado o caráter orientado a dados, os testes devem cobrir:
- Lógica de avaliação de regras (dado input, verificar se regra correta é correspondida)
- Precedência de regras (garantir que regra correta vence em conflitos)
- Casos extremos (dados faltantes, correspondências ambíguas, conflitos de regras)
- Performance (tempo de pesquisa de regra com grandes conjuntos de regras)

## Workflow de Desenvolvimento de Features

Este projeto usa SpecKit para desenvolvimento estruturado de features:

```bash
# Criar uma nova especificação de feature
/speckit.specify

# Planejar a implementação
/speckit.plan

# Gerar tarefas de implementação
/speckit.tasks

# Executar tarefas
/speckit.implement

# Analisar consistência entre artefatos
/speckit.analyze

# Obter clarificações em áreas não especificadas
/speckit.clarify

# Criar constituição do projeto (princípios centrais)
/speckit.constitution

# Gerar checklist de testes
/speckit.checklist
```

## Setup e Execução do Projeto

### Pré-requisitos

1. **PostgreSQL** - Banco de dados para armazenar produtos e regras
2. **Python 3.8+** - Linguagem principal do projeto
3. **Virtual Environment** - Recomendado para isolamento de dependências

### Configuração Inicial Automática

Ao inicializar o projeto pela primeira vez, certifique-se de que:

#### 1. Banco de Dados PostgreSQL

A conexão padrão assume:
- Host: `localhost`
- Database: `market_v1`
- Variáveis de ambiente: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

**Como criar o banco de dados:**

```bash
# Conectar ao PostgreSQL como superusuário
psql -U postgres

# Dentro do psql, criar o banco de dados
CREATE DATABASE market_v1;

# Sair do psql
\q
```

**Ou usando linha de comando (sem entrar no psql):**

```bash
createdb -U postgres -h localhost market_v1
```

**Verificar se o banco foi criado:**

```bash
psql -U postgres -h localhost -l | grep market_v1
```

**Variáveis de ambiente esperadas:**

```bash
# Exemplos de valores
export DB_HOST=localhost
export DB_NAME=market_v1
export DB_USER=postgres
export DB_PASSWORD=sua_senha_aqui

# Ou criar arquivo .env (se o projeto suportar)
echo "DB_HOST=localhost" >> .env
echo "DB_NAME=market_v1" >> .env
echo "DB_USER=postgres" >> .env
echo "DB_PASSWORD=sua_senha_aqui" >> .env
```

#### 2. Tabelas Necessárias

O projeto requer as seguintes estruturas no banco:

**Tabela `produtos_tabela` (Produtos)**
```sql
CREATE TABLE produtos_tabela (
    id VARCHAR PRIMARY KEY,           -- Código de barras (renomeado de 'codbar')
    descricao VARCHAR(255),           -- Descrição do produto
    ncm VARCHAR(8),                   -- NCM do produto
    categoria VARCHAR(255),           -- Categoria atribuída (NULL inicialmente)
    data_classificacao TIMESTAMP,     -- Data da classificação
    -- Colunas adicionais opcionais:
    -- desc_sem_acento, desc_upper, desc_lower, foto, main_category, etc.
);
```

**Tabela `regras_de_classificacao` (Regras de Classificação)**
```sql
CREATE TABLE regras_de_classificacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE,
    ativo BOOLEAN DEFAULT TRUE,
    prioridade INTEGER DEFAULT 100,
    criterio_palavras_chave VARCHAR(255),      -- Palavra-chave para buscar em descrições
    criterio_ncm VARCHAR(255),                 -- Padrão NCM (ex: "8471%")
    criterio_tamanho_min FLOAT,                -- Tamanho mínimo do produto
    criterio_tamanho_max FLOAT,                -- Tamanho máximo
    criterio_quantidade_min INTEGER,           -- Quantidade mínima
    criterio_quantidade_max INTEGER,           -- Quantidade máxima
    criterio_categoria VARCHAR(255),           -- Categoria a filtrar
    resultado_classificacao VARCHAR(255) NOT NULL,  -- Categoria resultado
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prioridade ON regras_de_classificacao(prioridade DESC);
CREATE INDEX idx_ativa ON regras_de_classificacao(ativo);
```

#### 3. Instalação de Dependências

```bash
# Criar virtual environment
python3 -m venv venv

# Ativar virtual environment
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências do projeto
pip install -e .
```

### Como Rodar o Batch Classification

```bash
# Ativar virtual environment
source venv/bin/activate

# Ver estatísticas gerais de classificação
python3 -m classifier.cli.classify_batch --stats

# Classificar 500 produtos (padrão)
python3 -m classifier.cli.classify_batch --limit 500

# Classificar 100 produtos com offset 0
python3 -m classifier.cli.classify_batch --limit 100 --offset 0

# Classificar em modo simulação (sem atualizar BD)
python3 -m classifier.cli.classify_batch --limit 500 --dry-run

# Filtrar por NCM específico
python3 -m classifier.cli.classify_batch --where "ncm LIKE '8471%'" --limit 500

# Saída em JSON
python3 -m classifier.cli.classify_batch --limit 500 --json

# Ativar logging verboso
python3 -m classifier.cli.classify_batch --limit 500 --verbose
```

### Pontos Importantes Configurados

1. **Nomes de Tabelas:** Projeto usa `produtos_tabela` (português correto), não `productos_tabela`
2. **Chave Primária:** Coluna `id` da tabela `produtos_tabela` contém códigos de barras (string)
3. **Regras:** Todas as regras de classificação lidas dinamicamente do banco via engine.py
4. **Performance:** Sistema carrega 79.201+ produtos de forma eficiente
5. **Logging:** Sistema registra cada step da classificação para debugging

## Troubleshooting - Erros Comuns e Soluções

### Erro: "relation \"produtos_tabela\" does not exist"

**Causa:** A tabela `produtos_tabela` não foi criada no banco de dados.

**Solução:**

```bash
# 1. Verificar se o banco de dados foi criado
psql -U postgres -h localhost -l | grep market_v1

# 2. Se não existir, criar o banco
createdb -U postgres -h localhost market_v1

# 3. Conectar ao banco e criar a tabela
psql -U postgres -h localhost -d market_v1 -c "
CREATE TABLE produtos_tabela (
    id VARCHAR PRIMARY KEY,
    descricao VARCHAR(255),
    ncm VARCHAR(8),
    categoria VARCHAR(255),
    data_classificacao TIMESTAMP
);
"
```

### Erro: "column \"categoria\" does not exist"

**Causa:** A coluna `categoria` ou `data_classificacao` não foi adicionada à tabela.

**Solução:**

```bash
psql -U postgres -h localhost -d market_v1 -c "
ALTER TABLE produtos_tabela ADD COLUMN categoria VARCHAR(255);
ALTER TABLE produtos_tabela ADD COLUMN data_classificacao TIMESTAMP;
"
```

### Erro: "column \"ativo\" does not exist" (ao rodar batch)

**Causa:** A tabela `regras_de_classificacao` possui coluna `ativa` ao invés de `ativo`.

**Solução:**

```bash
psql -U postgres -h localhost -d market_v1 -c "
ALTER TABLE regras_de_classificacao RENAME COLUMN ativa TO ativo;
"
```

### Erro: "could not connect to server: Connection refused"

**Causa:** PostgreSQL não está rodando ou a conexão está incorreta.

**Solução:**

```bash
# 1. Verificar se PostgreSQL está rodando
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # Mac

# 2. Iniciar PostgreSQL (se não estiver rodando)
sudo systemctl start postgresql  # Linux
brew services start postgresql@14  # Mac (versão pode variar)

# 3. Verificar credenciais (usuário/senha/host)
export DB_HOST=localhost
export DB_USER=postgres
export DB_NAME=market_v1
export DB_PASSWORD=sua_senha

# 4. Testar conexão
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "SELECT 1;"
```

### Erro: "FATAL: password authentication failed for user \"postgres\""

**Causa:** Senha incorreta do usuário PostgreSQL.

**Solução:**

```bash
# 1. Redefinir senha do usuário postgres (no Linux)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'nova_senha';"

# 2. Atualizar variável de ambiente
export DB_PASSWORD=nova_senha

# 3. Testar conexão
psql -U postgres -h localhost -d market_v1
```

### Erro: "python3: command not found"

**Causa:** Python 3 não está instalado ou não está no PATH.

**Solução:**

```bash
# Verificar instalação
python3 --version

# Se não estiver instalado
# Ubuntu/Debian
sudo apt-get install python3 python3-pip python3-venv

# Mac
brew install python3

# Windows - Baixar do https://www.python.org/downloads/
```

### Erro: "ModuleNotFoundError: No module named 'classifier'"

**Causa:** O projeto não foi instalado com `pip install -e .` ou o venv não está ativado.

**Solução:**

```bash
# 1. Ativar virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instalar o projeto
pip install -e .

# 3. Verificar instalação
python3 -c "import classifier; print('OK')"
```

### Erro: "No rules matched for product" (todos os produtos)

**Causa:** Não há regras ativas na tabela `regras_de_classificacao` ou as regras não correspondem aos produtos.

**Solução:**

```bash
# 1. Verificar regras ativas
psql -U postgres -h localhost -d market_v1 -c "
SELECT id, nome, ativo, prioridade FROM regras_de_classificacao WHERE ativo = TRUE;
"

# 2. Se não houver regras, inserir algumas de teste
psql -U postgres -h localhost -d market_v1 -c "
INSERT INTO regras_de_classificacao (nome, ativo, prioridade, criterio_palavras_chave, resultado_classificacao)
VALUES ('Test Rule', TRUE, 1, 'laptop', 'ELETRÔNICOS');
"

# 3. Verificar descrições dos produtos para correspondência
psql -U postgres -h localhost -d market_v1 -c "
SELECT id, descricao FROM produtos_tabela LIMIT 5;
"
```

### Erro: "value \"...\" is out of range for type integer"

**Causa:** Tentando inserir um valor de string muito grande em uma coluna inteira ou usando ID de produto com muitos dígitos.

**Solução:** Garantir que `id` em `produtos_tabela` é VARCHAR, não INTEGER.

```bash
# Verificar tipo de coluna
psql -U postgres -h localhost -d market_v1 -c "
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'produtos_tabela' AND column_name = 'id';
"

# Se for INTEGER, converter para VARCHAR
psql -U postgres -h localhost -d market_v1 -c "
ALTER TABLE produtos_tabela ALTER COLUMN id TYPE VARCHAR;
"
```

### Como Ativar Logging Verboso

Para entender melhor o que está acontecendo:

```bash
# Rodar com verbose
python3 -m classifier.cli.classify_batch --limit 100 --verbose

# Com log level DEBUG
python3 -m classifier.cli.classify_batch --limit 100 --log-level DEBUG

# Salvar logs em arquivo
python3 -m classifier.cli.classify_batch --limit 100 --verbose 2>&1 | tee batch.log
```

## Notas Importantes para Desenvolvimento Futuro

- **Evite Débito Técnico:** O motor de regras deve permanecer simples e genérico; não adicione casos especiais no código
- **Documentação:** Cada tipo de regra ou estratégia de correspondência deve ser documentada com exemplos no banco de dados ou em um guia de regras
- **Compatibilidade Retroativa:** Ao alterar schema de regras, garanta que regras existentes continuem funcionando ou tenham caminhos de migração claros
- **Monitoramento:** Implemente logging para rastrear hits de regras e erros de classificação para melhoria contínua
- **Nomes de Colunas:** Sempre use nomes em português e verificar correspondência exata entre código Python e schema do banco
