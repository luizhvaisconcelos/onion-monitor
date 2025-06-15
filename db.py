import sqlite3
import os
import logging
import csv
import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("db")

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'onion_monitor.db')

def get_db_connection():
    """
    Obtém uma conexão com o banco de dados.
    
    Returns:
        sqlite3.Connection: Conexão com o banco de dados
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa o banco de dados, criando as tabelas necessárias.
    """
    logger.info("Inicializando banco de dados...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Cria a tabela de fontes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fontes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                url TEXT NOT NULL,
                tipo TEXT NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_check TIMESTAMP,
                status TEXT DEFAULT 'ativo'
            )
        ''')
        
        # Cria a tabela de coletas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coletas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo_busca TEXT NOT NULL,
                link_encontrado TEXT NOT NULL,
                titulo TEXT,
                descricao TEXT,
                fonte_id INTEGER,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validado BOOLEAN DEFAULT 0,
                score_validacao INTEGER DEFAULT 0,
                metodo_validacao TEXT,
                observacoes_validacao TEXT,
                data_validacao TIMESTAMP,
                FOREIGN KEY (fonte_id) REFERENCES fontes (id)
            )
        ''')
        
        # Cria a tabela de auditoria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao TEXT NOT NULL,
                descricao TEXT,
                dados TEXT,
                usuario TEXT DEFAULT 'sistema',
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cria a tabela de status_fontes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_fontes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fonte_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                data_verificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detalhes TEXT,
                FOREIGN KEY (fonte_id) REFERENCES fontes (id)
            )
        ''')
        
        # Verifica se já existem fontes cadastradas
        cursor.execute('SELECT COUNT(*) FROM fontes')
        count = cursor.fetchone()[0]
        
        # Se não existirem fontes, cadastra as fontes padrão
        if count == 0:
            fontes_padrao = [
                ('Ahmia', 'https://ahmia.fi/', 'surface', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Dark.fail', 'https://dark.fail/', 'lista', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Onion.live', 'https://onion.live/', 'lista', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Tor.taxi', 'https://tor.taxi/', 'lista', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Onion.land', 'https://onion.land/', 'lista', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('DarkSearch', 'https://darksearch.io/', 'surface', 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo')
            ]
            
            cursor.executemany(
                'INSERT INTO fontes (nome, url, tipo, ativo, ultimo_check, status) VALUES (?, ?, ?, ?, ?, ?)',
                fontes_padrao
            )
            
            logger.info(f"Cadastradas {len(fontes_padrao)} fontes padrão.")
        
        conn.commit()
        logger.info("Banco de dados inicializado com sucesso.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise
    
    finally:
        conn.close()

def adicionar_fonte(nome, url, tipo, ativo=True):
    """
    Adiciona uma nova fonte de busca.
    
    Args:
        nome (str): Nome da fonte
        url (str): URL da fonte
        tipo (str): Tipo da fonte (surface, darkweb, lista)
        ativo (bool, optional): Se a fonte está ativa. Defaults to True.
    """
    logger.info(f"Adicionando fonte: {nome} ({url})")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO fontes (nome, url, tipo, ativo, status) VALUES (?, ?, ?, ?, ?)',
            (nome, url, tipo, ativo, 'ativo')
        )
        
        conn.commit()
        logger.info(f"Fonte '{nome}' adicionada com sucesso.")
        
        # Registra a ação no log de auditoria
        registrar_auditoria(
            acao="adicionar_fonte",
            descricao=f"Adicionada nova fonte: {nome}",
            dados=f"URL: {url}, Tipo: {tipo}, Ativo: {ativo}"
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao adicionar fonte: {str(e)}")
        raise
    
    finally:
        conn.close()

def obter_fontes(apenas_ativas=True):
    """
    Obtém todas as fontes cadastradas.
    
    Args:
        apenas_ativas (bool, optional): Se deve retornar apenas fontes ativas. Defaults to True.
        
    Returns:
        list: Lista de dicionários com as fontes
    """
    logger.info(f"Obtendo fontes (apenas_ativas={apenas_ativas})")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if apenas_ativas:
            cursor.execute('SELECT * FROM fontes WHERE ativo = 1 ORDER BY nome')
        else:
            cursor.execute('SELECT * FROM fontes ORDER BY nome')
        
        fontes = cursor.fetchall()
        fontes_lista = []
        
        for fonte in fontes:
            fonte_dict = dict(fonte)
            fontes_lista.append(fonte_dict)
            
        logger.info(f"Obtidas {len(fontes_lista)} fontes.")
        
        return fontes_lista
        
    except Exception as e:
        logger.error(f"Erro ao obter fontes: {str(e)}")
        return []
    
    finally:
        conn.close()

def registrar_coleta(termo_busca, link_encontrado, titulo, descricao, fonte_id):
    """
    Registra uma coleta no banco de dados.
    
    Args:
        termo_busca (str): Termo buscado
        link_encontrado (str): Link encontrado
        titulo (str): Título do resultado
        descricao (str): Descrição do resultado
        fonte_id (int): ID da fonte
        
    Returns:
        int: ID da coleta registrada
    """
    logger.info(f"Registrando coleta: {termo_busca} -> {link_encontrado}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se o link já existe para o mesmo termo
        cursor.execute(
            'SELECT id FROM coletas WHERE termo_busca = ? AND link_encontrado = ?',
            (termo_busca, link_encontrado)
        )
        
        existente = cursor.fetchone()
        
        if existente:
            logger.info(f"Link já registrado para este termo (ID: {existente['id']})")
            
            # Registra a ação no log de auditoria
            registrar_auditoria(
                acao="coleta_duplicada",
                descricao=f"Tentativa de registrar link já existente",
                dados=f"Termo: {termo_busca}, Link: {link_encontrado}, ID existente: {existente['id']}"
            )
            
            return existente['id']
        
        # Insere a nova coleta
        cursor.execute(
            'INSERT INTO coletas (termo_busca, link_encontrado, titulo, descricao, fonte_id) VALUES (?, ?, ?, ?, ?)',
            (termo_busca, link_encontrado, titulo, descricao, fonte_id)
        )
        
        coleta_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Coleta registrada com sucesso (ID: {coleta_id})")
        
        # Registra a ação no log de auditoria
        registrar_auditoria(
            acao="registrar_coleta",
            descricao=f"Registrada nova coleta para o termo '{termo_busca}'",
            dados=f"Link: {link_encontrado}, Fonte ID: {fonte_id}"
        )
        
        return coleta_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar coleta: {str(e)}")
        raise
    
    finally:
        conn.close()

def registrar_validacao(coleta_id, validado, score_validacao, metodo_validacao, observacoes):
    """
    Registra a validação de um vazamento.
    
    Args:
        coleta_id (int): ID da coleta
        validado (bool): Se o vazamento foi validado
        score_validacao (int): Score de validação (0-100)
        metodo_validacao (str): Método utilizado para validação
        observacoes (str): Observações sobre a validação
    """
    logger.info(f"Registrando validação para coleta ID {coleta_id}: validado={validado}, score={score_validacao}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            UPDATE coletas 
            SET validado = ?, 
                score_validacao = ?, 
                metodo_validacao = ?, 
                observacoes_validacao = ?,
                data_validacao = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (validado, score_validacao, metodo_validacao, observacoes, coleta_id)
        )
        
        conn.commit()
        logger.info(f"Validação registrada com sucesso para coleta ID {coleta_id}")
        
        # Registra a ação no log de auditoria
        registrar_auditoria(
            acao="registrar_validacao",
            descricao=f"Registrada validação para coleta ID {coleta_id}",
            dados=f"Validado: {validado}, Score: {score_validacao}, Método: {metodo_validacao}"
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar validação: {str(e)}")
        raise
    
    finally:
        conn.close()

def obter_coletas(termo=None, data_inicio=None, data_fim=None, apenas_validados=None):
    """
    Obtém coletas com filtros.
    
    Args:
        termo (str, optional): Termo para filtrar. Defaults to None.
        data_inicio (str, optional): Data de início (formato YYYY-MM-DD). Defaults to None.
        data_fim (str, optional): Data de fim (formato YYYY-MM-DD). Defaults to None.
        apenas_validados (bool, optional): Se deve retornar apenas validados. Defaults to None.
        
    Returns:
        list: Lista de dicionários com as coletas
    """
    logger.info(f"Obtendo coletas (termo={termo}, data_inicio={data_inicio}, data_fim={data_fim}, apenas_validados={apenas_validados})")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = '''
            SELECT c.*, f.nome as fonte_nome
            FROM coletas c
            LEFT JOIN fontes f ON c.fonte_id = f.id
            WHERE 1=1
        '''
        
        params = []
        
        if termo:
            query += ' AND c.termo_busca LIKE ?'
            params.append(f'%{termo}%')
        
        if data_inicio:
            query += ' AND DATE(c.data_coleta) >= DATE(?)'
            params.append(data_inicio)
        
        if data_fim:
            query += ' AND DATE(c.data_coleta) <= DATE(?)'
            params.append(data_fim)
        
        if apenas_validados is not None:
            query += ' AND c.validado = ?'
            params.append(1 if apenas_validados else 0)
        
        query += ' ORDER BY c.data_coleta DESC'
        
        cursor.execute(query, params)
        coletas = cursor.fetchall()
        coletas_lista = []
        
        for coleta in coletas:
            coleta_dict = dict(coleta)
            coletas_lista.append(coleta_dict)
            
        logger.info(f"Obtidas {len(coletas_lista)} coletas.")
        
        # Registra a ação no log de auditoria
        registrar_auditoria(
            acao="consultar_coletas",
            descricao=f"Consulta de coletas com filtros",
            dados=f"Termo: {termo}, Período: {data_inicio or 'início'} a {data_fim or 'fim'}, Apenas validados: {apenas_validados}"
        )
        
        return coletas_lista
        
    except Exception as e:
        logger.error(f"Erro ao obter coletas: {str(e)}")
        return []
    
    finally:
        conn.close()

def obter_estatisticas_validacao():
    """
    Obtém estatísticas de validação.
    
    Returns:
        dict: Dicionário com estatísticas
    """
    logger.info("Obtendo estatísticas de validação")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total de validados
        cursor.execute('SELECT COUNT(*) FROM coletas WHERE validado = 1')
        validados = cursor.fetchone()[0]
        
        # Total de não validados
        cursor.execute('SELECT COUNT(*) FROM coletas WHERE validado = 0')
        nao_validados = cursor.fetchone()[0]
        
        # Score médio
        cursor.execute('SELECT AVG(score_validacao) FROM coletas WHERE validado = 1')
        score_medio = cursor.fetchone()[0]
        score_medio = round(score_medio) if score_medio else 0
        
        # Métodos de validação
        cursor.execute('''
            SELECT metodo_validacao, COUNT(*) as quantidade
            FROM coletas
            WHERE validado = 1
            GROUP BY metodo_validacao
            ORDER BY quantidade DESC
        ''')
        metodos = cursor.fetchall()
        metodos_lista = []
        
        for metodo in metodos:
            metodo_dict = dict(metodo)
            metodos_lista.append(metodo_dict)
        
        estatisticas = {
            'validados': validados,
            'nao_validados': nao_validados,
            'score_medio': score_medio,
            'metodos': metodos_lista
        }
        
        logger.info(f"Estatísticas obtidas: {validados} validados, {nao_validados} não validados, score médio {score_medio}")
        
        return estatisticas
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de validação: {str(e)}")
        return {
            'validados': 0,
            'nao_validados': 0,
            'score_medio': 0,
            'metodos': []
        }
    
    finally:
        conn.close()

def exportar_coletas_csv(filepath, termo=None, data_inicio=None, data_fim=None, apenas_validados=None):
    """
    Exporta coletas para um arquivo CSV.
    
    Args:
        filepath (str): Caminho do arquivo CSV
        termo (str, optional): Termo para filtrar. Defaults to None.
        data_inicio (str, optional): Data de início (formato YYYY-MM-DD). Defaults to None.
        data_fim (str, optional): Data de fim (formato YYYY-MM-DD). Defaults to None.
        apenas_validados (bool, optional): Se deve exportar apenas validados. Defaults to None.
    """
    logger.info(f"Exportando coletas para CSV: {filepath}")
    
    # Obtém as coletas com os filtros
    coletas = obter_coletas(termo, data_inicio, data_fim, apenas_validados)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Define os campos do CSV
            fieldnames = [
                'id', 'data_coleta', 'termo_busca', 'link_encontrado', 
                'titulo', 'descricao', 'fonte_nome', 'validado', 
                'score_validacao', 'metodo_validacao', 'observacoes_validacao', 
                'data_validacao'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for coleta in coletas:
                # Escreve cada coleta como uma linha no CSV
                writer.writerow({
                    'id': coleta['id'],
                    'data_coleta': coleta['data_coleta'],
                    'termo_busca': coleta['termo_busca'],
                    'link_encontrado': coleta['link_encontrado'],
                    'titulo': coleta['titulo'],
                    'descricao': coleta['descricao'],
                    'fonte_nome': coleta['fonte_nome'],
                    'validado': 'Sim' if coleta['validado'] else 'Não',
                    'score_validacao': coleta.get('score_validacao', 0),
                    'metodo_validacao': coleta.get('metodo_validacao', ''),
                    'observacoes_validacao': coleta.get('observacoes_validacao', ''),
                    'data_validacao': coleta.get('data_validacao', '')
                })
        
        logger.info(f"Exportadas {len(coletas)} coletas para {filepath}")
        
    except Exception as e:
        logger.error(f"Erro ao exportar coletas para CSV: {str(e)}")
        raise

def registrar_auditoria(acao, descricao, dados=None):
    """
    Registra uma ação no log de auditoria.
    
    Args:
        acao (str): Tipo de ação realizada
        descricao (str): Descrição da ação
        dados (str, optional): Dados adicionais. Defaults to None.
    """
    logger.info(f"Registrando auditoria: {acao} - {descricao}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se a tabela auditoria existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditoria'")
        if not cursor.fetchone():
            # Cria a tabela se não existir
            cursor.execute('''
                CREATE TABLE auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acao TEXT NOT NULL,
                    descricao TEXT,
                    dados TEXT,
                    usuario TEXT DEFAULT 'sistema',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Tabela 'auditoria' criada.")
        
        # Insere o registro de auditoria
        cursor.execute(
            'INSERT INTO auditoria (acao, descricao, dados) VALUES (?, ?, ?)',
            (acao, descricao, dados)
        )
        
        conn.commit()
        logger.info(f"Auditoria registrada com sucesso: {acao}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar auditoria: {str(e)}")
        
    finally:
        conn.close()

def obter_registros_auditoria(data_inicio=None, data_fim=None, limite=100):
    """
    Obtém registros de auditoria com filtros.
    
    Args:
        data_inicio (str, optional): Data de início (formato YYYY-MM-DD). Defaults to None.
        data_fim (str, optional): Data de fim (formato YYYY-MM-DD). Defaults to None.
        limite (int, optional): Limite de registros. Defaults to 100.
        
    Returns:
        list: Lista de dicionários com os registros
    """
    logger.info(f"Obtendo registros de auditoria (data_inicio={data_inicio}, data_fim={data_fim}, limite={limite})")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = 'SELECT * FROM auditoria WHERE 1=1'
        params = []
        
        if data_inicio:
            query += ' AND DATE(data_hora) >= DATE(?)'
            params.append(data_inicio)
        
        if data_fim:
            query += ' AND DATE(data_hora) <= DATE(?)'
            params.append(data_fim)
        
        query += ' ORDER BY data_hora DESC LIMIT ?'
        params.append(limite)
        
        cursor.execute(query, params)
        registros = cursor.fetchall()
        registros_lista = []
        
        for registro in registros:
            registro_dict = dict(registro)
            registros_lista.append(registro_dict)
            
        logger.info(f"Obtidos {len(registros_lista)} registros de auditoria.")
        
        return registros_lista
        
    except Exception as e:
        logger.error(f"Erro ao obter registros de auditoria: {str(e)}")
        return []
    
    finally:
        conn.close()

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
