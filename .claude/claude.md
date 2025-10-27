# ⚙️ Instruções para Claude Code

## 🎯 Comportamento Esperado

### ❌ NÃO Fazer (sem ser pedido):
- Criar documentação adicional
- Fazer sumários visuais
- Criar checklists ou guias extras
- Commits automáticos
- Exploração proativa de código

### ✅ Fazer APENAS quando solicitado:
- Criar documentação (apenas se pedir: "cria documentação", "salva esse guia", etc)
- Fazer commits (apenas se pedir: "faz commit", "salva no git")
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

---
**Última atualização:** 26/10/2025
