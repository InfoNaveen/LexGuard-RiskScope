"""Test script for LexGuard RiskScope API."""
import requests
import json
import time
from websocket import create_connection

# TODO: Update with your Cloud Run URL
BASE_URL = "http://localhost:8080"  # For local testing
# BASE_URL = "https://lexguard-backend-{region}.run.app"  # For production

def test_health():
    """Test health check endpoint."""
    print("🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_ingest():
    """Test clause ingestion."""
    print("📥 Testing clause ingestion...")
    
    payload = {
        "job_id": "test-job-001",
        "clauses": [
            {
                "clause_id": "clause-1",
                "text": "Employee agrees not to compete with the Company or engage in any business that competes with the Company for a period of two (2) years following termination of employment, within a 50-mile radius of any Company office.",
                "page_number": 5
            },
            {
                "clause_id": "clause-2",
                "text": "All intellectual property, inventions, discoveries, and works created by Employee during employment shall be the sole and exclusive property of the Company, including any work created outside of normal business hours.",
                "page_number": 7
            },
            {
                "clause_id": "clause-3",
                "text": "Company may collect, store, and share Employee's personal data including location data, browsing history, and biometric information with third-party partners for business purposes.",
                "page_number": 12
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pipeline/ingest",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    return payload["job_id"]

def test_analyze(job_id):
    """Test analysis trigger."""
    print(f"🔍 Testing analysis for job {job_id}...")
    
    response = requests.get(f"{BASE_URL}/api/analyze/{job_id}")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_websocket(job_id):
    """Test WebSocket streaming."""
    print(f"🔌 Testing WebSocket for job {job_id}...")
    
    ws_url = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
    
    try:
        ws = create_connection(f"{ws_url}/ws/{job_id}")
        print("WebSocket connected!")
        
        # Listen for events
        event_count = 0
        while event_count < 20:  # Listen for up to 20 events
            try:
                result = ws.recv()
                event = json.loads(result)
                print(f"📨 Event: {event['event']}")
                if event.get('clause_id'):
                    print(f"   Clause: {event['clause_id']}")
                if event.get('data'):
                    print(f"   Data: {json.dumps(event['data'], indent=4)[:200]}...")
                print()
                
                event_count += 1
                
                # Break if job complete
                if event['event'] == 'job_complete':
                    break
                    
            except Exception as e:
                print(f"Error receiving: {e}")
                break
        
        ws.close()
        print("WebSocket closed")
        
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    print()

def test_report(job_id):
    """Test report retrieval."""
    print(f"📊 Testing report retrieval for job {job_id}...")
    
    # Wait a bit for analysis to complete
    print("Waiting for analysis to complete...")
    time.sleep(5)
    
    response = requests.get(f"{BASE_URL}/api/report/{job_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        report = response.json()
        print(f"Job Status: {report['status']}")
        print(f"Total Clauses: {report['total_clauses']}")
        print(f"Processed: {report['processed_clauses']}")
        print()
        
        # Print first clause analysis if available
        if report['clauses']:
            clause = report['clauses'][0]
            print("First Clause Analysis:")
            print(f"  Type: {clause['clause_type']}")
            print(f"  Severity: {clause['severity']}")
            print(f"  Risk Scores: {clause['risk_scores']}")
            print(f"  Summary: {clause['plain_language_summary'][:100]}...")
            print(f"  Adversary Argument: {clause['adversary_argument'][:150]}...")
            print(f"  Recommendation: {clause['negotiation_recommendation'][:100]}...")
    else:
        print(f"Response: {response.text}")
    
    print()

def main():
    """Run all tests."""
    print("=" * 60)
    print("LexGuard RiskScope API Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test health
        test_health()
        
        # Test ingest
        job_id = test_ingest()
        
        # Test analyze
        test_analyze(job_id)
        
        # Test WebSocket (optional - comment out if not needed)
        # test_websocket(job_id)
        
        # Wait for analysis to complete
        print("⏳ Waiting 30 seconds for analysis to complete...")
        time.sleep(30)
        
        # Test report
        test_report(job_id)
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
