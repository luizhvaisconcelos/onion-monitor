import sqlite3
import logging
import datetime
import json
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auditoria.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integracao_auditoria")

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
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def obter_relatorio_auditoria(periodo):
    """
    Obtém um relatório de auditoria para o período especificado.
    
    Args:
        periodo (str): Período do relatório ('hoje', 'semana', 'mes', 'tudo')
        
    Returns:
        dict: Relatório de auditoria
    """
    logger.info(f"Gerando relatório de auditoria para o período: {periodo}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Define a data de início com base no período
        data_inicio = None
        
        if periodo == 'hoje':
            # Corrigido para usar apenas a data, sem o horário, para capturar todos os eventos do dia atual
            data_inicio = datetime.datetime.now().strftime('%Y-%m-%d')
        elif periodo == 'semana':
            data_inicio = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        elif periodo == 'mes':
            data_inicio = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        elif periodo == 'total':
            # Não define data_inicio para obter todos os registros
            pass
        
        # Constrói a consulta SQL
        query = 'SELECT * FROM auditoria'
        params = []
        
        if data_inicio:
            # Corrigido para usar DATE() para comparar apenas a parte da data e o campo correto data_registro
            query += ' WHERE DATE(data_registro) >= DATE(?)'
            params.append(data_inicio)
        
        query += ' ORDER BY data_registro DESC'
        
        # Executa a consulta
        cursor.execute(query, params)
        eventos = cursor.fetchall()
        
        # Converte para lista de dicionários
        eventos_lista = []
        for evento in eventos:
            evento_dict = dict(evento)
            eventos_lista.append(evento_dict)
        
        # Contagem por tipo de ação
        if data_inicio:
            count_query = '''
                SELECT acao, COUNT(*) as quantidade
                FROM auditoria
                WHERE DATE(data_registro) >= DATE(?)
                GROUP BY acao
                ORDER BY quantidade DESC
            '''
        else:
            count_query = '''
                SELECT acao, COUNT(*) as quantidade
                FROM auditoria
                GROUP BY acao
                ORDER BY quantidade DESC
            '''
        
        cursor.execute(count_query, params if data_inicio else [])
        
        contagem_por_tipo = []
        for tipo in cursor.fetchall():
            contagem_por_tipo.append(dict(tipo))
        
        # Total de eventos
        total_eventos = len(eventos_lista)
        
        # Se não houver eventos, cria um registro de exemplo para evitar página em branco
        if total_eventos == 0:
            # Registra um evento de visualização para garantir que haja pelo menos um registro
            registrar_auditoria(
                acao="visualizacao_relatorio",
                descricao=f"Visualização do relatório de auditoria para o período '{periodo}'",
                dados=f"Período: {periodo}, Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Busca novamente os eventos após registrar o evento de visualização
            cursor.execute(query, params)
            eventos = cursor.fetchall()
            
            eventos_lista = []
            for evento in eventos:
                evento_dict = dict(evento)
                eventos_lista.append(evento_dict)
            
            # Atualiza a contagem por tipo
            cursor.execute(count_query, params if data_inicio else [])
            
            contagem_por_tipo = []
            for tipo in cursor.fetchall():
                contagem_por_tipo.append(dict(tipo))
            
            # Atualiza o total de eventos
            total_eventos = len(eventos_lista)
        
        # Monta o relatório
        relatorio = {
            'periodo': periodo,
            'data_inicio': data_inicio,
            'data_fim': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_eventos': total_eventos,
            'contagem_por_tipo': contagem_por_tipo,
            'eventos': eventos_lista
        }
        
        logger.info(f"Relatório gerado com sucesso: {total_eventos} eventos")
        
        return relatorio
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de auditoria: {str(e)}")
        return {
            'periodo': periodo,
            'erro': str(e),
            'total_eventos': 0,
            'contagem_por_tipo': [],
            'eventos': []
        }
    
    finally:
        conn.close()

def exportar_relatorio_csv(periodo, filepath):
    """
    Exporta um relatório de auditoria para CSV com codificação UTF-8 e BOM para compatibilidade com Excel.
    
    Args:
        periodo (str): Período do relatório ('hoje', 'semana', 'mes', 'tudo')
        filepath (str): Caminho do arquivo CSV
    """
    logger.info(f"Exportando relatório de auditoria para CSV: {filepath}")
    
    relatorio = obter_relatorio_auditoria(periodo)
    
    try:
        import csv
        from io import BytesIO
        
        # Usar BytesIO para lidar com bytes em vez de strings
        with open(filepath, 'wb') as csvfile:
            # Adicionar BOM UTF-8 para garantir que o Excel reconheça corretamente os caracteres
            csvfile.write(b'\xef\xbb\xbf')
            
            # Reabrir o arquivo para escrita de texto após escrever o BOM
            csvfile.close()
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                # Define os campos do CSV
                fieldnames = ['id', 'data_registro', 'acao', 'descricao', 'dados', 'usuario']
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for evento in relatorio['eventos']:
                    # Escreve cada evento como uma linha no CSV
                    writer.writerow({
                        'id': evento['id'],
                        'data_registro': evento.get('data_registro', ''),
                        'acao': evento['acao'],
                        'descricao': evento['descricao'],
                        'dados': evento['dados'],
                        'usuario': evento.get('usuario', 'sistema')
                    })
        
        logger.info(f"Exportados {len(relatorio['eventos'])} eventos para {filepath}")
        
    except Exception as e:
        logger.error(f"Erro ao exportar relatório para CSV: {str(e)}")
        raise

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
