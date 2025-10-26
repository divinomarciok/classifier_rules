# Classifier v2: Motor de Regras Orientado a Dados

Um sistema de classificação de produtos orientado a dados com avaliação flexível de regras, resolução de prioridades e auditoria abrangente.

## Visão Geral

**Classifier v2** move a lógica de classificação de regras Python codificadas para uma arquitetura orientada por banco de dados. As regras são armazenadas no banco de dados (tabela `regras_de_classificacao`), permitindo que usuários não-técnicos gerenciem classificações sem alterações no código.

### Características Principais

- **Avaliação de Regras Orientada a Dados**: Regras definidas no banco de dados, não no código
- **Resolução de Conflitos Baseada em Prioridade**: Múltiplas regras correspondentes sempre se resolvem consistentemente
- **Auditoria Abrangente**: Rastreabilidade completa de todas as decisões de classificação
- **Processamento em Lote**: Classifique múltiplos produtos do banco de dados com um comando
- **Importação/Exportação CSV**: Suporte para fluxos de trabalho baseados em planilhas
- **Correspondência Flexível de Critérios**: Palavras-chave, padrões NCM, intervalos de tamanho/quantidade

## Arquitetura

```
RuleEngine (Python)
    ├── Matcher (correspondência de critérios)
    ├── Evaluator (seleção de regra)
    └── AuditLog (registro de decisões)
         ↓
    PostgreSQL Database
    ├── regras_de_classificacao (tabela de regras)
    ├── auditoria_classificacao (log de auditoria)
    └── criterios_palavras_chave (índice de palavras-chave)
```

## Início Rápido

### Instalação

```bash
# Clonar repositório
git clone <repository-url>
cd classifier-rules

# Criar ambiente virtual
python3.8+ -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
pip install -e .  # Instalar pacote em modo desenvolvimento
```

### Configuração

```bash
# Copiar arquivo de ambiente exemplo
cp .env.example .env

# Editar .env com suas credenciais de banco de dados
# DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
```

### Configuração do Banco de Dados

```bash
# Inicializar banco de dados (cria tabelas e migrações)
python -c "from classifier.utils import init_database; init_database()"
```

### Primeira Classificação

```python
from classifier.engine import RuleEngine

# Criar instância do engine
engine = RuleEngine()

# Classificar um produto
product = {
    "id": "P001",
    "description": "laptop computer",
    "ncm": "84713090",
    "size": 0.5,
    "quantity": 1
}

result = engine.evaluate(product)
print(result)
# Saída: {'classification': 'ELETRÔNICOS', 'rule_id': 1, 'priority': 100, ...}
```

## Uso

### Avaliação Básica de Regra (US1)

```python
engine = RuleEngine()
product = {"id": "P001", "description": "laptop", "ncm": "84713090"}
result = engine.evaluate(product)
```

### Classificação em Lote a partir do Banco de Dados (US4)

```bash
# Classificar 500 produtos não classificados
python -m classifier.cli.classify_batch -500

# Com filtros personalizados
python -m classifier.cli.classify_batch -1000 --offset 100
```

### Classificação CSV (US5)

```bash
# Classificação CSV simples
python -m classifier.cli.classify_csv \
  --input produtos.csv \
  --output resultado.csv

# Com trilha de auditoria
python -m classifier.cli.classify_csv \
  --input produtos.csv \
  --output resultado.csv \
  --audit auditoria.csv

# Também atualizar banco de dados
python -m classifier.cli.classify_csv \
  --input produtos.csv \
  --output resultado.csv \
  --update-db
```

## Documentação

- **[Especificação](specs/001-rule-engine/spec.md)**: Especificação completa de recursos com 5 histórias de usuário
- **[Plano de Implementação](specs/001-rule-engine/plan.md)**: Arquitetura técnica e estrutura do projeto
- **[Modelo de Dados](specs/001-rule-engine/data-model.md)**: Esquema de banco de dados e relacionamentos entre entidades
- **[Guia CSV](specs/001-rule-engine/CSV_CLARIFICATION.md)**: Modos CSV e locais de armazenamento
- **[Guia de Início Rápido](specs/001-rule-engine/quickstart.md)**: Guia detalhado de configuração e uso

## Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src/classifier tests/

# Executar arquivo de teste específico
pytest tests/unit/test_matcher.py

# Executar testes que correspondem ao padrão
pytest -k "test_priority" -v
```

## Estrutura do Projeto

```
.
├── src/classifier/
│   ├── __init__.py          # Classes de exceção
│   ├── models.py            # Modelos de dados (Rule, Product, etc)
│   ├── engine.py            # Classe RuleEngine principal
│   ├── evaluator.py         # Lógica de avaliação de regra
│   ├── matcher.py           # Correspondência de critérios
│   ├── audit.py             # Serviço de log de auditoria
│   ├── utils.py             # Utilitários de configuração e banco de dados
│   └── cli/
│       ├── classify_batch.py     # Script de classificação em lote
│       ├── classify_csv.py       # Script de importação/exportação CSV
│       └── export_batch.py       # Script de exportação de banco de dados
├── tests/
│   ├── conftest.py          # Fixtures do Pytest
│   ├── contract/            # Testes de contrato da API
│   ├── integration/         # Testes ponta-a-ponta
│   └── unit/                # Testes de componentes
├── migrations/              # Migrações de banco de dados
│   ├── 001_create_tables.sql
│   ├── 002_create_indexes.sql
│   └── ROLLBACK.md
├── docs/                    # Documentação
├── specs/                   # Especificações de recursos
├── input/                   # Arquivos CSV de entrada
├── output/                  # Arquivos de saída
├── setup.py                 # Configuração de pacote
└── requirements.txt         # Dependências
```

## Esquema de Banco de Dados

### regras_de_classificacao (Regras)
```sql
id              | SERIAL PRIMARY KEY
prioridade      | INTEGER (maior = mais importante)
nome            | VARCHAR (nome da regra)
ativo           | BOOLEAN (ativo/inativo)
criterio_palavras_chave     | VARCHAR (palavras-chave para correspondência)
criterio_ncm    | VARCHAR (padrão NCM com *)
criterio_tamanho_min | FLOAT
criterio_tamanho_max | FLOAT
criterio_quantidade_min | INT
criterio_quantidade_max | INT
resultado_classificacao | VARCHAR
data_criacao    | TIMESTAMP
data_atualizacao | TIMESTAMP
```

### auditoria_classificacao (Log de Auditoria)
```sql
id              | SERIAL PRIMARY KEY
id_regra        | INTEGER FOREIGN KEY
id_produto      | VARCHAR
descricao_produto | VARCHAR
criterios_combinados | VARCHAR (JSON)
resultado_classificacao | VARCHAR
data_classificacao | TIMESTAMP
tempo_avaliacao_ms | INTEGER
```

## Configuração

### Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|----------|---------|-------------|
| `DB_HOST` | Sim | - | Nome do servidor PostgreSQL |
| `DB_NAME` | Sim | - | Nome do banco de dados |
| `DB_USER` | Sim | - | Usuário do banco de dados |
| `DB_PASSWORD` | Sim | - | Senha do banco de dados |
| `DB_PORT` | Não | 5432 | Porta PostgreSQL |
| `APP_LOG_LEVEL` | Não | INFO | Nível de log |
| `ENABLE_RULE_CACHING` | Não | true | Cache de regras em memória |

## Desenvolvimento

### Executando Testes

```bash
# Todos os testes
pytest

# Arquivo de teste específico
pytest tests/unit/test_matcher.py -v

# Com relatório de cobertura
pytest --cov=src/classifier --cov-report=html

# Testes de performance
pytest tests/performance/ -v
```

### Estilo de Código

```bash
# Formatar código com black
black src/ tests/

# Verificar código com flake8
flake8 src/ tests/

# Verificação de tipo com mypy
mypy src/
```

## Metas de Desempenho

- **Avaliação de Regra**: < 500ms para 95º percentil com 10.000 regras ativas
- **Processamento em Lote**: 500 produtos em < 5 minutos
- **Processamento CSV**: 50.000 linhas em < 10 minutos
- **Log de Auditoria**: 100% de completude para todas as classificações

## Solução de Problemas

### Problemas de Conexão com Banco de Dados

```python
from classifier.utils import get_db_connection
try:
    conn = get_db_connection()
except DatabaseError as e:
    print(f"Falha na conexão: {e}")
```

### Nenhuma Regra Corresponde

```python
result = engine.evaluate(product)
if result['classification'] == 'NO_MATCH':
    print(f"Produto {product['id']} não correspondeu a nenhuma regra")
    # Verificar logs de auditoria para tentativas de correspondência
```

### Problemas de Codificação CSV

Certifique-se de que os arquivos CSV estejam codificados em UTF-8:

```bash
# Converter CSV para UTF-8 se necessário
iconv -f ISO-8859-1 -t UTF-8 entrada.csv > entrada_utf8.csv
```

## Contribuindo

1. Criar branch de recurso a partir de `main`
2. Seguir a especificação em `specs/001-rule-engine/spec.md`
3. Escrever testes primeiro (abordagem TDD)
4. Garantir que todos os testes passem: `pytest`
5. Seguir estilo de código: `black` e `flake8`
6. Criar pull request com descrição

## Licença

[Sua Licença Aqui]

## Suporte

Para problemas, dúvidas ou sugestões:
- Verifique a [Especificação](specs/001-rule-engine/spec.md)
- Revise o [Guia de Início Rápido](specs/001-rule-engine/quickstart.md)
- Abra uma issue no GitHub

## Roteiro

### Fase 1: MVP (Histórias de Usuário 1-3)
- ✓ Avaliação básica de regra
- ✓ Resolução de prioridade
- ✓ Log de auditoria

### Fase 2: Scripts (Histórias de Usuário 4-5)
- ⏳ Classificação em lote a partir do banco de dados
- ⏳ Suporte de importação/exportação CSV

### Fase 3: Polimento e Implantação
- ⏳ Otimização de desempenho
- ⏳ Documentação abrangente
- ⏳ Guia de implantação em produção

---

**Última Atualização**: 2025-10-25
**Versão**: 0.1.0-alpha
**Status**: Em Desenvolvimento
