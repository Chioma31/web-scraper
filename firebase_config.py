import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

def initialize_firebase():
    load_dotenv()
    
    # Get the path to your service account key file
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    if not service_account_path:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH environment variable is not set")
    
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    db = firestore.client()
    return db

# Initialize Firestore
db = initialize_firebase()

def save_opportunity(opportunity_data):
    """
    Save an opportunity to Firestore
    """
    try:
        # Add to 'opportunities' collection
        doc_ref = db.collection('opportunities').document()
        doc_ref.set(opportunity_data)
        return {"id": doc_ref.id, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

def get_opportunities():
    """
    Get all opportunities from Firestore
    """
    try:
        opportunities = []
        docs = db.collection('opportunities').stream()
        for doc in docs:
            opportunity = doc.to_dict()
            opportunity['id'] = doc.id
            opportunities.append(opportunity)
        return opportunities
    except Exception as e:
        return {"error": str(e), "status": "error"} 