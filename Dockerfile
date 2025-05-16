FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install only essential build dependencies and clean up in the same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip

# Copy only necessary application files
COPY *.py ./
COPY start.sh ./
RUN chmod +x ./start.sh

# Expose ports for both Streamlit and Flask
EXPOSE 8501
EXPOSE 5000

# Start both services
CMD ["./start.sh"] 