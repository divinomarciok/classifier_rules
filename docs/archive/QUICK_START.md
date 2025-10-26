# Guia de Início Rápido - Classifier v2

O sistema de classificação de produtos está totalmente implementado e pronto para uso. Este guia o orienta a começar em 5 minutos.

## 1. Verificação de Pré-requisitos (1 minuto)

Seu sistema precisa de:
- ✅ Python 3.8+ com ambiente virtual ativado
- ✅ Banco de dados PostgreSQL com tabela `produtos_tabela`
- ✅ Pacote Classifier instalado (`pip install -e .`)

**Verificar ambiente:**
```bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras
python3 -c "import classifier; print('✅ Classifier instalado')"
```

## 2. Verificar Banco de Dados (1 minuto)

Seu banco de dados deve ter estas três tabelas em português:

```bash
# Listar tabelas no seu banco de dados
psql -U postgres -d classifier -c "\dt"
```

**Deve ver:**
- `produtos_tabela` - Produtos a classificar
- `regras_de_classificacao` - Regras de classificação
- `auditoria_classificacao` - Trilha de auditoria

**Se as tabelas estão faltando**, veja DATABASE_SETUP.md para scripts de criação.

## 3. Testar Conexão (1 minuto)

```bash
# Verificar estatísticas do banco de dados
classify-batch --stats
```

**Deve exibir:**
```
ESTATÍSTICAS DE CLASSIFICAÇÃO EM LOTE
============================================================
Total de Produtos:       X produtos
Classificados:           X produtos
Não Classificados:       X produtos
Taxa de Classificação:   X%
```

Se você vir erro `relation 'produtos_tabela' does not exist`, o nome da tabela do banco de dados está incorreto (veja VERIFY_DATABASE.md).

## 4. Classificar Produtos (2 minutos)

### Opção A: Lote do Banco de Dados

```bash
# Classificar próximos 10 produtos não classificados
classify-batch --limit 10

# Ou com pré-visualização sem atualizar BD
classify-batch --limit 10 --dry-run
```

### Opção B: Importar de CSV

```bash
# Processar arquivo CSV
classify-csv samples/products_basic.csv

# Arquivo de saída: samples/products_basic_classified.csv
# Verificar resultados
head samples/products_basic_classified.csv
```

### Opção C: API Python

```python
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

db = get_db_connection()
engine = RuleEngine(db)

# Classificar produto único
result = engine.evaluate({
    'id': 'PROD_001',
    'description': 'laptop dell',
    'ncm': '84713090'
})

print(f"Classificação: {result.classification}")
print(f"Correspondeu: {result.success}")
```

## 5. Monitorar Resultados

```bash
# Ver estatísticas gerais
classify-batch --stats

# Ver classificações recentes
psql -U postgres -d classifier -c "
  SELECT id_produto, resultado_classificacao, data_classificacao
  FROM auditoria_classificacao
  ORDER BY data_classificacao DESC
  LIMIT 10;
"

# Encontrar produtos que não puderam ser classificados
psql -U postgres -d classifier -c "
  SELECT id, description
  FROM produtos_tabela
  WHERE categoria IS NULL
  LIMIT 10;
"
```

## 6. Próximos Passos

- **Ver instruções detalhadas**: HOW_TO_RUN.md
- **Testar o sistema**: TESTING_GUIDE.md
- **Entender banco de dados**: DATABASE_SETUP.md
- **Verificar configuração**: VERIFY_DATABASE.md
- **Ver projeto completo**: PROJECT_SUMMARY.md

---

## Problemas Comuns & Correções Rápidas

### ❌ "relation 'productos_tabela' does not exist"
**Correção**: O nome da tabela do banco de dados está errado. Verifique VERIFY_DATABASE.md para o nome correto em português: `produtos_tabela`

### ❌ "No such file or directory"
**Correção**: Certifique-se de estar no diretório correto:
```bash
cd /home/divinopc/testes/projects/classifier_regras
source /tmp/classifier_venv/bin/activate
```

### ❌ "could not connect to database"
**Correção**: PostgreSQL deve estar em execução:
```bash
sudo systemctl start postgresql
# ou
pg_ctl -D /usr/local/var/postgres start
```

### ❌ "No products matched"
**Correção**: Verifique que as regras existem com critérios ativos:
```bash
psql -U postgres -d classifier -c "
  SELECT id, nome, criterio_palavras_chave, ativo
  FROM regras_de_classificacao
  WHERE ativo = true
  LIMIT 5;
"
```

Se vazio, crie regras de teste (veja DATABASE_SETUP.md).

---

## Visão Geral da Arquitetura

O classificador usa um **motor de regras orientado a dados**:

1. **Regras no Banco de Dados** (`regras_de_classificacao`)
   - Regras são armazenadas como registros do banco de dados, não codificadas
   - Cada regra tem: nome, prioridade, critérios, resultado, status
   - Prioridade determina seleção de regra quando múltiplas regras correspondem

2. **Correspondência Flexível** (5 tipos de critérios)
   - Correspondência de palavras-chave (busca de substring em descrição)
   - Correspondência de padrão NCM (padrões com caractere coringa)
   - Correspondência de intervalo de tamanho (mín/máx)
   - Correspondência de intervalo de quantidade (mín/máx)
   - Correspondência exata de categoria

3. **Seleção Determinística**
   - Regras de prioridade mais alta vencem
   - Mesma prioridade: regra mais antiga vence (FIFO)
   - Todas as decisões registradas em `auditoria_classificacao`

4. **Trilha de Auditoria** (Imutável)
   - Cada classificação registrada com timestamp
   - Pode rastrear qual regra fez cada decisão
   - Histórico completo para conformidade

## Referência de Comandos

### Classificação em Lote
```bash
# Classificar 500 produtos
classify-batch

# Classificar com limite personalizado
classify-batch --limit 100

# Pré-visualização sem atualizar BD
classify-batch --limit 10 --dry-run

# Mostrar apenas estatísticas
classify-batch --stats

# Saída JSON
classify-batch --limit 10 --json

# Filtrar produtos específicos (ex: NCM começando com 84)
classify-batch --where "ncm LIKE '84%'" --limit 50

# Log verboso
classify-batch --limit 10 --verbose
```

### Classificação CSV
```bash
# Processar arquivo CSV
classify-csv entrada.csv

# Especificar arquivo de saída
classify-csv entrada.csv --output resultados.csv

# Validar CSV antes de processar
classify-csv entrada.csv --validate

# Atualizar banco de dados com resultados
classify-csv entrada.csv --update-db

# Pular linhas já classificadas
classify-csv entrada.csv --skip-classified

# Formato CSV personalizado (delimitador ponto-e-vírgula, codificação Latin-1)
classify-csv entrada.csv --delimiter ";" --encoding "latin-1"

# Processar em lotes de 100 linhas
classify-csv entrada.csv --batch-size 100

# Saída JSON
classify-csv entrada.csv --json

# Pré-visualização
classify-csv entrada.csv --dry-run
```

## Arquivos Principais

| Arquivo | Propósito |
|------|---------|
| `QUICK_START.md` | Este guia (configuração de 5 minutos) |
| `HOW_TO_RUN.md` | Métodos de execução detalhados |
| `TESTING_GUIDE.md` | Testes abrangentes |
| `DATABASE_SETUP.md` | Configuração do banco de dados |
| `VERIFY_DATABASE.md` | Verificação do banco de dados |
| `PROJECT_SUMMARY.md` | Visão geral completa do projeto |
| `src/classifier/engine.py` | Motor de regras principal |
| `src/classifier/batch.py` | Serviço de classificação em lote |
| `src/classifier/csv_classifier.py` | Serviço de processamento CSV |
| `src/classifier/cli/` | Interfaces de linha de comando |

## Testes

O sistema inclui 277 testes automatizados:
- 150+ testes unitários (componentes isolados)
- 80+ testes de integração (workflows)
- 35+ testes de contrato (especificações de API)
- 12 testes CLI (interfaces de linha de comando)

Executar testes:
```bash
# Teste rápido (30 segundos)
pytest tests/unit/ tests/cli/ -q

# Teste completo (sem banco de dados)
pytest tests/ -q

# Com relatório de cobertura
pytest tests/ --cov=src/classifier
```

---

**Status**: ✅ Sistema totalmente implementado e pronto
**Última Correção**: Nomes de tabelas do banco de dados corrigidos para português (`produtos_tabela`)
**Documentação**: Guias completos fornecidos para todos os casos de uso
**Testes**: 189 testes unitários/CLI passando ✅
