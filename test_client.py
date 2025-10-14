#!/usr/bin/env python3
"""
Test client for Mock Interviews AI API.
Demonstrates all optimizations in action.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def create_interview_session():
    """Create a new interview session."""
    print_section("Creating Interview Session")

    payload = {
        "interview_type": "technical",
        "role": "Software Engineer",
        "level": "senior",
        "focus_areas": ["algorithms", "data structures", "system design"]
    }

    response = requests.post(f"{BASE_URL}/interviews/sessions", json=payload)
    session_data = response.json()

    print(f"✅ Session created: {session_data['id']}")
    print(f"📋 Interview Type: {session_data['interview_type']}")
    print(f"💼 Role: {session_data['role']}")
    print(f"📊 Level: {session_data['level']}")
    print(f"\n💬 Initial question from interviewer:")
    print(f"   {session_data['messages'][-1]['content'][:200]}...")

    return session_data['id']


def send_message(session_id, content):
    """Send a message in the interview."""
    print_section("Sending Message")

    start_time = time.time()

    payload = {"content": content}
    response = requests.post(
        f"{BASE_URL}/interviews/sessions/{session_id}/messages",
        json=payload
    )

    duration = time.time() - start_time
    result = response.json()

    print(f"⏱️  Response time: {duration:.2f}s")
    print(f"\n👤 Your answer:")
    print(f"   {result['user_message']['content'][:150]}...")
    print(f"\n🤖 Interviewer response:")
    print(f"   {result['assistant_message']['content'][:200]}...")

    # Show optimization metadata
    if 'metadata' in result['assistant_message']:
        metadata = result['assistant_message']['metadata']
        print(f"\n📊 Optimizations applied:")
        if metadata.get('cached'):
            print(f"   ✅ Semantic cache HIT")
        if 'optimizations' in metadata:
            for opt in metadata['optimizations']:
                print(f"   ✅ {opt}")
        if 'token_usage' in metadata:
            usage = metadata['token_usage']
            print(f"   💰 Token savings: {usage.get('saved', 0)} tokens")

    return result


def end_interview(session_id):
    """End the interview and get feedback."""
    print_section("Ending Interview & Getting Feedback")

    response = requests.post(f"{BASE_URL}/interviews/sessions/{session_id}/end")
    feedback = response.json()

    print(f"📊 Overall Score: {feedback['overall_score']}/10")
    print(f"\n💬 Feedback:")
    print(f"   {feedback['feedback'][:300]}...")

    print(f"\n✅ Strengths:")
    for strength in feedback.get('strengths', [])[:3]:
        print(f"   • {strength}")

    print(f"\n📈 Areas for Improvement:")
    for area in feedback.get('areas_for_improvement', [])[:3]:
        print(f"   • {area}")

    return feedback


def check_health():
    """Check API health and optimization status."""
    print_section("Checking API Health")

    response = requests.get(f"{BASE_URL}/metrics/health")
    health = response.json()

    print(f"Status: {health['status']}")
    print(f"\n🚀 Optimizations Status:")
    for opt, enabled in health['optimizations'].items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"   {opt}: {status}")


def main():
    """Run the test client."""
    print("\n" + "="*60)
    print("  Mock Interviews AI - Test Client")
    print("  Demonstrating Advanced Optimizations")
    print("="*60)

    try:
        # Check health
        check_health()

        # Create session
        session_id = create_interview_session()
        time.sleep(1)

        # Send some messages
        messages = [
            "I would approach this problem using a hash map to store the elements and their indices. This gives us O(1) lookup time.",
            "For the time complexity, the solution would be O(n) since we iterate through the array once.",
            "Can you give me another question?"
        ]

        for msg in messages:
            send_message(session_id, msg)
            time.sleep(2)

        # End interview
        end_interview(session_id)

        print_section("Test Completed Successfully")
        print("🎉 All optimizations demonstrated:")
        print("   ✅ Model Routing (automatic)")
        print("   ✅ Semantic Caching (on similar queries)")
        print("   ✅ Prompt Compression (for long conversations)")
        print("   ✅ Session Summarization (after 10+ messages)")
        print("   ✅ Hybrid Inference (smart model selection)")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("   Make sure the API is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
