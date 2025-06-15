import os
import logging
import sqlite3
import csv
import datetime
import json
import io
from io import TextIOWrapper

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
                status TEXT DEFAULT 'desconhecido',
                ultimo_check TIMESTAMP,
                detalhes TEXT
            )
        ''')
        
        # Verifica se a coluna detalhes existe, se não, adiciona
        try:
            cursor.execute("SELECT detalhes FROM fontes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Adicionando coluna 'detalhes' à tabela fontes")
            cursor.execute("ALTER TABLE fontes ADD COLUMN detalhes TEXT")
        
        # Cria a tabela de status das fontes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_fontes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fonte_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                detalhes TEXT,
                data_verificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fonte_id) REFERENCES fontes (id)
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
                FOREIGN KEY (fonte_id) REFERENCES fontes (id)
            )
        ''')
        
        # Cria a tabela de validações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coleta_id INTEGER NOT NULL,
                validado BOOLEAN NOT NULL,
                score_validacao INTEGER,
                metodo_validacao TEXT,
                observacoes TEXT,
                data_validacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coleta_id) REFERENCES coletas (id)
            )
        ''')
        
        # Cria a tabela de auditoria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao TEXT NOT NULL,
                descricao TEXT,
                dados TEXT,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cria a tabela de resultados (para validação semântica)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                termo TEXT NOT NULL,
                contexto TEXT,
                valido BOOLEAN NOT NULL,
                status INTEGER,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("Banco de dados inicializado com sucesso.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        
    finally:
        conn.close()

def obter_fontes(apenas_ativas=False):
    """
    Obtém a lista de fontes cadastradas.
    
    Args:
        apenas_ativas (bool): Se True, retorna apenas fontes ativas
        
    Returns:
        list: Lista de fontes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if apenas_ativas:
            cursor.execute('SELECT * FROM fontes WHERE ativo = 1 ORDER BY nome')
        else:
            cursor.execute('SELECT * FROM fontes ORDER BY nome')
            
        fontes = [dict(fonte) for fonte in cursor.fetchall()]
        
        return fontes
        
    except Exception as e:
        logger.error(f"Erro ao obter fontes: {str(e)}")
        return []
        
    finally:
        conn.close()

def adicionar_fonte(nome, url, tipo, ativo=True):
    """
    Adiciona uma nova fonte.
    
    Args:
        nome (str): Nome da fonte
        url (str): URL da fonte
        tipo (str): Tipo da fonte (surface, deep, dark)
        ativo (bool): Se a fonte está ativa
        
    Returns:
        int: ID da fonte adicionada ou None em caso de erro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO fontes (nome, url, tipo, ativo) VALUES (?, ?, ?, ?)',
            (nome, url, tipo, ativo)
        )
        
        conn.commit()
        
        # Obtém o ID da fonte adicionada
        fonte_id = cursor.lastrowid
        
        logger.info(f"Fonte adicionada com sucesso: {nome} (ID: {fonte_id})")
        
        return fonte_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao adicionar fonte: {str(e)}")
        return None
        
    finally:
        conn.close()

def registrar_coleta(termo_busca, link_encontrado, titulo, descricao, fonte_id=None):
    """
    Registra uma coleta de link.
    
    Args:
        termo_busca (str): Termo buscado
        link_encontrado (str): Link encontrado
        titulo (str): Título do resultado
        descricao (str): Descrição do resultado
        fonte_id (int): ID da fonte
        
    Returns:
        int: ID da coleta registrada ou None em caso de erro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO coletas (termo_busca, link_encontrado, titulo, descricao, fonte_id) VALUES (?, ?, ?, ?, ?)',
            (termo_busca, link_encontrado, titulo, descricao, fonte_id)
        )
        
        conn.commit()
        
        # Obtém o ID da coleta registrada
        coleta_id = cursor.lastrowid
        
        logger.info(f"Coleta registrada com sucesso: {termo_busca} -> {link_encontrado} (ID: {coleta_id})")
        
        return coleta_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar coleta: {str(e)}")
        return None
        
    finally:
        conn.close()

def registrar_validacao(coleta_id, validado, score_validacao=None, metodo_validacao=None, observacoes=None):
    """
    Registra uma validação de coleta.
    
    Args:
        coleta_id (int): ID da coleta
        validado (bool): Se a coleta foi validada
        score_validacao (int): Score de validação
        metodo_validacao (str): Método de validação
        observacoes (str): Observações sobre a validação
        
    Returns:
        int: ID da validação registrada ou None em caso de erro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO validacoes (coleta_id, validado, score_validacao, metodo_validacao, observacoes) VALUES (?, ?, ?, ?, ?)',
            (coleta_id, validado, score_validacao, metodo_validacao, observacoes)
        )
        
        conn.commit()
        
        # Obtém o ID da validação registrada
        validacao_id = cursor.lastrowid
        
        logger.info(f"Validação registrada com sucesso: Coleta ID {coleta_id}, Validado: {validado} (ID: {validacao_id})")
        
        return validacao_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar validação: {str(e)}")
        return None
        
    finally:
        conn.close()

def registrar_auditoria(acao, descricao=None, dados=None):
    """
    Registra uma ação de auditoria.
    
    Args:
        acao (str): Ação realizada
        descricao (str): Descrição da ação
        dados (str): Dados adicionais
        
    Returns:
        int: ID da auditoria registrada ou None em caso de erro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO auditoria (acao, descricao, dados) VALUES (?, ?, ?)',
            (acao, descricao, dados)
        )
        
        conn.commit()
        
        # Obtém o ID da auditoria registrada
        auditoria_id = cursor.lastrowid
        
        logger.info(f"Auditoria registrada com sucesso: {acao} (ID: {auditoria_id})")
        
        return auditoria_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar auditoria: {str(e)}")
        return None
        
    finally:
        conn.close()

def obter_coletas(termo=None, fonte_id=None, apenas_validadas=False, limite=100):
    """
    Obtém a lista de coletas registradas.
    
    Args:
        termo (str): Filtro por termo de busca
        fonte_id (int): Filtro por fonte
        apenas_validadas (bool): Se True, retorna apenas coletas validadas
        limite (int): Limite de resultados
        
    Returns:
        list: Lista de coletas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = '''
            SELECT c.*, f.nome as fonte_nome, v.validado, v.score_validacao, v.metodo_validacao, v.observacoes
            FROM coletas c
            LEFT JOIN fontes f ON c.fonte_id = f.id
            LEFT JOIN validacoes v ON c.id = v.coleta_id
        '''
        
        params = []
        where_clauses = []
        
        if termo:
            where_clauses.append('c.termo_busca LIKE ?')
            params.append(f'%{termo}%')
            
        if fonte_id:
            where_clauses.append('c.fonte_id = ?')
            params.append(fonte_id)
            
        if apenas_validadas:
            where_clauses.append('v.validado = 1')
            
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
            
        query += ' ORDER BY c.data_coleta DESC LIMIT ?'
        params.append(limite)
        
        cursor.execute(query, params)
        coletas = [dict(coleta) for coleta in cursor.fetchall()]
        
        return coletas
        
    except Exception as e:
        logger.error(f"Erro ao obter coletas: {str(e)}")
        return []
        
    finally:
        conn.close()

def obter_estatisticas_validacao():
    """
    Obtém estatísticas de validação.
    
    Returns:
        dict: Estatísticas de validação
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total de coletas
        cursor.execute('SELECT COUNT(*) as total FROM coletas')
        total_coletas = cursor.fetchone()['total']
        
        # Total de coletas validadas
        cursor.execute('''
            SELECT COUNT(*) as total_validadas
            FROM coletas c
            JOIN validacoes v ON c.id = v.coleta_id
            WHERE v.validado = 1
        ''')
        total_validadas = cursor.fetchone()['total_validadas']
        
        # Total de coletas por fonte
        cursor.execute('''
            SELECT f.nome, COUNT(*) as total
            FROM coletas c
            JOIN fontes f ON c.fonte_id = f.id
            GROUP BY f.id
            ORDER BY total DESC
        ''')
        coletas_por_fonte = [dict(row) for row in cursor.fetchall()]
        
        # Total de coletas validadas por fonte
        cursor.execute('''
            SELECT f.nome, COUNT(*) as total_validadas
            FROM coletas c
            JOIN fontes f ON c.fonte_id = f.id
            JOIN validacoes v ON c.id = v.coleta_id
            WHERE v.validado = 1
            GROUP BY f.id
            ORDER BY total_validadas DESC
        ''')
        validadas_por_fonte = [dict(row) for row in cursor.fetchall()]
        
        # Termos mais buscados
        cursor.execute('''
            SELECT termo_busca, COUNT(*) as total
            FROM coletas
            GROUP BY termo_busca
            ORDER BY total DESC
            LIMIT 10
        ''')
        termos_mais_buscados = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_coletas': total_coletas,
            'total_validadas': total_validadas,
            'coletas_por_fonte': coletas_por_fonte,
            'validadas_por_fonte': validadas_por_fonte,
            'termos_mais_buscados': termos_mais_buscados
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de validação: {str(e)}")
        return {
            'total_coletas': 0,
            'total_validadas': 0,
            'coletas_por_fonte': [],
            'validadas_por_fonte': [],
            'termos_mais_buscados': []
        }
        
    finally:
        conn.close()

def exportar_coletas_csv():
    """
    Exporta as coletas para um arquivo CSV.
    
    Returns:
        io.BytesIO: Conteúdo do arquivo CSV
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                c.id, c.termo_busca, c.link_encontrado, c.titulo, c.descricao, 
                f.nome as fonte_nome, c.data_coleta,
                v.validado, v.score_validacao, v.metodo_validacao, v.observacoes
            FROM coletas c
            LEFT JOIN fontes f ON c.fonte_id = f.id
            LEFT JOIN validacoes v ON c.id = v.coleta_id
            ORDER BY c.data_coleta DESC
        ''')
        
        coletas = cursor.fetchall()
        
        # Cria um buffer de memória para o CSV
        output = io.BytesIO()
        output.write(b'\xef\xbb\xbf')  # BOM UTF-8
        
        # Cria um wrapper de texto para o CSV
        text_output = TextIOWrapper(output, encoding='utf-8', newline='', write_through=True)
        
        # Cria o escritor CSV
        writer = csv.writer(text_output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Escreve o cabeçalho
        writer.writerow([
            'ID', 'Termo Buscado', 'Link Encontrado', 'Título', 'Descrição',
            'Fonte', 'Data Coleta', 'Validado', 'Score', 'Método', 'Observações'
        ])
        
        # Escreve os dados
        for coleta in coletas:
            writer.writerow([
                coleta['id'],
                coleta['termo_busca'],
                coleta['link_encontrado'],
                coleta['titulo'],
                coleta['descricao'],
                coleta['fonte_nome'],
                coleta['data_coleta'],
                'Sim' if coleta['validado'] else 'Não',
                coleta['score_validacao'],
                coleta['metodo_validacao'],
                coleta['observacoes']
            ])
        
        # Retorna ao início do buffer
        output.seek(0)
        
        return output
        
    except Exception as e:
        logger.error(f"Erro ao exportar coletas para CSV: {str(e)}")
        return None
        
    finally:
        conn.close()

def obter_registros_auditoria(limite=100):
    """
    Obtém os registros de auditoria.
    
    Args:
        limite (int): Limite de resultados
        
    Returns:
        list: Lista de registros de auditoria
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT * FROM auditoria ORDER BY data_registro DESC LIMIT ?',
            (limite,)
        )
        
        registros = [dict(registro) for registro in cursor.fetchall()]
        
        return registros
        
    except Exception as e:
        logger.error(f"Erro ao obter registros de auditoria: {str(e)}")
        return []
        
    finally:
        conn.close()

def obter_resultados(termo=None, url=None, valido=None, limite=100):
    """
    Obtém os resultados de validação semântica.
    
    Args:
        termo (str): Filtro por termo
        url (str): Filtro por URL
        valido (bool): Filtro por validação
        limite (int): Limite de resultados
        
    Returns:
        list: Lista de resultados
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = 'SELECT * FROM resultados'
        
        params = []
        where_clauses = []
        
        if termo:
            where_clauses.append('termo LIKE ?')
            params.append(f'%{termo}%')
            
        if url:
            where_clauses.append('url LIKE ?')
            params.append(f'%{url}%')
            
        if valido is not None:
            where_clauses.append('valido = ?')
            params.append(valido)
            
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
            
        query += ' ORDER BY data_coleta DESC LIMIT ?'
        params.append(limite)
        
        cursor.execute(query, params)
        resultados = [dict(resultado) for resultado in cursor.fetchall()]
        
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao obter resultados: {str(e)}")
        return []
        
    finally:
        conn.close()

def verificar_status_fontes():
    """
    Verifica o status de todas as fontes cadastradas.
    
    Returns:
        dict: Estatísticas da verificação
    """
    from coletor import verificar_status_fonte as verificar_fonte
    
    logger.info("Verificando status das fontes...")
    
    fontes = obter_fontes()
    total = len(fontes)
    online = 0
    offline = 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for fonte in fontes:
            try:
                # Verifica o status da fonte
                status_info = verificar_fonte({'id': fonte['id'], 'url': fonte['url']})
                
                # Determina o status
                if status_info['online']:
                    status = 'online'
                    online += 1
                else:
                    status = 'offline'
                    offline += 1
                
                # Atualiza o status na tabela de fontes
                cursor.execute(
                    'UPDATE fontes SET status = ?, ultimo_check = CURRENT_TIMESTAMP, detalhes = ? WHERE id = ?',
                    (status, json.dumps(status_info), fonte['id'])
                )
                
                # Registra o status na tabela de status_fontes
                cursor.execute(
                    'INSERT INTO status_fontes (fonte_id, status, detalhes) VALUES (?, ?, ?)',
                    (fonte['id'], status, json.dumps(status_info))
                )
                
                logger.info(f"Fonte {fonte['nome']} ({fonte['url']}) está {status}")
                
            except Exception as e:
                logger.error(f"Erro ao verificar status da fonte {fonte['nome']}: {str(e)}")
        
        conn.commit()
        
        logger.info(f"Verificação concluída: {online} online, {offline} offline, {total} total")
        
        return {
            'total': total,
            'online': online,
            'offline': offline
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao verificar status das fontes: {str(e)}")
        return {
            'total': total,
            'online': 0,
            'offline': 0,
            'error': str(e)
        }
        
    finally:
        conn.close()

def migrar_banco():
    """
    Realiza migrações necessárias no banco de dados.
    """
    logger.info("Iniciando migração do banco de dados...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna detalhes existe na tabela fontes
        try:
            cursor.execute("SELECT detalhes FROM fontes LIMIT 1")
            logger.info("Coluna 'detalhes' já existe na tabela fontes")
        except sqlite3.OperationalError:
            logger.info("Adicionando coluna 'detalhes' à tabela fontes")
            cursor.execute("ALTER TABLE fontes ADD COLUMN detalhes TEXT")
            
        conn.commit()
        logger.info("Migração concluída com sucesso")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro durante a migração: {str(e)}")
        
    finally:
        conn.close()

# Inicializa o banco de dados se o arquivo for executado diretamente
if __name__ == "__main__":
    init_db()
    migrar_banco()
