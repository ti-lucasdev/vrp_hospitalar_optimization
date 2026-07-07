import random
# Importamos as funções de tempo real da nova interface
from src.interface.visualizacao import inicializar_tela, atualizar_frame_tempo_real, manter_tela_aberta
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

def rodar_teste():
    print("=== Inicializando Teste do Motor Genético (VRP) em Tempo Real ===")
    
    QUANTIDADE_PONTOS = 100
    pontos = gerar_pontos_aleatorios(QUANTIDADE_PONTOS)
    
    modelos_veiculos = [
        Veiculo(id_veiculo=1, capacidade_max=75.0, autonomia_max=500.0),
        Veiculo(id_veiculo=2, capacidade_max=75.0, autonomia_max=500.0),
        Veiculo(id_veiculo=3, capacidade_max=75.0, autonomia_max=500.0),
        Veiculo(id_veiculo=4, capacidade_max=75.0, autonomia_max=500.0),
        Veiculo(id_veiculo=5, capacidade_max=75.0, autonomia_max=500.0),
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
    
    # [Etapa 1] Inicializa a interface gráfica
    inicializar_tela()
    
    # [Etapa 2] Execução com callback para visualização em tempo real
    print(f"\nEvoluindo rotas para {QUANTIDADE_PONTOS} pontos... Veja a janela do Pygame!")
    melhor_solucao = otimizador.executar(
        callback=lambda melhor, historico: atualizar_frame_tempo_real(pontos, melhor, historico)
    )
    
    print("\n================ PROCESSAMENTO CONCLUÍDO ================")
    print(f"Melhor Custo Final: {melhor_solucao.fitness:.2f}")
    
    # [Etapa 3] Retenção da tela para auditoria final
    manter_tela_aberta()

if __name__ == "__main__":
    # Para gerar cenários diferentes, altere a seed ou comente a linha abaixo
    random.seed(42)
    rodar_teste()