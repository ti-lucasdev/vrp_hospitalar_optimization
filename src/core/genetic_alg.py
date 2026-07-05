import math
import random
import numpy as np
from typing import List
from src.core.models import PontoEntrega, Veiculo, IndividuoVRP

class GerenciadorDistancias:
    """Pré-calcula a matriz de distâncias para otimizar o desempenho do fitness."""
    def __init__(self, pontos: List[PontoEntrega]):
        self.pontos = pontos
        self.tamanho = len(pontos)
        self.matriz = np.zeros((self.tamanho, self.tamanho))
        self._pre_calcular()

    def _pre_calcular(self):
        for i in range(self.tamanho):
            for j in range(self.tamanho):
                p1, p2 = self.pontos[i], self.pontos[j]
                self.matriz[i][j] = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def obter(self, id1: int, id2: int) -> float:
        return self.matriz[id1][id2]


class CalculadorFitness:
    """Motor de avaliação que computa distâncias, prioridades e penalidades."""
    def __init__(self, gerenciador: GerenciadorDistancias, 
                 penalidade_capacidade: float = 10000.0, 
                 penalidade_autonomia: float = 10000.0, 
                 peso_prioridade: float = 3.0):
        self.gerenciador = gerenciador
        self.penalidade_capacidade = penalidade_capacidade
        self.penalidade_autonomia = penalidade_autonomia
        self.peso_prioridade = peso_prioridade

    def avaliar_veiculo(self, veiculo: Veiculo, pontos: List[PontoEntrega]) -> float:
        distancia_total = 0.0
        carga_total = 0.0
        
        if len(veiculo.rota) <= 1:
            return 0.0
        
        for i in range(len(veiculo.rota) - 1):
            id_p1 = veiculo.rota[i]
            id_p2 = veiculo.rota[i+1]
            
            distancia_trecho = self.gerenciador.obter(id_p1, id_p2)
            distancia_total += distancia_trecho
            carga_total += pontos[id_p2].demanda_carga
            
            if pontos[id_p2].e_critico:
                distancia_total += (distancia_trecho * self.peso_prioridade)
        
        fitness = distancia_total
        if carga_total > veiculo.capacidade_max: 
            fitness += self.penalidade_capacidade
        if distancia_total > veiculo.autonomia_max: 
            fitness += self.penalidade_autonomia
        return fitness

    def avaliar_individuo(self, individuo: IndividuoVRP, pontos: List[PontoEntrega]) -> float:
        """Calcula o fitness total somando o custo de todos os veículos da frota."""
        individuo.fitness = sum(self.avaliar_veiculo(v, pontos) for v in individuo.frotas)
        return individuo.fitness

# ====================================================================
# FUNÇÕES DE ESCOPO GLOBAL (Fora das classes)
# ====================================================================

def inicializar_populacao_heuristica(pontos: List[PontoEntrega], 
                                     modelos_veiculos: List[Veiculo], 
                                     tamanho_populacao: int, 
                                     gerenciador: GerenciadorDistancias) -> List[IndividuoVRP]:
    """Gera a população inicial utilizando a heurística do vizinho mais próximo aleatorizado."""
    populacao = []
    ids_clientes_originais = [p.id_ponto for p in pontos if p.id_ponto != 0]

    for _ in range(tamanho_populacao):
        clientes_restantes = ids_clientes_originais.copy()
        
        frota_individuo = [Veiculo(id_veiculo=v.id_veiculo, 
                                   capacidade_max=v.capacidade_max, 
                                   autonomia_max=v.autonomia_max) for v in modelos_veiculos]
        
        for veiculo in frota_individuo:
            veiculo.resetar_rota()
            carga_atual = 0.0
            ponto_atual = 0 
            
            while clientes_restantes:
                candidatos = []
                for c_id in clientes_restantes:
                    dist = gerenciador.obter(ponto_atual, c_id)
                    candidatos.append((c_id, dist))
                
                candidatos.sort(key=lambda x: x[1])
                pool_selecao = candidatos[:3]
                
                alocou = False
                random.shuffle(pool_selecao)
                
                for c_id, _ in pool_selecao:
                    if carga_atual + pontos[c_id].demanda_carga <= veiculo.capacidade_max:
                        veiculo.rota.append(c_id)
                        carga_atual += pontos[c_id].demanda_carga
                        clientes_restantes.remove(c_id)
                        ponto_atual = c_id
                        alocou = True
                        break
                
                if not alocou:
                    break
            
            veiculo.rota.append(0)
            
        if clientes_restantes:
            for c_id in clientes_restantes:
                veiculo_aleatorio = random.choice(frota_individuo)
                veiculo_aleatorio.rota.insert(-1, c_id)
        
        populacao.append(IndividuoVRP(frotas=frota_individuo))
        
    return populacao

def cruzamento_ox(pai1_genes: List[int], pai2_genes: List[int]) -> List[int]:
    """Aplica o Ordered Crossover (OX) para matrizes de permutação."""
    tamanho = len(pai1_genes)
    if tamanho <= 1:
        return pai1_genes.copy()
        
    filho = [-1] * tamanho
    
    inicio, fim = sorted(random.sample(range(tamanho), 2))
    filho[inicio:fim+1] = pai1_genes[inicio:fim+1]
    
    posicao_insercao = (fim + 1) % tamanho
    for gene in pai2_genes:
        if gene not in filho:
            if gene not in filho: 
                filho[posicao_insercao] = gene
                posicao_insercao = (posicao_insercao + 1) % tamanho
            
    return filho

def extrair_genes(individuo: IndividuoVRP) -> List[int]:
    """Extrai a sequência linear de clientes, ignorando os zeros (depósito)."""
    genes = []
    for veiculo in individuo.frotas:
        for p in veiculo.rota:
            if p != 0:
                genes.append(p)
    return genes

def mutacao_swap(genes: List[int], taxa_mutacao: float) -> List[int]:
    """Aplica mutação trocando a posição de dois nós na sequência logística."""
    genes_mutados = genes.copy()
    if random.random() < taxa_mutacao:
        tamanho = len(genes_mutados)
        if tamanho >= 2:
            idx1, idx2 = random.sample(range(tamanho), 2)
            genes_mutados[idx1], genes_mutados[idx2] = genes_mutados[idx2], genes_mutados[idx1]
    return genes_mutados

def decodificar_genes_para_frota(genes: List[int], pontos: List[PontoEntrega], modelos_veiculos: List[Veiculo]) -> IndividuoVRP:
    """Mapeia a sequência linear de clientes de volta para frotas validando restrições de carga."""
    frota = [Veiculo(id_veiculo=v.id_veiculo, capacidade_max=v.capacidade_max, autonomia_max=v.autonomia_max) for v in modelos_veiculos]
    
    veiculo_atual_idx = 0
    carga_atual = 0.0
    
    for v in frota:
        v.resetar_rota()
        
    for gene in genes:
        demanda = pontos[gene].demanda_carga
        
        if carga_atual + demanda > frota[veiculo_atual_idx].capacidade_max:
            frota[veiculo_atual_idx].rota.append(0)
            veiculo_atual_idx += 1
            carga_atual = 0.0
            
            if veiculo_atual_idx >= len(frota):
                veiculo_atual_idx = len(frota) - 1
        
        frota[veiculo_atual_idx].rota.append(gene)
        carga_atual += demanda
        
    for v in frota:
        if v.rota[-1] != 0:
            v.rota.append(0)
            
    return IndividuoVRP(frotas=frota)

def selecao_torneio(populacao: List[IndividuoVRP], tamanho_torneio: int = 3) -> IndividuoVRP:
    """Seleciona o indivíduo com o menor custo (fitness) entre K competidores aleatórios."""
    competidores = random.sample(populacao, tamanho_torneio)
    return min(competidores, key=lambda ind: ind.fitness)

# ====================================================================
# CLASSE DE ORQUESTRAÇÃO
# ====================================================================

class OtimizadorVRP:
    """Motor principal que orquestra a evolução do Algoritmo Genético."""
    def __init__(self, pontos: List[PontoEntrega], modelos_veiculos: List[Veiculo], 
                 tamanho_populacao: int = 100, max_geracoes: int = 500, 
                 max_estagnacao: int = 50, taxa_mutacao: float = 0.1, 
                 taxa_elitismo: float = 0.03):
        
        self.pontos = pontos
        self.modelos_veiculos = modelos_veiculos
        self.tamanho_populacao = tamanho_populacao
        self.max_geracoes = max_geracoes
        self.max_estagnacao = max_estagnacao
        self.taxa_mutacao = taxa_mutacao
        self.num_elite = max(1, int(tamanho_populacao * taxa_elitismo))
        
        self.gerenciador_dist = GerenciadorDistancias(pontos)
        self.calculador_fitness = CalculadorFitness(self.gerenciador_dist)
        
        self.melhor_individuo_global = None
        self.historico_fitness = []

    # ----------------------------------------------------------------
    # INTEGRANTE 2 - Lucas Camilo (MODIFICAÇÃO PARA RENDERIZAÇÃO EM TEMPO REAL)
    # Padrão Inversão de Controle (IoC) via Injeção de Callback:
    # O parâmetro 'callback' aceita uma assinatura executável (callable). 
    # Essa abordagem foi escolhida para desacoplar a lógica matemática do 
    # algoritmo genético de qualquer dependência direta da interface gráfica (Pygame),
    # mantendo o núcleo computacional puro, testável e reutilizável.
    # ----------------------------------------------------------------
    def executar(self, callback=None) -> IndividuoVRP:
        populacao = inicializar_populacao_heuristica(
            self.pontos, self.modelos_veiculos, self.tamanho_populacao, self.gerenciador_dist
        )
        
        geracao_atual = 0
        estagnacao = 0
        
        while geracao_atual < self.max_geracoes and estagnacao < self.max_estagnacao:
            
            for individuo in populacao:
                self.calculador_fitness.avaliar_individuo(individuo, self.pontos)
                
            populacao.sort(key=lambda ind: ind.fitness)
            melhor_da_geracao = populacao[0]
            
            if self.melhor_individuo_global is None or melhor_da_geracao.fitness < self.melhor_individuo_global.fitness:
                self.melhor_individuo_global = melhor_da_geracao
                estagnacao = 0
            else:
                estagnacao += 1
                
            self.historico_fitness.append(self.melhor_individuo_global.fitness)
            
            # --------------------------------------------------------
            # INTEGRANTE 2 - Lucas Camilo (MODIFICAÇÃO PARA RENDERIZAÇÃO EM TEMPO REAL)
            # Despacho Síncrono de Telemetria Interativa:
            # Verifica se um observador externo interceptou o loop.
            # Se verdadeiro, invoca o callback passando o estado consolidado da geração:
            # o melhor fenótipo gerado até aqui e o vetor histórico de convergência.
            # Isso alimenta a renderização dinâmica em tempo real a cada iteração do algoritmo.
            # --------------------------------------------------------
            if callback is not None:
                callback(self.melhor_individuo_global, self.historico_fitness)
            
            nova_populacao = populacao[:self.num_elite]
            
            vagas_restantes = self.tamanho_populacao - self.num_elite
            for _ in range(vagas_restantes):
                pai1 = selecao_torneio(populacao)
                pai2 = selecao_torneio(populacao)
                
                genes_pai1 = extrair_genes(pai1)
                genes_pai2 = extrair_genes(pai2)
                
                genes_filho = cruzamento_ox(genes_pai1, genes_pai2)
                genes_filho = mutacao_swap(genes_filho, self.taxa_mutacao)
                
                filho = decodificar_genes_para_frota(genes_filho, self.pontos, self.modelos_veiculos)
                nova_populacao.append(filho)
                
            populacao = nova_populacao
            geracao_atual += 1
            
        return self.melhor_individuo_global