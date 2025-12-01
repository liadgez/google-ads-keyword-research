from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional
import sys
import os

# Add api directory to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from keyword_planner import generate_keyword_ideas
from competitor_research import CompetitorResearcher
import asyncio

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

class CompetitorRequest(BaseModel):
    url: HttpUrl
    method: Optional[str] = "gemini"  # gemini, google, or hybrid
    
    @validator('url')
    def validate_url(cls, v):
        return str(v)
    
    @validator('method')
    def validate_method(cls, v):
        if v not in ['gemini', 'google', 'hybrid']:
            raise ValueError('method must be gemini, google, or hybrid')
        return v

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

@app.post("/competitor-research")
async def competitor_research(request: CompetitorRequest):
    print(f"Received competitor research request for URL: {request.url}")
    
    try:
        researcher = CompetitorResearcher()
        result = await researcher.analyze(request.url, request.method)
        
        # Convert Pydantic model to dict for JSON response
        return {
            "success": True,
            "brand_info": result.brand_info.model_dump(),
            "keywords": [k.model_dump() for k in result.keywords],
            "selected_keyword": result.selected_keyword,
            "competitors": [c.model_dump() for c in result.competitors],
            "citations": [c.model_dump() for c in result.citations],
            "market_insight": result.market_insight,
            "metadata": result.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
