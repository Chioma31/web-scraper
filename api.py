from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
import traceback
from main import find_creative_opportunities, Opportunity
from firebase_config import save_opportunity, get_opportunities
import threading
import time
import schedule
from datetime import datetime
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_opportunities():
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

def run_scheduler():
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            time.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up the application...")
    
    # Schedule the job to run every 30 minutes
    schedule.every(30).minutes.do(fetch_opportunities)
    
    # Run the job immediately on startup
    fetch_opportunities()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler started. Will fetch opportunities every 30 minutes.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down the application...")
    # Add any cleanup code here if needed

app = FastAPI(
    title="Creative Opportunities API",
    description="API for finding creative opportunities for Nigerian creatives",
    version="1.0.0",
    lifespan=lifespan
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

@app.get("/opportunities", response_model=List[Opportunity])
async def get_opportunities_endpoint():
    try:
        logger.info("Fetching opportunities from Firestore...")
        opportunities = get_opportunities()
        logger.info(f"Successfully fetched {len(opportunities)} opportunities from Firestore")
        return opportunities
    except Exception as e:
        error_msg = f"Error fetching opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create", response_model=List[Opportunity])
async def refresh_opportunities():
    try:
        logger.info("Starting to fetch new creative opportunities...")
        result = find_creative_opportunities()
        opportunities = result["opportunities"]
        
        # Save each opportunity to Firestore
        for opportunity in opportunities:
            save_opportunity(opportunity)
            
        logger.info(f"Successfully saved {len(opportunities)} opportunities to Firestore")
        return opportunities
    except Exception as e:
        error_msg = f"Error adding opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 