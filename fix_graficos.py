"""
Script de Correção dos Gráficos - Onion Monitor v3
Corrige problemas com dados vazios nos gráficos da página de análise
"""

import sqlite3
import os
from datetime import datetime

def corrigir_graficos():
    """Corrige problemas dos gráficos vazios"""
    
    print("="*60)
    print("CORREÇÃO DOS GRÁFICOS - ONION MONITOR V3")
    print("="*60)
    
    db_path = 'onion_monitor.db'
    if not os.path.exists(db_path):
        print("❌ ERRO: Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Verificar e corrigir coletas sem fonte_id
        print("\n1. VERIFICANDO COLETAS SEM FONTE_ID:")
        cursor.execute("SELECT COUNT(*) FROM coletas WHERE fonte_id IS NULL")
        sem_fonte = cursor.fetchone()[0]
        
        if sem_fonte > 0:
            print(f"   ⚠️  Encontradas {sem_fonte} coletas sem fonte_id")
            
            # Verifica se existe uma fonte padrão
            cursor.execute("SELECT id FROM fontes WHERE nome LIKE '%Ahmia%' OR nome LIKE '%padrão%' ORDER BY id LIMIT 1")
            fonte_padrao = cursor.fetchone()
            
            if fonte_padrao:
                fonte_id = fonte_padrao[0]
                print(f"   🔧 Definindo fonte padrão ID={fonte_id} para coletas órfãs...")
                
                cursor.execute("UPDATE coletas SET fonte_id = ? WHERE fonte_id IS NULL", (fonte_id,))
                conn.commit()
                
                cursor.execute("SELECT COUNT(*) FROM coletas WHERE fonte_id IS NULL")
                restantes = cursor.fetchone()[0]
                print(f"   ✅ Corrigido! Restam {restantes} coletas sem fonte")
            else:
                print("   🔧 Criando fonte padrão...")
                cursor.execute('''
                    INSERT INTO fontes (nome, url, tipo, ativo) 
                    VALUES ('Fonte Padrão', 'https://ahmia.fi/', 'surface', 1)
                ''')
                fonte_id = cursor.lastrowid
                
                cursor.execute("UPDATE coletas SET fonte_id = ? WHERE fonte_id IS NULL", (fonte_id,))
                conn.commit()
                print(f"   ✅ Fonte padrão criada (ID={fonte_id}) e aplicada!")
        else:
            print("   ✅ Todas as coletas possuem fonte_id")
        
        # 2. Testar as consultas dos gráficos
        print("\n2. TESTANDO CONSULTAS DOS GRÁFICOS:")
        
        # Teste 1: Distribuição de Validação
        print("\n   📊 Teste 1 - Distribuição de Validação:")
        try:
            cursor.execute("""
                SELECT 
                    CASE WHEN validado = 1 THEN 'Validados' ELSE 'Não Validados' END as categoria,
                    COUNT(*) as quantidade
                FROM coletas
                GROUP BY CASE WHEN validado = 1 THEN 'Validados' ELSE 'Não Validados' END
            """)
            resultado = cursor.fetchall()
            
            if resultado:
                for row in resultado:
                    print(f"      ✅ {row['categoria']}: {row['quantidade']}")
            else:
                print("      ❌ Resultado vazio!")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
        
        # Teste 2: Coletas por Fonte
        print("\n   📊 Teste 2 - Coletas por Fonte:")
        try:
            cursor.execute('''
                SELECT f.nome as fonte_nome, COUNT(*) as quantidade
                FROM coletas c
                INNER JOIN fontes f ON c.fonte_id = f.id
                GROUP BY f.nome
                ORDER BY quantidade DESC
            ''')
            resultado = cursor.fetchall()
            
            if resultado:
                for row in resultado:
                    print(f"      ✅ {row['fonte_nome']}: {row['quantidade']} coletas")
            else:
                print("      ❌ INNER JOIN falhou! Testando LEFT JOIN...")
                
                cursor.execute('''
                    SELECT f.nome as fonte_nome, COUNT(c.id) as quantidade
                    FROM fontes f
                    LEFT JOIN coletas c ON f.id = c.fonte_id
                    GROUP BY f.nome
                    ORDER BY quantidade DESC
                ''')
                resultado_alt = cursor.fetchall()
                
                if resultado_alt:
                    print("      ✅ LEFT JOIN funcionou:")
                    for row in resultado_alt:
                        print(f"         {row['fonte_nome']}: {row['quantidade']} coletas")
                else:
                    print("      ❌ Ambos JOINs falharam!")
                    
        except Exception as e:
            print(f"      ❌ Erro: {e}")
        
        # Teste 3: Top Termos
        print("\n   📊 Teste 3 - Top Termos:")
        try:
            cursor.execute('''
                SELECT termo_busca, COUNT(*) as quantidade
                FROM coletas
                WHERE termo_busca IS NOT NULL AND termo_busca != ''
                GROUP BY termo_busca
                ORDER BY quantidade DESC
                LIMIT 5
            ''')
            resultado = cursor.fetchall()
            
            if resultado:
                for row in resultado:
                    print(f"      ✅ '{row['termo_busca'][:20]}...': {row['quantidade']}")
            else:
                print("      ❌ Nenhum termo encontrado!")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
        
        # 3. Verificar integridade referencial
        print("\n3. VERIFICANDO INTEGRIDADE REFERENCIAL:")
        
        # Encontrar coletas com fonte_id inválido
        cursor.execute('''
            SELECT c.fonte_id, COUNT(*) as quantidade
            FROM coletas c
            LEFT JOIN fontes f ON c.fonte_id = f.id
            WHERE c.fonte_id IS NOT NULL AND f.id IS NULL
            GROUP BY c.fonte_id
        ''')
        referencias_quebradas = cursor.fetchall()
        
        if referencias_quebradas:
            print("   ⚠️  Referencias quebradas encontradas:")
            for ref in referencias_quebradas:
                print(f"      fonte_id={ref['fonte_id']}: {ref['quantidade']} coletas")
                
            # Corrigir referencias quebradas
            for ref in referencias_quebradas:
                print(f"   🔧 Corrigindo coletas com fonte_id={ref['fonte_id']}...")
                cursor.execute("UPDATE coletas SET fonte_id = 1 WHERE fonte_id = ?", (ref['fonte_id'],))
            
            conn.commit()
            print("   ✅ Referencias quebradas corrigidas!")
        else:
            print("   ✅ Integridade referencial OK!")
        
        # 4. Estatísticas finais
        print("\n4. ESTATÍSTICAS FINAIS:")
        cursor.execute("SELECT COUNT(*) FROM coletas")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM coletas WHERE validado = 1")
        validados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fontes WHERE ativo = 1")
        fontes_ativas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT termo_busca) FROM coletas")
        termos_unicos = cursor.fetchone()[0]
        
        print(f"   📊 Total de coletas: {total}")
        print(f"   ✅ Validados: {validados}")
        print(f"   🌐 Fontes ativas: {fontes_ativas}")
        print(f"   🔍 Termos únicos: {termos_unicos}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("Reinicie o Onion Monitor e teste a página de análise.")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    corrigir_graficos()