#!/usr/bin/env python3
"""
Local test script for Task 2 scoring.
Run: python test_local.py
"""

import json

import requests

# Sample Task 2 essay (266 words)
SAMPLE_ESSAY = """Some people believe that unpaid community service should be a compulsory part of high school programmes. To what extent do you agree or disagree?

In recent years, there has been growing debate about whether high school students should be required to participate in unpaid community service as part of their curriculum. While some argue this requirement would be beneficial, I partially agree with this proposition, believing that voluntary participation would be more effective than compulsion.

On the one hand, mandatory community service could provide numerous benefits to both students and society. Firstly, it would expose young people to real-world problems and foster a sense of social responsibility. Through activities such as helping the elderly or environmental conservation, students would develop empathy and understanding of diverse social issues. Additionally, these experiences could help students discover potential career paths and develop practical skills that cannot be learned in traditional classroom settings. Moreover, communities would benefit from the additional support, particularly in areas with limited resources.

On the other hand, forcing students to participate in community service may have counterproductive effects. When activities are mandatory, students might view them as mere obligations rather than meaningful contributions, potentially developing negative attitudes toward volunteering. Furthermore, adding compulsory service to already demanding academic schedules could increase stress levels and reduce time for essential studies or personal development. Some students may also have family responsibilities or part-time jobs that make additional commitments challenging.

In conclusion, while community service offers valuable learning experiences and social benefits, making it compulsory may diminish its intended impact. Instead, schools should strongly encourage voluntary participation and provide diverse opportunities that appeal to different interests, allowing students to engage genuinely with their communities while maintaining autonomy over their choices."""

def test_local_scoring():
    """Test the /score endpoint locally."""
    url = "http://localhost:8000/score"
    
    request_data = {
        "task_type": "task2",
        "essay": SAMPLE_ESSAY,
        "question": "Some people believe that unpaid community service should be a compulsory part of high school programmes. To what extent do you agree or disagree?"
    }
    
    print("Testing Task 2 scoring locally...")
    print(f"Essay length: {len(SAMPLE_ESSAY.split())} words\n")
    
    try:
        response = requests.post(url, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Scoring successful!\n")
            print(f"Overall Band: {result['overall']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Dispersion: {result['dispersion']}")
            print(f"Votes: {result['votes']}\n")
            
            print("Per-criterion scores:")
            for criterion in result['per_criterion']:
                print(f"  - {criterion['name']}: {criterion['band']}")
            
            print(f"\nPrompt Hash: {result['meta']['prompt_hash'][:16]}...")
            print(f"Token Usage: {result['meta']['token_usage']}")
            
            # Save full response for inspection
            with open("test_response.json", "w") as f:
                json.dump(result, f, indent=2)
            print("\n📄 Full response saved to test_response.json")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running:")
        print("   cd LLM && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_local_scoring()
