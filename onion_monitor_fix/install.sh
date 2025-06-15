#!/bin/bash

echo "🔐 Iniciando instalação do Onion Monitor v1 🔐"
echo "=============================================="

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir mensagens de progresso
progress() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Função para exibir mensagens de sucesso
success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

# Função para exibir mensagens de erro
error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Função para exibir mensagens de aviso
warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
    warning "Este script não está sendo executado como root."
    warning "Algumas operações podem falhar. Recomendamos executar com sudo."
    read -p "Deseja continuar mesmo assim? (s/n): " choice
    if [ "$choice" != "s" ] && [ "$choice" != "S" ]; then
        error "Instalação cancelada pelo usuário."
        exit 1
    fi
fi

# Criar diretório de logs se não existir
mkdir -p logs
touch logs/app.log logs/coletor.log logs/db.log logs/busca_semantica.log logs/auditoria.log logs/migration.log

progress "Verificando dependências do sistema..."

# Verificar e instalar dependências do sistema
apt_packages=(
    python3
    python3-pip
    python3-venv
    tor
    sqlite3
    curl
    git
)

pip_packages=(
    flask
    requests
    beautifulsoup4
    pysocks
    stem
    lxml
    selenium
    webdriver-manager
    pandas
    matplotlib
    seaborn
    nltk
    scikit-learn
)

# Verificar se apt-get está disponível
if command -v apt-get &> /dev/null; then
    progress "Atualizando repositórios..."
    apt-get update -qq
    
    for package in "${apt_packages[@]}"; do
        if ! dpkg -l | grep -q $package; then
            progress "Instalando $package..."
            apt-get install -y $package
        else
            success "$package já está instalado."
        fi
    done
else
    warning "apt-get não encontrado. Pulando instalação de pacotes do sistema."
    warning "Certifique-se de que os seguintes pacotes estão instalados:"
    for package in "${apt_packages[@]}"; do
        echo "  - $package"
    done
fi

# Verificar se o serviço Tor está instalado e iniciar
if command -v tor &> /dev/null; then
    progress "Verificando serviço Tor..."
    if systemctl is-active --quiet tor; then
        success "Serviço Tor já está em execução."
    else
        progress "Iniciando serviço Tor..."
        systemctl start tor
        if systemctl is-active --quiet tor; then
            success "Serviço Tor iniciado com sucesso."
        else
            warning "Não foi possível iniciar o serviço Tor. Algumas funcionalidades podem não funcionar corretamente."
        fi
    fi
else
    warning "Tor não encontrado. A busca em sites .onion não funcionará corretamente."
fi

# Criar e ativar ambiente virtual
progress "Criando ambiente virtual Python..."
if [ -d "venv" ]; then
    success "Ambiente virtual já existe."
else
    python3 -m venv venv
    success "Ambiente virtual criado."
fi

# Ativar ambiente virtual
progress "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências Python
progress "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar se todas as dependências foram instaladas
missing_packages=()
for package in "${pip_packages[@]}"; do
    if ! pip show $package &> /dev/null; then
        missing_packages+=($package)
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    warning "Algumas dependências Python não foram instaladas corretamente:"
    for package in "${missing_packages[@]}"; do
        echo "  - $package"
    done
    progress "Tentando instalar pacotes faltantes individualmente..."
    for package in "${missing_packages[@]}"; do
        pip install $package
    done
fi

# Inicializar banco de dados
progress "Inicializando banco de dados..."
python -c "from db import init_db, migrar_banco; init_db(); migrar_banco()"
if [ $? -eq 0 ]; then
    success "Banco de dados inicializado com sucesso."
else
    error "Erro ao inicializar banco de dados."
    exit 1
fi

# Verificar conexão com Tor
progress "Verificando conexão com Tor..."
python torcheck.py
if [ $? -eq 0 ]; then
    success "Conexão com Tor verificada com sucesso."
else
    warning "Não foi possível verificar a conexão com Tor. A busca em sites .onion pode não funcionar corretamente."
fi

# Criar fontes de exemplo se não existirem
progress "Verificando fontes cadastradas..."
python -c "from db import obter_fontes, adicionar_fonte; fontes = obter_fontes(); 
if not fontes:
    print('Adicionando fontes de exemplo...')
    adicionar_fonte('Pastebin', 'https://pastebin.com', 'surface')
    adicionar_fonte('Reddit', 'https://www.reddit.com', 'surface')
    adicionar_fonte('GitHub', 'https://github.com', 'surface')
    adicionar_fonte('Onion Forum', 'http://onionforumxyz.onion', 'dark')
    adicionar_fonte('Leak Market', 'http://leakmarketxyz.onion', 'dark')
    print('Fontes de exemplo adicionadas com sucesso.')
else:
    print(f'{len(fontes)} fontes já cadastradas.')"

# Verificar se o diretório static existe
if [ ! -d "static" ]; then
    progress "Criando diretório static..."
    mkdir -p static/css static/js static/images
fi

# Verificar se o diretório templates existe
if [ ! -d "templates" ]; then
    progress "Criando diretório templates..."
    mkdir -p templates
fi

# Verificar permissões dos diretórios
progress "Verificando permissões..."
chmod -R 755 .
chmod -R 777 logs
chmod 666 *.db

success "Instalação concluída com sucesso!"
echo ""
echo "Para iniciar o Onion Monitor, execute:"
echo "  source venv/bin/activate && python app.py"
echo ""
echo "O sistema estará disponível em: http://localhost:5000"
echo ""
echo "🔐 Onion Monitor v1 - Monitoramento de vazamentos na Deep/Dark Web 🔐"
