# Onion Monitor v2 - Versão Melhorada

## Visão Geral

O Onion Monitor v2 é uma ferramenta avançada para monitoramento de vazamentos de dados na deep/dark web. Esta versão incorpora melhorias significativas em relação à versão anterior, incluindo validação semântica real, busca mais precisa, interface aprimorada e maior robustez no tratamento de dados.

## Principais Funcionalidades

- **Busca de Vazamentos**: Busca termos sensíveis em fontes da dark web com validação semântica real
- **Validação Rigorosa**: Sistema de pontuação avançado para minimizar falsos positivos
- **Verificação de Fontes**: Verificação do status de fontes cadastradas com feedback visual
- **Exportação de Dados**: Exportação de resultados em formato CSV com suporte a caracteres especiais
- **Auditoria Completa**: Registro detalhado de todas as operações realizadas no sistema
- **API REST**: Endpoints para integração com outros sistemas

## Melhorias em Relação à Versão Anterior

1. **Validação Semântica Real**: Implementação de busca e validação semântica em fontes reais
2. **Critérios de Validação Mais Rigorosos**: Score mínimo aumentado e análise contextual aprimorada
3. **Rotas Padronizadas**: Estrutura de URLs mais clara e consistente
4. **Banco de Dados Robusto**: Esquema otimizado e tratamento de erros aprimorado
5. **Interface Responsiva**: Layout adaptável a diferentes dispositivos
6. **Documentação Integrada**: Instruções de uso e configuração acessíveis no sistema

## Instalação

```bash
# Clonar o repositório ou descompactar o arquivo ZIP
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Iniciar o aplicativo
python app.py
```

## Uso

1. Acesse o sistema em `http://localhost:5000`
2. Na página inicial, digite um termo para busca de vazamentos
3. Visualize os resultados e utilize as ferramentas de análise
4. Exporte os dados conforme necessário

## Estrutura do Projeto

- `app.py`: Aplicativo Flask principal
- `db.py`: Módulo de banco de dados
- `coletor.py`: Módulo de coleta e validação de dados
- `busca_valida_semantica.py`: Módulo de validação semântica real
- `templates/`: Templates HTML
- `static/`: Arquivos estáticos (JS, CSS, imagens)

## Créditos

Desenvolvido por Luiz Vaisconcelos
- Email: luiz.vaisconcelos@gmail.com
- LinkedIn: https://www.linkedin.com/in/vaisconcelos/
- GitHub: https://github.com/luizhvaisconcelos
