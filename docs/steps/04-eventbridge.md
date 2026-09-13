# Step 4 — Create EventBridge and trigger the Step Function

**Status:** ✅ Complete

## Objective

Schedule or event-trigger the Step Function from Step 3.

## Prerequisites

- [x] Step 3 complete — Step Function created and tested

## Tasks

- [x] Create an EventBridge custom bus
- [x] Create a rule that matches Project X request events
- [x] Configure the rule to trigger the Step Function
- [x] Test matching and non-matching events

## Overview

Step 4 is where your POC becomes event-driven.

Right now you manually start Step Functions:

```text
You
 ↓
Step Functions
 ↓
ValidateRequest Lambda
```

After Step 4:

```text
You send an event
      ↓
EventBridge custom bus
      ↓
EventBridge rule
      ↓
Step Functions starts automatically
      ↓
ValidateRequest Lambda
```

AWS supports using a Step Functions state machine as an EventBridge rule target.

## 4.1 Create a custom EventBridge bus

Open **AWS Console → Amazon EventBridge → Event buses**, then click **Create event bus**.

Name the bus `project-x-poc-bus`.

Leave other settings at default for now.

Create it.

A custom event bus is useful here because it gives your application events their own place instead of mixing them into the AWS account's default bus. EventBridge custom buses are intended for events from your own applications/services.

Your architecture now has the `project-x-poc-bus` bus, but nothing is sending events to it yet.

## 4.2 Understand the EventBridge event format

We will send an event like this:

```json
{
  "Source": "projectx.requests",
  "DetailType": "RequestReceived",
  "Detail": {
    "requestId": "REQ-4001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }
}
```

There are three important parts:

| Field | POC value | Meaning |
| --- | --- | --- |
| `Source` | `projectx.requests` | The event came from the Project X request-processing domain. |
| `DetailType` | `RequestReceived` | A new request has arrived. |
| `Detail` | The business payload | The request data to process. |

AWS requires `Source`, `DetailType`, and `Detail` for custom `PutEvents` entries.

## 4.3 Create an EventBridge rule

Now we need to tell EventBridge: whenever a `RequestReceived` event from `projectx.requests` arrives, start the Step Functions workflow.

Go to **EventBridge → Rules → Create rule** and use:

| Setting | Value |
| --- | --- |
| Name | `project-x-request-received-rule` |
| Description | Starts Project X workflow when a new request is received |
| Event bus | `project-x-poc-bus` |
| Rule type | Rule with an event pattern |

Continue.

## 4.4 Configure the event pattern

Choose **Custom pattern**, or the equivalent option in the current console.

Paste:

```json
{
  "source": [
    "projectx.requests"
  ],
  "detail-type": [
    "RequestReceived"
  ]
}
```

This means the event matches if `source == projectx.requests` **and** `detail-type == RequestReceived`.

EventBridge rules compare incoming events to their event pattern and route matching events to targets.

Notice we are not checking the request type yet.

So both `CHANGE_ADDRESS` and `CANCEL_POLICY` will match as long as `source = projectx.requests` and `detail-type = RequestReceived`.

That's intentional.

The workflow can decide what to do with the request later.

## 4.5 Configure the target

For **Select target**, choose **AWS service → Step Functions state machine**. Select `project-x-poc-workflow`.

Now EventBridge knows:

```text
matching event
    ↓
project-x-poc-workflow
```

## 4.6 Let EventBridge create an IAM role

EventBridge needs permission to start your state machine.

You will see an execution-role section.

Choose **Create a new role for this specific resource** or a similarly named option. AWS may generate a role name like `Amazon_EventBridge_Invoke_Step_Functions_xxxxx`.

That's fine.

Conceptually:

```text
EventBridge
    |
    | IAM permission:
    | states:StartExecution
    |
    v
Step Functions
```

This is the same AWS security concept you've already seen:

```text
Step Functions
    ↓ permission
Lambda
```

Now you're adding:

```text
EventBridge
    ↓ permission
Step Functions
```

Your permission chain is becoming:

```text
EventBridge IAM Role
      ↓
StartExecution
      ↓
Step Functions IAM Role
      ↓
InvokeFunction
      ↓
Lambda
```

This is a very important AWS architecture pattern.

## 4.7 Choose the Step Functions input

This is where I want you to pay attention.

If EventBridge sends the entire event to Step Functions, your state machine receives something like:

```json
{
  "version": "0",
  "id": "abcd-1234",
  "detail-type": "RequestReceived",
  "source": "projectx.requests",
  "account": "123456789012",
  "time": "2026-09-11T...",
  "region": "us-east-1",
  "resources": [],
  "detail": {
    "requestId": "REQ-4001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }
}
```

But your Lambda currently expects:

```json
{
  "requestId": "REQ-4001",
  "requestType": "CHANGE_ADDRESS"
}
```

Notice the problem?

The data would be inside `detail.requestId` instead of `requestId`. For this POC, configure the EventBridge target to send only `$.detail` to Step Functions.

## 4.8 Configure target input

When configuring the Step Functions target, look for **Configure target input** or **Additional settings**. Choose **Part of the matched event** or **Input path**.

Use:

```text
$.detail
```

This is important.

It transforms this:

```json
{
  "source": "projectx.requests",
  "detail-type": "RequestReceived",
  "detail": {
    "requestId": "REQ-4001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }
}
```

into this Step Functions input:

```json
{
  "requestId": "REQ-4001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}
```

Exactly what your workflow already knows how to process.

Your data path becomes:

```text
EventBridge event

{
  metadata...
  detail: {
       business data
  }
}

        ↓ $.detail

Step Functions

{
  business data
}
```

That's a very useful pattern.

## 4.9 Finish creating the rule

Continue through **Tags → Review**.

No tags are necessary for this POC.

Click **Create rule**.

You should now have `project-x-request-received-rule` associated with `project-x-poc-bus` and targeting `project-x-poc-workflow`.

## 4.10 Review the architecture

You have:

```text
                AWS

    +-----------------------+
    | EventBridge           |
    |                       |
    | project-x-poc-bus     |
    +-----------+-----------+
                |
                | Rule:
                | RequestReceived
                |
                v
    +-----------------------+
    | Step Functions        |
    |                       |
    | project-x-poc-workflow|
    +-----------+-----------+
                |
                v
    +-----------------------+
    | Lambda                |
    |                       |
    | project-x-poc-        |
    | validator             |
    +-----------------------+
```

But we haven't tested it yet.

## 4.11 Create an event file

Go to your local project folder:

```bash
cd project-x-poc
```

Create `eventbridge-request.json`:

```bash
cat > eventbridge-request.json <<'EOF'
[
  {
    "Source": "projectx.requests",
    "DetailType": "RequestReceived",
    "Detail": "{\"requestId\":\"REQ-4001\",\"requestType\":\"CHANGE_ADDRESS\",\"customerId\":\"C12345\"}",
    "EventBusName": "project-x-poc-bus"
  }
]
EOF
```

Notice something unusual: `"Detail": "{\"requestId\": ... }"`.

Detail is passed to the EventBridge API as a JSON-encoded string containing a JSON object. AWS's CLI examples use this same structure.

Check your file:

```bash
cat eventbridge-request.json
```

## 4.12 Send the EventBridge event

Now run:

```bash
aws events put-events \
  --entries file://eventbridge-request.json \
  --region us-east-1
```

If everything is correct, you should see something similar to:

```json
{
  "FailedEntryCount": 0,
  "Entries": [
    {
      "EventId": "some-event-id"
    }
  ]
}
```

The important part is `FailedEntryCount: 0`.

That means EventBridge accepted the event.

AWS assigns an event ID when the event is accepted.

## 4.13 Check Step Functions

Now go to:

```text
AWS Console
→ Step Functions
→ project-x-poc-workflow
```

Look under **Executions**.

You should see a new execution that you did not manually start.

Open it.

Expected:

```text
Start
   ↓
ValidateRequest
   ↓
Succeeded
```

This is the important moment.

You ran `aws events put-events`, and AWS automatically did:

```text
EventBridge
   ↓
matched rule
   ↓
started Step Functions
   ↓
called Lambda
```

You did not manually start the state machine.

## 4.14 Check the Step Functions input

Open the new execution.

Look at **Execution input**. Because we configured `$.detail`, you should see something close to:

```json
{
  "requestId": "REQ-4001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}
```

If instead you see:

```text
{
  "version": "0",
  "id": "...",
  "detail": {
    ...
  }
}
```

then EventBridge is sending the entire event.

That's not a disaster.

Go back to **EventBridge → Rules → project-x-request-received-rule → Edit → Target** and change the target input to `$.detail`.

Then test again.

## 4.15 Test an event that should not match

Now let's prove the rule is really doing filtering.

Create:

```bash
cat > wrong-event.json <<'EOF'
[
  {
    "Source": "something.else",
    "DetailType": "RequestReceived",
    "Detail": "{\"requestId\":\"REQ-4002\",\"requestType\":\"CHANGE_ADDRESS\",\"customerId\":\"C12345\"}",
    "EventBusName": "project-x-poc-bus"
  }
]
EOF
```

Send it:

```bash
aws events put-events \
  --entries file://wrong-event.json \
  --region us-east-1
```

EventBridge will likely still return `FailedEntryCount = 0`.

Why?

Because the event itself was valid and successfully sent.

But our rule says `source` must equal `projectx.requests`. Your event has `something.else`.

Therefore:

```text
Event accepted by bus
       ↓
rule evaluates event
       ↓
doesn't match
       ↓
Step Functions NOT started
```

Go to Step Functions.

There should be no new execution for `REQ-4002`.

This distinction is very important: an event being accepted does not mean the rule matched.

## 4.16 Test invalid business data

Now send another valid EventBridge event, but deliberately omit `requestId`.

Create:

```bash
cat > invalid-request.json <<'EOF'
[
  {
    "Source": "projectx.requests",
    "DetailType": "RequestReceived",
    "Detail": "{\"requestType\":\"CHANGE_ADDRESS\",\"customerId\":\"C12345\"}",
    "EventBusName": "project-x-poc-bus"
  }
]
EOF
```

Send it:

```bash
aws events put-events \
  --entries file://invalid-request.json \
  --region us-east-1
```

Now EventBridge should:

```text
accept event
 ↓
match rule
 ↓
start Step Functions
```

But your Lambda should fail because `requestId is required`.

So the execution should follow:

```text
EventBridge
    ↓
Step Functions
    ↓
ValidateRequest
    ↓ ERROR
ValidationFailed
```

This proves something very important:

EventBridge filtering asks, “Is this the type of event I'm interested in?” Business validation asks, “Is the content of this request valid?”

Those should generally not be confused.

## 4.17 Review EventBridge metrics

Go back to **EventBridge → Rules → project-x-request-received-rule** and look for **Monitoring**. You'll eventually see metrics such as:

- Invocations
- Matched events
- Failed invocations

For our POC, you don't need alarms yet.

But remember this location.

Later, if an event is sent but Step Functions doesn't start, one of the first things to investigate is whether the EventBridge rule matched.

## 4.18 Understand the architecture

This is no longer just a chain of manually invoked AWS services.

You've introduced decoupling.

Without EventBridge:

```text
Producer
   |
   | must know Step Functions
   v
Step Functions
```

With EventBridge:

```text
Producer
   |
   | publishes business event
   v
EventBridge
   |
   +---------+---------+---------+
   |         |         |         |
   v         v         v         v
Workflow   Audit    Metrics    Future
```

The sender only says, “A request was received.”

It does not necessarily have to know all the downstream consumers.

That's one of the reasons EventBridge fits your Project X architecture.

### Why we chose RequestReceived

Think of `RequestReceived` as a business event.

Later you could have:

- `RequestReceived`
- `RequestValidated`
- `IntentIdentified`
- `RequestNeedsInformation`
- `TransactionSubmitted`
- `TransactionCompleted`
- `TransactionFailed`

Do not create all of these yet.

For this POC, `RequestReceived` is enough.

### Completed architecture

You should now have:

```text
                         AWS

                  +----------------+
                  | EventBridge    |
                  |                |
                  | Custom Bus     |
                  | project-x-poc  |
                  +-------+--------+
                          |
                 Event pattern:
                 source =
                 projectx.requests

                 detail-type =
                 RequestReceived
                          |
                          v
                 +----------------+
                 | EventBridge    |
                 | Rule           |
                 +-------+--------+
                         |
                         | states:StartExecution
                         v
                +--------------------+
                | Step Functions     |
                |                    |
                | project-x-poc-     |
                | workflow           |
                +---------+----------+
                          |
                          | lambda:InvokeFunction
                          v
                +--------------------+
                | Lambda             |
                |                    |
                | validator          |
                +--------------------+
```

## Verification checklist

- [x] `project-x-poc-bus` created
- [x] `project-x-request-received-rule` created
- [x] Pattern source is `projectx.requests`
- [x] Pattern detail type is `RequestReceived`
- [x] Rule target is `project-x-poc-workflow`
- [x] EventBridge can start the workflow
- [x] Target passes `$.detail` to Step Functions
- [x] `aws events put-events` succeeds
- [x] `REQ-4001` automatically starts Step Functions
- [x] Wrong source does not start Step Functions
- [x] Missing `requestId` reaches `ValidationFailed`

## Next Step

Once the checklist is complete, proceed to [Step 5 — Create API Gateway and send an HTTP request](05-api-gateway.md).
