import requests
import logging
import re
from bs4 import BeautifulSoup
import datetime
from db import registrar_coleta, registrar_auditoria

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("busca_semantica.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("busca_semantica")

def termo_presente_em_contexto(html, termo):
    """
    Verifica se um termo está presente no contexto HTML e extrai o trecho relevante.
    
    Args:
        html (str): Conteúdo HTML da página
        termo (str): Termo a ser buscado
        
    Returns:
        str: Contexto onde o termo foi encontrado ou None
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        texto = soup.get_text(separator=' ')
        match = re.search(rf'(.{{0,100}}\b{re.escape(termo)}\b.{{0,100}})', texto, re.IGNORECASE)
        return match.group(0).strip() if match else None
    except Exception as e:
        logger.error(f"Erro ao analisar HTML: {str(e)}")
        return None

def buscar_e_validar_termo(termo, url, fonte_id=None, usar_proxy=False):
    """
    Busca um termo em uma URL específica e valida sua presença.
    
    Args:
        termo (str): Termo a ser buscado
        url (str): URL onde buscar o termo
        fonte_id (int, optional): ID da fonte no banco de dados
        usar_proxy (bool, optional): Se deve usar proxy Tor
        
    Returns:
        dict: Resultado da busca e validação
    """
    logger.info(f"Buscando termo '{termo}' em {url}")
    
    # Registra a ação de busca
    registrar_auditoria(
        acao="busca_semantica",
        descricao=f"Busca semântica do termo '{termo}' em {url}",
        dados=None
    )
    
    # Configuração de proxy se necessário
    proxies = None
    if usar_proxy:
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050',
        }
    
    try:
        # Tenta acessar a URL com timeout
        response = requests.get(url, proxies=proxies, timeout=25)
        
        if response.status_code == 200:
            # Verifica se o termo está presente no contexto
            contexto = termo_presente_em_contexto(response.text, termo)
            
            if contexto:
                # Registra a coleta bem-sucedida
                coleta_id = registrar_coleta(
                    termo_busca=termo,
                    link_encontrado=url,
                    titulo=f"Vazamento contendo {termo}",
                    descricao=contexto,
                    fonte_id=fonte_id
                )
                
                # Registra a ação de validação
                registrar_auditoria(
                    acao="validacao_semantica",
                    descricao=f"Validação semântica positiva para '{termo}' em {url}",
                    dados=f"Contexto: {contexto[:100]}..."
                )
                
                return {
                    "id": coleta_id,
                    "url": url,
                    "termo": termo,
                    "contexto": contexto,
                    "valido": True,
                    "status": 200,
                    "fonte_id": fonte_id
                }
            else:
                logger.info(f"Termo '{termo}' não encontrado no contexto de {url}")
        else:
            logger.warning(f"Falha ao acessar {url}: Status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Erro ao acessar {url}: {str(e)}")
    
    # Registra a ação de validação negativa
    registrar_auditoria(
        acao="validacao_semantica",
        descricao=f"Validação semântica negativa para '{termo}' em {url}",
        dados=f"Erro ou termo não encontrado"
    )
    
    return {
        "url": url,
        "termo": termo,
        "contexto": None,
        "valido": False,
        "status": None,
        "fonte_id": fonte_id
    }

def validar_semanticamente(termo, links, fonte_id=None, usar_proxy=False):
    """
    Valida semanticamente um termo em múltiplos links.
    
    Args:
        termo (str): Termo a ser validado
        links (list): Lista de URLs para validar
        fonte_id (int, optional): ID da fonte
        usar_proxy (bool, optional): Se deve usar proxy Tor
        
    Returns:
        list: Resultados da validação para cada link
    """
    resultados = []
    
    for url in links:
        resultado = buscar_e_validar_termo(termo, url, fonte_id, usar_proxy)
        resultados.append(resultado)
    
    # Conta quantos resultados válidos foram encontrados
    validos = sum(1 for r in resultados if r["valido"])
    
    logger.info(f"Validação semântica concluída para '{termo}': {validos}/{len(links)} resultados válidos")
    
    return resultados
