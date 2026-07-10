# Otimização de Roteamento Hospitalar (VRP)

Sistema de otimização logística aplicado a **entregas hospitalares críticas**, que utiliza **Algoritmos Genéticos** para resolver o Problema de Roteamento de Veículos (VRP). O motor de otimização estocástico é acoplado a uma camada de visualização em tempo real e a um assistente de IA (LLM), permitindo a auditoria humana da convergência das rotas e a consulta em linguagem natural sobre a solução final.

> Este projeto faz parte do **Tech Challenge (Fase 2)** de Inteligência Artificial.

---

## Sumário

1. [Equipe de Desenvolvimento](#1-equipe-de-desenvolvimento)
2. [Visão Geral do Escopo](#2-visão-geral-do-escopo)
3. [Arquitetura e Contrato de Desacoplamento](#3-arquitetura-e-contrato-de-desacoplamento)
4. [Core — Motor Genético (Integrante 1)](#4-core--motor-genético-integrante-1)
5. [Interface Gráfica e Telemetria (Integrante 2)](#5-interface-gráfica-e-telemetria-integrante-2)
6. [Camada de Inteligência Artificial (Integrante 3)](#6-camada-de-inteligência-artificial-integrante-3)
7. [Testes Automatizados](#7-testes-automatizados)
8. [Configuração e Execução](#8-configuração-e-execução)
9. [Infraestrutura e Deploy (Integrante 4)](#9-infraestrutura-e-deploy-integrante-4)

---

## 1. Equipe de Desenvolvimento

Trabalho desenvolvido de forma colaborativa, com a seguinte divisão de responsabilidades:

| Integrante                                                      | Responsável | Módulo |
|-----------------------------------------------------------------|-------------|--------|
| **Integrante 1** — Marcius Lucas Fernandes (rm371349)                   | Core do sistema, motor genético, heurísticas de inicialização e modelagem matemática | `src/core/` |
| **Integrante 2** — Lucas Camilo (rm373405)                      | Interface gráfica (Pygame), telemetria, integração síncrona com o motor e testes automatizados | `src/interface/` |
| **Integrante 3** — Gustavo de Carvalho Dantas (rm372153)        | Camada de inteligência cognitiva (LLM) sobre os dados finais da otimização | `src/ia/` |
| **Integrante 4** — Sabrina de Oliveira Zago Capanema (rm370447) | Empacotamento (Docker), provisionamento de nuvem (Terraform) e documentação de arquitetura | *(planejado)* |

---

## 2. Visão Geral do Escopo

O sistema resolve o VRP no contexto de logística hospitalar crítica, integrando três camadas independentes:

- Um **motor de otimização estocástico** (Algoritmo Genético) que evolui soluções de roteamento respeitando restrições de capacidade, autonomia e prioridade de pontos com urgência médica.
- Uma **interface gráfica em tempo real** que funciona como um gêmeo digital interativo, permitindo ao analista assistir ao processo de convergência frame a frame.
- Um **assistente de IA** que, ao final do processamento, responde perguntas sobre a melhor solução encontrada (instruções aos motoristas, relatórios executivos e sugestões de melhoria).

Para a renderização foi utilizada a biblioteca **Pygame**, escolhida por permitir a atualização contínua e a pintura frame a frame, viabilizando a visualização da evolução biológica do algoritmo em tempo real.

---

## 3. Arquitetura e Contrato de Desacoplamento

A arquitetura prevê **separação estrita entre Core, Interface e IA**. As três camadas nunca importam a implementação umas das outras — elas se encontram apenas em fronteiras de dados bem definidas, o que mantém o núcleo computacional puro, testável e reutilizável.

```
main.py
  ├── src/core/       →  Motor genético (agnóstico a Pygame e OpenAI)
  ├── src/interface/  →  Renderização Pygame (consome o Core via callback)
  └── src/ia/         →  LLM (consome apenas o contexto estruturado)
```

### 3.1 Integração Core → Interface (Callback / IoC)

A integração ocorre via **Inversão de Controle (IoC) baseada em funções callback**. O motor genético (`OtimizadorVRP`) roda de forma agnóstica à interface; a cada geração concluída, o loop interno dispara o callback, enviando o melhor indivíduo e o histórico atual para que a interface redesenhe o grafo instantaneamente.

**Execução padrão (agnóstica à interface):**
```python
otimizador = OtimizadorVRP(pontos=pontos_logistica, modelos_veiculos=frota_disponivel)
melhor_solucao = otimizador.executar()
```

**Execução com callback (monitoramento em tempo real):**
```python
melhor_solucao = otimizador.executar(
    callback=lambda melhor, historico: atualizar_frame_tempo_real(pontos, melhor, historico)
)
```

A lambda captura a lista estática de `pontos` por closure e mapeia as variáveis dinâmicas (`melhor`, `historico`) diretamente para o pipeline de pintura da interface.

### 3.2 Integração Core → IA (Contexto Estruturado)

A fronteira entre o resultado da otimização e a LLM é a função pura `construir_contexto(pontos, solucao)`, que serializa o `IndividuoVRP` num dicionário JSON. A camada de IA **não conhece o Pygame** e a interface **não conhece a OpenAI** — a integração é feita exclusivamente por esse contexto e por uma função `responder(pergunta)`.

---

## 4. Core — Motor Genético (Integrante 1)

O núcleo modela o problema e conduz a evolução das soluções.

### 4.1 Modelagem de Dados (`src/core/models.py`)

- **`PontoEntrega`** — um nó do grafo (hospital/unidade ou depósito). Atributos: coordenadas `(x, y)`, `demanda_carga` e `e_critico` (define alta prioridade no fitness). O ID `0` representa o **Hospital Central (depósito)**.
- **`Veiculo`** — uma unidade da frota, com `capacidade_max`, `autonomia_max` e a `rota` (lista ordenada de IDs).
- **`IndividuoVRP`** — um cromossomo (uma solução completa): a frota inteira e seu `fitness`.

### 4.2 Função de Fitness

O `CalculadorFitness` avalia cada solução computando:

- **Distância total** percorrida por cada veículo (matriz de distâncias pré-calculada em `GerenciadorDistancias` para desempenho).
- **Multiplicador de prioridade** (`peso_prioridade`) sobre os trechos que chegam a pontos críticos.
- **Penalidades** (10000) quando um veículo excede `capacidade_max` ou `autonomia_max`.

Quanto **menor** o fitness, melhor a solução.

### 4.3 Operadores Evolutivos

- **Inicialização heurística**: população inicial gerada pela heurística do **vizinho mais próximo aleatorizado**, respeitando a capacidade dos veículos.
- **Codificação**: crossover e mutação operam sobre uma sequência linear de genes (clientes), que é depois **decodificada** de volta para frotas validando as restrições de carga.
- **Cruzamento OX** (`Ordered Crossover`): preserva a ordem relativa de permutações.
- **Mutação Swap**: troca a posição de dois nós na sequência logística.
- **Seleção por torneio** e **elitismo** para preservar os melhores indivíduos entre gerações.

O loop encerra ao atingir `max_geracoes` ou após `max_estagnacao` gerações sem melhoria.

---

## 5. Interface Gráfica e Telemetria (Integrante 2)

A camada de apresentação consome os dados brutos gerados pelo motor (frotas, rotas ordinais, fitness e histórico) e os representa graficamente como um gêmeo digital interativo.

### 5.1 Conversão de Coordenadas e Identidade Visual

Os pontos flutuam em um sistema cartesiano abstrato no intervalo `[-20.0, 20.0]`. Como o Pygame usa pixels a partir do canto superior esquerdo `(0,0)`, uma transformação linear com margens de segurança de 60px previne o corte de nós nas bordas:

```python
def converter_coordenadas(x_cartesiano, y_cartesiano):
    pixel_x = ((x_cartesiano + 20) * (680 / 40)) + 60
    pixel_y = ((-y_cartesiano + 20) * (580 / 40)) + 60
    return int(pixel_x), int(pixel_y)
```

Elementos visuais:
- **Hospital Central (depósito)**: destacado em vermelho suave (`COR_HOSPITAL`).
- **Pontos de entrega padrão**: círculos azuis (`COR_PONTO_NORMAL`).
- **Pontos críticos de urgência médica**: âmbar (`COR_PONTO_CRITICO`), com **animação senoidal de pulsação** (`math.sin`) para capturar a atenção do operador.
- **Rotas**: cada veículo ativo recebe uma cor exclusiva da paleta `CORES_ROTAS`.

### 5.2 HUD e Visualização Estatística

A janela é dividida em regiões bem definidas — **viewport principal** (renderização do grafo) e **HUD lateral** (painel escuro de telemetria). O HUD exibe:

- **Custo atual (fitness)**: valor numérico do custo total em tempo real.
- **Barras de carga volumétrica**: somam a demanda dos pontos visitados por veículo e desenham barras de progresso, alertando sobre a proximidade do limite de capacidade.
- **Curva de convergência histórica**: gráfico de linhas do vetor `historico_fitness`, comprovando a estabilização dos operadores evolutivos.

### 5.3 Controle de Execução e Estabilidade do S.O.

Processamentos matemáticos pesados tendem a reter o fluxo de execução; ao atingir o critério de parada, o S.O. pode marcar a janela como "Não Respondendo". Para mitigar isso, a função `manter_tela_aberta()` chaveia a thread principal para um laço focado estritamente em responder aos eventos do S.O., congelando o estado final das rotas para auditoria humana prolongada até o usuário fechar a janela.

---

## 6. Camada de Inteligência Artificial (Integrante 3)

Acopla uma camada de inteligência cognitiva (LLM — OpenAI) sobre os dados finais da otimização. A experiência é **unificada no `main.py`**: após a convergência do algoritmo genético, a janela Pygame é alargada e ganha uma terceira coluna com o **chat do assistente de IA** (mapa e dashboard permanecem visíveis), exibindo perguntas de exemplo clicáveis.

- Nenhuma requisição é feita à API até o usuário perguntar.
- Requer `OPENAI_API_KEY` no ambiente ou em um arquivo `.env` (ver `.env.example`). **Sem a chave, a simulação roda normalmente e apenas o chat fica desativado.**
- O modelo é configurável via `OPENAI_MODEL` (default `gpt-4o-mini`).

**Módulos** (`src/ia/`): construção do contexto em `contexto.py`, engenharia de prompt em `prompts.py` e integração com a OpenAI em `assistente.py`.

**Contrato de dados** — ao final do processamento, o objeto `melhor_solucao` (instância de `IndividuoVRP`) encapsula o cenário otimizado. A camada de IA lê estes atributos para montar o contexto:

```python
# Custo total consolidado (distância + penalidades) para o Relatório Executivo
custo_total = melhor_solucao.fitness

# Varredura das frotas para geração de instruções aos motoristas
for veiculo in melhor_solucao.frotas:
    if len(veiculo.rota) > 2:  # ignora veículos ociosos (rota [0, 0])
        sequencia_visitas = veiculo.rota                                      # ex.: [0, 4, 11, 2, 0]
        carga_atual = sum(pontos[idx].demanda_carga for idx in veiculo.rota)  # demanda alocada
        contem_ponto_critico = any(pontos[idx].e_critico for idx in veiculo.rota)
```

**Tarefas suportadas pelo assistente**: instruções operacionais por veículo (com alertas de segurança para pontos `e_critico`), relatório de eficiência logística (custo de fitness, ociosidade de carga, gargalos) e sugestões de melhoria nas rotas.

---

## 7. Testes Automatizados

Suíte em **pytest** que isola a lógica matemática e os pipelines de dados dos efeitos colaterais gráficos. Cobertura principal:

- **Motor genético** (`test_genetic.py`): operadores evolutivos e integridade das soluções.
- **Determinismo geométrico** (`test_visualizacao.py`): garante que `(0.0, 0.0)` seja mapeado ao centro do viewport e que os extremos `(-20.0, 20.0)` respeitem as margens de proteção.
- **Integridade de telemetria**: usa um `MockOtimizadorVRP` para certificar que fitness e histórico cruzam a fronteira do callback sem perda de precisão.
- **Regras de logística na HUD**: valida o cálculo acumulado de carga que dimensiona as barras gráficas.
- **Camada de IA** (`test_ia_contexto.py`): exercita `construir_contexto` de forma pura, **sem acessar a rede**.

Execução: `pytest tests/`

---

## 8. Configuração e Execução

### 8.1 Pré-requisitos

- **Versão do Python:** Recomenda-se obrigatoriamente o uso do **Python 3.12** ou **3.13**.
  
> ⚠️ **Nota importante de ambiente (Compatibilidade):** > - A aplicação **não roda no Python 3.11** ou anterior. O instalador (`pip`) irá travar na montagem do ambiente devido à dependência `numpy==2.5.1`, que exige nativamente o interpretador na versão 3.12 ou superior.
> - Em versões experimentais ou de desenvolvimento como o **Python 3.14**, a instalação do ambiente padrão via `requirements.txt` pode falhar no processo de compilação C++ devido à falta de binários pré-compilados (`.whl`) para algumas bibliotecas tradicionais. Para contornar cenários no Python 3.14, o arquivo de dependências foi ajustado manualmente para utilizar o ecossistema da comunidade através do pacote `pygame-ce==2.5.7`.

### 8.2 Clonar e criar o ambiente virtual

```bash
git clone <url-do-repositorio>
cd vrp_hospitalar_optimization
python -m venv .venv
```

Ativação do ambiente:
- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `call .venv\Scripts\activate.bat`
- **Linux / macOS:** `source .venv/bin/activate`

### 8.3 Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 8.4 (Opcional) Configurar a IA

```bash
cp .env.example .env   # e preencha OPENAI_API_KEY
```

### 8.5 Executar

```bash
python main.py     # inicia a simulação gráfica com convergência em tempo real e chat de IA
pytest tests/      # roda a suíte de testes automatizados
```

> `main.py` define `random.seed(42)` para cenários reproduzíveis — comente ou altere a seed para gerar rotas diferentes a cada execução.

---

## 9. Infraestrutura e Deploy (Integrante 4)

A aplicação completa (Core, Interface Pygame e camada de IA) foi empacotada em containers Docker, com infraestrutura provisionada na AWS via Terraform e um pipeline de CI/CD via GitHub Actions.

### 9.1 Containerização e execução headless do Pygame

Como o Pygame exige nativamente um servidor de exibição, e ambientes de nuvem operam em modo *headless*, foi adotada a solução de **display virtual via Xvfb**, iniciado em segundo plano dentro do próprio container:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    freeglut3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99

CMD ["/bin/bash", "-c", "Xvfb :99 -screen 0 1200x700x24 & sleep 1 && pytest tests/ -v"]
```

> **Nota de compatibilidade:** a imagem base foi atualizada de `python:3.10-slim` para `python:3.12-slim`, já que a dependência `numpy==2.5.1` exige nativamente Python 3.12+.
>
> **Nota de implementação:** optou-se por iniciar o Xvfb manualmente em vez de usar o wrapper `xvfb-run`, que trava indefinidamente sem o pacote `xauth` instalado — abordagem validada em testes locais e no pipeline de CI/CD.

O propósito do modo headless aqui é permitir que a suíte de testes automatizados (`pytest tests/`) rode de forma confiável em ambientes sem monitor (CI/CD) — não a hospedagem remota da janela interativa, que exigiria tecnologias de streaming (VNC) fora do escopo do projeto.

### 9.2 Pipeline de CI/CD (GitHub Actions)

A cada `push`, o workflow `.github/workflows/ci-cd.yml` executa: build da imagem Docker → testes automatizados dentro do container → (exclusivamente na branch `main`, e apenas se os testes passarem) login na AWS e push da imagem validada para o Amazon ECR.

### 9.3 Infraestrutura como código (Terraform)

Definida em `terraform/`, provisiona:

- **Amazon ECR** — repositório privado de imagens Docker, com scan de vulnerabilidades automático;
- **AWS Secrets Manager** — armazena a `OPENAI_API_KEY` com segurança, fora do código-fonte;
- **IAM** — usuário dedicado ao CI/CD com permissão mínima (apenas push no ECR), sem acesso administrativo.

A execução em produção (job batch no ECS Fargate, consumindo a imagem do ECR e a chave do Secrets Manager) está documentada na arquitetura, mas não mantida ativa permanentemente — evitando custos de infraestrutura ociosa em ambiente acadêmico. O provisionamento é validado sob demanda via `terraform apply` / `terraform destroy`.