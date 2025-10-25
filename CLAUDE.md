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

## Notas Importantes para Desenvolvimento Futuro

- **Evite Débito Técnico:** O motor de regras deve permanecer simples e genérico; não adicione casos especiais no código
- **Documentação:** Cada tipo de regra ou estratégia de correspondência deve ser documentada com exemplos no banco de dados ou em um guia de regras
- **Compatibilidade Retroativa:** Ao alterar schema de regras, garanta que regras existentes continuem funcionando ou tenham caminhos de migração claros
- **Monitoramento:** Implemente logging para rastrear hits de regras e erros de classificação para melhoria contínua
