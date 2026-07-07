"""
Testes das funções puras de texto do painel de chat (Integrante 3).

_sanitizar_texto e _quebrar_texto não dependem de janela aberta — apenas do
módulo de fontes do Pygame — então podem ser testadas de forma headless.
"""
import pygame
import pytest

import src.interface.visualizacao as visualizacao
from src.interface.visualizacao import _quebrar_texto, _sanitizar_texto


@pytest.fixture(scope="module")
def fonte():
    """Carrega a mesma fonte da interface, sem abrir janela."""
    pygame.font.init()
    return pygame.font.SysFont(visualizacao.SEGOE_UI, 13)


# ====================================================================
# SANITIZAÇÃO: NENHUM CARACTERE SEM GLIFO PODE CHEGAR À TELA
# ====================================================================

def test_sanitizar_remove_emojis_sem_glifo(fonte):
    """
    Objetivo: garantir que emojis (ausentes na fonte da interface) sejam
    descartados em vez de virarem retângulos vazios ("tofu") na tela.

    Importância: o Pygame/SDL_ttf não tem fallback de fontes, e o filtro por
    fonte.metrics sozinho deixa passar símbolos como o U+2705 — regressão
    real encontrada durante o desenvolvimento.
    """
    resultado = _sanitizar_texto("Rota concluída ✅ pelo caminhão 🚚", fonte)

    assert "✅" not in resultado, "Emoji BMP (U+2705) deveria ser removido"
    assert "🚚" not in resultado, "Emoji fora do BMP deveria ser removido"
    assert "Rota concluída" in resultado, "Texto normal não pode ser afetado"


def test_sanitizar_substitui_simbolos_por_equivalentes(fonte):
    """
    Objetivo: símbolos tipográficos comuns em respostas de LLM (bullets,
    travessões, aspas curvas, reticências) devem virar equivalentes simples,
    não serem descartados.
    """
    resultado = _sanitizar_texto("• Item — “aspas” e reticências…", fonte)

    assert resultado == '- Item - "aspas" e reticências...'


def test_sanitizar_preserva_portugues_e_quebras_de_linha(fonte):
    """
    Objetivo: acentuação do português e quebras de parágrafo (usadas pela
    quebra de linhas do painel) devem atravessar a sanitização intactas.
    """
    texto = "Atenção: o ponto 3 é crítico!\nAção imediata no coração da rota."

    assert _sanitizar_texto(texto, fonte) == texto


def test_sanitizar_resultado_so_contem_glifos_renderizaveis(fonte):
    """
    Objetivo: propriedade geral do filtro — todo caractere que sobrevive
    (exceto \\n) precisa ter glifo confirmado na fonte.
    """
    resultado = _sanitizar_texto("Texto com \t tab, ✅ emoji e → seta", fonte)

    for char in resultado:
        assert char == "\n" or fonte.metrics(char)[0] is not None, (
            f"Caractere sem glifo sobrou após sanitização: {char!r}"
        )


# ====================================================================
# QUEBRA DE LINHAS: O TEXTO PRECISA CABER NA COLUNA DO CHAT
# ====================================================================

def test_quebrar_texto_respeita_largura_maxima(fonte):
    """
    Objetivo: nenhuma linha produzida pode exceder a largura em pixels da
    área de texto, senão o texto vaza para fora do painel de chat.
    """
    largura_max = 120
    linhas = _quebrar_texto(
        "uma frase razoavelmente longa para caber em linhas estreitas",
        fonte,
        largura_max,
    )

    assert len(linhas) > 1, "Frase longa deveria ser quebrada em várias linhas"
    for linha in linhas:
        assert fonte.size(linha)[0] <= largura_max, f"Linha estourou a largura: {linha!r}"


def test_quebrar_texto_preserva_paragrafos(fonte):
    """
    Objetivo: cada \\n do texto original deve iniciar uma nova linha,
    preservando a estrutura de parágrafos das respostas da LLM.
    """
    assert _quebrar_texto("primeiro\nsegundo", fonte, 300) == ["primeiro", "segundo"]


def test_quebrar_palavra_maior_que_a_linha(fonte):
    """
    Objetivo: uma palavra isolada mais larga que a linha inteira deve ser
    quebrada por caracteres, sem perder conteúdo nem estourar a largura.
    """
    largura_max = 60
    palavra = "Pneumoultramicroscopicossilicovulcanoconiótico"
    linhas = _quebrar_texto(palavra, fonte, largura_max)

    assert len(linhas) > 1, "Palavra gigante deveria ser quebrada"
    for linha in linhas:
        assert fonte.size(linha)[0] <= largura_max, f"Linha estourou a largura: {linha!r}"
    assert "".join(linhas) == palavra, "A quebra não pode perder caracteres"
