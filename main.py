from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional
import sys
import os

# Add api directory to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from keyword_planner import generate_keyword_ideas
from competitor_research import CompetitorResearcher
from whatsapp_handler import WhatsAppHandler
from whatsapp_client import WhatsAppClient
import asyncio
import datetime

app = FastAPI(title="Google Ads Keyword Research Tool")

# Initialize WhatsApp handler
whatsapp_handler = WhatsAppHandler()

# Background task for hourly messages
async def hourly_scheduler():
    """Sends a message every hour to the last active user"""
    print("⏰ Hourly scheduler started!")
    
    while True:
        try:
            # Calculate time until next hour
            now = datetime.datetime.now()
            next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            wait_seconds = (next_hour - now).total_seconds()
            
            print(f"⏰ Next message at {next_hour.strftime('%H:%M')}, waiting {int(wait_seconds)}s")
            await asyncio.sleep(wait_seconds)
            
            # Read the last user's number
            target_number = None
            if os.path.exists("last_user.txt"):
                with open("last_user.txt", "r") as f:
                    target_number = f.read().strip()
            
            if target_number:
                current_time = datetime.datetime.now().strftime("%H:%M")
                message = f"Hellow world! it's now {current_time}"
                
                print(f"⏰ Sending hourly message to {target_number}: {message}")
                client = WhatsAppClient()
                await client.send_text_message(target_number, message)
            else:
                print("⏰ No active user found for hourly message yet.")
                
        except Exception as e:
            print(f"❌ Error in hourly scheduler: {e}")
            # Wait 1 minute before retrying on error
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Start the background task
    asyncio.create_task(hourly_scheduler())

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

# ============================================
# WHATSAPP WEBHOOK ENDPOINTS
# ============================================

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Webhook verification endpoint for WhatsApp
    Meta will call this to verify the webhook URL
    """
    result = whatsapp_handler.verify_webhook(mode, token, challenge)
    
    if result:
        return PlainTextResponse(content=result, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receive incoming WhatsApp messages
    """
    try:
        body = await request.json()
        
        # Extract message data
        entry = body.get("entry", [])
        if not entry:
            return {"status": "no entry"}
        
        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no changes"}
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            # Could be a status update, ignore
            return {"status": "no messages"}
        
        # Process each message (usually just one)
        for message in messages:
            # Process message in background to respond quickly
            asyncio.create_task(whatsapp_handler.handle_message(message))
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        # Return 200 anyway to avoid Meta retrying
        return {"status": "error", "message": str(e)}

# ============================================
# STATIC FILES (Must be last)
# ============================================

# Serve static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
