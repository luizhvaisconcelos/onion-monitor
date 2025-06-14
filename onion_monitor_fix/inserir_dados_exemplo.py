import sqlite3
import datetime
import os

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

def inserir_dados_exemplo():
    """
    Insere dados de exemplo no banco de dados para demonstração.
    """
    print("Inserindo dados de exemplo no banco de dados...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se já existem dados na tabela coletas
        cursor.execute('SELECT COUNT(*) FROM coletas')
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Já existem {count} registros na tabela coletas. Pulando inserção de dados de exemplo.")
            return
        
        # Obtém as fontes disponíveis
        cursor.execute('SELECT id, nome FROM fontes')
        fontes = cursor.fetchall()
        
        if not fontes:
            print("Nenhuma fonte encontrada. Verifique a tabela de fontes.")
            return
        
        # Dados de exemplo para inserção
        dados_exemplo = [
            # Termo, Link, Título, Descrição, Fonte ID
            ("senha vazada", "http://abcdefghijklmnopqrstuvwxyzabcdef.onion/leaked_data", "Vazamento de senhas corporativas", "Conjunto de credenciais vazadas de empresas de tecnologia", 1),
            ("cartão de crédito", "http://3g2upl4pq6kufc4m.onion/search/cc_dump", "Dump de cartões de crédito", "Dados de cartões de crédito vazados de e-commerce", 2),
            ("dados pessoais", "http://zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion/wiki/index.php/Main_Page", "Informações pessoais expostas", "Documentos com dados pessoais vazados", 3),
            ("banco de dados", "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/", "Vazamento de banco de dados", "Banco de dados SQL completo com informações de clientes", 1),
            ("documentos confidenciais", "http://hss3uro2hsxfogfq.onion/", "Documentos confidenciais vazados", "Arquivos internos de empresa de segurança", 2),
            ("lista de emails", "http://underdj5ziov3ic7.onion/", "Lista de emails corporativos", "Emails e senhas de funcionários", 3),
            ("código fonte", "http://deepdot35wvmeyd5.onion/", "Código fonte vazado", "Repositório de código fonte de aplicativo bancário", 1),
            ("chaves privadas", "http://76qugh5bey5gum7l.onion/", "Chaves privadas expostas", "Chaves criptográficas de servidores", 2),
            ("credenciais", "http://jdpskjmgy6kk4urv.onion/", "Credenciais de acesso VPN", "Usuários e senhas de VPN corporativa", 3),
            ("informações financeiras", "http://vfqnd6mieccqyiit.onion/", "Dados financeiros vazados", "Relatórios financeiros e dados bancários", 1)
        ]
        
        # Data atual e datas anteriores para simular coletas em diferentes momentos
        data_atual = datetime.datetime.now()
        
        # Insere os dados de exemplo
        for i, (termo, link, titulo, descricao, fonte_id) in enumerate(dados_exemplo):
            # Calcula uma data no passado (entre 1 e 30 dias atrás)
            dias_atras = (i % 30) + 1
            data_coleta = (data_atual - datetime.timedelta(days=dias_atras)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Alguns registros serão validados, outros não
            validado = 1 if i % 3 == 0 else 0
            score = 85 if validado else 0
            metodo = "automático" if validado else None
            observacoes = "Validado pelo sistema" if validado else None
            data_validacao = data_coleta if validado else None
            
            cursor.execute(
                '''
                INSERT INTO coletas (
                    termo_busca, link_encontrado, titulo, descricao, fonte_id,
                    data_coleta, validado, score_validacao, metodo_validacao,
                    observacoes_validacao, data_validacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (termo, link, titulo, descricao, fonte_id, data_coleta, validado, 
                 score, metodo, observacoes, data_validacao)
            )
            
            # Registra a ação no log de auditoria
            cursor.execute(
                'INSERT INTO auditoria (acao, descricao, dados) VALUES (?, ?, ?)',
                (
                    "inserir_exemplo" if not validado else "validar_exemplo",
                    f"Inserção de dados de exemplo para o termo '{termo}'",
                    f"Link: {link}, Fonte ID: {fonte_id}, Validado: {validado}"
                )
            )
        
        conn.commit()
        print(f"Inseridos {len(dados_exemplo)} registros de exemplo com sucesso.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir dados de exemplo: {str(e)}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    inserir_dados_exemplo()

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
