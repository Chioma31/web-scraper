import requests
import json

def test_root():
    response = requests.get("http://localhost:8000/")
    print("Root endpoint test:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_opportunities():
    print("Testing opportunities endpoint...")
    response = requests.get("http://localhost:8000/opportunities")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Number of opportunities found: {len(data['opportunities'])}")
        # Print first opportunity as sample
        if data['opportunities']:
            print("\nSample opportunity:")
            print(json.dumps(data['opportunities'][0], indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Starting API tests...\n")
    test_root()
    test_opportunities() 