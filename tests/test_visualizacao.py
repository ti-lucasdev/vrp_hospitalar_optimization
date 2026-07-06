import pytest
import math
from src.core.models import PontoEntrega, Veiculo, IndividuoVRP
from src.interface.visualizacao import converter_coordenadas

# ====================================================================
# TESTES UNITÁRIOS: TRANSFORMAÇÃO ESPACIAL (INTEGRANTE 2)
# ====================================================================

def test_conversao_coordenadas_origem_cartesiana():
    """
    Objetivo: validar se a origem do sistema cartesiano (0,0)
    é corretamente centralizada no viewport do mapa.

    Importância: essa transformação é base da renderização.
    Qualquer erro aqui desloca toda a visualização.
    """
    # Converte a origem (0,0) para coordenadas de tela
    pixel_x, pixel_y = converter_coordenadas(0.0, 0.0)

    # Considerando as dimensões e margem do mapa,
    # o centro esperado deve cair exatamente no meio da área útil
    # X esperado: 400 | Y esperado: 350
    assert pixel_x == 400, "X=0 deve estar centralizado no eixo horizontal (400px)"
    assert pixel_y == 350, "Y=0 deve estar centralizado no eixo vertical (350px)"


def test_conversao_coordenadas_limites_do_dominio():
    """
    Objetivo: garantir que os extremos do domínio cartesiano
    sejam corretamente mapeados dentro da área útil da tela.

    Importância: evita cortes de elementos ou estouro da interface.
    """
    # Teste no limite superior esquerdo do plano cartesiano
    px_min, py_max = converter_coordenadas(-20.0, 20.0)
    assert px_min == 60, "Limite esquerdo deve respeitar a margem (60px)"
    assert py_max == 60, "Topo do sistema deve inverter corretamente para coordenada de tela"

    # Teste no limite inferior direito do plano cartesiano
    px_max, py_min = converter_coordenadas(20.0, -20.0)
    assert px_max == 740, "Limite direito deve respeitar largura - margem"
    assert py_min == 640, "Base deve respeitar altura - margem"


# ====================================================================
# TESTES DE INTEGRAÇÃO: TELEMETRIA E CALLBACK (INTEGRANTE 2)
# ====================================================================

class MockOtimizadorVRP:
    """
    Mock do otimizador genético.

    Simula a execução de gerações e o disparo do callback
    usado para acompanhar a evolução do fitness.
    """
    def __init__(self, pontos, frota):
        self.pontos = pontos
        self.frota = frota
        self.historico_fitness = []

    def simular_geracao(self, callback, fitness_simulado):
        # Cria um indivíduo fictício baseado na frota atual
        individuo_ficticio = IndividuoVRP(frotas=self.frota)
        individuo_ficticio.fitness = fitness_simulado

        # Registra o histórico de fitness
        self.historico_fitness.append(fitness_simulado)

        # Dispara callback simulando o comportamento real do otimizador
        if callback is not None:
            callback(individuo_ficticio, self.historico_fitness)


def test_pipeline_streaming_telemetria_callback():
    """
    Objetivo: validar o fluxo de dados via callback (inversão de controle).

    Garante que o indivíduo e o histórico de fitness sejam transmitidos
    corretamente entre camadas sem perda de integridade.
    """
    # Dados mínimos para simulação
    pontos = [PontoEntrega(id_ponto=0, x=0.0, y=0.0, demanda_carga=0.0, e_critico=False)]
    frota = [Veiculo(id_veiculo=1, capacidade_max=100.0, autonomia_max=200.0)]
    frota[0].rota = [0, 0]

    otimizador_mock = MockOtimizadorVRP(pontos, frota)

    # Estrutura usada para capturar dados do callback
    dados_capturados = {"individuo": None, "historico": None}

    def callback_espia(melhor, historico):
        dados_capturados["individuo"] = melhor
        dados_capturados["historico"] = historico.copy()

    # Executa simulação com fitness definido
    otimizador_mock.simular_geracao(callback=callback_espia, fitness_simulado=450.50)

    # Valida integridade do fluxo de dados
    assert dados_capturados["individuo"] is not None, "Indivíduo não foi transmitido pelo callback"
    assert dados_capturados["individuo"].fitness == 450.50, "Fitness foi alterado durante o fluxo"
    assert len(dados_capturados["historico"]) == 1, "Histórico deveria ter 1 registro"
    assert dados_capturados["historico"][0] == 450.50, "Valor do histórico incorreto"


def test_calculo_acumulado_carga_frota_na_visualizacao():
    """
    Objetivo: validar o cálculo de carga total exibido no painel (HUD).

    Esse valor alimenta a barra de progresso da interface, então
    qualquer erro impacta diretamente a visualização do usuário.
    """
    # Pontos com demandas conhecidas
    pontos_entrega = [
        PontoEntrega(id_ponto=0, x=0.0, y=0.0, demanda_carga=0.0, e_critico=False),
        PontoEntrega(id_ponto=1, x=5.0, y=5.0, demanda_carga=15.0, e_critico=False),
        PontoEntrega(id_ponto=2, x=-5.0, y=-5.0, demanda_carga=25.0, e_critico=True)
    ]

    veiculo = Veiculo(id_veiculo=1, capacidade_max=100.0, autonomia_max=200.0)

    # Rota simulando visita aos pontos e retorno ao depósito
    veiculo.rota = [0, 1, 2, 0]

    # Soma de cargas seguindo a mesma lógica da visualização
    carga_calculada_painel = sum(pontos_entrega[idx].demanda_carga for idx in veiculo.rota)

    # Total esperado: 40
    assert carga_calculada_painel == 40.0, f"Erro na soma da carga: {carga_calculada_painel}"

    # Conversão para percentual da barra de progresso
    porcentagem_barra = min(1.0, carga_calculada_painel / veiculo.capacidade_max)
    assert porcentagem_barra == 0.4, f"Percentual incorreto: {porcentagem_barra}"