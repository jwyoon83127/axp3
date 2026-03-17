import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import jira_exporter

app = FastAPI(title="Jira AX Insight API")

# Get the absolute path of the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On Vercel, the bundled CSV is in BASE_DIR. 
# For refreshing, we might need to use /tmp but for now we read from the bundled one.
CSV_FILE = os.path.join(BASE_DIR, "jira_AS_full_data.csv")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "dash.html"))

@app.get("/api/data")
async def get_data():
    # Priority: Check /tmp/ if it was refreshed in this session, otherwise use bundled
    tmp_csv = "/tmp/jira_AS_full_data.csv"
    target_csv = tmp_csv if os.path.exists(tmp_csv) else CSV_FILE
    
    if not os.path.exists(target_csv):
        raise HTTPException(status_code=404, detail="CSV file not found. Please refresh data first.")
    
    try:
        # Read CSV and return as JSON
        df = pd.read_csv(target_csv)
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")

@app.get("/api/download-csv")
async def download_csv():
    tmp_csv = "/tmp/jira_AS_full_data.csv"
    target_csv = tmp_csv if os.path.exists(tmp_csv) else CSV_FILE
    
    if not os.path.exists(target_csv):
        raise HTTPException(status_code=404, detail="CSV file not found.")
    return FileResponse(target_csv, media_type='text/csv', filename="jira_AS_full_data.csv")

@app.get("/jira_AS_full_data.csv")
async def get_csv_file():
    tmp_csv = "/tmp/jira_AS_full_data.csv"
    target_csv = tmp_csv if os.path.exists(tmp_csv) else CSV_FILE
    
    if not os.path.exists(target_csv):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target_csv)

@app.post("/api/refresh")
async def refresh_data():
    try:
        # On Vercel, we must write to /tmp
        # We need to modify jira_exporter to accept a path or we can temporarily change directory
        # but better to modify jira_exporter to return data or take a path.
        
        # For now, let's call the function. We'll need to update jira_exporter.py 
        # to handle the /tmp path if running on Vercel.
        
        # We pass the filename which jira_exporter uses.
        # But jira_exporter uses os.path.join(os.path.dirname(__file__), filename)
        # We can't easily change that without modifying jira_exporter.
        
        # Let's try to run it. If it fails due to read-only, we'll know.
        # Actually, let's proactively fix jira_exporter to use /tmp if possible.
        
        jira_exporter.export_jira_as_data_to_csv()
        
        return {"status": "success", "message": "Jira data refreshed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
