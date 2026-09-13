# Step 5 — Create API Gateway and send an HTTP request

**Status:** ✅ Complete

## Objective

Expose the Step Function from Step 3 via a REST API.

## Prerequisites

- [x] Step 3 complete — Step Function created and tested

## Tasks

- [x] Create an API Gateway HTTP API
- [x] Create a route and integration that publishes to EventBridge
- [x] Deploy the API
- [x] Send an HTTP request to the API endpoint

## Verification

- [x] API Gateway exists in `us-east-1`
- [x] HTTP request to the API endpoint triggers the Step Function
- [x] API returns expected response

Step 5 adds API Gateway. After this step, you won't need aws events put-events to start Project X.

The target is:

curl / Postman
      │
      │ POST /requests
      ▼
API Gateway HTTP API
      │
      │ PutEvents
      ▼
EventBridge
project-x-poc-bus
      │
      ▼
RequestReceived rule
      │
      ▼
Step Functions
project-x-poc-workflow
      │
      ▼
Lambda
project-x-poc-validator

We'll use API Gateway HTTP API → EventBridge directly. API Gateway supports the EventBridge-PutEvents AWS service integration, so we don't need another Lambda just to publish the event. AWS documentation: HTTP API AWS service integrations

## 5.1 Create an HTTP API

Go to:

AWS Console
→ API Gateway
→ APIs
→ Create API

You'll see different API types.

Find:

HTTP API

and click Build.

Make sure you're creating an HTTP API, not REST API.

Name it:

project-x-poc-api

If the console asks you to add an integration immediately, look for an AWS service integration. Depending on the current console flow, you may also be able to create the API first and add the integration afterward.

Our desired route is:

POST /requests
## 5.2 Understand what we're building

Previously you manually ran:

aws events put-events ...

Essentially telling EventBridge:

{
  "Source": "projectx.requests",
  "DetailType": "RequestReceived",
  "Detail": "{...}",
  "EventBusName": "project-x-poc-bus"
}

Now API Gateway will do that for you.

The caller sends:

{
  "requestId": "REQ-5001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

API Gateway turns that into an EventBridge PutEvents call.

## 5.3 Create the EventBridge integration

Inside your HTTP API, find:

Integrations

Choose:

Create integration

For integration type, select:

AWS service

Select:

EventBridge

and then:

PutEvents

The important integration subtype is:

EventBridge-PutEvents

If your console shows Integration subtype, select exactly that.

## 5.4 Create the IAM role

This is another place where our IAM pattern repeats.

API Gateway needs permission to call:

events:PutEvents

because API Gateway is going to publish to EventBridge.

Our permissions now look like:

API Gateway
     │
     │ events:PutEvents
     ▼
EventBridge

EventBridge
     │
     │ states:StartExecution
     ▼
Step Functions

Step Functions
     │
     │ lambda:InvokeFunction
     ▼
Lambda

You may need to provide an IAM role for the integration.

If the console offers to create/manage the role, use that option.

If it requires you to create one manually, go to:

IAM
→ Roles
→ Create role

For trusted entity/service choose:

API Gateway

Name it:

project-x-api-eventbridge-role

Give it permission to:

events:PutEvents

Ideally only against your:

project-x-poc-bus

For this POC, a policy conceptually looks like:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "events:PutEvents",
      "Resource": "YOUR_EVENT_BUS_ARN"
    }
  ]
}

You can find your bus ARN under:

EventBridge
→ Event buses
→ project-x-poc-bus

It will look approximately like:

arn:aws:events:us-east-1:
123456789012:
event-bus/project-x-poc-bus

Don't copy the example ARN; use yours.

## 5.5 Configure the PutEvents parameters

This is the most important part of Step 5.

The integration needs to construct the EventBridge event.

Configure:

Source
projectx.requests
DetailType
RequestReceived
EventBusName
project-x-poc-bus

For:

Detail

we want the HTTP request body.

For an HTTP API parameter mapping, this is typically:

$request.body

So conceptually API Gateway creates:

Source
     = projectx.requests

DetailType
     = RequestReceived

EventBusName
     = project-x-poc-bus

Detail
     = $request.body

This is the key mapping.

## 5.6 Understand the transformation

Suppose your caller sends:

POST /requests
Content-Type: application/json

with:

{
  "requestId": "REQ-5001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

API Gateway effectively publishes:

{
  "source": "projectx.requests",
  "detail-type": "RequestReceived",
  "detail": {
    "requestId": "REQ-5001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }
}

EventBridge then evaluates your Step 4 rule:

{
  "source": [
    "projectx.requests"
  ],
  "detail-type": [
    "RequestReceived"
  ]
}

It matches.

Then because we configured:

$.detail

in Step 4, Step Functions receives:

{
  "requestId": "REQ-5001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

And your existing Lambda already understands that.

So we're not changing Step Functions or Lambda.

We're simply adding another component in front of what already works.

## 5.7 Create the route

Now create a route.

Go to:

API Gateway
→ project-x-poc-api
→ Routes

Create:

POST /requests

Be careful with the HTTP method.

We want:

POST

not GET.

Attach your EventBridge integration to this route.

The relationship becomes:

project-x-poc-api

Route
POST /requests
       │
       ▼
Integration
EventBridge-PutEvents
## 5.8 Configure the stage

HTTP APIs normally have a:

$default

stage.

For our POC, that's fine.

Enable:

Auto-deploy

if it isn't already enabled.

That means changes to your API configuration are automatically deployed to the $default stage.

You do not need:

dev
test
qa
prod

stages yet.

We'll deal with environment separation later.

## 5.9 Find your API endpoint

Go to your API details.

You should see an Invoke URL or API endpoint similar to:

https://abc123xyz.execute-api.us-east-1.amazonaws.com

Therefore your endpoint is:

https://abc123xyz.execute-api.us-east-1.amazonaws.com/requests

Don't use that example URL; copy yours from the console.

## 5.10 Test with curl

Now go to your Mac Terminal.

Run:

curl -i -X POST \
  'YOUR_API_ENDPOINT/requests' \
  -H 'Content-Type: application/json' \
  -d '{
    "requestId": "REQ-5001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }'

For example:

POST
   ↓
https://abc123.execute-api.us-east-1.amazonaws.com/requests

API Gateway should return a successful HTTP response.

Don't worry yet if the response is an EventBridge-style acknowledgement rather than your final transaction result.

That's expected.

Our architecture is currently asynchronous.

## 5.11 Immediately check Step Functions

This is the real test.

Go to:

AWS Console
→ Step Functions
→ project-x-poc-workflow
→ Executions

You should see a new execution.

You did not:

Start execution

and you did not:

aws events put-events

You only made:

HTTP POST /requests

Yet AWS should have done:

HTTP POST
   ↓
API Gateway
   ↓
EventBridge PutEvents
   ↓
project-x-poc-bus
   ↓
Rule matched
   ↓
Step Functions started
   ↓
ValidateRequest
   ↓
Lambda
   ↓
Succeeded

Open the execution.

The input should be:

{
  "requestId": "REQ-5001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

And ValidateRequest should be green.

If that happens:

🎯 Your first end-to-end AWS ingress POC works.
## 5.12 Test invalid business data

Now try:

curl -i -X POST \
  'YOUR_API_ENDPOINT/requests' \
  -H 'Content-Type: application/json' \
  -d '{
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }'

Notice:

requestId

is missing.

What do you expect?

API Gateway itself currently doesn't know that's invalid.

Therefore:

API Gateway
    ↓
accepts HTTP request

EventBridge
    ↓
accepts event

Rule
    ↓
matches RequestReceived

Step Functions
    ↓
starts workflow

ValidateRequest
    ↓
Lambda detects missing requestId

Catch
    ↓
ValidationFailed

Go to Step Functions and confirm exactly that happens.

This is useful because you're starting to see separation of responsibilities.

## 5.13 Understand the responsibilities

At this point:

API Gateway answers:

How does an external caller enter my AWS application?

EventBridge answers:

What business event occurred, and which consumers care about it?

Step Functions answers:

What workflow should happen because of that event?

Lambda answers:

Perform this specific deterministic piece of work.

So:

API Gateway
     │
     │ ingress
     ▼
EventBridge
     │
     │ event routing
     ▼
Step Functions
     │
     │ orchestration
     ▼
Lambda
     │
     │ deterministic logic
     ▼
Business outcome

This separation is fundamental to the architecture you're learning.

## 5.14 Why doesn't curl receive the final Lambda result?

This is important.

You might expect:

curl
 ↓
API Gateway
 ↓
...
 ↓
Lambda
 ↓
"VALID"
 ↓
curl receives VALID

But that's not what we've built.

We've built:

Caller
   │
   │ POST request
   ▼
API Gateway
   │
   │ publish event
   ▼
EventBridge
   │
   └── API request accepted
          ↓
      HTTP response


Meanwhile asynchronously:

EventBridge
   ↓
Step Functions
   ↓
Lambda
   ↓
processing continues

The HTTP request is effectively saying:

"Project X, here's a request for you to process."

Not:

"Keep my HTTP connection open until the entire business transaction finishes."

This asynchronous model fits your eventual Project X workflow well because some requests could involve multiple validations, agents, external APIs, Pega transactions, follow-up communication, retries, and potentially long-running processing.

## 5.15 Test using Postman if you prefer

You can also use Postman.

Method:

POST

URL:

YOUR_API_ENDPOINT/requests

Header:

Content-Type: application/json

Body → raw → JSON:

{
  "requestId": "REQ-5002",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C67890",
  "newAddress": {
    "street": "456 Main Street",
    "city": "Jacksonville",
    "state": "FL",
    "zip": "32256"
  }
}

Send.

Then check Step Functions.

## 5.16 Look at API Gateway metrics

Go to:

API Gateway
→ project-x-poc-api
→ Monitor

You'll eventually see metrics such as requests, latency, 4xx responses, and 5xx responses.

For now, don't configure alarms.

We're just learning where to look.

## 5.17 Your IAM chain is getting interesting

You now have several independent identities:

             API Gateway
                  │
        project-x-api-eventbridge-role
                  │
          events:PutEvents
                  ▼
             EventBridge
                  │
         EventBridge IAM role
                  │
       states:StartExecution
                  ▼
            Step Functions
                  │
        Step Functions IAM role
                  │
       lambda:InvokeFunction
                  ▼
               Lambda
                  │
         Lambda execution role
                  │
             CloudWatch

This is a key AWS lesson:

The AWS service performing an action needs authorization to perform that action.

Later you'll extend this:

Step Functions/Lambda
       │
       │ bedrock-agentcore:InvokeAgentRuntime
       ▼
AgentCore Runtime
       │
       │ bedrock:InvokeModel
       ▼
Claude
## 5.18 Don't add authentication yet

Your POC API is currently effectively:

POST /requests
    ↓
No application authentication

That's okay temporarily for the learning POC, but don't treat that as a production design.

Don't add:

Entra ID
OAuth
JWT Authorizer
mTLS
DataPower
WAF

yet.

We'll do security after the core flow works.

For your eventual architecture, the ingress becomes much more like:

On-prem producer
       ↓
IBM DataPower
       ↓
OAuth / mTLS
       ↓
API Gateway
       ↓
EventBridge

But adding all that now would obscure what you're learning.

Step 5 completion test

Your final test should be:

curl -X POST \
  'YOUR_API_ENDPOINT/requests' \
  -H 'Content-Type: application/json' \
  -d '{
    "requestId": "REQ-5003",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }'

Then verify:

POST /requests
      │
      ▼
project-x-poc-api
      │
      ▼
project-x-poc-bus
      │
      ▼
project-x-request-received-rule
      │
      ▼
project-x-poc-workflow
      │
      ▼
ValidateRequest
      │
      ▼
project-x-poc-validator
      │
      ▼
VALID

Your checklist is:

- [x] project-x-poc-api exists
- [x] API type = HTTP API
- [x] POST /requests exists
- [x] Integration = EventBridge-PutEvents
- [x] Source = projectx.requests
- [x] DetailType = RequestReceived
- [x] EventBusName = project-x-poc-bus
- [x] Detail = HTTP request body
- [x] API Gateway IAM role can events:PutEvents
- [x] curl returns successful HTTP response
- [x] EventBridge rule matches
- [x] Step Functions starts automatically
- [x] REQ-5003 appears as workflow input
- [x] ValidateRequest succeeds
- [x] Invalid request reaches ValidationFailed

Once REQ-5003 goes from curl all the way to your Lambda, stop there. Step 5 is complete.

## Next Step

Proceed to [Step 6 — Rebuild those resources using CDK/IaC](06-cdk-iac.md).
