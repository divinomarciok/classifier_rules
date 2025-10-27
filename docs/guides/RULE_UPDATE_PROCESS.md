# 📋 Processo de Atualização e Validação de Regras de Classificação

**Data**: 2025-10-26
**Status**: Documentado
**Objetivo**: Guia para atualizar regras quando produtos estão sendo classificados errado

---

## 🎯 Visão Geral do Processo

Quando você identifica produtos sendo classificados em categorias erradas, o processo de correção segue estas fases:

1. **Análise de Padrões** - Identificar o padrão de erro
2. **Diagnóstico** - Entender por que a regra atual está gerando falsos positivos
3. **Correção de Regra** - Atualizar a regra com critérios mais precisos
4. **Re-classificação** - Rodar batch classification com as regras atualizadas
5. **Validação** - Verificar se o problema foi resolvido

---

## 🤖 Guia Técnico para IA: Como Adicionar Novas Regras de Classificação

**IMPORTANTE**: Siga este checklist ANTES de criar qualquer migration com novas regras.

### ✅ Pré-Requisitos de Implementação

1. **Entender o Formato de Palavras-Chave**
   - ⚠️ **CRÍTICO**: Keywords são separadas por **VÍRGULA (,)**, NÃO por pipe (|)
   - ❌ ERRADO: `'danone grego|iog. danone'`
   - ✅ CERTO: `'danone grego,iog. danone'`
   - O matcher em `src/classifier/matcher.py` usa `keywords.split(',')` (linha 122)

2. **Entender a Estrutura de Critérios**
   - Cada regra em `regras_de_classificacao` tem campos opcionais:
     - `criterio_palavras_chave`: Substring case-insensitive matching (USE VÍRGULA!)
     - `criterio_ncm`: NCM code patterns (suporta wildcard *)
     - `criterio_tamanho_min/max`: Size range (em litros/kg)
     - `criterio_quantidade_min/max`: Quantity range
   - **TODOS os critérios especificados devem bater** (lógica AND)

3. **Verificar a Categoria ID Correta**
   ```sql
   SELECT id, nome FROM categorias ORDER BY nome;
   -- Laticínios = ID 7
   -- Hortifrúti = ID 10
   -- etc.
   ```

### 📝 Passo a Passo: Adicionar Novas Regras

#### Fase 1: Planejamento
```
1. Identificar a categoria-alvo (ex: Laticínios, ID 7)
2. Listar todas as variações do produto (ex: Danone Natural, Danone Grego, Activia, etc.)
3. Para CADA variação, criar uma regra separada com palavras-chave específicas
4. Definir prioridade: Variações mais específicas > Variações genéricas
   - Danone Activia (mais específica): prioridade 130
   - Danone Natural (média): prioridade 125
   - Iogurte Genérico (menos específica): prioridade 110
```

#### Fase 2: Criar Migration File
```
1. Encontrar o número da próxima migration
   $ ls migrations/ | grep -E '^\d+_' | sort -V | tail -1
   → Resultado: 005_create_criterios_palavras_chave.sql
   → Próxima: 006_add_*_rules.sql

2. Criar arquivo: migrations/006_add_lacteos_danone_rules.sql

3. IMPORTANTE: Adicionar comentário no topo:
   -- NOTE: Keywords are separated by COMMA (,) NOT pipe (|)
```

#### Fase 3: Escrever SQL com Formato Correto
```sql
-- Template correto para cada regra:
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Nome Descritivo Regra',
    7,                           -- Category ID
    125,                         -- Priority (higher = more important)
    'palavra1,palavra2,palavra3', -- COMMA-SEPARATED (MUITO IMPORTANTE!)
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'palavra1,palavra2,palavra3',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;
```

#### Fase 4: Atualizar Utilitários
```
1. Editar: src/classifier/utils.py
2. Função: init_database() (linha ~214)
3. Adicionar a nova migration ao pattern:

   ANTES:
   if f.name.startswith(('001_', '002_', '003_', '004_', '005_'))

   DEPOIS:
   if f.name.startswith(('001_', '002_', '003_', '004_', '005_', '006_'))
```

#### Fase 5: Executar Migration
```python
from src.classifier.utils import get_db_connection
from pathlib import Path

conn = get_db_connection()
cursor = conn.cursor()

migration_file = Path('migrations/006_add_lacteos_danone_rules.sql')
with open(migration_file) as f:
    sql = f.read()

cursor.execute(sql)
conn.commit()
cursor.close()
conn.close()

print('✓ Migration executed!')
```

#### Fase 6: Testar ANTES de Validar
```python
# TESTE 1: Verificar se regras foram inseridas
from src.classifier.engine import RuleEngine
from src.classifier.utils import get_db_connection

conn = get_db_connection()
engine = RuleEngine(db_connection=conn, cache_rules=False)
rules = engine.get_rules(active_only=True)
danone_rules = [r for r in rules if 'danone' in r.nome.lower()]
print(f'Found {len(danone_rules)} Danone rules')

# TESTE 2: Verificar se keyword matching funciona
from src.classifier.matcher import Matcher
from src.classifier.models import Product, Rule

product = Product(description='Danone Iogurte Natural 500ml', ncm='0402')
rule = Rule(
    id=1, prioridade=100, nome="Test", ativo=True, categoria_id=7,
    criterio_palavras_chave='danone iogurte,danone natural'
)
matches = Matcher.matches_all_criteria(product, rule)
print(f'Match result: {matches}')  # Deve ser True!
```

#### Fase 7: Validar com Produtos de Teste
```python
# Criar lista de produtos para testar
test_products = [
    {'id': '001', 'description': 'Danone Iogurte Natural 500ml', 'ncm': '0402'},
    {'id': '002', 'description': 'Iog.Danone Grego 200g', 'ncm': '0402'},
    # ... mais produtos
]

# Avaliar cada um
from src.classifier.engine import RuleEngine
conn = get_db_connection()
engine = RuleEngine(db_connection=conn, cache_rules=False)

for product in test_products:
    result = engine.evaluate(product)
    status = '✓' if result.classification == 'Laticínios' else '✗'
    print(f'{status} {product["description"]} → {result.classification}')

# Todos devem passar (✓)!
```

### 🚨 Erros Comuns e Soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `NO_MATCH` para todos os produtos | Keywords com `\|` em vez de `,` | Usar VÍRGULA como separador |
| Alguns produtos ainda não classificam | Prioridade muito baixa vs. outras regras | Aumentar `prioridade` da regra |
| Migration falha com "column already exists" | Migration já foi executada antes | Usar `ON CONFLICT` ou deletar regras antigas |
| Matcher retorna False quando deveria True | Descrição do produto não contém exatamente a keyword | Testar com `Matcher._match_keywords()` diretamente |

### 📋 Checklist Final Antes de Confirmar

- [ ] Migration file criado com nome sequencial correto (006_, 007_, etc.)
- [ ] TODOS os keywords separados por **VÍRGULA (,)** não por pipe
- [ ] Comentário no topo da migration explicando o separador
- [ ] src/classifier/utils.py atualizado com novo prefixo de migration
- [ ] Migration executada com sucesso (sem erros SQL)
- [ ] Pelo menos 5 produtos de teste classificam corretamente
- [ ] Nenhuma regra antiga conflita com as novas (testar com `cache_rules=False`)
- [ ] Documentado: nome da regra, prioridade, e variações cobertas

---

## 📊 Exemplo Real: Caso Danone Banana

### O Problema
```
Produto: "Iog.Danone Danio Banana/Cereais/Mel 125G"
Categoria Atual: Hortifrúti (ERRADO ❌)
Categoria Correta: Laticínios (CERTO ✅)
Motivo: A regra de Hortifrúti procurava por "banana" e pegou este iogurte
```

### A Causa Raiz
**Regra Antiga (Problema):**
```sql
Hortifrúti → criterio_palavras_chave = "banana"
```
Esta regra é **muito genérica** e pega qualquer produto que contenha a palavra "banana", inclusive:
- Iogurtes com sabor banana (Danone, Nestlé, etc.)
- Sucos de banana
- Bebidas com banana

### A Solução
**Regra Nova (Corrigida):**
```sql
Hortifrúti → criterio_palavras_chave = "banana in natura|banana fresca"
```
Agora a regra é **muito específica** e só pega bananas que são frutas de verdade, não ingredientes em produtos processados.

---

## 🔍 Padrões de Erro Comuns e Como Corrigir

### Padrão 1: Palavra-chave Genérica Demais
**Exemplo:** "Iogurte com banana" classificado como Hortifrúti

**Problema:**
```python
# ERRADO - muito genérico
Hortifrúti: "banana"
```

**Solução:**
```python
# CERTO - específico para frutas in natura
Hortifrúti: "banana in natura|banana fresca"
Laticínios: "iogurte|iog."  # Mais específico também
```

---

### Padrão 2: Conflito entre Categorias
**Exemplo:** "Salgadinho presunto" classificado como Açougue

**Problema:**
```python
# Ambas as regras batem
Açougue: "presunto"
Biscoitos: "salgadinho"
# Qual vence? Depende da ordem de execução
```

**Solução:**
```python
# Fazer a regra mais específica vencer
Biscoitos: "salgadinho"  # Palavra-chave primária
Açougue: "presunto"  # Só para presunto puro, não em produtos processados
```

---

### Padrão 3: Ingrediente vs Produto Final
**Exemplo:** "Miojo de Carnes" classificado como Açougue

**Problema:**
```python
# Regra pega o ingrediente, não o tipo de produto
Açougue: "carne|frango"
```

**Solução:**
```python
# Ser mais específico com o tipo de carne
Açougue: "carne vermelha|carne bovina|carne de boi|frango"
# Mercearia: "miojo|macarrão instantâneo"
```

---

## 📝 Como Reportar Erros para Correção

Quando você encontrar produtos sendo classificados errado, reporte **sempre** neste formato:

```
Produto: "[NOME EXATO DO PRODUTO]"
Categoria Atual: [CATEGORIA ATUAL]
Categoria Esperada: [CATEGORIA CORRETA]
Motivo: "[POR QUE ESTÁ ERRADO]"
```

### Exemplo 1:
```
Produto: "Iog.Danone Danio Banana/Cereais/Mel 125G"
Categoria Atual: Hortifrúti
Categoria Esperada: Laticínios
Motivo: "É um iogurte, não uma fruta. A regra 'banana' está muito genérica"
```

### Exemplo 2:
```
Produto: "Salgadinho presunto 50G"
Categoria Atual: Açougue e frios
Categoria Esperada: Biscoitos e snacks
Motivo: "É um salgadinho, não uma carne. Deveria bater com 'salgadinho' primeiro"
```

### Exemplo 3:
```
Produto: "Miojo de carnes"
Categoria Atual: Açougue e frios
Categoria Esperada: Mercearia
Motivo: "É um macarrão instantâneo, não uma carne. Ingrediente não define o produto"
```

---

## 🔧 Processo Técnico de Correção

### Fase 1: Análise (O que farei quando você reportar)

```python
# 1. Identificar a regra que está pegando errado
SELECT * FROM regras_de_classificacao
WHERE criterio_palavras_chave ILIKE '%banana%'

# 2. Ver quantos produtos estão sendo afetados
SELECT COUNT(*) FROM produtos_tabela
WHERE categoria_id = 10
AND descricao ILIKE '%iogurte%'

# 3. Validar se o padrão é consistente
SELECT DISTINCT LEFT(descricao, 30)
FROM produtos_tabela
WHERE categoria_id = 10
AND descricao ILIKE '%danone%'
```

### Fase 2: Correção de Regra

**Opção A: Atualizar a regra existente**
```sql
UPDATE regras_de_classificacao
SET criterio_palavras_chave = 'banana in natura|banana fresca'
WHERE nome = 'Banana Hortifruti'
AND categoria_id = 10;
```

**Opção B: Criar uma nova regra mais específica**
```sql
INSERT INTO regras_de_classificacao
(nome, categoria_id, prioridade, criterio_palavras_chave, ativo)
VALUES ('Banana In Natura Hortifruti', 10, 110, 'banana in natura', TRUE);
```

### Fase 3: Re-classificação

```bash
# 1. Marcar produtos afetados como pending
UPDATE produtos_tabela
SET status_classificacao = 'pending', categoria_id = NULL
WHERE categoria_id = 10;  -- ou a categoria afetada

# 2. Rodar batch classification
python3 -m classifier.cli.classify_batch --limit 500 --verbose

# 3. Ver estatísticas
python3 -m classifier.cli.classify_batch --stats
```

### Fase 4: Validação

```sql
-- Verificar se o produto problemático foi corrigido
SELECT
  p.descricao,
  c.nome as categoria,
  p.status_classificacao
FROM produtos_tabela p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE p.descricao ILIKE '%danone%banana%'
LIMIT 5;
```

---

## 📋 Checklist de Correção

Quando eu receber um relatório de erro, seguirei este checklist:

- [ ] **Leitura do Reporte**
  - Validar que o produto, categoria atual e esperada estão claros
  - Identificar o motivo do erro

- [ ] **Análise**
  - Rodar query para entender quantos produtos são afetados
  - Verificar se é um falso positivo único ou padrão recorrente
  - Analisar a regra atual e por que está gerando erro

- [ ] **Diagnóstico**
  - Determinar se o problema é:
    - Palavra-chave muito genérica?
    - Conflito com outra categoria?
    - Falta de contexto (ingrediente vs produto)?
    - Regra não existe?

- [ ] **Correção**
  - Decidir se é UPDATE ou INSERT de nova regra
  - Aplicar a correção no banco

- [ ] **Re-classificação**
  - Marcar produtos afetados como pending
  - Rodar batch classification

- [ ] **Validação**
  - Verificar se o produto agora está na categoria correta
  - Confirmar que outros produtos similares também foram corrigidos
  - Gerar relatório de antes/depois

- [ ] **Comunicação**
  - Informar ao usuário que a correção foi aplicada
  - Mostrar estatísticas de impacto

---

## 📊 Estado Atual das Regras (Base: 2025-10-26)

### Configuração Atual
- **Total de Categorias**: 15
- **Total de Regras**: 54 (6 antigas + 48 novas)
- **Estratégia de Correspondência**: Palavra-chave (icase) + critérios específicos
- **Produtos Classificados**: 779 (1.0% do total de 79.201)

### Regras por Categoria

#### Mercearia (ID 6)
```
- Arroz Mercearia           → "arroz"
- Feijão Mercearia          → "feijão"
- Macarrão Mercearia        → "macarrão|pasta"
- Sal Mercearia             → "sal"
- Açúcar Mercearia          → "açúcar"
- Farinha Mercearia         → "farinha"
```
**Status**: 49 produtos classificados ✅

#### Laticínios (ID 7)
```
- Leite Laticinio           → "leite"
- Queijo Laticinio          → "queijo"
- Iogurte Laticinio         → "iogurte|iog."
- Manteiga Laticinio        → "manteiga"
- Requeijão Laticinio       → "requeijão"
```
**Status**: 116 produtos classificados ✅

#### Padaria (ID 8)
```
- Pão Padaria               → "pão"
- Bolo Padaria              → "bolo"
- Biscoito Doce Padaria     → "biscoito doce"
- Rosca Padaria             → "rosca"
```
**Status**: 0 produtos classificados (palavras-chave muito específicas)

#### Açougue (ID 9)
```
- Carne Vermelha Acougue    → "carne vermelha|carne bovina"
- Frango Acougue            → "frango"
- Linguiça Acougue          → "linguiça"
- Presunto Acougue          → "presunto"
- Mortadela Acougue         → "mortadela"
```
**Status**: 0 produtos classificados (sem descrições de carne pura)

#### Hortifrúti (ID 10)
```
- Maçã Hortifruti           → "maçã in natura|maçã fresca"
- Banana Hortifruti         → "banana in natura|banana fresca"
- Laranja Hortifruti        → "laranja in natura|laranja fresca"
- Tomate Hortifruti         → "tomate in natura|tomate fresco"
- Alface Hortifruti         → "alface"
- Batata Hortifruti         → "batata"
```
**Status**: 0 produtos classificados (requer "in natura" ou "fresca")

#### Higiene Pessoal (ID 11)
```
- Shampoo Higiene           → "shampoo"
- Sabonete Higiene          → "sabonete"
- Pasta de Dente Higiene    → "pasta de dente|dentifrício"
- Desodorante Higiene       → "desodorante"
- Escova de Dente Higiene   → "escova de dente"
```
**Status**: 0 produtos classificados

#### Limpeza Doméstica (ID 12)
```
- Detergente Limpeza        → "detergente"
- Desinfetante Limpeza      → "desinfetante"
- Sabão em Pó Limpeza       → "sabão em pó"
- Amaciante Limpeza         → "amaciante"
- Alvejante Limpeza         → "alvejante"
```
**Status**: 0 produtos classificados

#### Biscoitos e Snacks (ID 13)
```
- Biscoito Salgado Snacks   → "biscoito salgado"
- Salgadinho Snacks         → "salgadinho"
- Bolinha Queijo Snacks     → "bolinha de queijo"
- Chips Snacks              → "chips"
- Chocolate Snacks          → "chocolate"
```
**Status**: 13 produtos classificados ✅

#### Bebidas (ID 14)
```
- Refrigerante Bebida       → "refrigerante"
- Suco Natural Bebida       → "suco natural|suco de fruta"
- Água Mineral Bebida       → "água mineral"
- Café Bebida               → "café"
```
**Status**: 1 produto classificado ✅

#### Pets e Utilidades (ID 15)
```
- Ração Pets                → "ração"
- Brinquedo Pet             → "brinquedo"
- Coleira Pet               → "coleira"
```
**Status**: 0 produtos classificados

---

## 🚨 Regras para Quando Reportar Erros

### Faça:
✅ Reporte o nome EXATO do produto (copie do banco se possível)
✅ Explique por que está errado (ingrediente? primeira palavra? tipo de produto?)
✅ Sugira a categoria correta
✅ Se encontrar padrão recorrente, liste 3-5 exemplos

### NÃO Faça:
❌ Não mude as regras manualmente no banco
❌ Não faça batch classification sem reportar antes
❌ Não assuma que uma regra está certa apenas porque classificou 1 produto
❌ Não delete categorias ou regras sem avisar

---

## 📞 Fluxo Completo: Do Erro à Correção

### Seu Lado (Usuário):
1. Encontra produto classificado errado
2. Reporta usando o formato padrão
3. Aguarda a correção
4. Valida se funciona

### Meu Lado (Claude):
1. Recebo o reporte
2. Analiso a regra problemática
3. Determino o tipo de erro
4. Atualizo a regra
5. Re-classifico os produtos afetados
6. Valido a correção
7. Informo o resultado

### Ciclo Iterativo:
```
Encontrar erro → Reportar → Corrigir → Validar → Repetir
```

---

## 📈 Métricas de Sucesso

Cada correção deve melhorar:
- **Taxa de Classificação Correta**: % de produtos com categoria correta
- **Cobertura**: # de produtos classificados vs. total
- **Redução de Falsos Positivos**: Produtos que saem da categoria errada
- **Consistência**: Produtos similares classificados na mesma categoria

---

## 🔄 Quando Revisar Todas as Regras

Considere revisar TODAS as 48 regras quando:
- Mais de 10% dos produtos estão sendo classificados errado
- Um padrão recorrente afeta múltiplas categorias
- As descrições dos produtos mudaram significativamente
- Novas categorias precisam ser adicionadas

---

## 📚 Referências Rápidas

### Query para ver produtos de uma categoria:
```sql
SELECT descricao, categoria_id, status_classificacao
FROM produtos_tabela
WHERE categoria_id = 10
LIMIT 20;
```

### Query para ver qual regra pegou um produto:
```sql
SELECT r.nome, r.criterio_palavras_chave
FROM regras_de_classificacao r
WHERE 'seu_produto_aqui' ILIKE '%' || r.criterio_palavras_chave || '%'
LIMIT 5;
```

### Rodar batch com verbosity:
```bash
python3 -m classifier.cli.classify_batch --limit 500 --verbose
```

### Ver estatísticas:
```bash
python3 -m classifier.cli.classify_batch --stats
```

---

## ✅ Conclusão

Este documento define o protocolo para:
1. **Identificar erros** - Quando você encontra um produto errado
2. **Reportar erros** - Como comunicar o problema
3. **Corrigir erros** - Que processo será seguido
4. **Validar correções** - Como confirmamos que funcionou

Mantenha este documento à mão quando tiver produtos classificados errado!

