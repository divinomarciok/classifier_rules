# Clarificações de Especificação — Rule Engine v1.2.1

**Data**: 2025-10-26
**Status**: ✅ Documentação alinhada com decisões de escopo e design

---

## Resumo Executivo

A especificação foi atualizada para 100% de clareza e consistência com base em decisões de negócio:

1. **Armazenamento de Resultado**: `categoria_id` FK é ÚNICO e AUTORITÁRIO (deprecated `resultado_classificacao`)
2. **Escopo MVP**: User Stories 1-3 (core engine) — IMPLEMENTAR AGORA
3. **Futuro**: User Stories 4-5 (batch, CSV) — Adiado, planejado para próximo ciclo
4. **Palavras-Chave**: Usar campo TEXT denormalizado, não tabela normalizada
5. **Equipe**: Single developer com timeline de 2-3 semanas para MVP

---

## Decisões Resolvidas

### 1️⃣ Ambiguidade de Armazenamento de Resultado

**Problema Original**: Spec mencionava `resultado_classificacao` (VARCHAR) mas plano moderno usava `categoria_id` (FK).

**Decisão Final**:
- ✅ **`categoria_id` (INTEGER FK)** é o ÚNICO campo para armazenar resultado
- ❌ **`resultado_classificacao`** foi REMOVIDO do schema
- 📝 **Audit logs** armazenam nome da categoria derivado do FK para legibilidade

**Impacto**:
- Schema normalizado, sem redundância
- FK integrity garante validação automática de categorias
- Auditoria rastreável via `auditoria_classificacao.categoria_id`

**Arquivos Atualizados**:
- `spec.md`: Adicionada nota em FR-001b
- `plan.md`: Seção Category Management clarificada (L27)
- `constitution.md`: `categoria_id` marcado como AUTHORITATIVE (L196-200)
- `tasks.md`: T009 usa apenas `categoria_id`, sem `resultado_classificacao`

---

### 2️⃣ Escopo MVP vs Futuro

**Problema Original**: CSV features (US4-US5) tinham tarefas completas mas marcadas "NOT IMPLEMENTED".

**Decisão Final**:
- ✅ **IN SCOPE MVP**: User Stories 1, 2, 3 (Fases 1-5)
  - Leitura de regras do banco
  - Resolução por prioridade
  - Audit logging

- ⏸️ **OUT OF SCOPE MVP**: User Stories 4, 5 (Fases 6-7)
  - Batch classification
  - CSV import/export
  - **Status**: Planned for future, tarefas preservadas para referência

**Timeline Ajustado**:
- Single developer: ~2-3 semanas para MVP (US1-US3)
- Após MVP: Estabilizar em produção, depois considerar US4-US5

**Arquivos Atualizados**:
- `spec.md`: Fase 3 marcada como "⏸️ PLANNED FOR FUTURE" (L27-30)
- `plan.md`: Seção "MVP Scope" adicionada (L21-36)
- `tasks.md`: Aviso "⏸️ PHASES 6-7: FUTURE FEATURES" (L353-367)
- `tasks.md`: Implementation Strategy reescrita para single developer (L852-894)

---

### 3️⃣ Tabela Normalizada de Palavras-Chave

**Problema Original**: Tabela `criterios_palavras_chave` era criada (T011) mas sua função era indefinida.

**Decisão Final**:
- ❌ **T011 REMOVIDO** das tarefas MVP
- ✅ **Usar denormalizado**: Campo `criterio_palavras_chave` (TEXT) em `regras_de_classificacao`
  - Matcher lê diretamente: split(","), trim, case-insensitive match
  - Sem queries adicionais, sem fixtures extras
  - Simples para single developer

- 📋 **Futuro (pós-MVP)**: Se reuso de keywords virar gargalo de performance, normalizar então
  - Schema proposto documentado em `constitution.md` para referência futura
  - Não bloqueia MVP

**Racional**:
- Complexidade desnecessária para dev solo
- TEXT field é adequado para volume típico
- Normalização é otimização, não requisito funcional

**Arquivos Atualizados**:
- `tasks.md`: T011 marcado REMOVIDO com explicação (L75-78)
- `plan.md`: Seção "Keywords Storage Design" adicionada (L269-283)
- `constitution.md`: `criterios_palavras_chave` marcado como "Optional, future use" (L141, L222-230)

---

## Checklist de Alinhamento

### Spec.md ✅
- [x] Resultado storage: `categoria_id` é único
- [x] CSV features: Marcado como "⏸️ PLANNED FOR FUTURE"
- [x] Palavras-chave: Sem referência a tabela normalizada
- [x] FR-001b: Nota explícita sobre deprecação de `resultado_clasificacion`

### Plan.md ✅
- [x] MVP Scope adicionado (IN/OUT of scope claro)
- [x] Categoria Management: `categoria_id` marcado AUTHORITATIVE
- [x] Keywords Storage Design: Explicação de denormalizado vs normalizado
- [x] Sem discussão de multi-developer strategies

### Tasks.md ✅
- [x] Escopo MVP (Fases 1-5) vs Futuro (Fases 6-7) clarificado no início
- [x] T011 removido com explicação
- [x] Phases 6-7 marcadas [FUTURE] com aviso no início
- [x] Implementation Strategy: Reescrita para single developer (~2-3 semanas)
- [x] Dependencies: MVP-focused, US4-US5 marcadas como futuro

### Constitution.md ✅
- [x] `categoria_id`: Marcado AUTHORITATIVE (L196-200)
- [x] `resultado_classificacao`: Documentado como DEPRECATED
- [x] Core Tables: Apenas 3 tabelas obrigatórias (sem `criterios_palavras_chave`)
- [x] Optional Tables: `criterios_palavras_chave` com schema proposto para futuro

---

## Próximos Passos

### Antes da Implementação
1. [ ] Review das alterações por stakeholder (confirmar alinhamento)
2. [ ] Validar timeline (2-3 semanas é realista?)
3. [ ] Preparar ambiente (PostgreSQL, Python 3.8+, `.env`)

### Implementação (Pronto!)
1. [ ] Executar Fase 1-2: Setup + Foundational (T001-T015) — ~6-8 horas
2. [ ] Executar Fase 3-5: US1-US3 Implementation (T016-T054) — ~30-40 horas
3. [ ] Deploy + stabilize em produção
4. [ ] **Depois**: Considerar US4-US5 se stakeholder solicitar

---

## Documentação Modificada

```
✅ /specs/001-rule-engine/spec.md
   - Line 27-30: CSV marcado como ⏸️ PLANNED FOR FUTURE
   - Line 209: FR-001b com nota sobre categoria_id AUTHORITATIVE
   - Line 245: Audit logs clarificados

✅ /specs/001-rule-engine/plan.md
   - Line 21-36: MVP Scope section adicionada
   - Line 27: categoria_id marcado AUTHORITATIVE
   - Line 269-283: Keywords Storage Design adicionada

✅ /specs/001-rule-engine/tasks.md
   - Line 13-19: SCOPE CLARIFICATION adicionada
   - Line 75-78: T011 removido
   - Line 353-367: ⏸️ PHASES 6-7 FUTURE FEATURES aviso
   - Line 670-685: Dependencies reescrito (MVP focus)
   - Line 852-894: Implementation Strategy (single dev, 2-3 weeks)

✅ /.specify/memory/constitution.md
   - Line 135-141: Core Tables clarificadas (sem criterios_palavras_chave obrigatório)
   - Line 196-200: categoria_id AUTHORITATIVE, resultado_classificacao DEPRECATED
   - Line 222-230: criterios_palavras_chave como optional future table
```

---

## Perguntas Respondidas

**P: Qual campo armazena o resultado?**
R: Apenas `categoria_id` (FK para categorias). `resultado_classificacao` foi removido.

**P: Quando implementar CSV?**
R: Futuro. MVP é US1-US3. CSV é US4-US5, adiado para próximo ciclo.

**P: Preciso criar tabela de palavras-chave normalizada?**
R: Não para MVP. Use campo TEXT. Tabela é otimização futura opcional.

**P: Quanto tempo leva?**
R: ~2-3 semanas para MVP (single developer, part-time 20-30 hrs/week).

**P: E depois do MVP?**
R: Estabilizar em produção, monitorar real-world usage, depois considerar US4-US5 se útil.

---

## Validação

**Status**: ✅ Documentação 100% consistente e alinhada

- ✅ Nenhuma ambiguidade terminológica
- ✅ Escopo claro (MVP vs Futuro)
- ✅ Decisões de design documentadas
- ✅ Timeline realista para single developer
- ✅ Tarefas prontas para implementação

**Próximo**: Execute `/speckit.implement` para começar User Story 1.

