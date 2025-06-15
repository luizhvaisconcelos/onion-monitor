import os
import logging
import csv
import datetime
import json
import io
from io import TextIOWrapper
from db import (
    init_db, get_db_connection, obter_fontes, adicionar_fonte, 
    registrar_coleta, registrar_validacao, obter_coletas, obter_resultados,
    obter_estatisticas_validacao, exportar_coletas_csv, 
    registrar_auditoria, obter_registros_auditoria
)
from coletor import buscar_termo, validar_vazamento_rigoroso, verificar_status_fonte, buscar_em_todas_fontes
from busca_valida_semantica import buscar_e_validar_termo, validar_semanticamente
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app")

# Inicializa o aplicativo Flask
app = Flask(__name__)
app.secret_key = 'onion_monitor_v2_secret_key'

# Inicializa o banco de dados
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    """Página inicial com busca e resultados."""
    termo = request.args.get('termo', '')
    
    # Se o formulário for enviado via POST, redireciona para GET com o termo como parâmetro
    if request.method == 'POST':
        termo = request.form.get('termo', '')
        return redirect(url_for('index', termo=termo))
    
    resultados = []
    resultados_validados = 0
    
    if termo:
        # Registra a ação de busca
        registrar_auditoria(
            acao="iniciar_busca",
            descricao=f"Busca iniciada para o termo: {termo}",
            dados=f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Realiza a busca
        resultados = buscar_em_todas_fontes(termo, usar_validacao_semantica=True)
        
        # Conta resultados validados
        resultados_validados = sum(1 for r in resultados if r.get('validado', False))
        
        # Registra a conclusão da busca
        registrar_auditoria(
            acao="concluir_busca_interface",
            descricao=f"Busca concluída na interface para o termo: {termo}",
            dados=f"Total de resultados: {len(resultados)}, Validados: {resultados_validados}"
        )
    
    return render_template('index.html', 
                          termo=termo, 
                          resultados=resultados, 
                          resultados_validados=resultados_validados,
                          total_resultados=len(resultados))

@app.route('/resultados')
def resultados():
    """Página de resultados de validação semântica."""
    termo = request.args.get('termo', '')
    
    # Obtém os resultados de validação semântica
    resultados_semanticos = obter_resultados(termo=termo, limite=100)
    
    return render_template('resultados.html', 
                          termo=termo, 
                          resultados=resultados_semanticos)

@app.route('/analise')
def analise():
    """Página de análise de dados."""
    # Obtém estatísticas de validação
    estatisticas = obter_estatisticas_validacao()
    
    return render_template('analise.html', estatisticas=estatisticas)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Página de cadastro de fontes."""
    mensagem = None
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        url = request.form.get('url')
        tipo = request.form.get('tipo')
        ativo = request.form.get('ativo') == 'on'
        
        if nome and url and tipo:
            # Adiciona a fonte
            fonte_id = adicionar_fonte(nome, url, tipo, ativo)
            
            if fonte_id:
                flash('Fonte adicionada com sucesso!', 'success')
                return redirect(url_for('cadastro'))
            else:
                flash('Erro ao adicionar fonte.', 'danger')
        else:
            flash('Preencha todos os campos obrigatórios.', 'warning')
    
    # Obtém a lista de fontes
    fontes = obter_fontes()
    
    return render_template('cadastro.html', fontes=fontes, mensagem=mensagem)

@app.route('/ferramentas')
def ferramentas():
    """Página de ferramentas."""
    # Obtém a lista de fontes
    fontes = obter_fontes()
    
    return render_template('ferramentas.html', fontes=fontes)

@app.route('/verificar-fonte', methods=['POST'])
def verificar_fonte():
    """Verifica o status de uma fonte."""
    fonte_id = request.form.get('fonte_id')
    url = request.form.get('url')
    
    if fonte_id and url:
        try:
            # Verifica o status da fonte
            status, detalhes = verificar_status_fonte(int(fonte_id), url)
            
            return jsonify({
                'success': True,
                'status': status,
                'detalhes': detalhes
            })
        except Exception as e:
            logger.error(f"Erro ao verificar fonte: {str(e)}")
            
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': False,
            'error': 'Parâmetros inválidos'
        })

@app.route('/validar-link', methods=['POST'])
def validar_link():
    """Valida um link manualmente."""
    link = request.form.get('link')
    titulo = request.form.get('titulo')
    descricao = request.form.get('descricao')
    
    if link and titulo and descricao:
        try:
            # Valida o link
            validado, score, metodo, observacoes = validar_vazamento_rigoroso(link, titulo, descricao)
            
            return jsonify({
                'success': True,
                'validado': validado,
                'score': score,
                'metodo': metodo,
                'observacoes': observacoes
            })
        except Exception as e:
            logger.error(f"Erro ao validar link: {str(e)}")
            
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': False,
            'error': 'Parâmetros inválidos'
        })

@app.route('/exportar-csv')
def exportar_csv():
    """Exporta as coletas para um arquivo CSV."""
    try:
        # Exporta as coletas
        output = exportar_coletas_csv()
        
        if output:
            # Registra a ação de exportação
            registrar_auditoria(
                acao="exportar_csv",
                descricao="Exportação de coletas para CSV",
                dados=None
            )
            
            return Response(
                output,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=coletas.csv"}
            )
        else:
            flash('Erro ao exportar coletas.', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {str(e)}")
        flash(f'Erro ao exportar: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/exportar-auditoria')
def exportar_auditoria():
    """Exporta os registros de auditoria para um arquivo CSV."""
    try:
        # Obtém os registros de auditoria
        registros = obter_registros_auditoria(limite=1000)
        
        # Cria um buffer de memória para o CSV
        output = io.BytesIO()
        output.write(b'\xef\xbb\xbf')  # BOM UTF-8
        
        # Cria um wrapper de texto para o CSV
        text_output = TextIOWrapper(output, encoding='utf-8', newline='', write_through=True)
        
        # Cria o escritor CSV
        writer = csv.writer(text_output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Escreve o cabeçalho
        writer.writerow(['ID', 'Ação', 'Descrição', 'Dados', 'Data Registro'])
        
        # Escreve os dados
        for registro in registros:
            writer.writerow([
                registro['id'],
                registro['acao'],
                registro['descricao'],
                registro['dados'],
                registro['data_registro']
            ])
        
        # Retorna ao início do buffer
        output.seek(0)
        
        # Registra a ação de exportação
        registrar_auditoria(
            acao="exportar_auditoria",
            descricao="Exportação de registros de auditoria para CSV",
            dados=None
        )
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=auditoria.csv"}
        )
    except Exception as e:
        logger.error(f"Erro ao exportar auditoria: {str(e)}")
        flash(f'Erro ao exportar: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/busca-semantica', methods=['POST'])
def busca_semantica():
    """Realiza uma busca semântica em uma URL específica."""
    termo = request.form.get('termo')
    url = request.form.get('url')
    
    if termo and url:
        try:
            # Realiza a busca semântica
            resultado = buscar_e_validar_termo(termo, url, usar_proxy=False)
            
            return jsonify({
                'success': True,
                'resultado': resultado
            })
        except Exception as e:
            logger.error(f"Erro na busca semântica: {str(e)}")
            
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': False,
            'error': 'Parâmetros inválidos'
        })

@app.route('/agendar-busca')
def agendar_busca():
    """Página de agendamento de buscas."""
    return render_template('agendar_busca.html')

@app.route('/instrucoes-agendamento')
def instrucoes_agendamento():
    """Página de instruções para agendamento de buscas."""
    return render_template('instrucoes_agendamento.html')

@app.route('/registros')
def registros_auditoria():
    """Página de registros de auditoria."""
    # Obtém os registros de auditoria
    registros = obter_registros_auditoria(limite=100)
    
    return render_template('registros.html', registros=registros)

@app.route('/relatorio-auditoria')
def relatorio_auditoria():
    """Página de relatório de auditoria."""
    # Obtém os registros de auditoria
    registros = obter_registros_auditoria(limite=1000)
    
    # Agrupa os registros por ação
    acoes = {}
    for registro in registros:
        acao = registro['acao']
        if acao not in acoes:
            acoes[acao] = []
        acoes[acao].append(registro)
    
    return render_template('relatorio_auditoria.html', acoes=acoes, registros=registros)

@app.route('/api/buscar', methods=['POST'])
def api_buscar():
    """API para busca de termos."""
    data = request.get_json()
    
    if not data or 'termo' not in data:
        return jsonify({
            'success': False,
            'error': 'Parâmetro "termo" obrigatório'
        }), 400
    
    termo = data['termo']
    usar_validacao_semantica = data.get('validacao_semantica', True)
    
    try:
        # Realiza a busca
        resultados = buscar_em_todas_fontes(termo, usar_validacao_semantica=usar_validacao_semantica)
        
        return jsonify({
            'success': True,
            'termo': termo,
            'resultados': resultados,
            'total': len(resultados),
            'validados': sum(1 for r in resultados if r.get('validado', False))
        })
    except Exception as e:
        logger.error(f"Erro na API de busca: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fontes', methods=['GET'])
def api_fontes():
    """API para obtenção de fontes."""
    try:
        # Obtém as fontes
        fontes = obter_fontes(apenas_ativas=request.args.get('apenas_ativas') == '1')
        
        return jsonify({
            'success': True,
            'fontes': fontes,
            'total': len(fontes)
        })
    except Exception as e:
        logger.error(f"Erro na API de fontes: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/estatisticas', methods=['GET'])
def api_estatisticas():
    """API para obtenção de estatísticas."""
    try:
        # Obtém as estatísticas
        estatisticas = obter_estatisticas_validacao()
        
        return jsonify({
            'success': True,
            'estatisticas': estatisticas
        })
    except Exception as e:
        logger.error(f"Erro na API de estatísticas: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos


from db import verificar_status_fontes

@app.route('/verificar_fontes')
def rota_verificar_fontes():
    verificar_status_fontes()
    return redirect(url_for('fontes'))  # Ajuste se a rota real for diferente