from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class PontoEntrega:
    """Representa um nó no grafo de roteamento (hospital/unidade ou depósito)."""
    id_ponto: int          
    x: float               
    y: float               
    demanda_carga: float   
    e_critico: bool        # True define alta prioridade no fitness

@dataclass
class Veiculo:
    """Representa uma unidade da frota com suas restrições operacionais."""
    id_veiculo: int
    capacidade_max: float  
    autonomia_max: float   
    rota: List[int] = field(default_factory=lambda: [0]) 
    
    def resetar_rota(self) -> None:
        """Reinicializa a rota garantindo a partida do depósito (ID 0)."""
        self.rota = [0]

@dataclass
class IndividuoVRP:
    """Representa um cromossomo no Algoritmo Genético (uma solução completa)."""
    frotas: List[Veiculo]
    fitness: float = float('inf') 
    
    def obter_rotas_formatadas(self) -> Dict[int, List[int]]:
        """
        Retorna o dicionário de rotas.
        Contrato de dados essencial para o Integrante 2 (Visualização) e 3 (LLM).
        """
        return {v.id_veiculo: v.rota for v in self.frotas}