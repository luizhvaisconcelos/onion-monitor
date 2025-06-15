#!/bin/bash
# Script de instalação e atualização do Onion Monitor v3
# Desenvolvido por um script de migração automatizado
# Data: 14-06-2025

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}      ONION MONITOR v3 - INSTALAÇÃO DE DEPENDÊNCIAS        ${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Por favor, execute este script como root (sudo).${NC}"
  exit 1
fi

# Verifica ambiente virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Criando ambiente virtual Python...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Ambiente virtual criado!${NC}"
else
    echo -e "${GREEN}✓ Ambiente virtual já existe.${NC}"
fi

# Ativa ambiente virtual
echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Ambiente virtual ativado!${NC}"

# Atualiza pip
echo -e "${YELLOW}Atualizando pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ Pip atualizado!${NC}"

# Instala ou atualiza dependências
echo -e "${YELLOW}Instalando dependências...${NC}"
pip install -r requirements_v3_complete.txt
echo -e "${GREEN}✓ Dependências instaladas com sucesso!${NC}"

# Verifica instalação de flask-sqlalchemy
echo -e "${YELLOW}Verificando instalação do Flask-SQLAlchemy...${NC}"
python3 -c "import flask_sqlalchemy; print('Flask-SQLAlchemy instalado corretamente!')" || { 
    echo -e "${RED}Erro na instalação do Flask-SQLAlchemy. Tentando instalar individualmente...${NC}"; 
    pip install flask-sqlalchemy;
}

# Verifica todas as dependências críticas
echo -e "${YELLOW}Verificando dependências críticas...${NC}"
python3 -c "
try:
    import flask
    import flask_sqlalchemy
    import sqlalchemy
    import loguru
    import pydantic
    import dotenv
    print('Todas as dependências críticas estão instaladas corretamente!')
except ImportError as e:
    print(f'ERRO: Dependência faltante: {e}')
    exit(1)
"

# Verifica status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}      INSTALAÇÃO CONCLUÍDA COM SUCESSO!                    ${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${YELLOW}Você pode agora executar a aplicação:${NC}"
    echo -e "    ${GREEN}source venv/bin/activate && python app.py${NC}"
    echo ""
else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}      ERRO NA INSTALAÇÃO DAS DEPENDÊNCIAS                  ${NC}"
    echo -e "${RED}============================================================${NC}"
    echo -e "${YELLOW}Tente instalar as dependências manualmente:${NC}"
    echo -e "    ${GREEN}pip install flask-sqlalchemy loguru pydantic python-dotenv${NC}"
    echo ""
fi