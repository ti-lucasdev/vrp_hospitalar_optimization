import pygame
import sys
import math

# Configurações da janela
LARGURA_MAPA = 800
LARGURA_PAINEL = 400 
LARGURA_JANELA = LARGURA_MAPA + LARGURA_PAINEL
ALTURA_JANELA = 700

# Cores da interface
COR_FUNDO_MAPA = (24, 26, 32)
COR_PAINEL = (32, 35, 43)
COR_TEXTO_PRINCIPAL = (240, 243, 250)
COR_TEXTO_MUTED = (140, 150, 170)

# Cores dos elementos exibidos no mapa
COR_HOSPITAL = (239, 68, 68)       # Vermelho
COR_PONTO_NORMAL = (59, 130, 246)  # Azul 
COR_PONTO_CRITICO = (245, 158, 11) # Laranja
COR_GRAFICO_LINHA = (16, 185, 129) # Verde

# Cores utilizadas para identificar cada rota
CORES_ROTAS = [
    (16, 185, 129),  # Verde
    (139, 92, 246),  # Violeta
    (236, 72, 153),  # Rosa Claro
    (6, 182, 212),   # Ciano
    (234, 179, 8)    # Amarelo
]

_fonte_titulo = None
_fonte_sub = None
_fonte_comum = None
_tela = None

def inicializar_tela():
    """Inicializa a janela do Pygame e carrega as fontes utilizadas na interface."""
    global _fonte_titulo, _fonte_sub, _fonte_comum, _tela

    pygame.init()
    pygame.font.init()

    _tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
    pygame.display.set_caption("Otimizador de Rotas Hospitalares (VRP)")

    _fonte_titulo = pygame.font.SysFont("Segoe UI", 18, bold=True)
    _fonte_sub = pygame.font.SysFont("Segoe UI", 14, bold=True)
    _fonte_comum = pygame.font.SysFont("Segoe UI", 13, bold=False)

def converter_coordenadas(x, y):
    """
    Converte as coordenadas do simulador para coordenadas da tela.

    O simulador trabalha com valores contínuos no intervalo de -20 a 20.
    Aqui esses valores são convertidos para pixels, considerando as margens
    da janela e a inversão do eixo Y para que a posição seja exibida
    corretamente na tela.
    """

    # Mantém uma margem entre os pontos e as bordas da janela.
    margem = 60

    # Calcula o fator de escala para cada eixo.
    escala_x = (LARGURA_MAPA - 2 * margem) / 40.0
    escala_y = (ALTURA_JANELA - 2 * margem) / 40.0

    # Converte a coordenada X para a posição correspondente na tela.
    tela_x = int((x + 20) * escala_x) + margem

    # Converte a coordenada Y invertendo o eixo para o padrão utilizado pelo Pygame.
    tela_y = int((-y + 20) * escala_y) + margem

    return tela_x, tela_y

def atualizar_frame_tempo_real(pontos_entrega, melhor_solucao, historico_fitness):
    """Desenha o mapa, as rotas e o painel de informações da simulação."""
    global _tela, _fonte_titulo, _fonte_sub, _fonte_comum

    # Processa os eventos da janela para permitir o fechamento da aplicação.
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if _tela is None:
        return

    # Obtém o tempo atual para controlar as animações da interface.
    tempo_atual = pygame.time.get_ticks()

    # ----------------------------------------------------
    # MAPA
    # ----------------------------------------------------

    # Define a área onde o mapa será desenhado.
    sub_tela_mapa = pygame.Rect(0, 0, LARGURA_MAPA, ALTURA_JANELA)
    pygame.draw.rect(_tela, COR_FUNDO_MAPA, sub_tela_mapa)

    # Cria uma camada transparente utilizada para o efeito de brilho das rotas.
    camada_glow = pygame.Surface((LARGURA_MAPA, ALTURA_JANELA), pygame.SRCALPHA)

    # Desenha todas as rotas da solução atual.
    for indice, veiculo in enumerate(melhor_solucao.frotas):

        # Desconsidera rotas que possuem apenas o ponto inicial e final.
        if len(veiculo.rota) > 2:

            cor_rota = CORES_ROTAS[indice % len(CORES_ROTAS)]
            pontos_da_linha = []

            # Converte cada ponto da rota para sua posição na tela.
            for id_ponto in veiculo.rota:
                ponto_real = pontos_entrega[id_ponto]
                px, py = converter_coordenadas(ponto_real.x, ponto_real.y)
                pontos_da_linha.append((px, py))

            if len(pontos_da_linha) >= 2:

                # Desenha primeiro uma linha mais larga e transparente para criar
                # um efeito de destaque na rota.
                pygame.draw.lines(camada_glow, (*cor_rota, 35), False, pontos_da_linha, 5)

                # Desenha a linha principal da rota.
                pygame.draw.lines(_tela, cor_rota, False, pontos_da_linha, 2)

    # Sobrepõe a camada de brilho ao mapa.
    _tela.blit(camada_glow, (0, 0))

    # ----------------------------------------------------
    # DESENHO DOS PONTOS
    # ----------------------------------------------------

    for ponto in pontos_entrega:

        # Converte a posição do ponto para a tela.
        px, py = converter_coordenadas(ponto.x, ponto.y)

        if ponto.id_ponto == 0:

            # O hospital recebe uma animação de pulsação para facilitar sua
            # identificação durante a simulação.
            pulso_hospital = (math.sin(tempo_atual * 0.002) + 1) / 2
            raio_aura = 10 + int(pulso_hospital * 3)

            # Desenha a aura e o marcador do hospital.
            pygame.draw.circle(_tela, (*COR_HOSPITAL, 60), (px, py), raio_aura)
            pygame.draw.circle(_tela, COR_HOSPITAL, (px, py), 8)
            pygame.draw.circle(_tela, (255, 255, 255), (px, py), 8, 1)

        else:

            if ponto.e_critico:

                # Os pontos críticos também possuem uma animação para destacar
                # sua prioridade no mapa.
                pulso = (math.sin(tempo_atual * 0.005) + 1) / 2
                raio_aura = 6 + int(pulso * 4)

                pygame.draw.circle(_tela, (*COR_PONTO_CRITICO, 50), (px, py), raio_aura)
                pygame.draw.circle(_tela, COR_PONTO_CRITICO, (px, py), 5)

            else:

                # Desenha os pontos de entrega comuns.
                pygame.draw.circle(_tela, COR_PONTO_NORMAL, (px, py), 5)
                pygame.draw.circle(_tela, (255, 255, 255), (px, py), 5, 1)

    # ----------------------------------------------------
    # PAINEL LATERAL
    # ----------------------------------------------------

    # Define a área reservada para o dashboard.
    sub_tela_painel = pygame.Rect(LARGURA_MAPA, 0, LARGURA_PAINEL, ALTURA_JANELA)
    pygame.draw.rect(_tela, COR_PAINEL, sub_tela_painel)

    # Exibe as informações principais da execução.
    txt_painel = _fonte_titulo.render("DASHBOARD VRP", True, COR_TEXTO_PRINCIPAL)
    _tela.blit(txt_painel, (LARGURA_MAPA + 20, 20))

    geracao_atual = len(historico_fitness)

    txt_geracao = _fonte_comum.render(
        f"Geração Atual: {geracao_atual}",
        True,
        COR_TEXTO_MUTED
    )

    _tela.blit(txt_geracao, (LARGURA_MAPA + 20, 48))

    txt_fit_label = _fonte_comum.render(
        "Melhor Custo (Fitness):",
        True,
        COR_TEXTO_MUTED
    )

    txt_fit_valor = _fonte_titulo.render(
        f"{melhor_solucao.fitness:.2f}",
        True,
        COR_GRAFICO_LINHA
    )

    _tela.blit(txt_fit_label, (LARGURA_MAPA + 20, 75))
    _tela.blit(txt_fit_valor, (LARGURA_MAPA + 20, 95))
    # ----------------------------------------------------
    # LEGENDA DO MAPA
    # ----------------------------------------------------

    y_legenda = 135

    txt_leg_titulo = _fonte_sub.render(
        "Legenda do Mapa",
        True,
        COR_TEXTO_PRINCIPAL
    )

    _tela.blit(txt_leg_titulo, (LARGURA_MAPA + 20, y_legenda))

    # Itens exibidos na legenda do mapa.
    itens_legenda = [
        (COR_HOSPITAL, "Hospital Central (Depósito)"),
        (COR_PONTO_CRITICO, "Ponto Crítico (Prioridade Alta)"),
        (COR_PONTO_NORMAL, "Ponto de Entrega Normal")
    ]

    for cor, rotulo in itens_legenda:

        y_legenda += 22

        # Desenha o marcador correspondente ao tipo de ponto.
        pygame.draw.circle(_tela, cor, (LARGURA_MAPA + 26, y_legenda + 8), 5)

        # Adiciona uma borda branca apenas aos pontos comuns.
        if cor != COR_PONTO_CRITICO and cor != COR_HOSPITAL:
            pygame.draw.circle(_tela, (255, 255, 255), (LARGURA_MAPA + 26, y_legenda + 8), 5, 1)

        txt_item = _fonte_comum.render(rotulo, True, COR_TEXTO_MUTED)
        _tela.blit(txt_item, (LARGURA_MAPA + 42, y_legenda))

    # ----------------------------------------------------
    # CAPACIDADE DA FROTA
    # ----------------------------------------------------

    y_offset = 245

    txt_frota_titulo = _fonte_sub.render(
        "Capacidade da Frota",
        True,
        COR_TEXTO_PRINCIPAL
    )

    _tela.blit(txt_frota_titulo, (LARGURA_MAPA + 20, y_offset))

    y_offset += 25

    # Exibe a ocupação de cada veículo utilizando barras de progresso.
    for indice, veiculo in enumerate(melhor_solucao.frotas):

        cor_rota = CORES_ROTAS[indice % len(CORES_ROTAS)]

        carga_total = sum(
            pontos_entrega[idx].demanda_carga
            for idx in veiculo.rota
        )

        # Garante que a porcentagem fique entre 0 e 100%.
        porcentagem = min(1.0, carga_total / veiculo.capacidade_max)

        largura_barra = 220

        # Desenha o fundo da barra.
        pygame.draw.rect(
            _tela,
            (45, 49, 60),
            (LARGURA_MAPA + 20, y_offset, largura_barra, 6),
            border_radius=3
        )

        # Preenche a barra de acordo com a carga transportada.
        if porcentagem > 0:
            pygame.draw.rect(
                _tela,
                cor_rota,
                (
                    LARGURA_MAPA + 20,
                    y_offset,
                    int(largura_barra * porcentagem),
                    6
                ),
                border_radius=3
            )

        status_texto = (
            f"V-{veiculo.id_veiculo}  |  "
            f"{carga_total:.0f} / {veiculo.capacidade_max} kg"
        )

        txt_veiculo = _fonte_comum.render(
            status_texto,
            True,
            COR_TEXTO_MUTED
        )

        _tela.blit(txt_veiculo, (LARGURA_MAPA + 20, y_offset + 10))

        y_offset += 35

    # ----------------------------------------------------
    # GRÁFICO DE CONVERGÊNCIA
    # ----------------------------------------------------

    # Área onde será desenhado o histórico de evolução do fitness.
    gx, gy, g_largura, g_altura = LARGURA_MAPA + 20, 460, 280, 115

    pygame.draw.rect(
        _tela,
        (20, 22, 28),
        (gx, gy, g_largura, g_altura),
        border_radius=6
    )

    if len(historico_fitness) > 1:

        min_fit = min(historico_fitness)
        max_fit = max(historico_fitness)

        # Evita divisão por zero caso todos os valores sejam iguais.
        range_fit = max_fit - min_fit if max_fit != min_fit else 1

        pontos_grafico = []

        # Converte os valores de fitness para posições dentro da área do gráfico.
        for i, fit in enumerate(historico_fitness):

            pos_x = gx + int(
                (i / (len(historico_fitness) - 1)) * g_largura
            )

            pos_y = (
                gy
                + g_altura
                - 8
                - int(((fit - min_fit) / range_fit) * (g_altura - 16))
            )

            pontos_grafico.append((pos_x, pos_y))

        # Liga todos os pontos formando a curva de evolução do algoritmo.
        if len(pontos_grafico) >= 2:
            pygame.draw.lines(
                _tela,
                COR_GRAFICO_LINHA,
                False,
                pontos_grafico,
                1,
            )

        txt_max = _fonte_comum.render(
            f"Max: {max_fit:.0f}",
            True,
            (90, 95, 110)
        )

        txt_min = _fonte_comum.render(
            f"Min: {min_fit:.0f}",
            True,
            COR_GRAFICO_LINHA
        )

        _tela.blit(txt_max, (gx + 10, gy + 5))
        _tela.blit(txt_min, (gx + 10, gy + g_altura - 20))

    # Atualiza a tela com todos os elementos desenhados neste frame.
    pygame.display.flip()


def manter_tela_aberta():
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
    pygame.quit()