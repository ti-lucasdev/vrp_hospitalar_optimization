import os

# Corrige o caminho de certificados corrompidos antes de iniciar a IA
if "SSL_CERT_FILE" in os.environ and not os.path.exists(os.environ["SSL_CERT_FILE"]):
    del os.environ["SSL_CERT_FILE"]

import random

# Importamos as funções novas de tempo real
from src.interface.visualizacao import inicializar_tela, atualizar_frame_tempo_real, manter_tela_aberta
from src.core.models import PontoEntrega, Veiculo
from src.core.genetic_alg import OtimizadorVRP
from src.ia.contexto import construir_contexto
from src.ia.assistente import criar_respondedor, montar_perguntas_exemplo

def gerar_pontos_aleatorios(quantidade: int) -> list[PontoEntrega]:
    """Gera automaticamente uma lista de pontos com coordenadas e cargas aleatórias."""
    pontos = [PontoEntrega(id_ponto=0, x=0.0, y=0.0, demanda_carga=0.0, e_critico=False)]
    for idx in range(1, quantidade):
        coord_x = random.uniform(-20.0, 20.0)
        coord_y = random.uniform(-20.0, 20.0)
        carga = float(random.randint(5, 25))
        critico = random.random() < 0.2
        pontos.append(
            PontoEntrega(id_ponto=idx, x=coord_x, y=coord_y, demanda_carga=carga, e_critico=critico)
        )
    return pontos

def rodar_teste():
    print("=== Inicializando Teste do Motor Genético (VRP) em Tempo Real ===")
    
    QUANTIDADE_PONTOS = 20 
    pontos = gerar_pontos_aleatorios(QUANTIDADE_PONTOS)
    
    modelos_veiculos = [
        Veiculo(id_veiculo=1, capacidade_max=75.0, autonomia_max=200.0),
        Veiculo(id_veiculo=2, capacidade_max=75.0, autonomia_max=200.0),
        Veiculo(id_veiculo=3, capacidade_max=75.0, autonomia_max=200.0),
        Veiculo(id_veiculo=4, capacidade_max=75.0, autonomia_max=200.0),
        Veiculo(id_veiculo=5, capacidade_max=75.0, autonomia_max=200.0),
    ]
    
    otimizador = OtimizadorVRP(
        pontos=pontos,
        modelos_veiculos=modelos_veiculos,
        tamanho_populacao=100,
        max_geracoes=300,
        max_estagnacao=40,
        taxa_mutacao=0.15,
        taxa_elitismo=0.03
    )
    
    # ----------------------------------------------------------------
    # [Etapa 1] Inicializa a interface gráfica antes de executar o algoritmo
    # genético. Faço isso para que a janela e as fontes já estejam
    # carregadas quando a execução começar, evitando atrasos durante
    # o processamento.
    # ----------------------------------------------------------------

    inicializar_tela()
    
    # ----------------------------------------------------------------
    # [Etapa 2] Acoplamento de Envelhecimento Visual via Expressão Lambda:
    # Injetamos uma função anônima que atua como ponte adaptadora. 
    # A estrutura captura a lista estática de 'pontos' através de escopo (closure)
    # e mapeia as variáveis dinâmicas fornecidas pelo otimizador ('melhor', 'historico')
    # diretamente para o pipeline de pintura por frame da interface visual.
    # ----------------------------------------------------------------
    print(f"\nEvoluindo rotas para {QUANTIDADE_PONTOS} pontos... Veja a janela do Pygame!")
    melhor_solucao = otimizador.executar(
        callback=lambda melhor, historico: atualizar_frame_tempo_real(pontos, melhor, historico)
    )
    
    print("\n================ PROCESSAMENTO CONCLUÍDO ================")
    print(f"Melhor Custo Final: {melhor_solucao.fitness:.2f}")

    # ----------------------------------------------------------------
    # [Etapa 3] Chat com o Assistente de IA na própria janela:
    # Após a convergência, a janela é alargada e ganha uma terceira coluna de chat com a LLM sobre a solução
    # final — mapa e dashboard permanecem visíveis. A ponte entre as camadas é a função `responder`, criada
    # pela camada de IA a partir do contexto estruturado — a interface não conhece a OpenAI e a IA não conhece o Pygame.
    # Nenhuma requisição é feita automaticamente: a LLM só é consultada quando o usuário pergunta.
    # Sem OPENAI_API_KEY, a janela apenas congela o resultado do fluxo anterior.
    # ----------------------------------------------------------------
    contexto = construir_contexto(pontos, melhor_solucao)
    responder = criar_respondedor(contexto)
    perguntas_exemplo = None
    if responder is not None:
        perguntas_exemplo = montar_perguntas_exemplo(contexto)
        print("\nChat com o assistente habilitado na janela — faça perguntas por lá.")
    else:
        print("\nAviso: OPENAI_API_KEY não definida (veja .env.example) — "
              "o chat da janela ficou desativado.")

    manter_tela_aberta(
        pontos_entrega=pontos,
        melhor_solucao=melhor_solucao,
        historico_fitness=otimizador.historico_fitness,
        responder=responder,
        perguntas_exemplo=perguntas_exemplo,
    )

if __name__ == "__main__":
    # Para gerar cenários e rotas diferentes a cada execução, comente a seed abaixo ou altere o seu valor
    random.seed()
    rodar_teste()