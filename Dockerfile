FROM python:3.12-slim

WORKDIR /app

# Copy only requirements first - Docker caches this layer, so if only
# your code changes (not dependencies), rebuilds are much faster.
COPY requirements-api.txt .

# Install PyTorch CPU-only first (much smaller than the default GPU version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements-api.txt
# Now copy everything else
COPY src/ ./src/
COPY data/processed/ ./data/processed/
COPY data/documents/ ./data/documents/
COPY models/ ./models/
COPY chroma_db/ ./chroma_db/

EXPOSE 8000

CMD ["python", "src/api/main.py"]