# test_fms_api.py: New file for Confident AI testing - use deepeval to evaluate API responses for correctness, hallucination, etc.

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase
import requests
import os

# Confident AI API key from .env
os.getenv("CONFIDENT_API_KEY")  # Automatically used by deepeval

API_ENDPOINT = "http://127.0.0.1:8000/generate-workout"  # or your live URL

def call_api(input_payload):
    response = requests.post(API_ENDPOINT, json=input_payload)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"API error: {response.text}")

# Example test cases (add more with your JSON inputs/expected)
test_cases = [
    {
        "input": {  # Near-perfect profile
            "overhead_squat": { "score": 0, "trunk_torso": { "upright_torso": 3, ... } , ... },
            # Full perfect input JSON
        },
        "expected_output": json.dumps({"difficulty_color": "Green", "effective_scores": {"overhead_squat": 3, ...}}),
        "expected_reason": "High scores should give Green/Power level"
    },
    # Add test case 2, etc.
]

for case in test_cases:
    actual_output = call_api(case["input"])

    test_case = LLMTestCase(
        input=str(case["input"]),
        actual_output=str(actual_output),
        expected_output=case["expected_output"],
        retrieval_context=["FMS book criteria"]
    )

    evaluate(
        test_cases=[test_case],
        metrics=[
            AnswerRelevancyMetric(threshold=0.7),
            FaithfulnessMetric(threshold=0.7),
            HallucinationMetric(threshold=0.3)
        ]
    )