# PROJETO: Otimização de Roteamento Hospitalar (VRP)

Este projeto consiste em um sistema de otimização logística aplicado a entregas hospitalares críticas, utilizando Algoritmos Genéticos para resolver o Problema de Roteamento de Veículos (VRP).

## Equipe de Desenvolvimento
Este trabalho foi desenvolvido de forma colaborativa, com a divisão de responsabilidades conforme abaixo:

* **Integrante 1 (Lucas):** Responsável pelo *Core* do Sistema, Motor Genético, heurísticas de inicialização e modelagem matemática.
* **Integrante 2 (Lucas Camilo):** Responsável pela Interface Gráfica (Pygame), telemetria, integração síncrona com o motor e testes automatizados.

---

## 1. Visão Geral do Escopo
O sistema resolve o VRP integrando um motor de otimização estocástico a uma camada de visualização em tempo real, permitindo a auditoria humana da convergência das rotas.

## 2. Componentes do Sistema
1. **Core (Integrante 1):** Modelagem de `PontoEntrega`, `Veiculo` e `IndividuoVRP`. Implementação do `OtimizadorVRP` e operadores evolutivos (Cruzamento OX e Mutação Swap).
2. **Interface (Integrante 2):** Implementação do `Pygame` para renderização, mapeamento de coordenadas cartesianas para *viewport* e painel de telemetria (HUD).
3. **Testes:** Suíte completa em `pytest` cobrindo determinismo geométrico e integridade de dados.

## 3. Como Executar
Siga as instruções para rodar o ambiente:

1. **Clone o repositório:** `git clone <url>`
2. **Crie o ambiente:** `python -m venv .venv`
3. **Ative o ambiente:** `.\.venv\Scripts\activate` (Windows)
4. **Instale as dependências:** `pip install -r requirements.txt`
5. **Execute a aplicação:** `python main.py`
6. **Execute os testes:** `pytest tests/`

---
*Nota: Este projeto faz parte do Tech Challenge de Inteligência Artificial.*