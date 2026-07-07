"""
Testes do construtor de contexto do módulo de IA (src/ia/contexto.py).

Valida o contrato de dados que alimenta a LLM sem qualquer chamada de rede,
no mesmo estilo de tests/test_visualizacao.py.
"""

from src.core.models import PontoEntrega, Veiculo, IndividuoVRP
from src.ia.contexto import construir_contexto


def _cenario_conhecido():
    """Monta um cenário determinístico: 3 pontos de entrega, 3 veículos (1 ocioso)."""
    pontos = [
        PontoEntrega(id_ponto=0, x=0.0, y=0.0, demanda_carga=0.0, e_critico=False),
        PontoEntrega(id_ponto=1, x=5.0, y=5.0, demanda_carga=10.0, e_critico=False),
        PontoEntrega(id_ponto=2, x=-5.0, y=3.0, demanda_carga=20.0, e_critico=True),
        PontoEntrega(id_ponto=3, x=2.0, y=-4.0, demanda_carga=30.0, e_critico=False),
    ]

    veiculo_com_critico = Veiculo(id_veiculo=1, capacidade_max=75.0, autonomia_max=200.0,
                                  rota=[0, 1, 2, 0])
    veiculo_sem_critico = Veiculo(id_veiculo=2, capacidade_max=60.0, autonomia_max=200.0,
                                  rota=[0, 3, 0])
    veiculo_ocioso = Veiculo(id_veiculo=3, capacidade_max=75.0, autonomia_max=200.0,
                             rota=[0, 0])

    solucao = IndividuoVRP(
        frotas=[veiculo_com_critico, veiculo_sem_critico, veiculo_ocioso],
        fitness=123.45,
    )
    return pontos, solucao


def test_custo_total_e_quantidade_pontos():
    pontos, solucao = _cenario_conhecido()

    contexto = construir_contexto(pontos, solucao)

    assert contexto["custo_total"] == 123.45
    # O depósito (ID 0) não conta como ponto de entrega.
    assert contexto["quantidade_pontos"] == 3


def test_filtro_de_veiculos_ociosos():
    pontos, solucao = _cenario_conhecido()

    contexto = construir_contexto(pontos, solucao)

    ids_incluidos = [v["id_veiculo"] for v in contexto["veiculos"]]
    assert ids_incluidos == [1, 2]  # veículo 3 (rota [0, 0]) fica de fora


def test_carga_total_e_percentual_ocupacao():
    pontos, solucao = _cenario_conhecido()

    contexto = construir_contexto(pontos, solucao)
    veiculo_1, veiculo_2 = contexto["veiculos"]

    # Veículo 1: pontos 1 (10kg) + 2 (20kg) = 30kg de 75kg -> 40%.
    assert veiculo_1["carga_total"] == 30.0
    assert veiculo_1["percentual_ocupacao"] == 40.0

    # Veículo 2: ponto 3 (30kg) de 60kg -> 50%.
    assert veiculo_2["carga_total"] == 30.0
    assert veiculo_2["percentual_ocupacao"] == 50.0


def test_identificacao_de_pontos_criticos():
    pontos, solucao = _cenario_conhecido()

    contexto = construir_contexto(pontos, solucao)
    veiculo_1, veiculo_2 = contexto["veiculos"]

    assert veiculo_1["contem_ponto_critico"] is True
    assert veiculo_1["ids_pontos_criticos_na_rota"] == [2]

    assert veiculo_2["contem_ponto_critico"] is False
    assert veiculo_2["ids_pontos_criticos_na_rota"] == []


def test_sequencia_de_visitas_preserva_rota_original():
    pontos, solucao = _cenario_conhecido()

    contexto = construir_contexto(pontos, solucao)

    assert contexto["veiculos"][0]["sequencia_visitas"] == [0, 1, 2, 0]
    assert contexto["veiculos"][1]["sequencia_visitas"] == [0, 3, 0]
