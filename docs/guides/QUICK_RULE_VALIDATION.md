# ⚡ Guia Rápido: Validação de Regras de Classificação

**Para quando você encontrar produtos errados e quiser reportar rapidinho**

---

## 🚀 Em 30 Segundos: Como Reportar Erro

### Formato Mínimo:
```
Produto: "NOME_EXATO"
Errado: Categoria_Atual
Correto: Categoria_Esperada
```

### Exemplo:
```
Produto: "Iog.Danone Danio Banana/Cereais/Mel 125G"
Errado: Hortifrúti
Correto: Laticínios
```

---

## 🔍 Checklist Rápido: É Realmente um Erro?

Antes de reportar, verifique:

- [ ] O produto está em categoria completamente errada? (Não é opinião, é fato)
- [ ] Conseguo descrever por que está errado?
- [ ] O nome do produto é uma fruta mas está em Laticínios? ❌ (Iogurte com sabor = Laticínios)
- [ ] O nome do produto é um laticínio mas está em Hortifrúti? ✅ (Isso é erro!)

---

## 📊 Matriz Rápida de Categorias

```
MERCEARIA              → Arroz, Feijão, Macarrão, Sal, Açúcar, Farinha
LATICÍNIOS             → Leite, Queijo, Iogurte, Manteiga, Requeijão
PADARIA                → Pão, Bolo, Biscoito Doce, Rosca
AÇOUGUE & FRIOS        → Carne Vermelha, Frango, Linguiça, Presunto, Mortadela
HORTIFRÚTI             → Maçã, Banana, Laranja, Tomate, Alface, Batata (IN NATURA)
HIGIENE PESSOAL        → Shampoo, Sabonete, Pasta de Dente, Desodorante, Escova
LIMPEZA DOMÉSTICA      → Detergente, Desinfetante, Sabão em Pó, Amaciante, Alvejante
BISCOITOS & SNACKS     → Biscoito Salgado, Salgadinho, Bolinha de Queijo, Chips
BEBIDAS                → Refrigerante, Suco, Água Mineral, Café
PETS & UTILIDADES      → Ração, Brinquedo Pet, Coleira
```

---

## ⚠️ Erros Comuns Já Corrigidos (Evite Reportar)

| Produtos | Antes | Depois | Status |
|----------|-------|--------|--------|
| Iogurte com sabor fruta | Hortifrúti | Laticínios | ✅ FIXADO |
| Salgadinho com sabor carne | Açougue | Biscoitos | ✅ FIXADO |
| Fruta em iogurte | Hortifrúti | Laticínios | ✅ FIXADO |

---

## 🎯 Regra de Ouro

```
PRIMEIRA PALAVRA + TIPO DE PRODUTO = CATEGORIA

Iogurte [+sabor] → Laticínios (não importa o sabor)
Salgadinho [+sabor] → Biscoitos (não importa o sabor)
Fruta in natura → Hortifrúti (não ingrediente)
```

---

## 📝 Quando Reportar

### ✅ REPORTE ISTO:
```
Produto: "Leite integral 1L"
Errado: Hortifrúti
Correto: Laticínios
```

### ❌ NÃO REPORTE ISTO:
```
Produto: "Iogurte sabor banana"
Errado: Hortifrúti
Correto: Laticínios
(JÁ FOI CORRIGIDO)
```

### ❓ INCERTO? REPORTE MESMO ASSIM:
Se não tem certeza, melhor reportar. Vou validar!

---

## 🔧 Tipos de Erro Mais Comuns

### Tipo 1: Palavra-chave Genérica
```
❌ "Banana" pega iogurte
✅ "Banana in natura" pega fruta
```

### Tipo 2: Conflito de Prioridade
```
❌ "Salgadinho presunto" vai para Açougue
✅ "Salgadinho presunto" vai para Biscoitos
```

### Tipo 3: Ingrediente vs Produto
```
❌ "Suco de Laranja" em Hortifrúti
✅ "Suco de Laranja" em Bebidas
```

### Tipo 4: Não Encontra Produto
```
❌ "Cerveja" não tem regra
✅ Criar regra em Bebidas
```

---

## 🚨 Sinais de Alerta

Considere suspeito se:
- Iogurte está em Hortifrúti ou Bebidas
- Salgadinho está em Açougue
- Carne está em Biscoitos
- Fruta processada está em Hortifrúti

---

## 📞 Fluxo Depois que Reportar

```
1. VOCÊ reporta erro
   ↓
2. EU analiso a regra
   ↓
3. EU atualizo a regra
   ↓
4. EU re-classifica produtos
   ↓
5. EU informo resultado
   ↓
6. VOCÊ valida se ficou certo
   ↓
7. PRÓXIMO ERRO? Volte ao passo 1
```

---

## 💡 Dicas para Não Errar

### Dica 1: Ignore o Sabor
```
"Iogurte sabor morango" → Laticínios (ignore "morango")
"Salgadinho sabor queijo" → Biscoitos (ignore "queijo")
"Suco sabor laranja" → Bebidas (ignore "laranja")
```

### Dica 2: Foque na Primeira Palavra
```
"Iog..." → sempre Laticínios
"Salgadinho..." → sempre Biscoitos
"Maçã..." → sempre Hortifrúti (se in natura)
"Carne..." → sempre Açougue
```

### Dica 3: Se Tiver "IN NATURA" ou "FRESCA", é Hortifrúti
```
"Maçã in natura" → Hortifrúti ✅
"Maçã em iogurte" → Laticínios ✅
"Maçã doce" → Padaria ✅
```

---

## 🎓 Exemplos Corretos (Não Reportar)

```
✅ "Maçã Fuji" → Hortifrúti
✅ "Iogurte Grego" → Laticínios
✅ "Salgadinho Queijo" → Biscoitos
✅ "Carne Vermelha 500g" → Açougue
✅ "Shampoo Neutro" → Higiene Pessoal
✅ "Detergente Neutro" → Limpeza Doméstica
✅ "Refrigerante 2L" → Bebidas
✅ "Ração para Cão" → Pets
```

---

## 🎓 Exemplos de Erros (Reportar ESTES)

```
❌ "Iogurte com Banana" em Hortifrúti → Deve ser Laticínios
❌ "Salgadinho Carne" em Açougue → Deve ser Biscoitos
❌ "Leite Integral" em Bebidas → Deve ser Laticínios
❌ "Fruta em Calda" em Hortifrúti → Deve ser Mercearia
```

---

## 📊 Dashboard de Regras (Estado Atual)

**Total: 54 regras**

```
✅ Bem calibradas (muito específicas):
   - Laticínios (pega "iogurte" corretamente)
   - Mercearia (pega produtos secos)
   - Biscoitos (pega "salgadinho" corretamente)

⚠️ Pouco sensíveis (poucas classificações):
   - Hortifrúti (exige "in natura")
   - Padaria (exige descrição específica)
   - Açougue (exige carne pura)

❌ Sem produtos ainda:
   - Higiene Pessoal
   - Limpeza Doméstica
   - Pets
```

---

## 🎯 Próximas Ações para Você

1. **Inspecione seus 79k produtos**
   - Rode algumas queries para identificar padrões
   - Procure por produtos com nomes diferentes

2. **Crie uma lista dos erros encontrados**
   - Agrupe por padrão (ex: iogurtes, salgadinhos)
   - Conte quantos produtos são afetados

3. **Reporte os erros em lote**
   - Não reporte 1 a 1
   - Agrupe produtos similares

4. **Aguarde as correções**
   - Cada reporte leva ~10-15 minutos para ser corrigido
   - Você pode validar depois

---

## 📞 Atalho: Reportar por Email

Copie e cole este template e envie quando encontrar erros:

```markdown
## Reportagem de Erros de Classificação - [DATA]

### Erro #1
Produto: "[NOME]"
Errado: [CAT_ATUAL]
Correto: [CAT_ESPERADA]
Exemplos similares: [SE HOUVER]

### Erro #2
[repetir para cada erro]

### Resumo
Total de produtos afetados: [#]
Padrão identificado: [DESCRIÇÃO]
```

---

## ✅ Pronto!

Agora você sabe como reportar erros de classificação de forma clara e eficiente.

**Próximo passo:** Inspecione seus produtos e reporte os que encontrar errados!

