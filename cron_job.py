import schedule
import time
import requests
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API URL from environment variable 
API_URL = os.getenv("API_URL")


def fetch_opportunities():
    try:
        logger.info(f"Starting scheduled opportunity fetch at {datetime.now()}")
        response = requests.post(API_URL)
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched opportunities: {response.json()}")
        else:
            logger.error(f"Failed to fetch opportunities. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error occurred while fetching opportunities: {str(e)}")

def main():
    # Schedule the job to run every 30 minutes
    schedule.every(30).minutes.do(fetch_opportunities)
    
    # Run the job immediately on startup
    fetch_opportunities()
    
    logger.info("Cron job started. Will fetch opportunities every 30 minutes.")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 