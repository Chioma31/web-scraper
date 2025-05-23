from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
import traceback
from main import find_creative_opportunities, Opportunity

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
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to Creative Opportunities API"}

@app.get("/opportunities", response_model=List[Opportunity])
async def get_opportunities():
    try:
        logger.info("Starting to fetch creative opportunities...")
        result = find_creative_opportunities()
        opportunities = result["opportunities"]
        logger.info(f"Successfully fetched {len(opportunities)} opportunities")
        return opportunities
    except Exception as e:
        error_msg = f"Error fetching opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch opportunities",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        )

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 