import sqlite3
import logging
import os
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migrate_db")

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

def migrate_database():
    """
    Migra o banco de dados para a versão mais recente.
    """
    logger.info("Iniciando migração do banco de dados...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se a tabela coletas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coletas'")
        if not cursor.fetchone():
            logger.error("Tabela 'coletas' não encontrada. Banco de dados pode estar corrompido.")
            return False
        
        # Verifica se a tabela fontes existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fontes'")
        if not cursor.fetchone():
            logger.info("Tabela 'fontes' não encontrada. Criando tabela...")
            cursor.execute('''
                CREATE TABLE fontes (
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
            
            # Insere fontes padrão
            fontes_padrao = [
                ('Ahmia', 'https://ahmia.fi/', 'surface', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Dark.fail', 'https://dark.fail/', 'lista', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Onion.live', 'https://onion.live/', 'lista', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Tor.taxi', 'https://tor.taxi/', 'lista', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('Onion.land', 'https://onion.land/', 'lista', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo'),
                ('DarkSearch', 'https://darksearch.io/', 'surface', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ativo')
            ]
            
            cursor.executemany(
                'INSERT INTO fontes (nome, url, tipo, ativo, ultimo_check, status) VALUES (?, ?, ?, ?, ?, ?)',
                fontes_padrao
            )
            
            logger.info(f"Cadastradas {len(fontes_padrao)} fontes padrão.")
        
        # Verifica se a coluna fonte_id existe na tabela coletas
        cursor.execute("PRAGMA table_info(coletas)")
        colunas = cursor.fetchall()
        colunas_nomes = [coluna['name'] for coluna in colunas]
        
        if 'fonte_id' not in colunas_nomes:
            logger.info("Coluna 'fonte_id' não encontrada na tabela 'coletas'. Adicionando coluna...")
            
            # Cria uma tabela temporária com a nova estrutura
            cursor.execute('''
                CREATE TABLE coletas_temp (
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
            
            # Copia os dados da tabela antiga para a nova, definindo fonte_id=1 (Ahmia) para registros existentes
            cursor.execute('''
                INSERT INTO coletas_temp (
                    id, termo_busca, link_encontrado, titulo, descricao, 
                    data_coleta, validado, score_validacao, metodo_validacao, 
                    observacoes_validacao, data_validacao, fonte_id
                )
                SELECT 
                    id, termo_busca, link_encontrado, titulo, descricao, 
                    data_coleta, validado, score_validacao, metodo_validacao, 
                    observacoes_validacao, data_validacao, 1
                FROM coletas
            ''')
            
            # Remove a tabela antiga
            cursor.execute("DROP TABLE coletas")
            
            # Renomeia a tabela temporária
            cursor.execute("ALTER TABLE coletas_temp RENAME TO coletas")
            
            logger.info("Coluna 'fonte_id' adicionada com sucesso à tabela 'coletas'.")
        
        # Verifica se a tabela auditoria existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditoria'")
        if not cursor.fetchone():
            logger.info("Tabela 'auditoria' não encontrada. Criando tabela...")
            cursor.execute('''
                CREATE TABLE auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acao TEXT NOT NULL,
                    descricao TEXT,
                    dados TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Tabela 'auditoria' criada com sucesso.")
        
        # Verifica se a tabela status_fontes existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='status_fontes'")
        if not cursor.fetchone():
            logger.info("Tabela 'status_fontes' não encontrada. Criando tabela...")
            cursor.execute('''
                CREATE TABLE status_fontes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fonte_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    data_verificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detalhes TEXT,
                    FOREIGN KEY (fonte_id) REFERENCES fontes (id)
                )
            ''')
            logger.info("Tabela 'status_fontes' criada com sucesso.")
        
        # Verifica se a coluna ultimo_check existe na tabela fontes
        cursor.execute("PRAGMA table_info(fontes)")
        colunas = cursor.fetchall()
        colunas_nomes = [coluna['name'] for coluna in colunas]
        
        if 'ultimo_check' not in colunas_nomes:
            logger.info("Coluna 'ultimo_check' não encontrada na tabela 'fontes'. Adicionando coluna...")
            cursor.execute("ALTER TABLE fontes ADD COLUMN ultimo_check TIMESTAMP")
            logger.info("Coluna 'ultimo_check' adicionada com sucesso à tabela 'fontes'.")
        
        # Verifica se a coluna status existe na tabela fontes
        if 'status' not in colunas_nomes:
            logger.info("Coluna 'status' não encontrada na tabela 'fontes'. Adicionando coluna...")
            cursor.execute("ALTER TABLE fontes ADD COLUMN status TEXT DEFAULT 'ativo'")
            logger.info("Coluna 'status' adicionada com sucesso à tabela 'fontes'.")
        
        # Atualiza todas as fontes para status ativo se não tiver valor
        cursor.execute("UPDATE fontes SET status = 'ativo' WHERE status IS NULL")
        
        conn.commit()
        logger.info("Migração do banco de dados concluída com sucesso.")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro durante a migração do banco de dados: {str(e)}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
