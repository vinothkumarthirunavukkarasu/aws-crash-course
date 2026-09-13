import json


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event))

    request_id = event.get("requestId")
    request_type = event.get("requestType")

    if not request_id:
        raise ValueError("requestId is required")

    if not request_type:
        raise ValueError("requestType is required")

    response = {
        "requestId": request_id,
        "requestType": request_type,
        "validationStatus": "VALID",
        "message": "Project X request passed initial validation"
    }

    print("Validation response:")
    print(json.dumps(response))

    return response