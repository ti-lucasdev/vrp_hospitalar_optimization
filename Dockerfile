FROM python:3.10-slim

# Instala o xvfb (display virtual em memoria) e dependencias necessarias
# para o Pygame conseguir inicializar mesmo sem monitor fisico conectado
# ao container.
RUN apt-get update && apt-get install -y \
    xvfb \
    freeglut3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Define o display virtual que o Pygame vai usar
ENV DISPLAY=:99

# Inicia o Xvfb em segundo plano (& ) e aguarda 1 segundo para garantir
# que o display esteja pronto, antes de rodar os testes automatizados.
# (Evitamos o wrapper xvfb-run, que trava sem o pacote xauth instalado.)
CMD ["/bin/bash", "-c", "Xvfb :99 -screen 0 1200x700x24 & sleep 1 && pytest tests/ -v"]