from common.error_handling import get_safety_reason

def test_get_safety_reason_known_code():
    error_message = "Veo could not generate videos because the input image violates Vertex AI's usage guidelines. If you think this was an error, send feedback. Support codes: 15236754"
    result = get_safety_reason(error_message)
    assert result == "Safety Filter Blocked: Celebrity (Support Code: 15236754). Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist for this feature. Please adjust your request."

def test_get_safety_reason_unknown_code():
    error_message = "Veo could not generate videos. Support codes: 99999999"
    result = get_safety_reason(error_message)
    assert result == "Safety Filter Blocked: Unknown Safety Issue (Support Code: 99999999). No additional details available. Please adjust your request."

def test_get_safety_reason_no_code():
    error_message = "A standard API error occurred."
    result = get_safety_reason(error_message)
    assert result is None

def test_get_safety_reason_code_syntax():
    error_message = "Support code: 58061214"
    result = get_safety_reason(error_message)
    assert result == "Safety Filter Blocked: Child (Support Code: 58061214). Rejects requests to generate content depicting children if personGeneration isn't set to 'allow_all' or if the project isn't on the allowlist for this feature. Please adjust your request."

if __name__ == "__main__":
    test_get_safety_reason_known_code()
    test_get_safety_reason_unknown_code()
    test_get_safety_reason_no_code()
    test_get_safety_reason_code_syntax()
    print("All tests passed!")
