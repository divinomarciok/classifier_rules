# Como Executar o Classificador - Guia Completo

Instruções passo-a-passo para executar o sistema de classificação de produtos.

---

## 🚀 Início Rápido (2 minutos)

### 1. Ativar o Ambiente Python
```bash
source /tmp/classifier_venv/bin/activate
```

### 2. Ir para o Diretório do Projeto
```bash
cd /home/divinopc/testes/projects/classifier_regras
```

### 3. Executar Classificação em Lote
```bash
classify-batch --limit 10
```

**Resultado**: Classifica 10 produtos do banco de dados e mostra resumo

### 4. Executar Classificação CSV
```bash
classify-csv samples/products_basic.csv
```

**Resultado**: Classifica produtos do arquivo CSV e cria `products_basic_classified.csv`

---

## 📋 Pré-requisitos

### O Que Você Precisa
- Python 3.8+ (você tem Python 3.12)
- Ambiente virtual com dependências instaladas (já feito)
- Banco de dados PostgreSQL (opcional, para recursos completos)

### Verificar Sua Configuração
```bash
# Verificar Python
python3 --version
# Saída: Python 3.12.x

# Verificar se ambiente está ativado
which python3
# Deve mostrar: /tmp/classifier_venv/bin/python3

# Verificar estrutura do projeto
ls -la /home/divinopc/testes/projects/classifier_regras/
# Deve mostrar: src/, tests/, docs/, samples/, etc.
```

---

## 📂 Estrutura de Diretórios

```
classifier_regras/
├── src/classifier/          # Código-fonte
│   ├── engine.py           # Motor de classificação principal
│   ├── matcher.py          # Correspondência de padrões
│   ├── evaluator.py        # Avaliação de regras
│   ├── audit.py            # Log de auditoria
│   ├── batch.py            # Processamento em lote
│   ├── csv_classifier.py   # Importação/exportação CSV
│   └── cli/                # Ferramentas de linha de comando
│       ├── classify_batch.py
│       └── classify_csv.py
│
├── samples/                 # Arquivos CSV de exemplo
│   ├── products_basic.csv
│   ├── products_full.csv
│   ├── products_semicolon.csv
│   └── products_invalid.csv
│
├── tests/                   # 277 testes automatizados
│   ├── unit/               # Testes de componentes
│   ├── integration/        # Testes de workflows
│   ├── contract/           # Testes de API
│   └── cli/                # Testes de ferramentas CLI
│
├── docs/                    # Documentação
│   ├── api.md
│   ├── rules_guide.md
│   ├── troubleshooting.md
│   └── deployment.md
│
└── migrations/              # Configuração de banco de dados
    └── *.sql files
```

---

## 🎯 Método 1: Classificação em Lote (do Banco de Dados)

### O Que Faz
Processa múltiplos produtos armazenados no banco de dados PostgreSQL.

### Pré-requisitos
- Banco de dados PostgreSQL com tabela `produtos_tabela`
- Regras em tabela `regras_de_classificacao`
- Conexão do banco de dados configurada em `.env`

### Executar

```bash
# Ativar ambiente
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Processar 10 produtos
classify-batch --limit 10

# Processar 100 produtos
classify-batch --limit 100

# Processar 500 produtos (limite padrão)
classify-batch

# Processar produtos começando do offset 500 (paginação)
classify-batch --limit 100 --offset 500

# Processar apenas produtos NCM específicos
classify-batch --where "ncm LIKE '8471%'"

# Pré-visualização sem atualizar banco de dados
classify-batch --limit 50 --dry-run

# Mostrar estatísticas gerais
classify-batch --stats

# Obter resultados como JSON
classify-batch --limit 10 --json
```

### O Que Você Verá
```
RESUMO DE CLASSIFICAÇÃO CSV
======================================================================
Arquivo de Entrada:  (processado em lote)
Arquivo de Saída:    (sem arquivo para modo lote)
Total Processado:    10 produtos
Total Correspondido: 8 produtos
Sem Correspondência: 2 produtos
Taxa de Correspondência: 80.0%
Linhas Puladas:      0
Tempo Decorrido:     1.234 ms (1.23s)

Resumo das Classificações:
  - ELETRÔNICOS........................................         8 produtos

Produtos sem Correspondência: 2 no total
  - PROD_UNKNOWN_1
  - PROD_UNKNOWN_2
======================================================================
```

### Opções Explicadas

| Opção | Propósito | Exemplo |
|--------|---------|---------|
| `--limit N` | Quantos produtos processar | `--limit 500` |
| `--offset N` | Pular primeiros N produtos (paginação) | `--offset 500` |
| `--where CLAUSE` | Filtrar produtos por condição SQL | `--where "ncm LIKE '8471%'"` |
| `--dry-run` | Simular sem atualizar banco de dados | `--dry-run` |
| `--stats` | Mostrar estatísticas, não processar | `--stats` |
| `--json` | Exibir resultados como JSON | `--json` |
| `--verbose` | Mostrar logs detalhados | `--verbose` |

---

## 📄 Método 2: Classificação CSV (do Arquivo)

### O Que Faz
1. Ler produtos de arquivo CSV
2. Classificar cada produto
3. Escrever resultados em novo arquivo CSV com classificações

### Pré-requisitos
- Arquivo CSV com colunas: `id`, `description`, `ncm`
- Colunas opcionais: `size`, `quantity`, `category`

### Executar
```bash
# Ativar ambiente
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Processar CSV de exemplo
classify-csv samples/products_basic.csv

# Especificar arquivo de saída
classify-csv samples/products_basic.csv --output meus_resultados.csv

# Validar CSV antes de processar
classify-csv samples/products_basic.csv --validate

# Pular produtos já classificados
classify-csv samples/products_basic.csv --skip-classified

# Usar delimitador ponto-e-vírgula (CSV Europeu)
classify-csv samples/products_semicolon.csv --delimiter ";"

# Lidar com codificação Latin-1
classify-csv dados_latin1.csv --encoding latin-1

# Atualizar banco de dados com classificações
classify-csv samples/products_basic.csv --update-db

# Obter saída JSON
classify-csv samples/products_basic.csv --json

# Combinar opções
classify-csv arquivo_grande.csv --output resultados.csv --skip-classified --update-db --verbose
```

### O Que Você Verá
```
RESUMO DE CLASSIFICAÇÃO CSV
======================================================================
Arquivo de Entrada:  (processado em lote)
Arquivo de Saída:    /home/usuario/products_basic_classified.csv
Total Processado:    15 produtos
Total Correspondido: 13 produtos
Sem Correspondência: 2 produtos
Taxa de Correspondência: 86.7%
Linhas Puladas:      0
Tempo Decorrido:     2.345 ms (2.35s)

Resumo das Classificações:
  - ELETRÔNICOS........................................        13 produtos

Produtos sem Correspondência: 2 no total
  - PROD_UNKNOWN_1
  - PROD_UNKNOWN_2
======================================================================
```

### Opções Explicadas

| Opção | Propósito | Exemplo |
|--------|---------|---------|
| `input.csv` | Arquivo CSV de entrada (obrigatório) | `produtos.csv` |
| `-o, --output` | Arquivo de saída (auto-gerado se omitido) | `-o resultados.csv` |
| `--validate` | Validar apenas formato CSV, não processar | `--validate` |
| `--skip-classified` | Pular produtos já classificados | `--skip-classified` |
| `--encoding` | Codificação do arquivo (utf-8, latin-1, etc) | `--encoding utf-8` |
| `--delimiter` | Caractere delimitador CSV | `--delimiter ";"` |
| `--batch-size` | Produtos por lote para eficiência de memória | `--batch-size 2000` |
| `--update-db` | Escrever classificações no banco de dados | `--update-db` |
| `--json` | Exibir resultados como JSON | `--json` |
| `--verbose` | Mostrar logs detalhados | `--verbose` |

### Formato CSV de Entrada

**Formato mínimo** (colunas obrigatórias):
```csv
id,description,ncm
PROD_001,laptop dell,84713090
PROD_002,monitor samsung,85287200
```

**Formato completo** (com campos opcionais):
```csv
id,description,ncm,size,quantity
PROD_001,laptop dell,84713090,2.5,50
PROD_002,monitor samsung,85287200,5.2,30
```

### Formato CSV de Saída

Mesmo da entrada, mais duas colunas novas:
```csv
id,description,ncm,size,quantity,classification,data_classificacao
PROD_001,laptop dell,84713090,2.5,50,ELETRÔNICOS,2025-10-25T11:30:00
PROD_002,monitor samsung,85287200,5.2,30,ELETRÔNICOS,2025-10-25T11:30:01
```

---

## 🐍 Método 3: API Python (Programático)

### O Que Faz
Usar o classificador diretamente do código Python.

### Pré-requisitos
- Ambiente Python ativado
- Módulos necessários importados

### Executar

#### Classificação Básica
```python
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

# Conectar ao banco de dados
db = get_db_connection()

# Criar engine
engine = RuleEngine(db)

# Classificar um produto único
result = engine.evaluate({
    'id': 'PROD_001',
    'description': 'laptop dell',
    'ncm': '84713090'
})

# Verificar resultado
print(f"Classificação: {result.classification}")
print(f"Sucesso: {result.success}")
print(f"ID da Regra: {result.rule_id}")
print(f"Nome da Regra: {result.rule_name}")
print(f"Tempo: {result.evaluation_time_ms}ms")
```

**Saída**:
```
Classificação: ELETRÔNICOS
Sucesso: True
ID da Regra: 1
Nome da Regra: Regra do Laptop
Tempo: 45ms
```

#### Classificação em Lote
```python
from classifier.batch import BatchClassifier

# Criar classificador em lote
batch = BatchClassifier(db)

# Processar 100 produtos
result = batch.classify_batch(limit=100)

# Verificar resultados
print(f"Total processado: {result['total_processed']}")
print(f"Total correspondido: {result['total_matched']}")
print(f"Taxa de correspondência: {result['match_rate']:.1%}")
print(f"Tempo: {result['elapsed_time_ms']}ms")

# Ver o que foi classificado
print("\nClassificações:")
for classification, count in result['classifications'].items():
    print(f"  {classification}: {count}")

# Ver o que não correspondeu
if result['no_match_products']:
    print("\nProdutos sem Correspondência:")
    for prod_id in result['no_match_products']:
        print(f"  {prod_id}")
```

#### Classificação CSV
```python
from classifier.csv_classifier import CSVClassifier

# Criar classificador CSV
classifier = CSVClassifier(db)

# Validar CSV
validation = classifier.validate_csv('entrada.csv')
if validation['valid']:
    print("✓ CSV é válido")
else:
    print("✗ CSV tem problemas:")
    for issue in validation['issues']:
        print(f"  - {issue}")

# Processar CSV
result = classifier.classify_csv(
    input_file='entrada.csv',
    output_file='saída.csv',
    skip_classified=False,
    update_db=True
)

print(f"Processado: {result['total_processed']} produtos")
print(f"Correspondido: {result['total_matched']} produtos")
print(f"Saída: {result['output_file']}")
```

#### Consultas de Auditoria
```python
from classifier.audit import AuditLog

# Criar logger de auditoria
audit = AuditLog(db)

# Obter histórico de classificação do produto
history = audit.get_product_history(product_id='PROD_001')
for entry in history:
    print(f"Regra {entry.id_regra}: {entry.resultado_classificacao}")

# Obter estatísticas de regra
stats = audit.get_rule_statistics(rule_id=1)
print(f"Vezes aplicada: {stats['times_applied']}")
print(f"Tempo médio: {stats['avg_time_ms']}ms")
print(f"Última usada: {stats['last_applied']}")

# Encontrar produtos sem correspondências
no_match = audit.get_no_match_classifications(limit=10)
for entry in no_match:
    print(f"Produto {entry.id_produto} não correspondeu a nenhuma regra")
```

---

## 🧪 Método 4: Testes (Verificar Tudo Funciona)

### Executar Todos os Testes
```bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Executar todos os testes
pytest tests/ -v
# Esperado: 277 testes passando

# Executar apenas testes rápidos (sem banco de dados)
pytest tests/unit/ tests/cli/ -q
# Esperado: ~160 testes em 2 segundos

# Executar teste específico
pytest tests/unit/test_matcher.py -v

# Executar com cobertura
pytest tests/ --cov=src/classifier --cov-report=html
```

### Executar Testes de Dados de Exemplo
```bash
# Processar CSV de exemplo (básico)
classify-csv samples/products_basic.csv

# Validar CSV de exemplo (inválido)
classify-csv samples/products_invalid.csv --validate

# Processar com delimitador diferente
classify-csv samples/products_semicolon.csv --delimiter ";"

# Processar com todos os campos
classify-csv samples/products_full.csv
```

---

## 🔧 Configuração

### Configuração do Ambiente
```bash
# Verificar variáveis de ambiente
cat .env

# Definir conexão do banco de dados (se necessário)
export DATABASE_URL="postgresql://user:password@localhost/classifier"

# Ou criar arquivo .env:
cat > .env << 'ENVFILE'
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_NAME=classifier
ENVFILE
```

### Instalar/Atualizar Dependências
```bash
# Ativar ambiente
source /tmp/classifier_venv/bin/activate

# Instalar todos os requisitos
pip install -r requirements.txt

# Ou instalar pacote específico
pip install psycopg2-binary==2.9.0
```

---

## 📊 Casos de Uso Comuns

### Caso de Uso 1: Teste Rápido de Classificação
```bash
# Teste rápido com 10 produtos
classify-batch --limit 10
```

### Caso de Uso 2: Processar Arquivo CSV Completo
```bash
# Processar arquivo completo
classify-csv meusarquivo.csv --output resultados.csv

# Depois atualizar banco de dados
classify-csv meusarquivo.csv --update-db
```

### Caso de Uso 3: Validar Antes de Processar
```bash
# Verificar arquivo primeiro
classify-csv meusarquivo.csv --validate

# Se válido, processar
if [ $? -eq 0 ]; then
    classify-csv meusarquivo.csv
fi
```

### Caso de Uso 4: Processar em Lotes
```bash
# Processar em lotes de 500 produtos
for offset in 0 500 1000 1500 2000; do
    classify-batch --limit 500 --offset $offset
done
```

### Caso de Uso 5: Exportar Classificações
```bash
# Processar CSV e salvar resultados
classify-csv produtos.csv --output produtos_classificados.csv

# Ou atualizar banco de dados diretamente
classify-csv produtos.csv --update-db
```

### Caso de Uso 6: Verificar Estatísticas
```bash
# Ver progresso geral
classify-batch --stats
```

---

## 🐛 Solução de Problemas

### Problema: "command not found: classify-batch"

**Solução**: Ativar ambiente virtual
```bash
source /tmp/classifier_venv/bin/activate
which classify-batch  # Deve mostrar: /tmp/classifier_venv/bin/classify-batch
```

### Problema: "ModuleNotFoundError: No module named 'classifier'"

**Solução**: Certifique-se de estar no diretório do projeto
```bash
cd /home/divinopc/testes/projects/classifier_regras
source /tmp/classifier_venv/bin/activate
```

### Problema: "Database connection failed"

**Solução**: Verificar se banco de dados está rodando ou usar modo mock
```bash
# Verificar banco de dados
psql -h localhost -U postgres -l

# Ou executar testes sem banco de dados
pytest tests/unit/ tests/cli/ -q
```

### Problema: "CSV file encoding error"

**Solução**: Especificar codificação
```bash
# Tentar UTF-8 (padrão)
classify-csv arquivo.csv

# Tentar Latin-1
classify-csv arquivo.csv --encoding latin-1

# Tentar ISO-8859-1
classify-csv arquivo.csv --encoding iso-8859-1
```

### Problema: "Permission denied" em arquivos de exemplo

**Solução**: Tornar arquivos legíveis
```bash
chmod +r samples/*.csv
```

---

## ✅ Checklist de Sucesso

Você executou com sucesso o classificador quando:

- [ ] Ambiente ativado: `source /tmp/classifier_venv/bin/activate`
- [ ] Diretório correto: `cd /home/divinopc/testes/projects/classifier_regras`
- [ ] Comandos CLI funcionam: `classify-batch --help` mostra ajuda
- [ ] Testes passam: `pytest tests/unit/ -q` mostra 150+ passando
- [ ] Processamento CSV funciona: `classify-csv samples/products_basic.csv` cria arquivo de saída
- [ ] Arquivo de saída criado: `ls samples/products_basic_classified.csv`
- [ ] Classificações adicionadas: `head -3 samples/products_basic_classified.csv` mostra coluna de classificação

---

## 📚 Caminho de Aprendizado

### Dia 1: Começando
1. Ativar ambiente e verificar configuração
2. Executar testes rápidos: `pytest tests/unit/ -q`
3. Processar CSV de exemplo: `classify-csv samples/products_basic.csv`
4. Verificar resultados: `head samples/products_basic_classified.csv`

### Dia 2: Entendendo o Sistema
1. Ler `PROJECT_SUMMARY.md` para visão geral da arquitetura
2. Executar classificação em lote: `classify-batch --limit 10`
3. Tentar opções diferentes: `classify-batch --stats`
4. Revisar IMPLEMENTATION_LOG.md para detalhes de implementação

### Dia 3: Uso Avançado
1. Ler `docs/api.md` para referência da API
2. Usar API Python diretamente do shell
3. Testar com seus próprios arquivos CSV
4. Revisar `docs/rules_guide.md` para entender criação de regras

### Dia 4+: Uso em Produção
1. Revisar `docs/deployment.md` para configuração de implantação
2. Criar banco de dados e tabelas de `migrations/`
3. Adicionar suas próprias regras de classificação
4. Processar dados de produção com confiança

---

## 🎓 Dicas e Truques

### Dica 1: Manter Janela de Terminal Aberta
```bash
# Manter uma janela com ambiente ativado
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Depois executar comandos conforme necessário
```

### Dica 2: Salvar Aliases de Comando
```bash
# Adicionar ao ~/.bashrc para acesso mais fácil
alias classify_proj='source /tmp/classifier_venv/bin/activate'

# Depois apenas digitar:
classify_proj  # Leva você ao projeto com ambiente pronto
```

### Dica 3: Criar Scripts de Teste
```bash
# Criar test.sh
#!/bin/bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras
pytest tests/unit/ -q

# Executá-lo
chmod +x test.sh
./test.sh
```

### Dica 4: Monitorar Progresso
```bash
# Assistir estatísticas de lote enquanto processa
watch -n 1 'classify-batch --stats'

# Processar e registrar resultados
classify-batch --limit 100 | tee batch_log.txt
```

---

## 📞 Obtendo Ajuda

1. **Para problemas de sistema**: Verificar seção "Solução de Problemas" em TESTING_GUIDE.md
2. **Para dúvidas de API**: Ver docs/api.md com 50+ exemplos
3. **Para criação de regras**: Ver docs/rules_guide.md
4. **Para implantação**: Ver docs/deployment.md
5. **Para arquitetura**: Ver PROJECT_SUMMARY.md

---

## Resumo

**3 Formas de Executar o Classificador**:

1. **CLI (Mais Fácil)**
   ```bash
   source /tmp/classifier_venv/bin/activate
   classify-batch --limit 10
   classify-csv samples/products_basic.csv
   ```

2. **Python (Flexível)**
   ```python
   from classifier.engine import RuleEngine
   engine = RuleEngine(db)
   result = engine.evaluate({'description': 'laptop', 'ncm': '84713090'})
   ```

3. **Testes (Verificação)**
   ```bash
   pytest tests/ -v
   ```

**Próximos Passos**:
- Executar classificação em lote: `classify-batch --limit 10`
- Processar arquivo CSV: `classify-csv samples/products_basic.csv`
- Ler PROJECT_SUMMARY.md para compreensão completa do sistema
- Explorar pasta docs/ para guias detalhados

Feliz classificação! 🚀
