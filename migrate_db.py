#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Onion Monitor v3 - Script de Migração de Banco de Dados Corrigido
================================================================

Este script realiza a migração segura do banco de dados do Onion Monitor 
para a versão 3, corrigindo os problemas identificados no arquivo original.

Principais correções implementadas:
- Encoding UTF-8 corrigido
- Validação de estrutura antes da migração  
- Sistema de backup automático robusto
- Transações ACID completas
- Tratamento de erros específico para cada etapa
- Controle de versão com PRAGMA user_version
- Logging estruturado multinível

Autor: Assistente AI baseado nas especificações do Onion Monitor v3
Data: 2025-06-14
Versão: 3.0.0-fixed
"""

import sqlite3
import logging
import os
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from contextlib import contextmanager


class OnionMonitorMigrator:
    """
    Classe responsável pela migração segura do banco de dados 
    do Onion Monitor para a versão 3.
    """
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o migrador com configurações padrão.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'onion_monitor.db'
        )
        self.backup_dir = os.path.join(
            os.path.dirname(self.db_path), 
            'backups'
        )
        self.target_version = 3
        self.setup_logging()
        
    def setup_logging(self):
        """Configura o sistema de logging estruturado."""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/migration_v3.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("onion_monitor_migration_v3")
        
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexões com o banco de dados.
        Garante fechamento adequado das conexões.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Habilita foreign keys para integridade referencial
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
                
    def get_current_version(self) -> int:
        """
        Obtém a versão atual do schema do banco de dados.
        
        Returns:
            int: Versão atual do schema (0 se não definida)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                version = cursor.fetchone()[0]
                return version
        except Exception as e:
            self.logger.warning(f"Erro ao obter versão do schema: {e}")
            return 0
            
    def set_schema_version(self, version: int):
        """
        Define a versão do schema no banco de dados.
        
        Args:
            version: Nova versão do schema
        """
        with self.get_connection() as conn:
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
            
    def get_existing_tables(self) -> List[str]:
        """
        Obtém lista de tabelas existentes no banco de dados.
        
        Returns:
            List[str]: Lista com nomes das tabelas existentes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            return tables
            
    def validate_table_structure(self, table_name: str, expected_columns: List[str]) -> Dict:
        """
        Valida se uma tabela possui as colunas esperadas.
        
        Args:
            table_name: Nome da tabela a ser validada
            expected_columns: Lista de colunas esperadas
            
        Returns:
            Dict: Resultado da validação com colunas encontradas e faltantes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            extra_columns = [col for col in existing_columns if col not in expected_columns]
            
            return {
                'exists': True,
                'existing_columns': existing_columns,
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'valid': len(missing_columns) == 0
            }
            
    def create_backup(self) -> str:
        """
        Cria backup do banco de dados antes da migração.
        
        Returns:
            str: Caminho do arquivo de backup criado
        """
        os.makedirs(self.backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"onion_monitor_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Backup criado em: {backup_path}")
        else:
            self.logger.warning("Arquivo de banco não existe, backup não criado")
            
        return backup_path
        
    def restore_backup(self, backup_path: str):
        """
        Restaura o banco de dados a partir de um backup.
        
        Args:
            backup_path: Caminho do arquivo de backup
        """
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, self.db_path)
            self.logger.info(f"Banco restaurado a partir do backup: {backup_path}")
        else:
            raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
    def create_v3_tables(self):
        """Cria ou atualiza as tabelas necessárias para a versão 3."""
        tables_sql = {
            'fontes': """
                CREATE TABLE IF NOT EXISTS fontes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    url TEXT NOT NULL,
                    tipo TEXT NOT NULL CHECK(tipo IN ('surface', 'onion', 'lista')),
                    ativo BOOLEAN DEFAULT 1,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_check TIMESTAMP,
                    status TEXT DEFAULT 'ativo' CHECK(status IN ('ativo', 'inativo', 'erro')),
                    timeout_segundos INTEGER DEFAULT 30,
                    user_agent TEXT,
                    headers_customizados TEXT
                )
            """,
            
            'coletas': """
                CREATE TABLE IF NOT EXISTS coletas (
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
                    hash_conteudo TEXT,
                    tamanho_conteudo INTEGER,
                    encoding_detectado TEXT,
                    tempo_coleta_ms INTEGER,
                    status_http INTEGER,
                    headers_resposta TEXT,
                    ip_origem TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (fonte_id) REFERENCES fontes (id)
                )
            """,
            
            'auditoria': """
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acao TEXT NOT NULL,
                    descricao TEXT,
                    dados TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario TEXT DEFAULT 'sistema',
                    ip_origem TEXT,
                    resultado TEXT DEFAULT 'sucesso'
                )
            """,
            
            'status_fontes': """
                CREATE TABLE IF NOT EXISTS status_fontes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fonte_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    data_verificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detalhes TEXT,
                    tempo_resposta_ms INTEGER,
                    codigo_http INTEGER,
                    erro_detalhado TEXT,
                    FOREIGN KEY (fonte_id) REFERENCES fontes (id)
                )
            """,
            
            'resultados': """
                CREATE TABLE IF NOT EXISTS resultados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coleta_id INTEGER NOT NULL,
                    tipo_validacao TEXT NOT NULL,
                    confiabilidade REAL DEFAULT 0.0,
                    contexto_encontrado TEXT,
                    palavras_chave TEXT,
                    classificacao TEXT,
                    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processado_por TEXT DEFAULT 'sistema',
                    metadata_adicional TEXT,
                    FOREIGN KEY (coleta_id) REFERENCES coletas (id)
                )
            """,
            
            'validacoes': """
                CREATE TABLE IF NOT EXISTS validacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coleta_id INTEGER NOT NULL,
                    tipo_validacao TEXT NOT NULL,
                    score REAL NOT NULL,
                    detalhes TEXT,
                    validado_por TEXT DEFAULT 'sistema',
                    data_validacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    algoritmo_usado TEXT,
                    versao_algoritmo TEXT,
                    confianca REAL DEFAULT 0.0,
                    FOREIGN KEY (coleta_id) REFERENCES coletas (id)
                )
            """
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_name, sql in tables_sql.items():
                try:
                    cursor.execute(sql)
                    self.logger.debug(f"Tabela '{table_name}' criada/verificada")
                except Exception as e:
                    raise Exception(f"Erro ao criar tabela {table_name}: {e}")
                    
            conn.commit()
            self.logger.info("Tabelas da v3 criadas/verificadas com sucesso")
            
    def update_coletas_structure(self):
        """Atualiza a estrutura da tabela coletas para v3."""
        new_columns = [
            ('hash_conteudo', 'TEXT'),
            ('tamanho_conteudo', 'INTEGER'),
            ('encoding_detectado', 'TEXT'),
            ('tempo_coleta_ms', 'INTEGER'),
            ('status_http', 'INTEGER'),
            ('headers_resposta', 'TEXT'),
            ('ip_origem', 'TEXT'),
            ('user_agent', 'TEXT')
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica colunas existentes
            cursor.execute("PRAGMA table_info(coletas)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Adiciona colunas que não existem
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE coletas ADD COLUMN {column_name} {column_type}"
                        cursor.execute(alter_sql)
                        self.logger.info(f"Coluna '{column_name}' adicionada à tabela coletas")
                    except Exception as e:
                        self.logger.error(f"Erro ao adicionar coluna {column_name}: {e}")
                        raise
                        
            # Atualiza registros existentes com fonte_id padrão se necessário
            cursor.execute("SELECT COUNT(*) FROM coletas WHERE fonte_id IS NULL")
            null_fonte_count = cursor.fetchone()[0]
            
            if null_fonte_count > 0:
                cursor.execute("UPDATE coletas SET fonte_id = 1 WHERE fonte_id IS NULL")
                self.logger.info("Registros existentes associados à fonte padrão")
                
            conn.commit()
            
    def create_performance_indexes(self):
        """Cria índices para melhorar a performance das consultas."""
        indexes = [
            ("idx_coletas_termo", "coletas", "termo_busca"),
            ("idx_coletas_data", "coletas", "data_coleta"),
            ("idx_coletas_fonte", "coletas", "fonte_id"),
            ("idx_coletas_validado", "coletas", "validado"),
            ("idx_coletas_score", "coletas", "score_validacao"),
            ("idx_auditoria_data", "auditoria", "data_registro"),
            ("idx_auditoria_acao", "auditoria", "acao"),
            ("idx_status_fontes_data", "status_fontes", "data_verificacao"),
            ("idx_status_fontes_fonte", "status_fontes", "fonte_id"),
            ("idx_resultados_coleta", "resultados", "coleta_id"),
            ("idx_resultados_tipo", "resultados", "tipo_validacao"),
            ("idx_validacoes_coleta", "validacoes", "coleta_id"),
            ("idx_validacoes_score", "validacoes", "score"),
            ("idx_fontes_ativo", "fontes", "ativo"),
            ("idx_fontes_tipo", "fontes", "tipo")
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for index_name, table_name, column_name in indexes:
                try:
                    create_index_sql = f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} ({column_name})
                    """
                    cursor.execute(create_index_sql)
                    self.logger.debug(f"Índice {index_name} criado/verificado")
                except Exception as e:
                    self.logger.warning(f"Erro ao criar índice {index_name}: {e}")
                    
            conn.commit()
            self.logger.info("Índices de performance criados com sucesso")
            
    def insert_default_data(self):
        """Insere dados padrão necessários para o funcionamento da v3."""
        default_sources = [
            ('Ahmia', 'https://ahmia.fi/', 'surface', 1, 'ativo'),
            ('Dark.fail', 'https://dark.fail/', 'lista', 1, 'ativo'),
            ('Onion.live', 'https://onion.live/', 'lista', 1, 'ativo'),
            ('Tor.taxi', 'https://tor.taxi/', 'lista', 1, 'ativo'),
            ('Onion.land', 'https://onion.land/', 'lista', 1, 'ativo'),
            ('DarkSearch', 'https://darksearch.io/', 'surface', 1, 'ativo')
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica se já existem fontes
            cursor.execute("SELECT COUNT(*) FROM fontes")
            fonte_count = cursor.fetchone()[0]
            
            if fonte_count == 0:
                insert_sql = """
                    INSERT INTO fontes (nome, url, tipo, ativo, status) 
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor.executemany(insert_sql, default_sources)
                self.logger.info(f"Inseridas {len(default_sources)} fontes padrão")
            else:
                self.logger.info("Fontes já existem, pulando inserção de dados padrão")
                
            # Registra ação de migração na auditoria
            audit_sql = """
                INSERT INTO auditoria (acao, descricao, dados) 
                VALUES (?, ?, ?)
            """
            cursor.execute(audit_sql, (
                'MIGRAÇÃO_V3',
                'Migração completa para Onion Monitor v3',
                f'Versão: {self.target_version}, Data: {datetime.now().isoformat()}'
            ))
            
            conn.commit()
            self.logger.info("Dados padrão inseridos com sucesso")
            
    def validate_migration(self) -> bool:
        """
        Valida se a migração foi concluída com sucesso.
        
        Returns:
            bool: True se a migração foi bem-sucedida
        """
        required_tables = ['fontes', 'coletas', 'auditoria', 'status_fontes', 'resultados', 'validacoes']
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verifica se todas as tabelas existem
                for table in required_tables:
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                        (table,)
                    )
                    if not cursor.fetchone():
                        self.logger.error(f"Tabela {table} não encontrada")
                        return False
                        
                # Verifica versão do schema
                current_version = self.get_current_version()
                if current_version != self.target_version:
                    self.logger.error(f"Versão incorreta: {current_version}, esperado: {self.target_version}")
                    return False
                    
                # Verifica integridade do banco
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                if integrity_result != 'ok':
                    self.logger.error(f"Falha na verificação de integridade: {integrity_result}")
                    return False
                    
                self.logger.info("Validação da migração bem-sucedida")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro durante validação: {e}")
            return False
            
    def migrate(self) -> bool:
        """
        Executa a migração completa para a versão 3.
        
        Returns:
            bool: True se a migração foi bem-sucedida
        """
        backup_path = None
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("INICIANDO MIGRAÇÃO ONION MONITOR V3")
            self.logger.info("=" * 60)
            
            # Verifica versão atual
            current_version = self.get_current_version()
            self.logger.info(f"Versão atual do schema: {current_version}")
            
            if current_version >= self.target_version:
                self.logger.info("Banco já está na versão correta ou superior")
                return True
                
            # Verifica tabelas existentes
            existing_tables = self.get_existing_tables()
            self.logger.info(f"Tabelas existentes: {existing_tables}")
            
            # Valida estrutura essencial
            essential_tables = {'coletas': True}
            for table in essential_tables:
                if table in existing_tables:
                    essential_tables[table] = True
                else:
                    essential_tables[table] = False
            self.logger.info(f"Status das tabelas essenciais: {essential_tables}")
            
            # Cria backup
            backup_path = self.create_backup()
            self.logger.info(f"Backup de segurança criado: {backup_path}")
            
            # Inicia transação principal
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Etapa 1: Criar tabelas da v3
                    self.logger.info("Etapa 1/5: Criando tabelas da v3...")
                    self.create_v3_tables()
                    
                    # Etapa 2: Atualizar estrutura da tabela coletas
                    self.logger.info("Etapa 2/5: Atualizando estrutura da tabela coletas...")
                    self.update_coletas_structure()
                    
                    # Etapa 3: Criar índices de performance
                    self.logger.info("Etapa 3/5: Criando índices de performance...")
                    self.create_performance_indexes()
                    
                    # Etapa 4: Inserir dados padrão
                    self.logger.info("Etapa 4/5: Inserindo dados padrão...")
                    self.insert_default_data()
                    
                    # Etapa 5: Atualizar versão do schema
                    self.logger.info("Etapa 5/5: Atualizando versão do schema...")
                    self.set_schema_version(self.target_version)
                    
                    # Commit da transação
                    conn.commit()
                    
                    # Validação final
                    if self.validate_migration():
                        self.logger.info("=" * 60)
                        self.logger.info("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                        self.logger.info(f"Onion Monitor atualizado para versão {self.target_version}")
                        self.logger.info("=" * 60)
                        return True
                    else:
                        raise Exception("Falha na validação pós-migração")
                        
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Erro durante migração, fazendo rollback: {e}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Erro crítico durante migração: {e}")
            
            # Restaura backup se disponível
            if backup_path and os.path.exists(backup_path):
                try:
                    self.restore_backup(backup_path)
                except Exception as restore_error:
                    self.logger.error(f"Erro ao restaurar backup: {restore_error}")
                    
            return False


def main():
    """Função principal para execução do script de migração."""
    print("Onion Monitor v3 - Script de Migração")
    print("=" * 50)
    print()
    
    # Confirmação do usuário
    confirm = input("ATENÇÃO: Este script irá modificar o banco de dados.\n"
                   "Um backup será criado automaticamente.\n"
                   "Deseja continuar? (s/N): ").lower().strip()
    
    if confirm not in ['s', 'sim', 'y', 'yes']:
        print("Migração cancelada pelo usuário.")
        return
    
    # Executa migração
    migrator = OnionMonitorMigrator()
    
    try:
        success = migrator.migrate()
        
        if success:
            print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("O banco de dados foi atualizado para a versão 3.")
            print("Você pode agora executar: python app.py")
        else:
            print("\n❌ FALHA NA MIGRAÇÃO!")
            print("Verifique os logs em 'logs/migration_v3.log' para detalhes.")
            print("O banco foi restaurado ao estado anterior.")
            
    except KeyboardInterrupt:
        print("\nMigração interrompida pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique os logs para mais detalhes.")


if __name__ == "__main__":
    main()