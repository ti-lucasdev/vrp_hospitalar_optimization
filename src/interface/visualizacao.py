import os
import pygame
import sys
import math
import queue
import threading

# Configurações da janela
LARGURA_MAPA = 800
LARGURA_PAINEL = 320
LARGURA_JANELA = LARGURA_MAPA + LARGURA_PAINEL
LARGURA_CHAT = 400  # Coluna extra aberta no modo chat (janela vai a 1520px)
ALTURA_JANELA = 700

# Fonte usada em todos os textos da interface
SEGOE_UI = "Segoe UI"

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
_fonte_rotulo = None
_tela = None

def inicializar_tela():
    """Inicializa a janela do Pygame e carrega as fontes utilizadas na interface."""
    global _fonte_titulo, _fonte_sub, _fonte_comum, _fonte_rotulo, _tela

    pygame.init()
    pygame.font.init()

    _tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
    pygame.display.set_caption("Otimizador de Rotas Hospitalares (VRP)")

    _fonte_titulo = pygame.font.SysFont(SEGOE_UI, 18, bold=True)
    _fonte_sub = pygame.font.SysFont(SEGOE_UI, 14, bold=True)
    _fonte_comum = pygame.font.SysFont(SEGOE_UI, 13, bold=False)
    _fonte_rotulo = pygame.font.SysFont(SEGOE_UI, 11, bold=True)

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
    """Processa os eventos da janela e desenha um frame completo da simulação."""

    # Processa os eventos da janela para permitir o fechamento da aplicação.
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if _tela is None:
        return

    _desenhar_simulacao(pontos_entrega, melhor_solucao, historico_fitness)

    # Atualiza a tela com todos os elementos desenhados neste frame.
    pygame.display.flip()


def _desenhar_simulacao(pontos_entrega, melhor_solucao, historico_fitness):
    """
    Desenha o mapa, as rotas e o painel de informações (dashboard).

    Não processa eventos nem atualiza a tela (flip) — quem chama controla o loop.
    """
    global _tela, _fonte_titulo, _fonte_sub, _fonte_comum

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

            # Rótulo com o ID do ponto acima da bolinha, com sombra para
            # continuar legível quando cruza as linhas das rotas. Facilita
            # relacionar o mapa com as rotas citadas no chat e no dashboard.
            txt_id = _fonte_rotulo.render(str(ponto.id_ponto), True, COR_TEXTO_PRINCIPAL)
            pos_rotulo = (px - txt_id.get_width() // 2, py - 24)
            sombra = _fonte_rotulo.render(str(ponto.id_ponto), True, (0, 0, 0))
            _tela.blit(sombra, (pos_rotulo[0] + 1, pos_rotulo[1] + 1))
            _tela.blit(txt_id, pos_rotulo)

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


# ----------------------------------------------------
# CHAT COM O ASSISTENTE DE IA (painel lateral pós-convergência)
# ----------------------------------------------------

# Cores específicas do painel de chat
COR_CHAT_USUARIO = (96, 165, 250)        # Azul claro (perguntas)
COR_CHAT_ASSISTENTE = COR_GRAFICO_LINHA  # Verde (respostas)
COR_CHAT_ERRO = (248, 113, 113)          # Vermelho claro (falhas de rede/API)
COR_CAIXA_INPUT = (20, 22, 28)
COR_BORDA_INPUT = (70, 78, 95)
COR_SUGESTAO_FUNDO = (42, 46, 56)
COR_SUGESTAO_HOVER = (58, 63, 78)
COR_DIVISORIA = (55, 60, 74)             # Linhas que separam as regiões do painel
COR_TRILHO_ROLAGEM = (45, 49, 60)        # Fundo da barra de rolagem da conversa

# Geometria do painel de chat (terceira coluna, à direita do dashboard)
_CHAT_MARGEM = 12
_CHAT_LARGURA_TEXTO = LARGURA_CHAT - 2 * _CHAT_MARGEM - 16
_CHAT_TOPO_CONTEUDO = 96
_CHAT_ALTURA_INPUT = 36


# Símbolos que a LLM costuma emitir e que têm um equivalente simples garantido
# na fonte da interface (bullets, travessões, aspas curvas, tab, espaço rígido).
_SUBSTITUICOES_TEXTO = {
    "\t": "  ",
    "•": "-", "◦": "-", "▪": "-", "‣": "-", "·": "-",
    "–": "-", "—": "-",
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "…": "...",
    " ": " ",
}


def _sanitizar_texto(texto, fonte):
    """
    Prepara um texto para renderização: troca símbolos comuns por equivalentes
    simples e descarta caracteres que a fonte não desenha.

    O Pygame/SDL_ttf não tem fallback de fontes como um navegador — qualquer
    caractere ausente na fonte (emojis, setas, marcadores exóticos) viraria um
    retângulo vazio ("tofu") na tela. O filtro combina duas checagens, porque
    `fonte.metrics` sozinho não é confiável (para alguns símbolos ele devolve
    as métricas do glifo-caixinha em vez de None): só passam caracteres da
    faixa latina do Unicode (< U+0250, que cobre todo o português) que também
    tenham glifo confirmado pela fonte.
    """
    for original, substituto in _SUBSTITUICOES_TEXTO.items():
        texto = texto.replace(original, substituto)
    return "".join(
        char for char in texto
        if char == "\n" or (ord(char) < 0x0250 and fonte.metrics(char)[0] is not None)
    )


def _quebrar_texto(texto, fonte, largura_max):
    """Quebra um texto em linhas que caibam em largura_max pixels (quebra por palavra)."""
    linhas = []
    for paragrafo in texto.split("\n"):
        atual = ""
        for palavra in paragrafo.split(" "):
            candidata = palavra if not atual else f"{atual} {palavra}"
            if fonte.size(candidata)[0] <= largura_max:
                atual = candidata
                continue
            if atual:
                linhas.append(atual)
            # Palavra isolada maior que a linha inteira: quebra por caracteres.
            while fonte.size(palavra)[0] > largura_max:
                corte = 1
                while corte < len(palavra) and fonte.size(palavra[:corte + 1])[0] <= largura_max:
                    corte += 1
                linhas.append(palavra[:corte])
                palavra = palavra[corte:]
            atual = palavra
        linhas.append(atual)
    return linhas


def _montar_linhas_conversa(historico_chat):
    """Converte o histórico [(papel, texto)] em linhas coloridas prontas para desenhar."""
    rotulos = {
        "usuario": ("Você", COR_CHAT_USUARIO),
        "assistente": ("Assistente", COR_CHAT_ASSISTENTE),
        "erro": ("Erro", COR_CHAT_ERRO),
    }
    linhas = []
    for papel, texto in historico_chat:
        rotulo, cor_rotulo = rotulos[papel]
        linhas.append((rotulo, cor_rotulo, True))
        cor_corpo = COR_CHAT_ERRO if papel == "erro" else COR_TEXTO_PRINCIPAL
        for linha in _quebrar_texto(texto, _fonte_comum, _CHAT_LARGURA_TEXTO):
            linhas.append((linha, cor_corpo, False))
        linhas.append(("", COR_TEXTO_MUTED, False))  # Espaço entre mensagens.
    return linhas


def _desenhar_sugestoes(perguntas_exemplo, area):
    """
    Desenha o bloco fixo de perguntas de exemplo no topo da área do chat.

    O bloco ocupa no máximo ~metade da área para o histórico da conversa nunca
    desaparecer; sugestões que não couberem inteiras são omitidas. Retorna
    (rects_clicaveis, y_final), onde y_final é onde o histórico começa.
    """
    mouse = pygame.mouse.get_pos()
    rects_sugestoes = []

    dica = "Digite sua pergunta, ou clique em um dos exemplos de perguntas abaixo:"
    y_atual = area.y
    for linha in _quebrar_texto(dica, _fonte_sub, area.width - 8):
        _tela.blit(_fonte_sub.render(linha, True, COR_TEXTO_PRINCIPAL), (area.x + 4, y_atual))
        y_atual += _fonte_sub.get_linesize()
    y_atual += 8

    limite_inferior = area.y + int(area.height * 0.55)
    for pergunta in perguntas_exemplo:
        linhas = _quebrar_texto(pergunta, _fonte_comum, _CHAT_LARGURA_TEXTO - 8)
        altura_carta = len(linhas) * _fonte_comum.get_linesize() + 12
        if y_atual + altura_carta > limite_inferior:
            break  # Não desenha sugestão que não caiba no espaço reservado.

        carta = pygame.Rect(area.x, y_atual, area.width, altura_carta)
        cor_fundo = COR_SUGESTAO_HOVER if carta.collidepoint(mouse) else COR_SUGESTAO_FUNDO
        pygame.draw.rect(_tela, cor_fundo, carta, border_radius=6)
        for i, linha in enumerate(linhas):
            txt = _fonte_comum.render(linha, True, COR_TEXTO_PRINCIPAL)
            _tela.blit(txt, (carta.x + 10, carta.y + 6 + i * _fonte_comum.get_linesize()))

        rects_sugestoes.append((carta, pergunta))
        y_atual += altura_carta + 8

    return rects_sugestoes, y_atual


def _desenhar_historico(historico_chat, area, scroll):
    """
    Desenha a conversa dentro de `area`, ancorada na mensagem mais recente,
    com barra de rolagem proporcional à direita quando o conteúdo não cabe
    (a roda do mouse controla a posição).

    Retorna o scroll máximo em pixels (0 quando a conversa inteira cabe).
    """
    if not historico_chat:
        txt_vazio = _fonte_comum.render("A conversa aparecerá aqui.", True, COR_TEXTO_MUTED)
        _tela.blit(txt_vazio, (area.x + 4, area.y + 8))
        return 0

    linhas = _montar_linhas_conversa(historico_chat)
    altura_linha = _fonte_comum.get_linesize()
    altura_total = len(linhas) * altura_linha
    scroll_maximo = max(0, altura_total - area.height)
    scroll = max(0, min(scroll, scroll_maximo))

    _tela.set_clip(area)
    if altura_total <= area.height:
        y_atual = area.y
    else:
        # Alinha o fim da conversa à base da área; scroll > 0 revela mensagens antigas.
        y_atual = area.bottom - altura_total + scroll
    for texto, cor, destaque in linhas:
        if texto and y_atual + altura_linha >= area.y and y_atual <= area.bottom:
            fonte = _fonte_sub if destaque else _fonte_comum
            _tela.blit(fonte.render(texto, True, cor), (area.x + 4, y_atual))
        y_atual += altura_linha
    _tela.set_clip(None)

    # Barra de rolagem: o tamanho do polegar reflete a fração visível da conversa.
    if scroll_maximo > 0:
        altura_polegar = max(24, int(area.height * (area.height / altura_total)))
        curso = area.height - altura_polegar
        y_polegar = area.y + int((1 - scroll / scroll_maximo) * curso)
        pygame.draw.rect(_tela, COR_TRILHO_ROLAGEM,
                         (area.right - 4, area.y, 4, area.height), border_radius=2)
        pygame.draw.rect(_tela, COR_BORDA_INPUT,
                         (area.right - 4, y_polegar, 4, altura_polegar), border_radius=2)

    return scroll_maximo


def _desenhar_caixa_entrada(texto_digitado, aguardando):
    """
    Desenha a caixa de digitação na base do painel de chat: cursor piscante,
    dica quando vazia e o indicador de "pensando" durante a consulta à LLM.

    Retorna o rect da caixa, usado para calcular a área útil do painel.
    """
    tempo_atual = pygame.time.get_ticks()
    caixa = pygame.Rect(LARGURA_JANELA + _CHAT_MARGEM,
                        ALTURA_JANELA - _CHAT_ALTURA_INPUT - 14,
                        LARGURA_CHAT - 2 * _CHAT_MARGEM, _CHAT_ALTURA_INPUT)
    pygame.draw.rect(_tela, COR_CAIXA_INPUT, caixa, border_radius=6)
    pygame.draw.rect(_tela, COR_BORDA_INPUT, caixa, 1, border_radius=6)

    if texto_digitado:
        visivel = texto_digitado
        # Mostra sempre o fim do texto quando ele ultrapassa a caixa.
        while _fonte_comum.size(visivel)[0] > caixa.width - 24:
            visivel = visivel[1:]
        if not aguardando and (tempo_atual // 500) % 2 == 0:
            visivel += "|"
        txt_input = _fonte_comum.render(visivel, True, COR_TEXTO_PRINCIPAL)
    else:
        dica = "Aguarde a resposta..." if aguardando else "Digite sua pergunta e pressione Enter"
        txt_input = _fonte_comum.render(dica, True, COR_TEXTO_MUTED)
    _tela.blit(txt_input, (caixa.x + 10, caixa.y + (caixa.height - txt_input.get_height()) // 2))

    # Indicador de resposta em andamento.
    if aguardando:
        pontinhos = "." * (1 + (tempo_atual // 400) % 3)
        txt_espera = _fonte_comum.render(
            f"Assistente está pensando{pontinhos}", True, COR_CHAT_ASSISTENTE
        )
        _tela.blit(txt_espera, (caixa.x + 4, caixa.y - 24))

    return caixa


def _desenhar_painel_chat(historico_chat, perguntas_exemplo,
                          texto_digitado, aguardando, scroll):
    """
    Desenha o painel de chat na terceira coluna da janela (à direita do dashboard).

    Duas regiões fixas: as perguntas de exemplo sempre visíveis no topo e o
    histórico da conversa com barra de rolagem logo abaixo.
    Retorna (rects_sugestoes, scroll_maximo): os retângulos clicáveis das
    perguntas de exemplo e o limite de rolagem do histórico para o loop de
    eventos aplicar no scroll do mouse.
    """
    x0 = LARGURA_JANELA + _CHAT_MARGEM

    # Fundo do painel e divisória em relação ao dashboard.
    pygame.draw.rect(_tela, COR_PAINEL, (LARGURA_JANELA, 0, LARGURA_CHAT, ALTURA_JANELA))
    pygame.draw.line(_tela, COR_DIVISORIA,
                     (LARGURA_JANELA, 0), (LARGURA_JANELA, ALTURA_JANELA))

    # Cabeçalho do assistente.
    txt_titulo = _fonte_titulo.render("ASSISTENTE DE LOGÍSTICA (IA)", True, COR_TEXTO_PRINCIPAL)
    _tela.blit(txt_titulo, (x0 + 8, 18))
    txt_sub = _fonte_comum.render(
        "Pergunte sobre as rotas, cargas e entregas", True, COR_TEXTO_MUTED
    )
    _tela.blit(txt_sub, (x0 + 8, 46))
    pygame.draw.line(_tela, COR_DIVISORIA,
                     (x0, _CHAT_TOPO_CONTEUDO - 16),
                     (LARGURA_JANELA + LARGURA_CHAT - _CHAT_MARGEM, _CHAT_TOPO_CONTEUDO - 16))

    caixa = _desenhar_caixa_entrada(texto_digitado, aguardando)

    # Área útil entre o cabeçalho e a caixa de digitação.
    area = pygame.Rect(x0, _CHAT_TOPO_CONTEUDO,
                       LARGURA_CHAT - 2 * _CHAT_MARGEM,
                       caixa.y - 28 - _CHAT_TOPO_CONTEUDO)

    # Sugestões fixas no topo; conversa rolável no espaço restante.
    rects_sugestoes, y_divisao = _desenhar_sugestoes(perguntas_exemplo, area)
    pygame.draw.line(_tela, COR_DIVISORIA, (area.x, y_divisao + 4), (area.right, y_divisao + 4))
    area_historico = pygame.Rect(area.x, y_divisao + 12,
                                 area.width, area.bottom - (y_divisao + 12))
    scroll_maximo = _desenhar_historico(historico_chat, area_historico, scroll)

    return rects_sugestoes, scroll_maximo


def _loop_chat(pontos_entrega, melhor_solucao, historico_fitness, responder, perguntas_exemplo):
    """
    Loop de eventos do modo chat: mapa e dashboard intactos, chat em coluna nova.

    Ao entrar, a janela é alargada para abrir a terceira coluna — nada da
    simulação é coberto. A função `responder` (injetada pelo main a partir da
    camada de IA) é bloqueante, então cada pergunta roda em uma thread de fundo
    e a resposta volta por uma fila — a janela continua responsiva enquanto a
    LLM trabalha.
    """
    global _tela

    # Força o Windows a recalcular a posição e jogar a janela para o centro do monitor
    os.environ['SDL_VIDEO_WINDOW_POS'] = "center"

    # Alarga a janela para acomodar a coluna do chat ao lado do dashboard.
    _tela = pygame.display.set_mode((LARGURA_JANELA + LARGURA_CHAT, ALTURA_JANELA))

    historico_chat = []      # Lista de (papel, texto): "usuario" | "assistente" | "erro".
    fila_respostas = queue.Queue()
    texto_digitado = ""
    aguardando = False
    scroll = 0
    scroll_maximo = 0
    rects_sugestoes = []

    def enviar(pergunta):
        nonlocal aguardando, texto_digitado, scroll
        historico_chat.append(("usuario", _sanitizar_texto(pergunta, _fonte_comum)))
        texto_digitado = ""
        scroll = 0
        aguardando = True
        threading.Thread(target=consultar, args=(pergunta,), daemon=True).start()

    def consultar(pergunta):
        try:
            fila_respostas.put(("assistente", responder(pergunta)))
        except Exception as erro:
            fila_respostas.put(("erro", f"Falha ao consultar a LLM: {erro}"))

    # Repetição de tecla para segurar Backspace ao corrigir a pergunta.
    pygame.key.set_repeat(400, 30)
    relogio = pygame.time.Clock()

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.TEXTINPUT and not aguardando:
                texto_digitado += evento.text

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_BACKSPACE:
                    texto_digitado = texto_digitado[:-1]
                elif evento.key == pygame.K_ESCAPE:
                    texto_digitado = ""
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if texto_digitado.strip() and not aguardando:
                        enviar(texto_digitado.strip())

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if not aguardando:
                    for carta, pergunta in rects_sugestoes:
                        if carta.collidepoint(evento.pos):
                            enviar(pergunta)
                            break

            elif evento.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(scroll + evento.y * 30, scroll_maximo))

        # Recolhe respostas concluídas pela thread de consulta, já saneadas
        # para a fonte da interface (evita "tofu" de emoji/símbolo sem glifo).
        try:
            papel, texto = fila_respostas.get_nowait()
            historico_chat.append((papel, _sanitizar_texto(texto, _fonte_comum)))
            aguardando = False
            scroll = 0
        except queue.Empty:
            pass

        _desenhar_simulacao(pontos_entrega, melhor_solucao, historico_fitness)
        rects_sugestoes, scroll_maximo = _desenhar_painel_chat(
            historico_chat, perguntas_exemplo,
            texto_digitado, aguardando, scroll,
        )
        pygame.display.flip()
        relogio.tick(30)

    pygame.quit()


def manter_tela_aberta(pontos_entrega=None, melhor_solucao=None, historico_fitness=None,
                       responder=None, perguntas_exemplo=None):
    """
    Mantém a janela responsiva após a convergência do algoritmo genético.

    Sem `responder`, apenas congela o último frame até o usuário fechar a janela
    (comportamento original). Com `responder` (função pergunta -> resposta criada
    pela camada de IA) e os dados da simulação, a janela é alargada e ganha uma
    coluna de chat com o assistente ao lado do dashboard — nenhuma requisição é
    feita até o usuário perguntar.
    """
    if responder is not None and melhor_solucao is not None:
        _loop_chat(pontos_entrega, melhor_solucao, historico_fitness or [],
                   responder, perguntas_exemplo or [])
        return

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
    pygame.quit()