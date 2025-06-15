# Documentação Técnica do Onion Monitor v1

## Visão Geral do Sistema

O Onion Monitor é uma ferramenta de monitoramento e busca de vazamentos de dados sensíveis na surface web, deep web e dark web. O sistema utiliza técnicas avançadas de coleta, validação semântica e análise para identificar possíveis vazamentos de informações confidenciais.

## Arquitetura do Sistema

O Onion Monitor foi desenvolvido com uma arquitetura modular, composta pelos seguintes componentes principais:

1. **Interface Web (Flask)**: Frontend para interação com o usuário
2. **Módulo de Coleta**: Responsável pela busca e coleta de dados em diferentes fontes
3. **Módulo de Validação**: Analisa e valida os dados coletados para identificar vazamentos reais
4. **Banco de Dados**: Armazena fontes, coletas, validações e registros de auditoria
5. **Integração Tor**: Permite acesso seguro a sites .onion na dark web

## Requisitos do Sistema

### Requisitos de Hardware
- CPU: 2 cores ou superior
- RAM: 4GB ou superior
- Armazenamento: 10GB de espaço livre

### Requisitos de Software
- Sistema Operacional: Linux (Ubuntu/Debian recomendado)
- Python 3.6 ou superior
- Tor (para acesso à dark web)
- Navegador web moderno (Chrome, Firefox)

## Instalação e Configuração

### Instalação Automatizada

1. Clone ou descompacte o repositório em um diretório de sua escolha
2. Navegue até o diretório do projeto
3. Execute o script de instalação com privilégios de administrador:

```bash
sudo chmod +x install.sh
sudo ./install.sh
```

O script realizará as seguintes ações:
- Instalação das dependências do sistema
- Configuração do ambiente virtual Python
- Instalação das bibliotecas Python necessárias
- Inicialização do banco de dados
- Verificação da conexão com a rede Tor
- Configuração de permissões e diretórios

### Instalação Manual

Se preferir realizar a instalação manualmente, siga os passos abaixo:

1. Instale as dependências do sistema:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv tor sqlite3 curl git
```

2. Crie e ative um ambiente virtual Python:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

4. Inicialize o banco de dados:
```bash
python -c "from db import init_db, migrar_banco; init_db(); migrar_banco()"
```

5. Verifique a conexão com Tor:
```bash
python torcheck.py
```

## Estrutura de Diretórios

```
omonitor/
├── app.py                    # Aplicação principal Flask
├── coletor.py                # Módulo de coleta e busca
├── db.py                     # Módulo de banco de dados
├── busca_valida_semantica.py # Módulo de validação semântica
├── requirements.txt          # Dependências Python
├── install.sh                # Script de instalação
├── torcheck.py               # Verificador de conexão Tor
├── static/                   # Arquivos estáticos
│   ├── css/                  # Folhas de estilo CSS
│   ├── js/                   # Arquivos JavaScript
│   └── images/               # Imagens e recursos visuais
├── templates/                # Templates HTML
│   ├── base.html             # Template base
│   ├── index.html            # Página inicial
│   ├── resultados.html       # Página de resultados
│   ├── analise.html          # Página de análise
│   ├── cadastro.html         # Página de cadastro
│   ├── ferramentas.html      # Página de ferramentas
│   └── registros.html        # Página de registros
└── logs/                     # Arquivos de log
    ├── app.log               # Log da aplicação
    ├── coletor.log           # Log do coletor
    ├── db.log                # Log do banco de dados
    └── busca_semantica.log   # Log de busca semântica
```

## Funcionalidades Principais

### Busca de Vazamentos

O sistema permite buscar termos sensíveis em diversas fontes da web, incluindo sites da surface web, deep web e dark web. Para realizar uma busca:

1. Acesse a página inicial
2. Digite o termo a ser buscado no campo de busca
3. Clique no botão "Buscar Vazamentos"
4. Aguarde o processamento da busca
5. Visualize os resultados na tabela

### Validação de Vazamentos

Cada resultado encontrado passa por um processo de validação para determinar se é um vazamento real:

- **Validação Automática**: O sistema analisa o contexto, conteúdo e características do link para atribuir um score de validação
- **Validação Manual**: O usuário pode validar manualmente um resultado clicando no botão de validação

### Gerenciamento de Fontes

O sistema permite cadastrar e gerenciar fontes de busca:

1. Acesse a página "Cadastro"
2. Preencha os campos com as informações da fonte
3. Clique em "Adicionar Fonte"

Para verificar o status das fontes:

1. Acesse a página "Ferramentas"
2. Clique em "Verificar" ao lado da fonte desejada

### Exportação de Dados

Os resultados das buscas podem ser exportados em formato CSV:

1. Realize uma busca
2. Clique no botão "Exportar para CSV"
3. Salve o arquivo no local desejado

### Registros de Auditoria

O sistema mantém registros de todas as ações realizadas:

1. Acesse a página "Registros"
2. Visualize o histórico de ações
3. Utilize os filtros para refinar a visualização

## Integração com Tor

O Onion Monitor utiliza a rede Tor para acessar sites .onion na dark web. Para garantir o funcionamento correto:

1. Verifique se o serviço Tor está em execução:
```bash
sudo systemctl status tor
```

2. Se não estiver em execução, inicie-o:
```bash
sudo systemctl start tor
```

3. Verifique a conexão com Tor:
```bash
python torcheck.py
```

## Solução de Problemas

### Problemas de Conexão com Tor

Se o sistema não conseguir conectar-se à rede Tor:

1. Verifique se o serviço Tor está em execução
2. Confirme se a porta 9050 está disponível e não bloqueada por firewall
3. Reinicie o serviço Tor: `sudo systemctl restart tor`

### Erros de Banco de Dados

Se ocorrerem erros relacionados ao banco de dados:

1. Verifique as permissões do arquivo de banco de dados: `chmod 666 onion_monitor.db`
2. Execute a migração do banco: `python -c "from db import migrar_banco; migrar_banco()"`
3. Se necessário, reinicialize o banco: `python -c "from db import init_db; init_db()"`

### Problemas de Dependências

Se houver erros relacionados a bibliotecas Python:

1. Verifique se todas as dependências estão instaladas: `pip list`
2. Reinstale as dependências: `pip install -r requirements.txt`
3. Atualize o pip: `pip install --upgrade pip`

## Segurança e Boas Práticas

- **Não utilize** o sistema para fins ilegais ou antiéticos
- Mantenha o sistema atualizado com as últimas correções de segurança
- Utilize o sistema em uma rede segura e isolada
- Não compartilhe credenciais ou informações sensíveis encontradas
- Reporte vazamentos legítimos às autoridades competentes

## Manutenção e Atualizações

Para manter o sistema funcionando corretamente:

1. Verifique regularmente o status das fontes
2. Atualize as dependências periodicamente
3. Monitore os logs para identificar possíveis problemas
4. Faça backup do banco de dados regularmente

## Suporte e Contato

Para suporte técnico ou dúvidas sobre o sistema, entre em contato:

- Email: suporte@onionmonitor.com
- GitHub: https://github.com/onionmonitor/v1

---

Desenvolvido por Luiz Vaisconcelos  
Email: luiz.vaisconcelos@gmail.com  
LinkedIn: https://www.linkedin.com/in/vaisconcelos/  
GitHub: https://github.com/luizhvaisconcelos
