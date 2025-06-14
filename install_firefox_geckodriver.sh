#!/bin/bash

echo "[INFO] Atualizando pacotes e instalando dependências..."
sudo apt update
sudo apt install -y wget jq tar firefox

echo "[INFO] Obtendo versão mais recente do geckodriver..."
GECKO_VER=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | jq -r .tag_name)

if [[ -z "$GECKO_VER" ]]; then
    echo "[ERRO] Não foi possível obter a versão do geckodriver."
    exit 1
fi

echo "[INFO] Baixando geckodriver versão $GECKO_VER..."
wget -q "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VER}/geckodriver-${GECKO_VER}-linux64.tar.gz"

if [[ ! -f "geckodriver-${GECKO_VER}-linux64.tar.gz" ]]; then
    echo "[ERRO] Falha ao baixar geckodriver."
    exit 1
fi

echo "[INFO] Extraindo e instalando geckodriver..."
tar -xvzf "geckodriver-${GECKO_VER}-linux64.tar.gz"
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/

echo "[INFO] Limpando arquivos temporários..."
rm -f "geckodriver-${GECKO_VER}-linux64.tar.gz"

echo "[OK] Instalação concluída!"
geckodriver --version
