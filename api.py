from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
import traceback
from main import find_creative_opportunities, Opportunity
from firebase_config import save_opportunity, get_opportunities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Creative Opportunities API",
    description="API for finding creative opportunities for Nigerian creatives",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Creative Opportunities API"}

@app.get("/opportunities")
async def get_opportunities_endpoint():
    try:
        logger.info("Fetching opportunities from Firestore...")
        opportunities = get_opportunities()
        logger.info(f"Successfully fetched {len(opportunities)} opportunities from Firestore")
        return opportunities
    except Exception as e:
        error_msg = f"Error fetching opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": str(e)}

@app.post("/create")
async def refresh_opportunities():
    try:
        logger.info("Starting to fetch new creative opportunities...")
        result = find_creative_opportunities()
        opportunities = result["opportunities"]
        
        # Save each opportunity to Firestore
        for opportunity in opportunities:
            save_opportunity(opportunity)
            
        logger.info(f"Successfully saved {len(opportunities)} opportunities to Firestore")
        return {"message": f"Successfully added {len(opportunities)} opportunities"}
    except Exception as e:
        error_msg = f"Error adding opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 