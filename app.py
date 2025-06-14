import sqlite3
import os
import logging
import csv
import datetime
import json
from db import (
    init_db, get_db_connection, obter_fontes, adicionar_fonte, 
    registrar_coleta, registrar_validacao, obter_coletas, 
    obter_estatisticas_validacao, exportar_coletas_csv, 
    registrar_auditoria, obter_registros_auditoria
)
from coletor import buscar_termo, validar_vazamento, verificar_status_fonte
from integracao_auditoria import obter_relatorio_auditoria, exportar_relatorio_csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify

# Inicializa o aplicativo Flask
app = Flask(__name__)
app.secret_key = 'onion_monitor_v1_secret_key'

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
        resultados = buscar_termo(termo)
        
        # Conta resultados validados
        resultados_validados = 0
        for r in resultados:
            try:
                if r['validado'] == 1:
                    resultados_validados += 1
            except (KeyError, TypeError):
                pass
        
        # Registra a conclusão da busca
        registrar_auditoria(
            acao="concluir_busca",
            descricao=f"Busca concluída para o termo: {termo}",
            dados=f"Resultados: {len(resultados)}, Validados: {resultados_validados}"
        )
    
    return render_template('index.html', resultados=resultados, termo=termo, resultados_validados=resultados_validados)

@app.route('/analise')
def analise():
    """Página de análise de dados coletados."""
    # Obtém estatísticas de validação
    estatisticas = obter_estatisticas_validacao()
    
    # Obtém contagem por fonte
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Contagem total de coletas
        cursor.execute('SELECT COUNT(*) FROM coletas')
        total_coletas = cursor.fetchone()[0]
        
        # Total de validados
        cursor.execute('SELECT COUNT(*) FROM coletas WHERE validado = 1')
        total_validados = cursor.fetchone()[0]
        
        # Total de termos únicos
        cursor.execute('SELECT COUNT(DISTINCT termo_busca) FROM coletas')
        total_termos = cursor.fetchone()[0]
        
        # Total de fontes ativas
        cursor.execute('SELECT COUNT(*) FROM fontes WHERE ativo = 1')
        total_fontes = cursor.fetchone()[0]
        
        # Contagem por fonte
        cursor.execute('''
            SELECT f.nome as fonte_nome, COUNT(*) as quantidade
            FROM coletas c
            JOIN fontes f ON c.fonte_id = f.id
            GROUP BY f.nome
            ORDER BY quantidade DESC
        ''')
        
        coletas_por_fonte = []
        for fonte in cursor.fetchall():
            coletas_por_fonte.append(dict(fonte))
        
        # Contagem por termo
        cursor.execute('''
            SELECT termo_busca, COUNT(*) as quantidade
            FROM coletas
            GROUP BY termo_busca
            ORDER BY quantidade DESC
            LIMIT 10
        ''')
        
        coletas_por_termo = []
        for termo in cursor.fetchall():
            coletas_por_termo.append(dict(termo))
        
        # Contagem por dia
        cursor.execute('''
            SELECT DATE(data_coleta) as data, COUNT(*) as quantidade
            FROM coletas
            GROUP BY DATE(data_coleta)
            ORDER BY data DESC
            LIMIT 30
        ''')
        
        coletas_por_dia = []
        for dia in cursor.fetchall():
            coletas_por_dia.append(dict(dia))
        
        # Últimas validadas
        cursor.execute('''
            SELECT c.*, f.nome as fonte_nome
            FROM coletas c
            JOIN fontes f ON c.fonte_id = f.id
            WHERE c.validado = 1
            ORDER BY c.data_validacao DESC
            LIMIT 10
        ''')
        
        ultimas_validadas = []
        for validada in cursor.fetchall():
            ultimas_validadas.append(dict(validada))
        
        # Registra a ação de análise
        registrar_auditoria(
            acao="visualizar_analise",
            descricao="Visualização da página de análise",
            dados=f"Estatísticas: {estatisticas['validados']} validados, {estatisticas['nao_validados']} não validados"
        )
        
        return render_template(
            'analise.html', 
            estatisticas=estatisticas,
            total_coletas=total_coletas,
            total_validados=total_validados,
            total_termos=total_termos,
            total_fontes=total_fontes,
            coletas_por_fonte=coletas_por_fonte,
            coletas_por_termo=coletas_por_termo,
            coletas_por_dia=coletas_por_dia,
            ultimas_validadas=ultimas_validadas
        )
        
    except Exception as e:
        flash(f"Erro ao carregar análises: {str(e)}", "danger")
        return render_template('analise.html', estatisticas=estatisticas)
    
    finally:
        conn.close()

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Página de cadastro de fontes."""
    if request.method == 'POST':
        nome = request.form.get('nome')
        url = request.form.get('url')
        tipo = request.form.get('tipo')
        ativo = request.form.get('ativo') == 'on'
        
        if not nome or not url or not tipo:
            flash("Todos os campos são obrigatórios!", "danger")
        else:
            try:
                adicionar_fonte(nome, url, tipo, ativo)
                flash(f"Fonte '{nome}' cadastrada com sucesso!", "success")
                return redirect(url_for('cadastro'))
            except Exception as e:
                flash(f"Erro ao cadastrar fonte: {str(e)}", "danger")
    
    # Obtém todas as fontes
    fontes = obter_fontes(apenas_ativas=False)
    
    # Registra a ação de visualização
    registrar_auditoria(
        acao="visualizar_cadastro",
        descricao="Visualização da página de cadastro de fontes",
        dados=f"Total de fontes: {len(fontes)}"
    )
    
    return render_template('cadastro.html', fontes=fontes)

@app.route('/exportar-csv')
def exportar_csv():
    """Exporta resultados para CSV."""
    termo = request.args.get('termo', '')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    apenas_validados = request.args.get('apenas_validados') == '1'
    
    # Cria um arquivo CSV em memória com BOM para UTF-8
    import io
    output = io.BytesIO()
    # Adiciona BOM (Byte Order Mark) para UTF-8
    output.write(b'\xef\xbb\xbf')
    
    # Obtém os resultados
    resultados = obter_coletas(termo, data_inicio, data_fim, apenas_validados)
    
    # Cria o escritor CSV com encoding UTF-8
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Escreve o cabeçalho
    writer.writerow([
        'ID', 'Data/Hora', 'Termo', 'Link', 'Título', 'Fonte', 
        'Validado', 'Score', 'Método', 'Observações'
    ])
    
    # Escreve os dados
    for r in resultados:
        fonte_nome = ''
        try:
            fonte_nome = r['fonte_nome']
        except (KeyError, IndexError):
            fonte_nome = 'Desconhecida'
            
        score = 0
        try:
            score = r['score_validacao']
        except (KeyError, IndexError):
            score = 0
            
        metodo = ''
        try:
            metodo = r['metodo_validacao']
        except (KeyError, IndexError):
            metodo = ''
            
        observacoes = ''
        try:
            observacoes = r['observacoes_validacao']
        except (KeyError, IndexError):
            observacoes = ''
            
        writer.writerow([
            r['id'],
            r['data_coleta'],
            r['termo_busca'],
            r['link_encontrado'],
            r['titulo'] or '',
            fonte_nome,
            'Sim' if r['validado'] == 1 else 'Não',
            score,
            metodo,
            observacoes
        ])
    
    # Configura a resposta
    output.seek(0)
    data_atual = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Registra a ação de exportação
    registrar_auditoria(
        acao="exportacao_csv",
        descricao=f"Exportação de resultados para CSV",
        dados=f"Termo: {termo}, Resultados: {len(resultados)}"
    )
    
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment;filename=onion_monitor_{data_atual}.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@app.route('/validar/<int:coleta_id>', methods=['POST'])
def validar(coleta_id):
    """Valida manualmente um resultado."""
    try:
        # Obtém a coleta
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM coletas WHERE id = ?', (coleta_id,))
        coleta = cursor.fetchone()
        conn.close()
        
        if not coleta:
            return jsonify({'success': False, 'message': 'Coleta não encontrada'})
        
        # Registra a validação manual
        registrar_validacao(
            coleta_id=coleta_id,
            validado=True,
            score_validacao=100,
            metodo_validacao='manual',
            observacoes='Validação manual pelo usuário'
        )
        
        # Registra a ação de validação manual
        registrar_auditoria(
            acao="validacao_manual",
            descricao=f"Validação manual de coleta ID {coleta_id}",
            dados=f"Link: {coleta['link_encontrado']}"
        )
        
        return jsonify({'success': True, 'message': 'Validação realizada com sucesso', 'score': 100})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

# Rota para validação manual via JavaScript
@app.route('/validar-manualmente/<int:id>', methods=['POST'])
def validar_manualmente(id):
    """Rota alternativa para validação manual via JavaScript."""
    return validar(id)

@app.route('/verificar-fonte/<int:fonte_id>')
def verificar_fonte(fonte_id):
    """Verifica o status de uma fonte."""
    try:
        # Obtém a fonte
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fontes WHERE id = ?', (fonte_id,))
        fonte = cursor.fetchone()
        conn.close()
        
        if not fonte:
            return jsonify({'success': False, 'message': 'Fonte não encontrada'})
        
        # Verifica o status
        status, detalhes = verificar_status_fonte(fonte['id'], fonte['url'])
        
        # Registra a ação de verificação
        registrar_auditoria(
            acao="verificar_fonte",
            descricao=f"Verificação de status da fonte ID {fonte['id']}",
            dados=f"Status: {status}, Detalhes: {detalhes}"
        )
        
        return jsonify({
            'success': True, 
            'message': 'Verificação realizada com sucesso',
            'status': status,
            'detalhes': detalhes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/relatorio-auditoria/<periodo>')
def relatorio_auditoria(periodo):
    """Página de relatório de auditoria."""
    # Obtém o relatório
    relatorio = obter_relatorio_auditoria(periodo)
    
    # Registra a ação de visualização
    registrar_auditoria(
        acao="visualizar_relatorio",
        descricao=f"Visualização do relatório de auditoria para o período '{periodo}'",
        dados=f"Total de eventos: {relatorio['total_eventos']}"
    )
    
    return render_template('relatorio_auditoria.html', relatorio=relatorio, periodo=periodo)

@app.route('/exportar-auditoria/<periodo>')
def exportar_auditoria(periodo):
    """Exporta relatório de auditoria para CSV."""
    # Obtém o relatório
    relatorio = obter_relatorio_auditoria(periodo)
    
    # Cria um arquivo CSV em memória com BOM para UTF-8
    import io
    output = io.BytesIO()
    # Adiciona BOM (Byte Order Mark) para UTF-8
    output.write(b'\xef\xbb\xbf')
    
    # Cria o escritor CSV com encoding UTF-8
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Escreve o cabeçalho
    writer.writerow(['Tipo', 'Quantidade', 'Percentual'])
    
    # Escreve os dados
    for tipo in relatorio.get('contagem_por_tipo', []):
        try:
            acao = tipo['acao'] if 'acao' in tipo else tipo[0]
            quantidade = tipo['quantidade'] if 'quantidade' in tipo else tipo[1]
            percentual = round((quantidade / relatorio['total_eventos'] * 100), 1) if relatorio['total_eventos'] > 0 else 0
            writer.writerow([acao, quantidade, f"{percentual}%"])
        except (KeyError, IndexError, TypeError):
            continue
    
    # Configura a resposta
    output.seek(0)
    data_atual = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Registra a ação de exportação
    registrar_auditoria(
        acao="exportacao_auditoria",
        descricao=f"Exportação de relatório de auditoria para CSV",
        dados=f"Período: {periodo}, Eventos: {relatorio['total_eventos']}"
    )
    
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment;filename=relatorio_auditoria_{periodo}_{data_atual}.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@app.route('/registros')
def registros():
    """Página de registros de auditoria."""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Obtém os registros
    registros = obter_registros_auditoria(data_inicio, data_fim, limite=500)
    
    # Registra a ação de visualização
    registrar_auditoria(
        acao="visualizar_registros",
        descricao="Visualização da página de registros de auditoria",
        dados=f"Total de registros: {len(registros)}"
    )
    
    return render_template('registros.html', registros=registros, request=request)

@app.route('/ferramentas')
def ferramentas():
    """Página de ferramentas auxiliares."""
    # Obtém todas as fontes
    fontes = obter_fontes(apenas_ativas=False)
    
    # Registra a ação de visualização
    registrar_auditoria(
        acao="visualizar_ferramentas",
        descricao="Visualização da página de ferramentas",
        dados=f"Total de fontes: {len(fontes)}"
    )
    
    return render_template('ferramentas.html', fontes=fontes)

@app.route('/agendar-busca')
def agendar_busca():
    """Página de instruções para agendamento de buscas."""
    # Registra a ação de visualização
    registrar_auditoria(
        acao="visualizar_agendamento",
        descricao="Visualização da página de agendamento de buscas",
        dados=None
    )
    
    return render_template('instrucoes_agendamento.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Desenvolvido por Luiz Vaisconcelos
# Email: luiz.vaisconcelos@gmail.com
# LinkedIn: https://www.linkedin.com/in/vaisconcelos/
# GitHub: https://github.com/luizhvaisconcelos
