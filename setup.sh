#!/bin/bash

# 🚀 Script de Setup Automático - Classifier Project
# Este script automatiza todo o processo de configuração do projeto

set -e  # Parar em caso de erro

echo "🚀 === Iniciando Setup do Classifier Project === 🚀"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir com cores
print_step() {
    echo -e "${BLUE}📍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1️⃣ Verificar pré-requisitos
print_step "Verificando pré-requisitos..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não está instalado!"
    exit 1
fi
print_success "Python 3 encontrado: $(python3 --version)"

if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL não está instalado. Você precisa instalá-lo manualmente."
    echo "   Linux: sudo apt-get install postgresql postgresql-contrib"
    echo "   macOS: brew install postgresql"
    exit 1
fi
print_success "PostgreSQL encontrado: $(psql --version)"

# 2️⃣ Criar ambiente virtual
print_step "Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Ambiente virtual criado"
else
    print_warning "Ambiente virtual já existe"
fi

# 3️⃣ Ativar ambiente virtual
print_step "Ativando ambiente virtual..."
source venv/bin/activate
print_success "Ambiente virtual ativado"

# 4️⃣ Atualizar pip
print_step "Atualizando pip..."
python3 -m pip install --quiet --upgrade pip
print_success "pip atualizado"

# 5️⃣ Instalar dependências
print_step "Instalando dependências..."
python3 -m pip install --quiet -r requirements.txt
print_success "Dependências instaladas"

# 6️⃣ Configurar variáveis de ambiente
print_step "Configurando variáveis de ambiente..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Arquivo .env criado"
    print_warning "⚠️  IMPORTANTE: Edite .env com suas credenciais do PostgreSQL"
    echo ""
    echo "   Abra o arquivo .env e configure:"
    echo "   - DB_HOST (geralmente localhost)"
    echo "   - DB_NAME (geralmente market_v1)"
    echo "   - DB_USER (geralmente postgres)"
    echo "   - DB_PASSWORD (sua senha do PostgreSQL)"
    echo ""
else
    print_warning "Arquivo .env já existe"
fi

# 7️⃣ Criar banco de dados (com verificação)
print_step "Verificando banco de dados..."
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-market_v1}"
DB_HOST="${DB_HOST:-localhost}"

if psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
    print_success "Banco de dados $DB_NAME encontrado"
else
    print_warning "Banco de dados não encontrado. Você precisa criar manualmente:"
    echo ""
    echo "   sudo -u postgres psql"
    echo "   CREATE DATABASE $DB_NAME;"
    echo "   \\q"
    echo ""
fi

# 8️⃣ Rodar migrations (se banco existir)
print_step "Verificando migrations..."
if psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
    read -p "Deseja rodar as migrations agora? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        python3 << 'EOF'
from src.classifier.utils import init_database
try:
    init_database()
    print("\n✅ Migrations executadas com sucesso!")
except Exception as e:
    print(f"\n❌ Erro ao executar migrations: {e}")
EOF
    fi
else
    print_warning "Banco de dados não acessível. Pule esta etapa."
fi

# 9️⃣ Testar conexão
print_step "Testando conexão com banco..."
python3 << 'EOF'
import os
from src.classifier.utils import get_db_connection

try:
    conn = get_db_connection()
    print("✅ Conexão com banco de dados OK")
    conn.close()
except Exception as e:
    print(f"⚠️  Não foi possível conectar: {e}")
    print("   Certifique-se de que:")
    print("   1. PostgreSQL está rodando")
    print("   2. O banco de dados existe")
    print("   3. As credenciais no .env estão corretas")
EOF

# 🔟 Resumo final
echo ""
echo "========================================================"
echo -e "${GREEN}✨ Setup Completo! ✨${NC}"
echo "========================================================"
echo ""
echo "Para começar:"
echo ""
echo "1. Ativar ambiente virtual:"
echo "   source venv/bin/activate"
echo ""
echo "2. Ver estatísticas:"
echo "   python3 -m classifier.cli.classify_batch --stats"
echo ""
echo "3. Classificar 100 produtos:"
echo "   python3 -m classifier.cli.classify_batch --limit 100"
echo ""
echo "4. Rodar testes:"
echo "   pytest tests/ -v"
echo ""
echo "Para mais informações, leia: docs/GUIA_COMPLETO.md"
echo ""
echo "========================================================"
