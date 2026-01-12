from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# IMPORTANT: Ensure this matches your file name (embedding.py)
import embedding 

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/find-fuel")
def find_fuel(data: PromptRequest):
    print(f"Analyzing: {data.prompt}")
    
    # 1. Ask Ollama (Make sure "qwen3" is the right name!)
    extracted = embedding.extract_search_params(data.prompt, model_name="qwen3:0.6b")
    
    if not extracted or "city" not in extracted:
        raise HTTPException(status_code=400, detail="AI could not understand the city or fuel.")

    # 2. Get Coordinates
    coords = embedding.get_coordinates(extracted["city"])
    if not coords:
        raise HTTPException(status_code=404, detail="City not found.")

    # 3. Get Prices
    stations = embedding.fetch_fuel_data(
        coords['lat'], coords['lon'], extracted.get("fuel_type", "Gazole")
    )

    return {"analysis": extracted, "results": stations}