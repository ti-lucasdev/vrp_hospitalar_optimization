"""
Camada de integração com a OpenAI API (Item 3 do Tech Challenge — Projeto 2).

Wrapper fino sobre o SDK `openai`: `criar_respondedor` recebe o dict produzido
por src.ia.contexto.construir_contexto e devolve uma função `responder(pergunta)`
que a camada de interface usa para o chat. Nenhuma requisição é feita na
criação — a primeira chamada à API acontece apenas na primeira pergunta do
usuário. Nenhuma função aqui conhece Pygame ou o loop do algoritmo genético —
a fronteira de integração é exclusivamente o contexto estruturado.

Configuração via variáveis de ambiente (carregadas também de um arquivo .env
na raiz do projeto, se existir — ver .env.example):
- OPENAI_API_KEY (obrigatória para o chat; sem ela a simulação roda normalmente)
- OPENAI_MODEL (opcional, default gpt-4o-mini)
"""

import os
import json
from typing import Callable, Optional
from dotenv import load_dotenv
from openai import OpenAI

from src.ia.prompts import SYSTEM_PROMPT_CHAT

# Variáveis já definidas no ambiente têm precedência sobre o .env.
load_dotenv()

MODELO_PADRAO = "gpt-4o-mini"


def _obter_modelo() -> str:
    return os.environ.get("OPENAI_MODEL", MODELO_PADRAO)


def montar_perguntas_exemplo(contexto: dict) -> list:
    """Monta sugestões de perguntas, usando os dados reais do cenário quando possível."""
    perguntas = [
        "Quais são as instruções de entrega dos motoristas?",
        "Poderia gerar um relatório completo sobre as rotas?",
        "Poderia sugerir melhorias nas rotas com base nos padrões identificados?",
        "Quais rotas possuem pontos críticos de urgência médica?",
        "Qual veículo está com a maior ocupação de capacidade?",
    ]
    if contexto["veiculos"]:
        id_exemplo = contexto["veiculos"][0]["id_veiculo"]
        perguntas.insert(3, f"Qual é a rota do motorista do veículo {id_exemplo}?")
    return perguntas


def criar_respondedor(contexto: dict) -> Optional[Callable[[str], str]]:
    """
    Cria a função de chat usada pela interface: responder(pergunta) -> resposta.

    Retorna None quando OPENAI_API_KEY não está definida (nem no ambiente nem
    no .env — ver .env.example): quem chama decide como degradar sem o chat.

    O contexto JSON é injetado uma única vez no system prompt e o histórico de
    mensagens fica retido na closure, permitindo conversa multi-turno. A função
    retornada é bloqueante (faz uma requisição HTTP), então a interface deve
    chamá-la fora da thread de renderização.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return None

    cliente = OpenAI()
    payload = json.dumps(contexto, ensure_ascii=False, indent=2)
    mensagens = [
        {"role": "system", "content": f"{SYSTEM_PROMPT_CHAT}\n\nDados da operação:\n{payload}"}
    ]

    def responder(pergunta: str) -> str:
        mensagens.append({"role": "user", "content": pergunta})
        try:
            resposta = cliente.chat.completions.create(
                model=_obter_modelo(),
                messages=mensagens,
            )
        except Exception:
            # Remove a pergunta órfã para que uma nova tentativa parta de um histórico íntegro.
            mensagens.pop()
            raise
        texto = resposta.choices[0].message.content
        mensagens.append({"role": "assistant", "content": texto})
        return texto

    return responder
