import requests
from bs4 import BeautifulSoup
import re
import json
import logging
import datetime
import random
import time
from db import get_db_connection, registrar_coleta, registrar_validacao, registrar_auditoria, obter_fontes

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("coletor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("coletor")

def buscar_termo(termo):
    """
    Busca um termo nas fontes cadastradas e registra os resultados.
    
    Args:
        termo (str): Termo a ser buscado
        
    Returns:
        list: Lista de resultados encontrados
    """
    logger.info(f"Iniciando busca pelo termo: {termo}")
    
    # Registra a ação de busca
    registrar_auditoria(
        acao="iniciar_busca",
        descricao=f"Busca iniciada para o termo: {termo}",
        dados=f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Obtém fontes ativas
    fontes = obter_fontes(apenas_ativas=True)
    
    if not fontes:
        logger.warning("Nenhuma fonte ativa encontrada.")
        return []
    
    resultados = []
    
    # Para cada fonte, realiza a busca
    for fonte in fontes:
        try:
            logger.info(f"Buscando em {fonte['nome']} ({fonte['url']})")
            
            # Verifica o status da fonte antes de buscar
            status, _ = verificar_status_fonte(fonte['id'], fonte['url'])
            
            if status != 'ativo':
                logger.warning(f"Fonte {fonte['nome']} está {status}. Pulando.")
                continue
            
            # Realiza a busca de acordo com o tipo de fonte
            if fonte['tipo'] == 'surface':
                # Fontes da surface web (Ahmia, DarkSearch, etc.)
                novos_resultados = buscar_em_surface(termo, fonte)
            elif fonte['tipo'] == 'lista':
                # Fontes de listas de links .onion (Dark.fail, Onion.live, etc.)
                novos_resultados = buscar_em_lista(termo, fonte)
            else:
                logger.warning(f"Tipo de fonte desconhecido: {fonte['tipo']}")
                continue
            
            # Adiciona os resultados à lista
            resultados.extend(novos_resultados)
            
            # Registra a ação de busca na fonte
            registrar_auditoria(
                acao="busca_fonte",
                descricao=f"Busca em {fonte['nome']} para o termo: {termo}",
                dados=f"Resultados: {len(novos_resultados)}"
            )
            
            # Pausa para não sobrecarregar as fontes
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erro ao buscar em {fonte['nome']}: {str(e)}")
    
    # Registra a conclusão da busca
    registrar_auditoria(
        acao="concluir_busca",
        descricao=f"Busca concluída para o termo: {termo}",
        dados=f"Total de resultados: {len(resultados)}"
    )
    
    logger.info(f"Busca concluída. {len(resultados)} resultados encontrados.")
    
    return resultados

def buscar_em_surface(termo, fonte):
    """
    Busca um termo em fontes da surface web.
    
    Args:
        termo (str): Termo a ser buscado
        fonte (dict): Informações da fonte
        
    Returns:
        list: Lista de resultados encontrados
    """
    resultados = []
    
    try:
        # Ahmia
        if fonte['nome'] == 'Ahmia':
            url = f"https://ahmia.fi/search/?q={termo}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                resultados_html = soup.select('.result')
                
                for resultado in resultados_html:
                    try:
                        titulo_elem = resultado.select_one('h4')
                        link_elem = resultado.select_one('a')
                        descricao_elem = resultado.select_one('.description')
                        
                        if titulo_elem and link_elem:
                            titulo = titulo_elem.text.strip()
                            link = link_elem['href']
                            descricao = descricao_elem.text.strip() if descricao_elem else ""
                            
                            # Registra a coleta
                            coleta_id = registrar_coleta(
                                termo_busca=termo,
                                link_encontrado=link,
                                titulo=titulo,
                                descricao=descricao,
                                fonte_id=fonte['id']
                            )
                            
                            # Valida o vazamento
                            validado, score, metodo, observacoes = validar_vazamento(link, titulo, descricao)
                            
                            if validado:
                                registrar_validacao(
                                    coleta_id=coleta_id,
                                    validado=validado,
                                    score_validacao=score,
                                    metodo_validacao=metodo,
                                    observacoes=observacoes
                                )
                            
                            # Adiciona ao resultado
                            resultados.append({
                                'id': coleta_id,
                                'termo_busca': termo,
                                'link_encontrado': link,
                                'titulo': titulo,
                                'descricao': descricao,
                                'fonte_id': fonte['id'],
                                'fonte_nome': fonte['nome'],
                                'data_coleta': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'validado': validado,
                                'score_validacao': score,
                                'metodo_validacao': metodo,
                                'observacoes_validacao': observacoes
                            })
                    except Exception as e:
                        logger.error(f"Erro ao processar resultado de {fonte['nome']}: {str(e)}")
        
        # DarkSearch
        elif fonte['nome'] == 'DarkSearch':
            # Simulação de resultados para DarkSearch (API real requer chave)
            # Em um ambiente real, seria necessário integrar com a API oficial
            
            # Gera alguns resultados simulados
            for i in range(3):
                titulo = f"Resultado {i+1} para {termo} em {fonte['nome']}"
                link = f"http://{termo.lower().replace(' ', '')}{random.randint(1000, 9999)}.onion/index.html"
                descricao = f"Descrição do resultado {i+1} para o termo {termo} encontrado em {fonte['nome']}."
                
                # Registra a coleta
                coleta_id = registrar_coleta(
                    termo_busca=termo,
                    link_encontrado=link,
                    titulo=titulo,
                    descricao=descricao,
                    fonte_id=fonte['id']
                )
                
                # Valida o vazamento
                validado, score, metodo, observacoes = validar_vazamento(link, titulo, descricao)
                
                if validado:
                    registrar_validacao(
                        coleta_id=coleta_id,
                        validado=validado,
                        score_validacao=score,
                        metodo_validacao=metodo,
                        observacoes=observacoes
                    )
                
                # Adiciona ao resultado
                resultados.append({
                    'id': coleta_id,
                    'termo_busca': termo,
                    'link_encontrado': link,
                    'titulo': titulo,
                    'descricao': descricao,
                    'fonte_id': fonte['id'],
                    'fonte_nome': fonte['nome'],
                    'data_coleta': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'validado': validado,
                    'score_validacao': score,
                    'metodo_validacao': metodo,
                    'observacoes_validacao': observacoes
                })
        
        else:
            logger.warning(f"Fonte surface não implementada: {fonte['nome']}")
    
    except Exception as e:
        logger.error(f"Erro ao buscar em {fonte['nome']}: {str(e)}")
    
    return resultados

def buscar_em_lista(termo, fonte):
    """
    Busca um termo em fontes de listas de links .onion.
    
    Args:
        termo (str): Termo a ser buscado
        fonte (dict): Informações da fonte
        
    Returns:
        list: Lista de resultados encontrados
    """
    resultados = []
    
    try:
        # Simulação de resultados para fontes de listas
        # Em um ambiente real, seria necessário implementar scrapers específicos
        
        # Gera alguns resultados simulados
        for i in range(2):
            titulo = f"Resultado {i+1} para {termo} em {fonte['nome']}"
            link = f"http://{termo.lower().replace(' ', '')}{random.randint(1000, 9999)}.onion/index.html"
            descricao = f"Descrição do resultado {i+1} para o termo {termo} encontrado em {fonte['nome']}."
            
            # Registra a coleta
            coleta_id = registrar_coleta(
                termo_busca=termo,
                link_encontrado=link,
                titulo=titulo,
                descricao=descricao,
                fonte_id=fonte['id']
            )
            
            # Valida o vazamento
            validado, score, metodo, observacoes = validar_vazamento(link, titulo, descricao)
            
            if validado:
                registrar_validacao(
                    coleta_id=coleta_id,
                    validado=validado,
                    score_validacao=score,
                    metodo_validacao=metodo,
                    observacoes=observacoes
                )
            
            # Adiciona ao resultado
            resultados.append({
                'id': coleta_id,
                'termo_busca': termo,
                'link_encontrado': link,
                'titulo': titulo,
                'descricao': descricao,
                'fonte_id': fonte['id'],
                'fonte_nome': fonte['nome'],
                'data_coleta': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'validado': validado,
                'score_validacao': score,
                'metodo_validacao': metodo,
                'observacoes_validacao': observacoes
            })
    
    except Exception as e:
        logger.error(f"Erro ao buscar em {fonte['nome']}: {str(e)}")
    
    return resultados

def validar_vazamento(link, titulo, descricao):
    """
    Valida se um link é um vazamento real.
    
    Args:
        link (str): Link encontrado
        titulo (str): Título do resultado
        descricao (str): Descrição do resultado
        
    Returns:
        tuple: (validado, score, metodo, observacoes)
    """
    logger.info(f"Validando vazamento: {link}")
    
    # Inicializa o score
    score = 0
    observacoes = []
    
    # Verifica se é um link .onion
    if '.onion' in link:
        score += 20
        observacoes.append("Link .onion (+20)")
    
    # Verifica palavras-chave no título
    palavras_chave_titulo = ['leak', 'vazamento', 'data', 'dump', 'hack', 'breach', 'database']
    for palavra in palavras_chave_titulo:
        if palavra.lower() in titulo.lower():
            score += 10
            observacoes.append(f"Palavra-chave no título: {palavra} (+10)")
    
    # Verifica palavras-chave na descrição
    palavras_chave_descricao = ['password', 'senha', 'credential', 'credencial', 'personal', 'pessoal', 'private', 'privado']
    for palavra in palavras_chave_descricao:
        if palavra.lower() in descricao.lower():
            score += 5
            observacoes.append(f"Palavra-chave na descrição: {palavra} (+5)")
    
    # Verifica padrões de dados sensíveis na descrição
    padroes = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "E-mail"),
        (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{2}\b', "CPF"),
        (r'\b\d{5}[-.\s]?\d{3}\b', "CEP"),
        (r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b', "Cartão de crédito")
    ]
    
    for padrao, tipo in padroes:
        if re.search(padrao, descricao):
            score += 15
            observacoes.append(f"Padrão de {tipo} encontrado (+15)")
    
    # Determina se é um vazamento válido (score >= 40)
    validado = score >= 40
    
    # Define o método de validação
    metodo = "automático"
    
    # Registra a ação de validação
    registrar_auditoria(
        acao="validacao_automatica",
        descricao=f"Validação automática de link: {link}",
        dados=f"Score: {score}, Validado: {validado}, Observações: {', '.join(observacoes)}"
    )
    
    logger.info(f"Validação concluída: score={score}, validado={validado}")
    
    return validado, score, metodo, ", ".join(observacoes)

def verificar_status_fonte(fonte_id, url):
    """
    Verifica o status de uma fonte.
    
    Args:
        fonte_id (int): ID da fonte
        url (str): URL da fonte
        
    Returns:
        tuple: (status, detalhes)
    """
    logger.info(f"Verificando status da fonte ID {fonte_id}: {url}")
    
    try:
        # Tenta acessar a URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Verifica o status da resposta
        if response.status_code == 200:
            status = "ativo"
            detalhes = f"Fonte ativa. Status code: {response.status_code}"
        else:
            status = "inativo"
            detalhes = f"Fonte inativa. Status code: {response.status_code}"
        
        # Atualiza o status da fonte no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Atualiza o status e a data de verificação
            cursor.execute(
                'UPDATE fontes SET status = ?, ultimo_check = CURRENT_TIMESTAMP WHERE id = ?',
                (status, fonte_id)
            )
            
            # Registra o status na tabela status_fontes
            cursor.execute(
                'INSERT INTO status_fontes (fonte_id, status, detalhes) VALUES (?, ?, ?)',
                (fonte_id, status, detalhes)
            )
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao atualizar status da fonte: {str(e)}")
            
        finally:
            conn.close()
        
        # Registra a ação de verificação
        registrar_auditoria(
            acao="verificar_fonte",
            descricao=f"Verificação de status da fonte ID {fonte_id}",
            dados=f"Status: {status}, Detalhes: {detalhes}"
        )
        
        logger.info(f"Status da fonte ID {fonte_id}: {status}")
        
        return status, detalhes
        
    except requests.exceptions.RequestException as e:
        status = "erro"
        detalhes = f"Erro ao acessar a fonte: {str(e)}"
        
        # Atualiza o status da fonte no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Atualiza o status e a data de verificação
            cursor.execute(
                'UPDATE fontes SET status = ?, ultimo_check = CURRENT_TIMESTAMP WHERE id = ?',
                (status, fonte_id)
            )
            
            # Registra o status na tabela status_fontes
            cursor.execute(
                'INSERT INTO status_fontes (fonte_id, status, detalhes) VALUES (?, ?, ?)',
                (fonte_id, status, detalhes)
            )
            
            conn.commit()
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Erro ao atualizar status da fonte: {str(db_error)}")
            
        finally:
            conn.close()
        
        # Registra a ação de verificação
        registrar_auditoria(
            acao="verificar_fonte",
            descricao=f"Verificação de status da fonte ID {fonte_id}",
            dados=f"Status: {status}, Detalhes: {detalhes}"
        )
        
        logger.error(f"Erro ao verificar status da fonte ID {fonte_id}: {str(e)}")
        
        return status, detalhes

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
