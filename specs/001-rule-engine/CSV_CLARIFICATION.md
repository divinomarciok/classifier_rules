# Esclarecimento: Onde Ficam os Dados Classificados (CSV)

**Branch**: `001-rule-engine`
**Criado**: 2025-10-25
**Propósito**: Explicar os dois modos de armazenamento de dados classificados

---

## 🎯 Sua Dúvida

> "Onde seria salvo os dados classificados por csv, aonde ficaria a classificacao dos depois de serem processados?"

Excelente pergunta! Existem **dois modos** de usar o CSV, e é importante entender a diferença:

---

## 📊 Dois Cenários com CSV

### **Cenário A: CSV é ORIGEM → Dados Voltem para o Banco**

```
Seu Excel/CSV
     ↓
Input: productos.csv
(id, description, ncm, size, quantity)
     ↓
[CLASSIFY_CSV.PY]
Classifica cada produto
     ↓
Output 1: clasificados.csv (original + categoría, rule_id, etc)
Output 2: BANCO DE DADOS é ATUALIZADO com a categoría
```

**Comando**:
```bash
python classify_csv.py --input productos.csv --output clasificados.csv --update-db
```

**Resultado**:
- ✅ Arquivo `clasificados.csv` criado (contém resultado)
- ✅ Banco de dados TAMBÉM atualizado
- ✅ Audit logs registram cada classificação

**Exemplo Output CSV**:
```csv
id,description,ncm,size,quantity,categoria,rule_id,rule_name,matched_criteria,evaluation_time_ms
P001,Laptop Dell XPS,84713090,0.5,1,ELECTRONICS,1,Laptop Rule,keywords: laptop,45
P002,USB Cable,85444290,0.02,100,CABLES,5,NCM 8544,ncm: 8544*,32
P003,Monitor Samsung,85287000,0.3,1,MONITORS,3,Display Rule,keywords: monitor,28
```

**Where**: `clasificados.csv` (mesmo diretório onde você rodou o comando)

---

### **Cenário B: CSV é DESTINO → Só Gera o Arquivo**

```
Banco de Dados
(produtos SEM categoria)
     ↓
[CLASSIFY_BATCH.PY -500]
Busca 500 produtos no banco
Classifica cada um
ATUALIZA o banco com categoria
     ↓
[EXPORT_BATCH.PY]
Exporta produtos classificados para CSV
     ↓
Output: clasificados_export.csv
(todos os dados + categoria)
```

**Comandos**:
```bash
# Passo 1: Classificar produtos do banco
python classify_batch.py -500

# Passo 2: Exportar para CSV (opcional)
python export_batch.py --output clasificados_export.csv
```

**Resultado**:
- ✅ Banco de dados atualizado
- ✅ Arquivo `clasificados_export.csv` gerado (opcional)

**Where**: `clasificados_export.csv` (mesmo diretório)

---

## 🔄 Fluxo Completo Recomendado

Vou descrever o **fluxo mais prático** para você:

### **Opção 1: Tudo no Banco (Recomendado para Produção)**

```bash
# 1. Você tem um CSV com produtos sem categoria
# productos_input.csv:
# id,description,ncm,size,quantity

# 2. IMPORTA para o banco (uma única vez)
python import_csv.py --input productos_input.csv

# 3. Depois, classifica direto do banco
python classify_batch.py -500

# 4. Os produtos ficam atualizados NO BANCO
# Resultado: produtos.categoria = "ELECTRONICS", etc

# 5. Se precisar exportar depois:
python export_batch.py --output resultados.csv
```

**Armazenamento Final**: Banco de dados (mais seguro e consultável)
**CSV é**: Opcional, apenas para backup/compartilhamento

---

### **Opção 2: Tudo em CSV (Recomendado para Ad-Hoc)**

```bash
# 1. Você tem um CSV
# productos.csv:
# id,description,ncm,size,quantity

# 2. Classifica direto do CSV
python classify_csv.py \
  --input productos.csv \
  --output clasificados.csv

# Resultado: clasificados.csv criado com:
# id,description,ncm,size,quantity,categoria,rule_id,rule_name,matched_criteria

# 3. (Opcional) Também atualiza o banco
python classify_csv.py \
  --input productos.csv \
  --output clasificados.csv \
  --update-db  # adiciona essa flag
```

**Armazenamento Final**: CSV (portátil) + Banco (se usar --update-db)
**CSV é**: Principal, arquivo de entrada/saída

---

## 📁 Estrutura de Arquivos Esperada

```
seu_projeto/
├── classify_batch.py          # Script para banco
├── classify_csv.py            # Script para CSV
├── export_batch.py            # Script para exportar banco → CSV
│
├── input/
│   └── productos.csv          # Seu arquivo de entrada (CSV)
│
└── output/
    ├── clasificados.csv       # Resultado (se usar classify_csv.py)
    ├── audit.csv              # Auditoria (se usar --audit)
    └── clasificados_export.csv # Exportação do banco (se usar export_batch.py)
```

---

## 💾 Onde Exatamente Ficam os Dados?

### **Após Rodar `python classify_batch.py -500`**

```
DATABASE (Banco de Dados)
└── Tabela: produtos
    ├── id: P001
    ├── description: "Laptop Dell"
    ├── ncm: "84713090"
    ├── categoria: "ELECTRONICS"  ← ATUALIZADO
    └── ...

DATABASE (Banco de Dados)
└── Tabela: auditoria_classificacao
    └── Entry: {rule_id: 1, id_produto: P001, resultado: ELECTRONICS, ...}
```

### **Após Rodar `python classify_csv.py --input input.csv --output output.csv`**

```
ARQUIVO: output.csv
├── Line 1: Headers (id,description,ncm,...,categoria,rule_id,...)
├── Line 2: P001,Laptop Dell,84713090,...,ELECTRONICS,1,...
└── ...

ARQUIVO: audit.csv (se usar --audit)
└── Cada linha = entrada de auditoria

DATABASE (Banco de Dados)
└── Tabela: auditoria_classificacao (REGISTRADAS, igual no batch)
```

---

## 🎬 Casos de Uso Práticos

### **Caso 1: Usuário Não-Técnico (Excel)**

```
1. Abre seu Excel
2. Salva como CSV → productos.csv
3. Roda no terminal:
   python classify_csv.py --input productos.csv --output resultados.csv
4. Abre resultados.csv no Excel
5. Vê toda a classificação pronta!
```

**Vantagem**: Não precisa conhecer banco de dados
**Desvantagem**: Dados só existem no CSV (não no banco)

---

### **Caso 2: Sistema Automático (Banco)**

```
1. Produtos já estão no banco sem categoria
2. Script roda automaticamente a noite:
   python classify_batch.py -500
3. Banco é atualizado com categoría
4. Aplicação lê o banco e mostra categoría
5. (Opcional) Exporta para CSV para backup:
   python export_batch.py --output backup.csv
```

**Vantagem**: Dados sempre sincronizados no banco
**Desvantagem**: Precisa ter banco configurado

---

### **Caso 3: Integração (CSV → Banco)**

```
1. Recebe arquivo de fornecedor (CSV)
2. Roda: python classify_csv.py --input fornecedor.csv --output fornecedor_classificado.csv --update-db
3. Resultado:
   - Arquivo fornecedor_classificado.csv criado
   - Banco também atualizado
4. Envia arquivo de volta para fornecedor
```

**Vantagem**: Melhor dos dois mundos
**Desvantagem**: Mais complexo

---

## 🔍 Resumo da Resposta

| Cenário | Input | Output | Armazenamento Final |
|---------|-------|--------|---------------------|
| **Batch DB** | Banco de dados | Banco atualizado | Database |
| **CSV Only** | CSV file | CSV file | CSV (local) |
| **CSV + DB** | CSV file | CSV file | CSV + Database |
| **DB Export** | Database | CSV file | CSV (local) |

---

## ⚙️ Opções de Linha de Comando

### **classify_batch.py** (Banco de Dados)
```bash
python classify_batch.py -500              # Classifica 500 produtos
python classify_batch.py -100 --offset 50  # Classifica 100 a partir do 50º
python classify_batch.py -1000 --where "categoria IS NULL"  # Custom filter
```

### **classify_csv.py** (CSV)
```bash
# Básico: entrada → saída
python classify_csv.py --input in.csv --output out.csv

# Com coluna mapeada:
python classify_csv.py --input in.csv --output out.csv \
  --product-id id_coluna \
  --description desc_coluna \
  --ncm ncm_coluna

# Com auditoria:
python classify_csv.py --input in.csv --output out.csv --audit audit.csv

# Atualizar banco também:
python classify_csv.py --input in.csv --output out.csv --update-db
```

---

## ✅ Recomendação Final

**Para você**: Use a **Opção 2 (CSV) inicialmente** porque:
1. ✅ Não precisa estar tudo no banco ainda
2. ✅ Pode testar com um Excel simples
3. ✅ Vê resultado imediato em arquivo
4. ✅ Quando quiser, move para banco

**Depois**: Migre para **Opção 1 (Batch)** quando:
1. ✅ Tiver muitos produtos (>1000)
2. ✅ Precisar atualizar regularmente
3. ✅ Quiser automatizar

Quer que eu adicione exemplos práticos nos documentos?
