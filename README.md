# RELATÓRIO TÉCNICO, MANUAL DE VISUALIZAÇÃO E INTEGRAÇÃO (VRP)

## Módulo de Interface Gráfica, Telemetria e Estabilidade de Sistema — 2º Integrante - Lucas Camilo

Este documento apresenta a camada de visualização do projeto VRP (Problema de Roteamento de Veículos), aplicado ao contexto de logística hospitalar crítica, funcionando como relatório técnico oficial e guia de engenharia.

Fiquei responsável pela organização estrutural do projeto em Python, configuração do ambiente de desenvolvimento, construção da interface gráfica, integração síncrona com o algoritmo genético e implementação dos testes automatizados de validação. O foco foi transformar as soluções cromossômicas abstratas do core em uma visualização reativa em tempo real, mantendo desacoplamento total entre lógica de negócio e interface.

---

# 1. Visão Geral do Escopo

Com o algoritmo genético e seus operadores evolutivos já implementados pelo Integrante 1, minha contribuição consistiu em consumir os dados brutos gerados (frotas, rotas ordinais, fitness e histórico) e representá-los graficamente através de um gêmeo digital interativo.

A arquitetura já previa a separação entre core e interface. A implementação seguiu estritamente esse princípio, mantendo a interface de apresentação como consumidora do motor genético via Inversão de Controle.

Para a renderização, foi utilizada a biblioteca **Pygame**, escolhida por permitir a atualização contínua e a pintura frame a frame da interface gráfica, viabilizando que o analista assista ao processo de convergência e evolução biológica do algoritmo em tempo real.

---

## Entregáveis Principais

| Componente | Status | Observação |
|------------|--------|-------------|
| Estrutura modular do projeto | 100% | Separação entre core e interface |
| Integração com o motor genético | 100% | Consumo do OtimizadorVRP |
| Conversão de coordenadas | 100% | Mapeamento cartesiano para pixels |
| HUD de telemetria | 100% | Exibição de métricas do sistema |
| Testes automatizados | 100% | Validação com pytest |

---

# 2. Decisões de Arquitetura

## 2.1 Integração com o Core (Execução do Motor e Callbacks)

A integração com o algoritmo genético ocorre através da classe `OtimizadorVRP`, responsável por executar o processo de otimização combinatória. Para evitar o acoplamento deletério entre a física do algoritmo e a camada gráfica, adotei um padrão de **Inversão de Controle (IoC) baseado em funções Callback via Expressões Lambda**.

O motor genético roda de forma agnóstica à interface. No entanto, a cada geração concluída, o loop interno do algoritmo dispara o callback, enviando o melhor indivíduo e o histórico atual para que a interface limpe o buffer da tela e redesenhe o grafo instantaneamente.

### Execução padrão (Agnóstica à Interface):
```python
otimizador = OtimizadorVRP(
    pontos=pontos_logistica,
    modelos_veiculos=frota_disponivel
)
melhor_solucao = otimizador.executar()
```
Execução com Callback (Monitoramento em Tempo Real):

```Python
melhor_solucao = otimizador.executar(
    callback=lambda melhor, historico: atualizar_frame_tempo_real(
        pontos, melhor, historico
    )
)
```
## 2.2 Conversão de Coordenadas e Identidade Visual
Os pontos de entrega gerados pelo algoritmo flutuam em um sistema cartesiano abstrato no intervalo de [-20.0, 20.0]. Como o Pygame utiliza coordenadas estritas em pixels a partir do canto superior esquerdo (0,0), foi desenvolvida uma função de transformação linear espacial. Esta função aplica margens de segurança de 60px para prevenir o estrangulamento visual ou corte de nós nas bordas da janela:

```Python
def converter_coordenadas(x_cartesiano, y_cartesiano):
    pixel_x = ((x_cartesiano + 20) * (680 / 40)) + 60
    pixel_y = ((-y_cartesiano + 20) * (580 / 40)) + 60
    return int(pixel_x), int(pixel_y)
```
Melhorias visuais e de UI/UX aplicadas:
Hospital Central (Depósito): Destacado com tamanho fixo e coloração vermelha suave (COR_HOSPITAL).

Pontos de Entrega Padrão: Representados por círculos na cor azul (COR_PONTO_NORMAL).

Pontos Críticos de Urgência Médica: Exibidos na cor âmbar (COR_PONTO_CRITICO) com uma animação senoidal de pulsação (math.sin), alterando dinamicamente o raio do nó ao longo do tempo para capturar a atenção imediata do operador humano.

Rotas Diferenciadas: Cada veículo ativo recebe uma cor exclusiva contida na paleta CORES_ROTAS, facilitando o rastreamento visual das trajetórias sobrepostas.

## 2.3 HUD e Visualização Estatística de Dados
A área total da interface de 1200x700px foi dividida em duas subregiões bem definidas:

Viewport Principal (800x700px): Espaço reservado para a renderização do grafo geográfico, nós hospitalares e as linhas de fluxo das rotas.

HUD Lateral (400x700px): Painel escuro de telemetria textual e gráfica para suporte à tomada de decisão.

Componentes de Telemetria Exibidos no HUD:
Custo Atual (Fitness): Exibição numérica em tempo real do custo total da rota (distâncias e penalidades).

Barras de Carga Volumétrica: O sistema lê a sequência de IDs de pontos visitados por cada veículo, soma suas demandas de carga em tempo real e desenha retângulos dinâmicos que funcionam como barras de progresso, alertando visualmente a proximidade do limite de capacidade máxima do veículo.

Curva de Convergência Histórica: Mapeamento pixel a pixel do vetor historico_fitness gerando um gráfico de linhas contínuo no canto inferior do painel, o que comprova visualmente a estabilização e eficácia dos operadores evolutivos do algoritmo.

# 3. Controle de Execução e Estabilidade do S.O.
Processamentos matemáticos pesados e contínuos tendem a reter o controle do fluxo de execução. Quando o algoritmo genético atinge seu critério de parada, se a aplicação encerrar ou interromper abruptamente a escuta do sistema, o Sistema Operacional (S.O.) assume que a janela travou por falta de consumo de sua fila de mensagens, exibindo o status de "Não Respondendo".

Para mitigar esse problema e garantir a usabilidade corporativa, implementei a função manter_tela_aberta() baseada na retenção de estado:

```Python
def manter_tela_aberta():
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

    pygame.quit()
    sys.exit()
```

Assim que a convergência é atingida no main.py, a thread principal chaveia a sua execução para este laço infinito focado estritamente em responder aos eventos do S.O. Isso congela o estado final das melhores rotas calculadas na tela, permitindo auditoria humana prolongada e análise estatística dos custos e frotas até que o usuário decida fechar a janela manualmente.

# 4. Testes Automatizados
Em conformidade com a responsabilidade de garantir a estabilidade do ecossistema de software, criei uma suíte de testes unitários e de integração utilizando o framework pytest. O objetivo foi isolar a lógica matemática e os pipelines de dados visuais de quaisquer efeitos colaterais puramente gráficos da interface.

A suíte implementada em tests/test_visualizacao.py cobre os seguintes pilares:

Determinismo Geométrico (test_conversao_coordenadas_origem_cartesiana): Garante que o ponto central (0.0, 0.0) seja mapeado exatamente no centro do Viewport útil da tela (400px, 350px).

Limites de Fronteira do Domínio (test_conversao_coordenadas_limites_do_dominio): Valida se os extremos cartesianos de (-20.0, 20.0) respeitam as margens de proteção estabelecidas sem risco de transbordo de tela.

Integridade de Telemetria (test_pipeline_streaming_telemetria_callback): Utiliza um objeto simulado (Mock) do motor genético para certificar que os dados de fitness e o histórico cruzam a fronteira do callback e chegam à camada visual de forma íntegra, sem perda de precisão decimal.

Validação de Regras de Logística na HUD (test_calculo_acumulado_carga_frota_na_visualizacao): Testa se o algoritmo agregador que varre as rotas computa corretamente a soma das demandas de carga dos pontos e gera o coeficiente percentual exato que dimensiona as barras gráficas na interface do usuário.

# 5. Guia de Configuração e Execução
Siga os passos abaixo para configurar o ambiente de desenvolvimento isolado, instalar as dependências necessárias e rodar a aplicação e seus testes.

## 5.1 Pré-requisitos
Certifique-se de ter o Python 3.10 ou superior instalado em seu sistema operacional.

## 5.2 Clonar o Repositório e Acessar o Diretório
```Bash
git clone <url-do-seu-repositorio>
cd <nome-do-repositorio>
```
## 5.3 Criar e Ativar o Ambiente Virtual (venv)

Linux / macOS:

```Bash
python3 -m venv venv
source venv/bin/activate
```

Windows (Prompt de Comando / CMD):

```DOS
python -m venv venv
call venv\Scripts\activate.bat
```

Windows (PowerShell):
```PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 5.4 Instalar as Dependências via Arquivo de Requisitos
Atualize o gerenciador de pacotes e realize a instalação automatizada de todas as dependências do ecossistema (pygame, numpy, pytest) mapeadas no arquivo de manifesto:

```Bash
pip install --upgrade pip
pip install -r requirements.txt
```
(Nota: Certifique-se de que o arquivo requirements.txt está presente na raiz do diretório com as linhas listando as dependências do projeto).

## 5.5 Executar a Aplicação Principal
Inicia a simulação gráfica renderizando a convergência das rotas em tempo real:

```Bash
python main.py
```

## 5.6 Executar a Suíte de Testes Automatizados
Para rodar a validação matemática desenvolvida para a camada visual:

```Bash
pytest tests/
```

# 6. Manual de Integração para os Próximos Integrantes
Para garantir a continuidade e a escalabilidade do Tech Challenge (Fase 2), este manual estabelece os contratos de dados, interfaces e diretrizes técnicas para os Integrantes 3 e 4.

## Módulo do Integrante 3 — Inteligência Artificial
Sua responsabilidade é acoplar uma camada de inteligência cognitiva (LLM - OpenAI ou equivalente) sobre os dados finais obtidos pelo motor de otimização. Você consumirá a melhor solução encontrada e desenvolverá os prompts necessários para a geração de relatórios executivos, instruções em linguagem natural para os motoristas e uma interface de consulta estilo chat.

Contrato de Dados (Como extrair as informações do Core)
Ao final do processamento no arquivo main.py, o objeto melhor_solucao (instância de IndividuoVRP) encapsula todo o cenário lógico otimizado. Você deve ler estes atributos para montar o contexto de prompt que será enviado à API da LLM:

```Python
# Custo total consolidado (distância + penalidades) para o Relatório Executivo
custo_total = melhor_solucao.fitness 

# Varredura das frotas para geração de Instruções aos Motoristas
for veiculo in melhor_solucao.frotas:
    if len(veiculo.rota) > 2:
        id_carro = veiculo.id_veiculo
        capacidade_maxima = veiculo.capacidade_max
        
        # Lista ordenada de IDs dos pontos a serem visitados (Ex: [0, 4, 11, 2, 0])
        sequencia_visitas = veiculo.rota 
        
        # Soma da demanda real de medicamentos alocada neste veículo
        carga_atual = sum(pontos[idx].demanda_carga for idx in veiculo.rota)
        
        # Identificação se a rota deste motorista possui algum ponto com urgência médica
        contem_ponto_critico = any(pontos[idx].e_critico for idx in veiculo.rota)
```

### Prompt do Sistema Sugerido (System Prompt)

Ao enviar os dados estruturados em JSON para a LLM, utilize uma parametrização de engenharia de prompt restrita:

```Plaintext
Você é o Assistente de Inteligência Artificial Especialista em Logística Médica do Hospital Central.
Com base nos dados estruturados de frotas e rotas fornecidos em formato JSON, gere:

1. Instruções Operacionais por Veículo: Instruções textuais claras para o motorista 
contendo a ordem das entregas e alertas explícitos de segurança caso sua rota possua
pontos com e_critico=True.

2. Relatório de Eficiência Logística: 
Um sumário focado em negócios para a diretoria detalhando o custo de fitness final, 
taxa de ociosidade de carga dos caminhões e avaliação de gargalos.
```

## Módulo do Integrante 4 — Infraestrutura e Cloud
Sua responsabilidade é empacotar a aplicação completa (Core, a Interface Pygame desenvolvida por mim, e as APIs de IA desenvolvidas pelo Integrante 3) utilizando containers Docker, provisionar a infraestrutura de computação e segurança em ambiente de nuvem utilizando Terraform e documentar a arquitetura da solução.

Desafio de Infraestrutura: Renderização do Pygame em Modo Headless
A biblioteca Pygame exige nativamente uma interface gráfica ou servidor de exibição ativo (X11, Wayland ou DirectX) acoplado ao hardware. Ambientes de nuvem (como instâncias AWS EC2, AWS ECS Fargate ou instâncias do Google Cloud) operam estritamente em modo Headless (servidores sem monitor).

Para evitar erros de inicialização do Pygame no ambiente do container, implemente uma das duas soluções de infraestrutura abaixo:

- Opção 1 (Driver Virtual Dummy via Variável de Ambiente): Configurar o Pygame para rodar no container direcionando a saída de vídeo para um driver fantasma em memória:

    ```Bash
    export SDL_VIDEODRIVER=dummy
    ```
-  Opção 2 (Servidor de Framebuffer Virtualizado no Dockerfile): Instalar o pacote xvfb na imagem Linux do container. O xvfb emula um display virtual em memória RAM, permitindo que o Pygame renderize os frames e execute as janelas normalmente dentro do container sem travar o pipeline:

    ```Dockerfile
    FROM python:3.10-slim
    RUN apt-get update && apt-get install -y xvfb freeglut3-dev && rm -rf /var/lib/apt/lists/*
    WORKDIR /app
    COPY . .
    RUN pip install -r requirements.txt
    # Dispara a aplicação empacotada dentro do wrapper do xvfb
    CMD ["xvfb-run", "--server-args=-screen 0 1200x700x24", "python", "main.py"]
    ```

### Recomendações de Arquitetura em Nuvem para provisionamento via Terraform:
- Armazenamento de Credenciais Securas: Utilizar o AWS Secrets Manager ou Google Secret Manager para guardar chaves de API restritas (OPENAI_API_KEY) necessárias para o módulo de IA.

- Automação de CI/CD: Estruturar um fluxo que acione o runner do pytest tests/ (desenvolvido por mim) antes de realizar o build e push automático da imagem Docker para o registro de containers da nuvem (AWS ECR ou Google Artifact Registry).