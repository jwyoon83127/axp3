import os
import subprocess
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Jira AX Insight API")

# Get the absolute path of the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "jira_AS_full_data.csv")
EXPORTER_SCRIPT = os.path.join(BASE_DIR, "jira_exporter.py")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "dash.html"))

@app.get("/api/data")
async def get_data():
    if not os.path.exists(CSV_FILE):
        raise HTTPException(status_code=404, detail="CSV file not found. Please refresh data first.")
    
    try:
        # Read CSV and return as JSON
        df = pd.read_csv(CSV_FILE)
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")

@app.get("/api/download-csv")
async def download_csv():
    if not os.path.exists(CSV_FILE):
        raise HTTPException(status_code=404, detail="CSV file not found.")
    return FileResponse(CSV_FILE, media_type='text/csv', filename="jira_AS_full_data.csv")

@app.get("/jira_AS_full_data.csv")
async def get_csv_file():
    if not os.path.exists(CSV_FILE):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(CSV_FILE)

@app.post("/api/refresh")
async def refresh_data():
    try:
        # Run the exporter script
        result = subprocess.run(["python3", EXPORTER_SCRIPT], capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "message": "Jira data refreshed successfully.", "output": result.stdout}
        else:
            raise HTTPException(status_code=500, detail=f"Exporter script failed: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# Optional: Serve other static files if needed
# app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
