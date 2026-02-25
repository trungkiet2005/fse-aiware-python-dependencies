FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Ollama port
EXPOSE 11434

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Start Ollama server in background\n\
ollama serve &\n\
sleep 10\n\
\n\
# Pull model\n\
ollama pull gemma2\n\
\n\
# Run application\n\
python main.py "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]
