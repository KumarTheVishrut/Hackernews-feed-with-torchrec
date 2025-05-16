FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for both Streamlit and Flask
EXPOSE 8501
EXPOSE 5000

# Create a script to start both services
RUN echo '#!/bin/bash\n\
python api.py &\n\
streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n' > /app/start.sh && \
chmod +x /app/start.sh

# Set entrypoint
ENTRYPOINT ["/app/start.sh"] 