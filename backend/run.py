import os
import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "10000")
    try:
        port = int(port_str)
    except ValueError:
        port = 10000
    
    print(f"Starting PrismAccuRAG server on 0.0.0.0:{port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
