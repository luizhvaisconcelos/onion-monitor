# Onion Monitor v1 - Manual do Usuário

## Introdução

O Onion Monitor v1 é um sistema de monitoramento de vazamentos com coleta de links .onion e análise de dados. Ele permite buscar termos sensíveis em diversas fontes da surface web e dark web, validar automaticamente os resultados encontrados, e manter um registro completo de todas as operações realizadas.

Este manual fornece instruções detalhadas sobre como instalar, configurar e utilizar o sistema.

## Índice

1. [Instalação](#instalação)
2. [Configuração](#configuração)
3. [Funcionalidades Principais](#funcionalidades-principais)
   - [Busca de Termos](#busca-de-termos)
   - [Análise de Resultados](#análise-de-resultados)
   - [Cadastro de Fontes](#cadastro-de-fontes)
   - [Ferramentas](#ferramentas)
   - [Registros de Auditoria](#registros-de-auditoria)
4. [Agendamento de Buscas](#agendamento-de-buscas)
5. [Validação de Vazamentos](#validação-de-vazamentos)
6. [Exportação de Dados](#exportação-de-dados)
7. [Manutenção](#manutenção)
8. [Solução de Problemas](#solução-de-problemas)

## Instalação

### Requisitos

- Python 3.6 ou superior
- Pip (gerenciador de pacotes do Python)
- Navegador web moderno (Chrome, Firefox, Edge, etc.)

### Passos para Instalação

1. **Descompacte o arquivo ZIP** em um diretório de sua escolha.

2. **Abra um terminal ou prompt de comando** e navegue até o diretório onde o sistema foi descompactado:
   ```
   cd caminho/para/onion_monitor_v1
   ```

3. **Instale as dependências** necessárias:
   ```
   pip install -r requirements.txt
   ```
   
   Se você tiver Python 2 e 3 instalados no mesmo sistema, talvez precise usar `pip3` em vez de `pip`.

4. **Execute o aplicativo**:
   ```
   python app.py
   ```
   
   Ou, se você tiver múltiplas versões do Python:
   ```
   python3 app.py
   ```

5. **Acesse o sistema** abrindo seu navegador e navegando para:
   ```
   http://localhost:5000
   ```

## Configuração

O sistema já vem pré-configurado com fontes padrão para busca na dark web. No entanto, você pode personalizar as seguintes configurações:

### Fontes de Busca

Acesse a página de **Cadastro** para adicionar, editar ou desativar fontes de busca. As fontes padrão incluem:

- Ahmia (mecanismo de busca para .onion)
- Dark.fail (lista de sites .onion)
- Onion.live (diretório de serviços onion)
- Tor.taxi (lista de links .onion)
- Onion.land (lista de links .onion)
- DarkSearch (mecanismo de busca para .onion)

### Banco de Dados

O sistema utiliza SQLite como banco de dados, armazenado no arquivo `onion_monitor.db`. Não é necessária nenhuma configuração adicional para o banco de dados.

## Funcionalidades Principais

### Busca de Termos

A página inicial do sistema permite buscar termos sensíveis nas fontes cadastradas.

1. Digite o termo que deseja buscar no campo de busca.
2. Clique no botão "Buscar".
3. O sistema irá buscar o termo em todas as fontes ativas e exibir os resultados encontrados.
4. Os resultados são automaticamente validados e classificados como vazamentos reais ou não.

### Análise de Resultados

A página de **Análise** fornece estatísticas e gráficos sobre os resultados encontrados.

- Total de coletas realizadas
- Total de termos buscados
- Total de fontes utilizadas
- Total de vazamentos validados
- Gráficos de coletas por fonte, por dia e por termo
- Lista das últimas validações realizadas

### Cadastro de Fontes

A página de **Cadastro** permite gerenciar as fontes de busca.

- Adicionar novas fontes
- Editar fontes existentes
- Ativar ou desativar fontes
- Visualizar o status atual de cada fonte

### Ferramentas

A página de **Ferramentas** oferece funcionalidades adicionais:

- **Verificação de Fontes**: Verifica o status de todas as fontes cadastradas e atualiza automaticamente.
- **Agendamento de Buscas**: Configura buscas automáticas para serem executadas periodicamente.
- **Exportação de Dados**: Exporta os resultados das buscas para arquivos CSV.
- **Relatórios de Auditoria**: Visualiza relatórios detalhados de todas as atividades do sistema.
- **Validação Manual**: Valida manualmente resultados que não foram validados automaticamente.
- **Registros de Atividade**: Visualiza o histórico completo de atividades e operações do sistema.

### Registros de Auditoria

A página de **Registros** exibe um histórico completo de todas as operações realizadas no sistema, incluindo:

- Buscas realizadas
- Validações de vazamentos
- Verificações de fontes
- Exportações de dados
- Outras atividades administrativas

## Agendamento de Buscas

O sistema permite agendar buscas automáticas para serem executadas periodicamente.

### No Linux/Mac (usando Cron)

1. Acesse a página de **Ferramentas** e clique em "Agendar Buscas".
2. Preencha o termo que deseja buscar e o intervalo de tempo.
3. O sistema irá gerar um comando para ser adicionado ao crontab.
4. Abra o terminal e execute:
   ```
   crontab -e
   ```
5. Adicione o comando gerado e salve o arquivo.

### No Windows (usando Agendador de Tarefas)

1. Acesse a página de **Ferramentas** e clique em "Agendar Buscas".
2. Preencha o termo que deseja buscar e o intervalo de tempo.
3. O sistema irá gerar um comando para ser usado no Agendador de Tarefas.
4. Abra o Agendador de Tarefas do Windows.
5. Crie uma nova tarefa e configure-a com o comando gerado.

## Validação de Vazamentos

O sistema valida automaticamente os resultados encontrados, atribuindo um score de 0 a 100 para cada resultado. Um resultado é considerado um vazamento real se o score for igual ou superior a 40.

### Critérios de Validação

Os critérios utilizados para validação incluem:

- Presença de palavras-chave relacionadas a vazamentos no link ou título
- Presença do termo buscado no link ou título
- Presença de extensões de arquivo comuns em vazamentos
- Presença de números que podem indicar datas ou quantidades
- Presença de domínios conhecidos de fóruns de vazamento
- Presença de palavras relacionadas a fóruns ou comunidades

### Validação Manual

Você também pode validar manualmente resultados que não foram validados automaticamente:

1. Na página inicial, localize o resultado que deseja validar.
2. Clique no botão de validação (ícone de check) ao lado do resultado.
3. O sistema irá marcar o resultado como validado e atribuir um score alto.

## Exportação de Dados

O sistema permite exportar os resultados das buscas para arquivos CSV.

1. Acesse a página de **Ferramentas** e clique em "Exportar CSV".
2. O sistema irá gerar um arquivo CSV com todos os resultados encontrados.
3. Você também pode exportar apenas os resultados de um termo específico, adicionando o parâmetro `termo` à URL.

## Manutenção

### Verificação de Fontes

É recomendável verificar regularmente o status das fontes cadastradas:

1. Acesse a página de **Ferramentas** e clique em "Verificar Fontes".
2. O sistema irá verificar o status de todas as fontes e atualizar automaticamente.
3. Fontes inativas serão marcadas como tal e não serão utilizadas nas buscas.

### Backup do Banco de Dados

É recomendável fazer backup regular do banco de dados:

1. Localize o arquivo `onion_monitor.db` no diretório do sistema.
2. Copie este arquivo para um local seguro.

## Solução de Problemas

### Erro ao iniciar o sistema

Se o sistema não iniciar corretamente, verifique:

1. Se todas as dependências foram instaladas corretamente.
2. Se o arquivo `onion_monitor.db` existe e não está corrompido.
3. Se a porta 5000 não está sendo utilizada por outro aplicativo.

### Erro ao buscar termos

Se ocorrerem erros durante a busca de termos, verifique:

1. Se as fontes cadastradas estão ativas e acessíveis.
2. Se o sistema tem acesso à internet.
3. Se o termo buscado não contém caracteres especiais que possam causar problemas.

### Erro ao validar resultados

Se ocorrerem erros durante a validação de resultados, verifique:

1. Se o banco de dados está funcionando corretamente.
2. Se o resultado que está tentando validar ainda existe no banco.

---

## Créditos

Desenvolvido por Luiz Vaisconcelos  
Email: luiz.vaisconcelos@gmail.com  
LinkedIn: https://www.linkedin.com/in/vaisconcelos/  
GitHub: https://github.com/luizhvaisconcelos

---

Para mais informações ou suporte, entre em contato através do email acima.
