from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional
import sys
import os

# Add api directory to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from keyword_planner import generate_keyword_ideas

app = FastAPI(title="Google Ads Keyword Research Tool")

# Request model
class KeywordRequest(BaseModel):
    url: HttpUrl
    
    @validator('url')
    def validate_url(cls, v):
        return str(v)
    keywords: Optional[List[str]] = None
    languageCode: Optional[str] = "en"
    locationIds: Optional[List[str]] = None

# API Endpoint
@app.post("/keyword-research")
def keyword_research(request: KeywordRequest):
    print(f"Received request for URL: {request.url}")
    
    result = generate_keyword_ideas(
        url=request.url,
        keywords=request.keywords,
        language_code=request.languageCode,
        location_ids=request.locationIds
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
    return result

# Serve static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
