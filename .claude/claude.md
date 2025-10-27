# ⚙️ Instruções para Claude Code

## 🎯 Comportamento Esperado

### ❌ NÃO Fazer (sem ser pedido):
- Criar documentação adicional
- Fazer sumários visuais
- Criar checklists ou guias extras
- **Commits automáticos** ⚠️ NUNCA fazer git commit/push
- Exploração proativa de código

### ✅ Fazer APENAS quando solicitado:
- Criar documentação (apenas se pedir: "cria documentação", "salva esse guia", etc)
- **⚠️ GIT CONTROL**: Reportar mudanças, você faz o commit (NUNCA fazer git commit/push automaticamente)
- Criar sumários (apenas se pedir: "resume", "sumário")
- Explorar código (apenas se pedir investigações específicas)

## 📝 Regra Principal
**Trabalhe de forma direta e minimalista:**
1. Receba a tarefa
2. Execute a tarefa
3. Reporte o resultado
4. Aguarde novo pedido

Sem extras, sem "helpfulness" excessiva, sem criar coisas que não foram solicitadas.

## 💾 Informações Importantes
- PostgreSQL está rodando em **Docker** (não localmente)
- setup.sh foi ajustado para funcionar com Docker
- SETUP_DOCKER.md contém instruções específicas para Docker

## ⚠️ Git Control (IMPORTANTE)

**Você é responsável por TODOS os commits e pushes.**

Quando eu fizer mudanças em arquivos:
1. ✅ Vou reportar: "Arquivo X foi modificado"
2. ✅ Vou listar: Quais linhas mudaram
3. ❌ NUNCA vou fazer `git add` ou `git commit`
4. ❌ NUNCA vou fazer `git push`

**Você faz assim:**
```bash
git add -A              # Adiciona tudo
git commit -m "..."     # Você escreve a mensagem
git push                # Você faz push
```

---
**Última atualização:** 26/10/2025
