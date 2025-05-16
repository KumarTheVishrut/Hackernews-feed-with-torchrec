#!/bin/bash
# Start the Flask API in the background
python api.py &
API_PID=$!

# Start Streamlit in the foreground
streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# If Streamlit exits, also terminate the API
kill $API_PID 