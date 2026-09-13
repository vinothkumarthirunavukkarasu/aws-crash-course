# Step 2 — Create one Lambda manually and test it

**Status:** ✅ Complete

## Objective

Create one Python Lambda in AWS, run it, and inspect its logs.

No Step Functions, EventBridge, API Gateway, AgentCore, or MCP yet.

## Prerequisites

- [ ] Step 1 complete — AWS CLI configured and authenticated

## Overview

At the end, this should work:

```
You
 |
 | Test event
 v
AWS Lambda
 |
 | runs Python
 v
Returns JSON
 |
 v
CloudWatch Logs
```

---

## 2.1 Open Lambda

In the AWS Console, make sure the top-right region says:

```
N. Virginia
us-east-1
```

Then search for:

```
Lambda
```

Open AWS Lambda and click:

```
Create function
```

Choose:

```
Author from scratch
```

Use:

| Setting | Value |
|---------|-------|
| Function name | `project-x-poc-validator` |
| Runtime | `Python 3.12` |
| Architecture | `x86_64` |
| Permissions | `Create a new role with basic Lambda permissions` |

Then click:

```
Create function
```

AWS will automatically create an IAM execution role for the Lambda.

---

## 2.2 Understand the Lambda execution role

After creation, go to:

```
Configuration → Permissions
```

You should see something like:

```
Execution role
project-x-poc-validator-role-xxxxx
```

This is important.

Your Lambda is **not** running as your `project-x-admin` user.

It runs as its own IAM role:

```
You
 |
 | create/deploy
 v
Lambda
 |
 | assumes
 v
Lambda execution role
 |
 v
AWS services
```

This concept will come back constantly in AWS.

Later:

| Service | IAM Role |
|---------|----------|
| Step Functions | IAM role |
| Lambda | IAM role |
| AgentCore | IAM role |
| API Gateway | IAM role |
| GitHub | IAM role |

---

## 2.3 Replace the default Lambda code

Go to:

```
Code → lambda_function.py
```

Replace everything with:

```python
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
```

Click:

```
Deploy
```

You should see:

```
Successfully updated the function
```

---

## 2.4 Create a test event

Click:

```
Test
```

AWS will ask you to configure a test event.

Choose:

```
Create new event
```

Event name:

```
ValidChangeAddressRequest
```

Paste:

```json
{
  "requestId": "REQ-1001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345",
  "newAddress": {
    "street": "123 Main Street",
    "city": "Jacksonville",
    "state": "FL",
    "zip": "32256"
  }
}
```

Save it.

Then click:

```
Test
```

---

## 2.5 Expected result

You should see:

```
Execution result: succeeded
```

And something similar to:

```json
{
  "requestId": "REQ-1001",
  "requestType": "CHANGE_ADDRESS",
  "validationStatus": "VALID",
  "message": "Project X request passed initial validation"
}
```

Congratulations — this is your first running Project X component in AWS.

The flow is:

```
Input JSON
   |
   v
Lambda
   |
   +--> requestId present?
   |
   +--> requestType present?
   |
   v
VALID
```

---

## 2.6 Test a failure

This is equally important.

Create another test event:

```
MissingRequestId
```

Use:

```json
{
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}
```

Click:

```
Test
```

This time it should fail with something like:

```
ValueError: requestId is required
```

Excellent.

We now know our Lambda supports both:

```
valid request
    ↓
success

invalid request
    ↓
error
```

This will matter when we connect Step Functions.

---

## 2.7 Look at CloudWatch logs

Now let's see where Lambda logs go.

From the Lambda page go to:

```
Monitor
```

Then:

```
View CloudWatch logs
```

You'll be taken to a log group similar to:

```
/aws/lambda/project-x-poc-validator
```

Inside it you'll see a log stream.

Open the latest one.

You should see:

```
START RequestId: ...

Received event:
{"requestId": "REQ-1001", ...}

Validation response:
{"requestId": "REQ-1001", ...}

END RequestId: ...

REPORT RequestId: ...
Duration: ...
Memory Size: ...
Max Memory Used: ...
```

This is your first introduction to CloudWatch Logs.

Later essentially everything in Project X will send logs there:

- Lambda
- Step Functions
- API Gateway
- AgentCore
- MCP server

---

## 2.8 Understand event and context

This Lambda signature:

```python
def lambda_handler(event, context):
```

is very important.

### `event`

Contains the input.

Today:

```json
{
  "requestId": "REQ-1001",
  "requestType": "CHANGE_ADDRESS"
}
```

Later this event could come from:

- API Gateway
- EventBridge
- Step Functions
- SQS
- another Lambda

So think:

```
event = input message
```

### `context`

Contains information about the running Lambda.

For example:

```python
context.aws_request_id
```

You can try:

```python
print("Lambda request ID:", context.aws_request_id)
```

That becomes useful for tracing.

---

## 2.9 Check the Lambda from your Mac

Now let's confirm that your local CLI can see it.

Run:

```bash
aws lambda list-functions \
  --region us-east-1
```

You should see:

```json
{
  "Functions": [
    {
      "FunctionName": "project-x-poc-validator"
    }
  ]
}
```

Now try:

```bash
aws lambda get-function \
  --function-name project-x-poc-validator \
  --region us-east-1
```

You should get Lambda configuration information.

That proves:

```
Your Mac
   |
 AWS CLI
   |
   v
AWS
   |
   v
project-x-poc-validator
```

---

## 2.10 Invoke Lambda from your Mac

This is optional but useful.

Create a file inside your project directory:

```bash
cat > event.json <<'EOF'
{
  "requestId": "REQ-2001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C67890"
}
EOF
```

Now invoke Lambda:

```bash
aws lambda invoke \
  --function-name project-x-poc-validator \
  --payload fileb://event.json \
  response.json
```

You should see something like:

```json
{
  "StatusCode": 200,
  "ExecutedVersion": "$LATEST"
}
```

Now:

```bash
cat response.json
```

Expected:

```json
{
  "requestId": "REQ-2001",
  "requestType": "CHANGE_ADDRESS",
  "validationStatus": "VALID",
  "message": "Project X request passed initial validation"
}
```

Now you have tested Lambda in two ways:

| Method | Path |
|--------|------|
| AWS Console | Console → Lambda |
| Mac CLI | Mac → AWS CLI → Lambda |

---

## Key Concept Before Step 3

Your Lambda currently exists independently:

```
            AWS

     +------------------+
     | Lambda           |
     |                  |
     | validator        |
     +------------------+
```

You manually invoke it.

But our real architecture needs:

```
Step Functions
      |
      v
Lambda
```

Step Functions will eventually send:

```json
{
  "requestId": "REQ-1001",
  "requestType": "CHANGE_ADDRESS"
}
```

to this exact Lambda.

So we aren't creating throwaway learning code.

This Lambda becomes the first state in our Project X workflow.

---

## Verification Checklist

Before moving on, verify these:

- [x] `project-x-poc-validator` exists
- [x] Python code deployed
- [x] Valid test returns `validationStatus = VALID`
- [x] Missing `requestId` throws an error
- [x] CloudWatch contains the logs
- [x] `aws lambda list-functions` sees the Lambda
- [x] CLI invocation works

If those work, Step 2 is complete.

## Next Step

Proceed to [Step 3 — Create a Step Function that calls Lambda](03-step-functions.md).
