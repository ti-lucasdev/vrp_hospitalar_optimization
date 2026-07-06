import random
import matplotlib.pyplot as plt
from src.core.models import PontoEntrega, Veiculo
from src.core.genetic_alg import OtimizadorVRP

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

def plotar_resultados_vrp(pontos: list, melhor_solucao, historico_fitness: list):
    """Plota o mapa de rotas no plano cartesiano e o gráfico de convergência do fitness."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Gráfico 1: Mapa de Rotas
    ax1.set_title("Mapa de Rotas Otimizadas (VRP)")
    ax1.set_xlabel("Coordenada X")
    ax1.set_ylabel("Coordenada Y")
    ax1.grid(True, linestyle="--", alpha=0.6)
    
    hospital = pontos[0]
    pontos_normais = [p for p in pontos[1:] if not p.e_critico]
    pontos_criticos = [p for p in pontos[1:] if p.e_critico]
    
    ax1.scatter(hospital.x, hospital.y, color="red", s=200, marker="H", label="Hospital (Depósito)", zorder=5)
    if pontos_normais:
        ax1.scatter([p.x for p in pontos_normais], [p.y for p in pontos_normais], color="blue", s=75, label="Entrega Regular", zorder=4)
    if pontos_criticos:
        ax1.scatter([p.x for p in pontos_criticos], [p.y for p in pontos_criticos], color="orange", s=100, marker="^", label="Medicamento Crítico", zorder=4)
    
    for p in pontos:
        ax1.annotate(f"ID {p.id_ponto}", (p.x + 0.5, p.y + 0.5), fontsize=9, fontweight="bold")
        
    cores_frotas = ["green", "purple", "darkorange", "cyan", "magenta", "black"]
    
    for idx, veiculo in enumerate(melhor_solucao.frotas):
        if len(veiculo.rota) > 2:
            cor = cores_frotas[idx % len(cores_frotas)]
            rota_x = [pontos[id_no].x for id_no in veiculo.rota]
            rota_y = [pontos[id_no].y for id_no in veiculo.rota]
            ax1.plot(rota_x, rota_y, color=cor, linewidth=2, linestyle="-", label=f"Veículo {veiculo.id_veiculo}", zorder=3)
            
    ax1.legend(loc="upper left", fontsize=9)
    
    # Gráfico 2: Convergência do Fitness
    ax2.set_title("Curva de Aprendizado do Algoritmo Genético")
    ax2.set_xlabel("Gerações")
    ax2.set_ylabel("Valor do Fitness (Custo Total)")
    ax2.grid(True, linestyle="--", alpha=0.6)
    
    ax2.plot(historico_fitness, color="crimson", linewidth=2.5, label="Melhor Custo Estocástico")
    ax2.legend(loc="upper right")
    
    plt.tight_layout()
    plt.show()

def rodar_teste():
    print("=== Inicializando Teste do Motor Genético (VRP) ===")
    
    QUANTIDADE_PONTOS = 20 
    
    pontos = gerar_pontos_aleatorios(QUANTIDADE_PONTOS)
    
    # Autonomia configurada para 200.0 para viabilizar a resolução geométrica de 20 pontos sem penalidades
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
    
    print(f"\nEvoluindo rotas para {QUANTIDADE_PONTOS} pontos... Aguarde.")
    melhor_solucao = otimizador.executar()
    
    print("\n================ RESULTADO FINAL ================")
    print(f"Melhor Custo (Fitness) Encontrado: {melhor_solucao.fitness:.2f}")
    print("-------------------------------------------------")
    
    for veiculo in melhor_solucao.frotas:
        if len(veiculo.rota) > 2:
            print(f"Veículo ID {veiculo.id_veiculo}:")
            print(f"  -> Rota Logística: {veiculo.rota}")
            carga_real = sum(pontos[idx].demanda_carga for idx in veiculo.rota)
            print(f"  -> Carga Alocada: {carga_real}/{veiculo.capacidade_max} kg")
            print("-" * 49)

    plotar_resultados_vrp(pontos, melhor_solucao, otimizador.historico_fitness)

if __name__ == "__main__":
    random.seed(42)
    rodar_teste()