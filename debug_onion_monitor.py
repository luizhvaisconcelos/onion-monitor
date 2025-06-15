# Script de Debug para Onion Monitor v3

## Arquivo: debug_onion_monitor.py

#!/usr/bin/env python3
"""
Script de debug para verificar estado do banco de dados
Onion Monitor v3 - Diagnóstico de problemas na página de análise
"""

import sqlite3
import os
from datetime import datetime

def verificar_banco_dados():
    """Verifica estrutura e dados do banco"""
    
    print("=" * 60)
    print("DIAGNÓSTICO ONION MONITOR V3 - BANCO DE DADOS")
    print("=" * 60)
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect('onion_monitor.db')
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        cursor = conn.cursor()
        
        # 1. VERIFICAR TABELAS EXISTENTES
        print("\n1. TABELAS EXISTENTES:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        for tabela in tabelas:
            print(f"   ✓ {tabela[0]}")
        
        # 2. VERIFICAR ESTRUTURA DAS TABELAS PRINCIPAIS
        print("\n2. ESTRUTURA DA TABELA COLETAS:")
        cursor.execute("PRAGMA table_info(coletas)")
        colunas_coletas = cursor.fetchall()
        for coluna in colunas_coletas:
            print(f"   - {coluna['name']}: {coluna['type']}")
        
        print("\n3. ESTRUTURA DA TABELA FONTES:")
        cursor.execute("PRAGMA table_info(fontes)")
        colunas_fontes = cursor.fetchall()
        for coluna in colunas_fontes:
            print(f"   - {coluna['name']}: {coluna['type']}")
        
        # 3. CONTAGENS BÁSICAS
        print("\n4. CONTAGENS BÁSICAS:")
        
        cursor.execute("SELECT COUNT(*) FROM coletas")
        total_coletas = cursor.fetchone()[0]
        print(f"   Total de coletas: {total_coletas}")
        
        cursor.execute("SELECT COUNT(*) FROM coletas WHERE validado = 1")
        total_validados = cursor.fetchone()[0]
        print(f"   Total validados: {total_validados}")
        
        cursor.execute("SELECT COUNT(*) FROM fontes")
        total_fontes = cursor.fetchone()[0]
        print(f"   Total de fontes: {total_fontes}")
        
        cursor.execute("SELECT COUNT(*) FROM fontes WHERE ativo = 1")
        fontes_ativas = cursor.fetchone()[0]
        print(f"   Fontes ativas: {fontes_ativas}")
        
        # 4. VERIFICAR PROBLEMA DOS JOINS
        print("\n5. TESTE DE JOINS (PROBLEMA DOS GRÁFICOS):")
        
        # Verificar se fonte_id existe e não é NULL
        cursor.execute("SELECT COUNT(*) FROM coletas WHERE fonte_id IS NULL")
        coletas_sem_fonte = cursor.fetchone()[0]
        print(f"   Coletas sem fonte_id (NULL): {coletas_sem_fonte}")
        
        cursor.execute("SELECT COUNT(*) FROM coletas WHERE fonte_id IS NOT NULL")
        coletas_com_fonte = cursor.fetchone()[0]
        print(f"   Coletas com fonte_id: {coletas_com_fonte}")
        
        # Testar INNER JOIN
        cursor.execute("""
            SELECT COUNT(*) FROM coletas c 
            INNER JOIN fontes f ON c.fonte_id = f.id
        """)
        join_resultado = cursor.fetchone()[0]
        print(f"   INNER JOIN coletas<->fontes: {join_resultado}")
        
        # Se INNER JOIN está vazio, identificar o problema
        if join_resultado == 0 and coletas_com_fonte > 0:
            print("   ⚠️ PROBLEMA IDENTIFICADO: INNER JOIN retorna 0 mas existem coletas!")
            
            # Verificar se fonte_id aponta para fontes válidas
            cursor.execute("SELECT DISTINCT fonte_id FROM coletas WHERE fonte_id IS NOT NULL LIMIT 10")
            fonte_ids = cursor.fetchall()
            print(f"   Fonte_ids nas coletas: {[row[0] for row in fonte_ids]}")
            
            cursor.execute("SELECT id FROM fontes LIMIT 10")
            fontes_ids = cursor.fetchall()
            print(f"   IDs na tabela fontes: {[row[0] for row in fontes_ids]}")
        
        # 6. TESTAR CONSULTAS DOS GRÁFICOS
        print("\n6. TESTE DAS CONSULTAS DOS GRÁFICOS:")
        
        # Gráfico: Coletas por fonte
        try:
            cursor.execute("""
                SELECT f.nome as fonte_nome, COUNT(*) as quantidade
                FROM coletas c
                INNER JOIN fontes f ON c.fonte_id = f.id
                GROUP BY f.nome
                ORDER BY quantidade DESC
                LIMIT 5
            """)
            resultado_fonte = cursor.fetchall()
            print(f"   Coletas por fonte (INNER): {len(resultado_fonte)} resultados")
            for row in resultado_fonte:
                print(f"     - {row['fonte_nome']}: {row['quantidade']}")
        except Exception as e:
            print(f"   ❌ Erro em coletas por fonte: {e}")
        
        # Alternativa com LEFT JOIN
        try:
            cursor.execute("""
                SELECT f.nome as fonte_nome, COUNT(c.id) as quantidade
                FROM fontes f
                LEFT JOIN coletas c ON f.id = c.fonte_id
                WHERE f.ativo = 1
                GROUP BY f.nome
                ORDER BY quantidade DESC
            """)
            resultado_fonte_left = cursor.fetchall()
            print(f"   Coletas por fonte (LEFT): {len(resultado_fonte_left)} resultados")
            for row in resultado_fonte_left:
                print(f"     - {row['fonte_nome']}: {row['quantidade']}")
        except Exception as e:
            print(f"   ❌ Erro em LEFT JOIN: {e}")
        
        # Gráfico: Top termos
        try:
            cursor.execute("""
                SELECT termo_busca, COUNT(*) as quantidade
                FROM coletas
                GROUP BY termo_busca
                ORDER BY quantidade DESC
                LIMIT 5
            """)
            resultado_termos = cursor.fetchall()
            print(f"   Top termos: {len(resultado_termos)} resultados")
            for row in resultado_termos:
                print(f"     - {row['termo_busca']}: {row['quantidade']}")
        except Exception as e:
            print(f"   ❌ Erro em top termos: {e}")
        
        # 7. AMOSTRAS DOS DADOS
        print("\n7. AMOSTRA DOS DADOS:")
        
        cursor.execute("SELECT * FROM coletas LIMIT 3")
        coletas_amostra = cursor.fetchall()
        if coletas_amostra:
            print("   Últimas coletas:")
            for row in coletas_amostra:
                print(f"     ID: {row['id']}, Termo: {row['termo_busca']}, Fonte_ID: {row.get('fonte_id', 'NULL')}")
        
        cursor.execute("SELECT * FROM fontes LIMIT 3")
        fontes_amostra = cursor.fetchall()
        if fontes_amostra:
            print("   Fontes cadastradas:")
            for row in fontes_amostra:
                print(f"     ID: {row['id']}, Nome: {row['nome']}, Ativo: {row.get('ativo', 'NULL')}")
        
        # 8. FOREIGN KEYS
        print("\n8. VERIFICAÇÃO DE FOREIGN KEYS:")
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        if fk_errors:
            print("   ❌ Erros de foreign key encontrados:")
            for error in fk_errors:
                print(f"     {error}")
        else:
            print("   ✓ Sem erros de foreign key")
        
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        print(f"   Foreign keys habilitadas: {'Sim' if fk_enabled else 'Não'}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO COMPLETO")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro durante diagnóstico: {e}")

if __name__ == "__main__":
    verificar_banco_dados()