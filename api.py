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
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504, 404, 403, 429]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_opportunities():
    try:
        logger.info(f"Starting scheduled opportunity fetch at {datetime.now()}")
        result = find_creative_opportunities()
        
        if not result or "opportunities" not in result:
            logger.error("No opportunities found in result")
            return
            
        opportunities = result["opportunities"]
        
        if not opportunities:
            logger.warning("No opportunities to save")
            return
        
        # Save each opportunity to Firestore
        for opportunity in opportunities:
            try:
                save_opportunity(opportunity)
                logger.info(f"Successfully saved opportunity: {opportunity.title}")
            except Exception as e:
                logger.error(f"Error saving opportunity {opportunity.title}: {str(e)}")
                continue
            
        logger.info(f"Successfully saved {len(opportunities)} opportunities to Firestore")
    except Exception as e:
        error_msg = f"Error in scheduled task: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def run_scheduler():
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying if there's an error

@app.on_event("startup")
async def startup_event():
    # Schedule the job to run every 30 minutes
    schedule.every(30).minutes.do(fetch_opportunities)
    
    # Run the job immediately on startup
    fetch_opportunities()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler started. Will fetch opportunities every 30 minutes.")

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
        
        if not result or "opportunities" not in result:
            logger.error("No opportunities found in result")
            return {"error": "No opportunities found"}
            
        opportunities = result["opportunities"]
        
        if not opportunities:
            logger.warning("No opportunities to save")
            return {"message": "No new opportunities found"}
        
        # Save each opportunity to Firestore
        saved_count = 0
        for opportunity in opportunities:
            try:
                save_opportunity(opportunity)
                saved_count += 1
                logger.info(f"Successfully saved opportunity: {opportunity.title}")
            except Exception as e:
                logger.error(f"Error saving opportunity {opportunity.title}: {str(e)}")
                continue
            
        logger.info(f"Successfully saved {saved_count} opportunities to Firestore")
        return {"message": f"Successfully added {saved_count} opportunities"}
    except Exception as e:
        error_msg = f"Error adding opportunities: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 