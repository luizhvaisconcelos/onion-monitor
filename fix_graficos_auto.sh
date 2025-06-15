#!/bin/bash

# Script de Aplicação Automática da Correção dos Gráficos
# Onion Monitor v3 - Correção dos Gráficos de Análise

echo "============================================================"
echo "APLICANDO CORREÇÃO DOS GRÁFICOS - ONION MONITOR V3"
echo "============================================================"

# Verifica se o arquivo app.py existe
if [ ! -f "app.py" ]; then
    echo "❌ Erro: Arquivo app.py não encontrado!"
    echo "Execute este script no diretório do Onion Monitor."
    exit 1
fi

# Cria backup do arquivo atual
echo "📁 Criando backup do app.py atual..."
cp app.py "app_backup_$(date +%Y%m%d_%H%M%S).py"
echo "✅ Backup criado: app_backup_$(date +%Y%m%d_%H%M%S).py"

# Para a aplicação se estiver rodando
echo "🛑 Parando aplicação em execução..."
pkill -f "python.*app.py" 2>/dev/null || true

# Aplica a correção usando Python
echo "🔧 Aplicando correção na função analise()..."
python3 << 'EOF'
import re

# Lê o arquivo app.py atual
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define a nova função analise corrigida
new_analise_function = '''@app.route('/analise')
def analise():
    """Página de análise de dados coletados com todos os gráficos funcionais"""
    try:
        # Obtém estatísticas básicas de validação
        estatisticas = obter_estatisticas_validacao()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ============================================================
        # ESTATÍSTICAS GERAIS (Cards superiores)
        # ============================================================
        
        # Total de coletas
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
        
        # ============================================================
        # CONSULTAS PARA OS GRÁFICOS (CORRIGIDAS)
        # ============================================================
        
        # 1. DISTRIBUIÇÃO DE VALIDAÇÃO (Gráfico Pizza)
        distribuicao_validacao = []
        try:
            # Busca validados e não validados
            cursor.execute(\\'''
                SELECT 
                    CASE WHEN validado = 1 THEN 'Validados' ELSE 'Não Validados' END as categoria,
                    COUNT(*) as quantidade
                FROM coletas 
                GROUP BY validado
                ORDER BY validado
            \\''')
            results = cursor.fetchall()
            
            # Garante que ambas categorias existam
            validados_count = 0
            nao_validados_count = 0
            
            for row in results:
                if row[0] == 'Validados':
                    validados_count = row[1]
                else:
                    nao_validados_count = row[1]
            
            # Adiciona sempre ambas as categorias
            if nao_validados_count > 0:
                distribuicao_validacao.append({'categoria': 'Não Validados', 'quantidade': nao_validados_count})
            if validados_count > 0:
                distribuicao_validacao.append({'categoria': 'Validados', 'quantidade': validados_count})
            
            # Se não houver dados, adiciona valores padrão
            if not distribuicao_validacao:
                distribuicao_validacao = [
                    {'categoria': 'Não Validados', 'quantidade': 0},
                    {'categoria': 'Validados', 'quantidade': 0}
                ]
                
        except Exception as e:
            logger.error(f"Erro na consulta de distribuição de validação: {e}")
            distribuicao_validacao = [
                {'categoria': 'Não Validados', 'quantidade': 0},
                {'categoria': 'Validados', 'quantidade': 0}
            ]
        
        # 2. COLETAS POR FONTE (Gráfico Barras)
        coletas_por_fonte = []
        try:
            # LEFT JOIN para mostrar todas as fontes, mesmo sem coletas
            cursor.execute(\\'''
                SELECT 
                    f.nome as fonte_nome, 
                    COALESCE(COUNT(c.id), 0) as quantidade
                FROM fontes f
                LEFT JOIN coletas c ON f.id = c.fonte_id
                WHERE f.ativo = 1
                GROUP BY f.id, f.nome
                ORDER BY quantidade DESC
            \\''')
            
            for fonte in cursor.fetchall():
                coletas_por_fonte.append({
                    'fonte_nome': fonte[0],
                    'quantidade': fonte[1]
                })
                
            # Se não houver dados, adiciona uma fonte padrão
            if not coletas_por_fonte:
                coletas_por_fonte = [{'fonte_nome': 'Nenhuma fonte ativa', 'quantidade': 0}]
                
        except Exception as e:
            logger.error(f"Erro na consulta de coletas por fonte: {e}")
            coletas_por_fonte = [{'fonte_nome': 'Erro ao carregar', 'quantidade': 0}]
        
        # 3. TOP TERMOS BUSCADOS (Tabela)
        coletas_por_termo = []
        try:
            cursor.execute(\\'''
                SELECT 
                    CASE 
                        WHEN LENGTH(termo_busca) > 20 THEN SUBSTR(termo_busca, 1, 20) || '...'
                        ELSE termo_busca
                    END as termo_busca, 
                    COUNT(*) as quantidade
                FROM coletas
                GROUP BY termo_busca
                ORDER BY quantidade DESC
                LIMIT 10
            \\''')
            
            for termo in cursor.fetchall():
                coletas_por_termo.append({
                    'termo_busca': termo[0],
                    'quantidade': termo[1]
                })
                
            # Se não houver dados
            if not coletas_por_termo:
                coletas_por_termo = [{'termo_busca': 'Nenhum termo pesquisado', 'quantidade': 0}]
                
        except Exception as e:
            logger.error(f"Erro na consulta de termos: {e}")
            coletas_por_termo = [{'termo_busca': 'Erro ao carregar', 'quantidade': 0}]
        
        # 4. COLETAS POR DIA (Gráfico Linha/Timeline)
        coletas_por_dia = []
        try:
            cursor.execute(\\'''
                SELECT 
                    DATE(data_coleta) as data, 
                    COUNT(*) as quantidade
                FROM coletas
                WHERE data_coleta >= datetime('now', '-30 days')
                GROUP BY DATE(data_coleta)
                ORDER BY data DESC
                LIMIT 30
            \\''')
            
            for dia in cursor.fetchall():
                coletas_por_dia.append({
                    'data': dia[0],
                    'quantidade': dia[1]
                })
                
            # Se não houver dados dos últimos 30 dias
            if not coletas_por_dia:
                import datetime
                hoje = datetime.date.today().strftime('%Y-%m-%d')
                coletas_por_dia = [{'data': hoje, 'quantidade': 0}]
                
        except Exception as e:
            logger.error(f"Erro na consulta por dia: {e}")
            import datetime
            hoje = datetime.date.today().strftime('%Y-%m-%d')
            coletas_por_dia = [{'data': hoje, 'quantidade': 0}]
        
        # 5. ÚLTIMAS VALIDAÇÕES (Tabela)
        ultimas_validadas = []
        try:
            cursor.execute(\\'''
                SELECT 
                    c.id,
                    c.termo_busca,
                    CASE 
                        WHEN LENGTH(c.link_encontrado) > 50 
                        THEN SUBSTR(c.link_encontrado, 1, 50) || '...'
                        ELSE c.link_encontrado
                    END as link_encontrado,
                    c.data_validacao,
                    c.score_validacao,
                    f.nome as fonte_nome
                FROM coletas c
                LEFT JOIN fontes f ON c.fonte_id = f.id
                WHERE c.validado = 1
                ORDER BY c.data_validacao DESC
                LIMIT 10
            \\''')
            
            for validada in cursor.fetchall():
                ultimas_validadas.append({
                    'id': validada[0],
                    'termo_busca': validada[1],
                    'link_encontrado': validada[2],
                    'data_validacao': validada[3],
                    'score_validacao': validada[4],
                    'fonte_nome': validada[5] or 'Fonte desconhecida'
                })
                
            # Se não houver validações
            if not ultimas_validadas:
                ultimas_validadas = [{
                    'id': 0,
                    'termo_busca': 'Nenhuma validação encontrada',
                    'link_encontrado': '-',
                    'data_validacao': None,
                    'score_validacao': 0,
                    'fonte_nome': '-'
                }]
                
        except Exception as e:
            logger.error(f"Erro na consulta de últimas validadas: {e}")
            ultimas_validadas = [{
                'id': 0,
                'termo_busca': 'Erro ao carregar',
                'link_encontrado': '-',
                'data_validacao': None,
                'score_validacao': 0,
                'fonte_nome': '-'
            }]
        
        conn.close()
        
        # Registra a ação de visualização com dados de debug
        registrar_auditoria(
            acao="visualizar_analise",
            descricao="Visualização da página de análise",
            dados=f"Estatísticas: {total_validados} validados, Distribuição: {len(distribuicao_validacao)} categorias, Fontes: {len(coletas_por_fonte)} fontes"
        )
        
        # Log de debug para verificar os dados
        logger.info(f"Dados para análise - Distribuição: {distribuicao_validacao}")
        logger.info(f"Dados para análise - Coletas por fonte: {coletas_por_fonte}")
        logger.info(f"Dados para análise - Termos: {len(coletas_por_termo)} termos")
        
        return render_template(
            'analise.html',
            # Estatísticas gerais
            estatisticas=estatisticas,
            total_coletas=total_coletas,
            total_validados=total_validados,
            total_termos=total_termos,
            total_fontes=total_fontes,
            
            # Dados para os gráficos (CORRIGIDOS)
            distribuicao_validacao=distribuicao_validacao,  # Para gráfico pizza
            coletas_por_fonte=coletas_por_fonte,            # Para gráfico barras
            coletas_por_termo=coletas_por_termo,            # Para tabela
            coletas_por_dia=coletas_por_dia,                # Para gráfico linha
            ultimas_validadas=ultimas_validadas             # Para tabela
        )
        
    except Exception as e:
        logger.error(f"Erro geral na página de análise: {e}")
        flash(f"Erro ao carregar análises: {str(e)}", "danger")
        
        # Retorna dados básicos em caso de erro
        return render_template('analise.html', 
            estatisticas={'validados': 0, 'nao_validados': 0, 'score_medio': 0},
            total_coletas=0,
            total_validados=0,
            total_termos=0,
            total_fontes=0,
            distribuicao_validacao=[],
            coletas_por_fonte=[],
            coletas_por_termo=[],
            coletas_por_dia=[],
            ultimas_validadas=[]
        )'''

# Busca o padrão da função analise atual
pattern = r'@app\.route\(\'/analise\'\)\ndef analise\(\):.*?(?=@app\.route|def |if __name__|$)'

# Substitui a função existente pela nova
new_content = re.sub(pattern, new_analise_function, content, flags=re.DOTALL)

# Se não encontrou a função para substituir, adiciona no final
if new_content == content:
    print("⚠️  Função analise() não encontrada. Adicionando no final do arquivo...")
    new_content = content.rstrip() + "\n\n" + new_analise_function + "\n"

# Salva o arquivo modificado
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Função analise() substituída com sucesso!")
EOF

# Verifica se a substituição foi bem-sucedida
if grep -q "CONSULTAS PARA OS GRÁFICOS (CORRIGIDAS)" app.py; then
    echo "✅ Correção aplicada com sucesso!"
else
    echo "❌ Erro ao aplicar correção. Restaurando backup..."
    cp "app_backup_$(date +%Y%m%d)*.py" app.py 2>/dev/null || true
    exit 1
fi

# Adiciona a rota de debug se não existir
if ! grep -q "/debug-analise" app.py; then
    echo "🔧 Adicionando rota de debug..."
    cat >> app.py << 'EOF'

@app.route('/debug-analise')
def debug_analise():
    """Rota de debug para verificar dados dos gráficos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        debug_info = {
            'status': 'OK',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Teste distribuição de validação
        cursor.execute('''
            SELECT 
                CASE WHEN validado = 1 THEN 'Validados' ELSE 'Não Validados' END as categoria,
                COUNT(*) as quantidade
            FROM coletas 
            GROUP BY validado
        ''')
        distribuicao = [{'categoria': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
        debug_info['distribuicao_validacao'] = distribuicao
        
        # Teste coletas por fonte
        cursor.execute('''
            SELECT f.nome, COALESCE(COUNT(c.id), 0) as quantidade
            FROM fontes f
            LEFT JOIN coletas c ON f.id = c.fonte_id
            WHERE f.ativo = 1
            GROUP BY f.id, f.nome
            ORDER BY quantidade DESC
        ''')
        fontes = [{'fonte': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
        debug_info['coletas_por_fonte'] = fontes
        
        # Teste contagens básicas
        cursor.execute('SELECT COUNT(*) FROM coletas')
        debug_info['total_coletas'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM coletas WHERE validado = 1')
        debug_info['total_validados'] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'erro': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500
EOF
    echo "✅ Rota de debug adicionada!"
fi

echo ""
echo "============================================================"
echo "✅ CORREÇÃO APLICADA COM SUCESSO!"
echo "============================================================"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Reinicie a aplicação: python app.py"
echo "2. Acesse: http://localhost:5000/analise"
echo "3. Teste os gráficos: Distribuição de Validação e Coletas por Fonte"
echo "4. Debug (opcional): http://localhost:5000/debug-analise"
echo ""
echo "📊 DADOS ESPERADOS:"
echo "- Distribuição: 12 Validados vs 2316 Não Validados"
echo "- Coletas por Fonte: Ahmia com 2328 coletas"
echo "- Top Termos: senha@123 (1125), Fulano@gmail.com (681)"
echo ""