# 🔍 Validação de Regras de Classificação

**Leia quando encontrar produtos classificados errado.**

---

## ⚡ Quick: Reportar Erro (30 segundos)

```
Produto: "[NOME_EXATO]"
Errado: [CATEGORIA_ATUAL]
Correto: [CATEGORIA_ESPERADA]
```

**Exemplo**:
```
Produto: "Iog.Danone Danio Banana 125G"
Errado: Hortifrúti
Correto: Laticínios
```

Pronto! Envie isso e eu vou corrigir.

---

## 🏷️ Matriz Rápida de Categorias

```
MERCEARIA                → Arroz, Feijão, Macarrão, Sal, Açúcar, Farinha
LATICÍNIOS               → Leite, Queijo, Iogurte, Manteiga, Requeijão
PADARIA                  → Pão, Bolo, Biscoito Doce, Rosca
AÇOUGUE                  → Carne Vermelha, Frango, Linguiça, Presunto
HORTIFRÚTI               → Maçã, Banana, Laranja, Tomate, Alface, Batata (IN NATURA)
HIGIENE PESSOAL          → Shampoo, Sabonete, Pasta de Dente, Desodorante
LIMPEZA DOMÉSTICA        → Detergente, Desinfetante, Sabão em Pó, Amaciante
BISCOITOS & SNACKS       → Biscoito Salgado, Salgadinho, Chips, Chocolate
BEBIDAS                  → Refrigerante, Suco, Água Mineral, Café
PETS & UTILIDADES        → Ração, Brinquedo, Coleira
```

---

## ✅ Checklist: É Realmente um Erro?

- [ ] Produto está em categoria COMPLETAMENTE errada?
- [ ] Não é apenas preferência pessoal?
- [ ] Consigo descrever por que está errado?

Se SIM a todas, reporte!

---

## ⚠️ Erros Já Corrigidos (NÃO reporte)

```
❌ "Iogurte com fruta" em Hortifrúti → JÁ FIXADO (deve ser Laticínios)
❌ "Salgadinho" em Açougue → JÁ FIXADO (deve ser Biscoitos)
❌ "Fruta em iogurte" em Hortifrúti → JÁ FIXADO (deve ser Laticínios)
```

---

## 🎓 Regra de Ouro

```
PRIMEIRA PALAVRA + TIPO = CATEGORIA

"Iogurte [+fruta]"   → Laticínios (ignore a fruta)
"Salgadinho [+sabor]" → Biscoitos (ignore o sabor)
"Fruta in natura"     → Hortifrúti (se não for ingrediente)
```

---

## 📚 Aprender Mais

Para entender melhor como funciona o processo:
- `docs/guides/QUICK_RULE_VALIDATION.md` - Referência rápida
- `docs/guides/RULE_ERRORS_CATALOG.md` - Exemplos de erros reais
- `docs/guides/RULE_UPDATE_PROCESS.md` - Processo técnico completo
  - **NEW**: Seção "🤖 Guia Técnico para IA" com passo a passo completo para adicionar novas regras
  - Inclui fase de planejamento, criação de migration, testes e validação

---

## 🚀 Próximo Passo

Encontrou um erro? Reporte usando o formato acima!

