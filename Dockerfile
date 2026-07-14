FROM python:3.12-slim

WORKDIR /app

# Dependências primeiro para aproveitar o cache de camadas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação (o banco NÃO entra na imagem — vem por volume)
COPY app.py .
COPY static/ static/

EXPOSE 8501

# Healthcheck no endpoint interno do Streamlit (usa o python da imagem, sem curl).
# start-period dá tempo do app subir antes de contar falhas.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"

# headless + endereço 0.0.0.0 para funcionar dentro do container
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
