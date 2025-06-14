import logging
import datetime
import os

# Configuração de logging para auditoria
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auditoria.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auditoria")

class AuditoriaManager:
    """
    Classe para gerenciar o registro detalhado de auditoria de todas as operações
    realizadas no sistema Onion Monitor.
    """
    
    def __init__(self, db_connection=None):
        """
        Inicializa o gerenciador de auditoria.
        
        Args:
            db_connection: Conexão com o banco de dados (opcional)
        """
        self.db_connection = db_connection
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        
        # Cria o diretório de logs se não existir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def registrar_evento(self, tipo_evento, descricao, dados=None, usuario=None):
        """
        Registra um evento de auditoria no banco de dados e no arquivo de log.
        
        Args:
            tipo_evento (str): Tipo do evento (busca, validacao, exportacao, etc.)
            descricao (str): Descrição detalhada do evento
            dados (dict, optional): Dados adicionais relacionados ao evento
            usuario (str, optional): Identificação do usuário que realizou a ação
        """
        timestamp = datetime.datetime.now()
        
        # Formata os dados para o log
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'tipo_evento': tipo_evento,
            'descricao': descricao,
            'dados': dados,
            'usuario': usuario or 'sistema'
        }
        
        # Registra no log
        logger.info(f"AUDITORIA: {tipo_evento} - {descricao}")
        
        # Registra no arquivo de log específico para o tipo de evento
        self._registrar_em_arquivo(tipo_evento, log_entry)
        
        # Registra no banco de dados se houver conexão
        if self.db_connection:
            self._registrar_em_banco(tipo_evento, descricao, dados, usuario, timestamp)
    
    def _registrar_em_arquivo(self, tipo_evento, log_entry):
        """
        Registra o evento em um arquivo de log específico para o tipo.
        
        Args:
            tipo_evento (str): Tipo do evento
            log_entry (dict): Dados do evento
        """
        log_file = os.path.join(self.log_dir, f"{tipo_evento}.log")
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry['timestamp']} - {log_entry['usuario']} - {log_entry['descricao']}")
                if log_entry['dados']:
                    f.write(f" - Dados: {log_entry['dados']}")
                f.write("\n")
        except Exception as e:
            logger.error(f"Erro ao registrar em arquivo de log: {str(e)}")
    
    def _registrar_em_banco(self, tipo_evento, descricao, dados, usuario, timestamp):
        """
        Registra o evento no banco de dados.
        
        Args:
            tipo_evento (str): Tipo do evento
            descricao (str): Descrição do evento
            dados (dict): Dados adicionais
            usuario (str): Identificação do usuário
            timestamp (datetime): Data e hora do evento
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Converte dados para string se não for None
            dados_str = str(dados) if dados else None
            
            cursor.execute(
                'INSERT INTO auditoria (acao, descricao, dados, data_registro) VALUES (?, ?, ?, ?)',
                (tipo_evento, descricao, dados_str, timestamp)
            )
            
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar em banco de dados: {str(e)}")
    
    def obter_eventos(self, tipo_evento=None, data_inicio=None, data_fim=None, limite=1000):
        """
        Obtém eventos de auditoria do banco de dados com filtros.
        
        Args:
            tipo_evento (str, optional): Filtrar por tipo de evento
            data_inicio (str, optional): Data de início (formato YYYY-MM-DD)
            data_fim (str, optional): Data de fim (formato YYYY-MM-DD)
            limite (int, optional): Limite de registros a retornar
            
        Returns:
            list: Lista de eventos de auditoria
        """
        if not self.db_connection:
            logger.error("Sem conexão com o banco de dados para obter eventos")
            return []
        
        try:
            cursor = self.db_connection.cursor()
            
            query = 'SELECT * FROM auditoria WHERE 1=1'
            params = []
            
            if tipo_evento:
                query += ' AND acao = ?'
                params.append(tipo_evento)
            
            if data_inicio:
                query += ' AND DATE(data_registro) >= DATE(?)'
                params.append(data_inicio)
            
            if data_fim:
                query += ' AND DATE(data_registro) <= DATE(?)'
                params.append(data_fim)
            
            query += ' ORDER BY data_registro DESC LIMIT ?'
            params.append(limite)
            
            cursor.execute(query, params)
            eventos = [dict(evento) for evento in cursor.fetchall()]
            
            return eventos
        except Exception as e:
            logger.error(f"Erro ao obter eventos de auditoria: {str(e)}")
            return []
    
    def exportar_eventos(self, arquivo_saida, tipo_evento=None, data_inicio=None, data_fim=None):
        """
        Exporta eventos de auditoria para um arquivo CSV.
        
        Args:
            arquivo_saida (str): Caminho do arquivo de saída
            tipo_evento (str, optional): Filtrar por tipo de evento
            data_inicio (str, optional): Data de início (formato YYYY-MM-DD)
            data_fim (str, optional): Data de fim (formato YYYY-MM-DD)
            
        Returns:
            bool: True se a exportação foi bem-sucedida, False caso contrário
        """
        eventos = self.obter_eventos(tipo_evento, data_inicio, data_fim, limite=10000)
        
        if not eventos:
            logger.warning("Nenhum evento para exportar")
            return False
        
        try:
            import csv
            
            with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'acao', 'descricao', 'dados', 'data_registro'])
                writer.writeheader()
                writer.writerows(eventos)
            
            logger.info(f"Exportados {len(eventos)} eventos para {arquivo_saida}")
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar eventos: {str(e)}")
            return False
    
    def gerar_relatorio_atividade(self, periodo='dia'):
        """
        Gera um relatório de atividade para o período especificado.
        
        Args:
            periodo (str): 'dia', 'semana' ou 'mes'
            
        Returns:
            dict: Relatório de atividade
        """
        if not self.db_connection:
            logger.error("Sem conexão com o banco de dados para gerar relatório")
            return {}
        
        try:
            cursor = self.db_connection.cursor()
            
            # Define o filtro de data com base no período
            hoje = datetime.date.today()
            
            if periodo == 'dia':
                data_inicio = hoje.strftime('%Y-%m-%d')
                data_fim = hoje.strftime('%Y-%m-%d')
            elif periodo == 'semana':
                data_inicio = (hoje - datetime.timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')
                data_fim = hoje.strftime('%Y-%m-%d')
            elif periodo == 'mes':
                data_inicio = hoje.replace(day=1).strftime('%Y-%m-%d')
                data_fim = hoje.strftime('%Y-%m-%d')
            else:
                logger.error(f"Período inválido: {periodo}")
                return {}
            
            # Contagem por tipo de evento
            cursor.execute('''
                SELECT acao, COUNT(*) as quantidade
                FROM auditoria
                WHERE DATE(data_registro) BETWEEN ? AND ?
                GROUP BY acao
                ORDER BY quantidade DESC
            ''', (data_inicio, data_fim))
            
            contagem_por_tipo = [dict(row) for row in cursor.fetchall()]
            
            # Total de eventos
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM auditoria
                WHERE DATE(data_registro) BETWEEN ? AND ?
            ''', (data_inicio, data_fim))
            
            total_eventos = cursor.fetchone()[0]
            
            # Eventos por dia
            cursor.execute('''
                SELECT DATE(data_registro) as data, COUNT(*) as quantidade
                FROM auditoria
                WHERE DATE(data_registro) BETWEEN ? AND ?
                GROUP BY DATE(data_registro)
                ORDER BY data
            ''', (data_inicio, data_fim))
            
            eventos_por_dia = [dict(row) for row in cursor.fetchall()]
            
            relatorio = {
                'periodo': periodo,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'total_eventos': total_eventos,
                'contagem_por_tipo': contagem_por_tipo,
                'eventos_por_dia': eventos_por_dia
            }
            
            return relatorio
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de atividade: {str(e)}")
            return {}

# Função auxiliar para obter uma instância do gerenciador de auditoria
def get_auditoria_manager(db_connection=None):
    """
    Obtém uma instância do gerenciador de auditoria.
    
    Args:
        db_connection: Conexão com o banco de dados (opcional)
        
    Returns:
        AuditoriaManager: Instância do gerenciador de auditoria
    """
    return AuditoriaManager(db_connection)

# Créditos
"""
Desenvolvido por Luiz Vaisconcelos
Email: luiz.vaisconcelos@gmail.com
LinkedIn: https://www.linkedin.com/in/vaisconcelos/
GitHub: https://github.com/luizhvaisconcelos
"""
