from typing import List
from src.core.models import PontoEntrega, IndividuoVRP


def construir_contexto(pontos: List[PontoEntrega], solucao: IndividuoVRP) -> dict:
    """
    Constrói o contexto estruturado (dict serializável em JSON) que alimenta a LLM.

    Formaliza o contrato de dados descrito no README (seção 6): consome o
    IndividuoVRP produzido pelo OtimizadorVRP e a lista original de pontos,
    sem qualquer dependência de rede — função pura e testável.

    Somente veículos com rota real (mais que depósito -> depósito) são incluídos.
    """
    veiculos = []
    for veiculo in solucao.frotas:
        # Rota [0, 0] significa veículo ocioso: não gera instrução nem entra no relatório.
        if len(veiculo.rota) <= 2:
            continue

        carga_total = sum(pontos[idx].demanda_carga for idx in veiculo.rota)
        ids_criticos = [idx for idx in veiculo.rota if pontos[idx].e_critico]

        veiculos.append({
            "id_veiculo": veiculo.id_veiculo,
            "capacidade_max": veiculo.capacidade_max,
            "autonomia_max": veiculo.autonomia_max,
            "sequencia_visitas": list(veiculo.rota),
            "carga_total": carga_total,
            "percentual_ocupacao": round((carga_total / veiculo.capacidade_max) * 100.0, 1),
            "contem_ponto_critico": bool(ids_criticos),
            "ids_pontos_criticos_na_rota": ids_criticos,
        })

    return {
        "custo_total": solucao.fitness,
        "quantidade_pontos": sum(1 for p in pontos if p.id_ponto != 0),
        "veiculos": veiculos,
    }
