#!/usr/bin/env python3
import os
import sys
import datetime
from coletor import buscar_termo
from db import registrar_auditoria

log_file = open('busca_agendada.log', 'a')
log_file.write(f"\n--- Execução em {datetime.datetime.now()} ---\n")

try:
    with open('termos_busca.txt', 'r') as f:
        termos = {linha.strip() for linha in f if linha.strip()}
        log_file.write(f"Termos carregados: {len(termos)}\n")

    for termo in termos:
        log_file.write(f"Buscando termo: {termo}\n")
        try:
            registrar_auditoria(
                acao="busca_agendada",
                descricao=f"Busca agendada para o termo: {termo}",
                dados=f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            resultados = buscar_termo(termo)
            registrar_auditoria(
                acao="busca_agendada_concluida",
                descricao=f"Busca agendada concluída para o termo: {termo}",
                dados=f"Resultados: {len(resultados)}"
            )
            log_file.write(f"Resultados encontrados: {len(resultados)}\n")
        except Exception as e:
            log_file.write(f"ERRO ao buscar termo '{termo}': {str(e)}\n")
            registrar_auditoria(
                acao="erro",
                descricao=f"Erro na busca agendada para o termo: {termo}",
                dados=f"Erro: {str(e)}"
            )
except Exception as e:
    log_file.write(f"ERRO CRÍTICO: {str(e)}\n")
    registrar_auditoria(
        acao="erro_critico",
        descricao="Erro crítico na execução da busca agendada",
        dados=f"Erro: {str(e)}"
    )

log_file.write("--- Fim da execução ---\n")
log_file.close()