# Step 3 — Create a Step Function that calls Lambda

**Status:** ⬜ Pending

## Objective

Build a state machine that invokes the Lambda function from Step 2.

## Prerequisites

- [ ] Step 2 complete — Lambda function created and tested

## Tasks

- [ ] Create a Step Function state machine
- [ ] Add a state that invokes the Lambda function
- [ ] Test the state machine execution

## Verification

- [ ] Step Function exists in `us-east-1`
- [ ] Step Function successfully invokes the Lambda
- [ ] Execution completes with expected output

tep 3 adds exactly one new AWS service: AWS Step Functions.

Your goal is:

Manual Start
    ↓
Step Functions
    ↓
project-x-poc-validator Lambda
    ↓
Success

We are not adding EventBridge yet.

Step 3.1 — Open AWS Step Functions

In the AWS Console, confirm the region is:

us-east-1

Search for:

Step Functions

Open AWS Step Functions → State machines → Create state machine.

Choose Create from blank / Build from scratch if presented.

For the state machine type, select:

Standard

This is the type I want us to use for Project X because our eventual workflow is long-running, auditable, and may involve retries/waiting/human or agent interactions.

Step 3.2 — Use Workflow Studio

You should now see Workflow Studio.

You'll have something resembling:

Start
  ↓
End

On the left side, search for:

Lambda

Find:

AWS Lambda — Invoke

Drag it between Start and End.

Now visually:

Start
  ↓
Lambda Invoke
  ↓
End

Click the Lambda state.

Step 3.3 — Select your Lambda

For Function name, select the Lambda we created in Step 2:

project-x-poc-validator

For Payload/Input, we want the Lambda to receive the Step Functions input.

Choose the option corresponding to using the state input as the payload.

The important thing is that if Step Functions receives:

{
  "requestId": "REQ-3001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

the Lambda should receive the same object as its event.

Step 3.4 — Rename the state

Rename:

Lambda Invoke

to:

ValidateRequest

Our workflow now reads nicely:

Start
   ↓
ValidateRequest
   ↓
End

This matters later when we have:

Start
   ↓
ValidateRequest
   ↓
IdentifyIntent
   ↓
ExtractData
   ↓
RunBusinessValidations
   ↓
InvokeAgent
   ↓
ExecuteTransaction
   ↓
Complete

State names should describe business/workflow operations, rather than implementation details such as CallLambda1.

Step 3.5 — Look at the generated ASL

Workflow Studio should have a Code view.

Open it.

You'll see something similar to:

{
  "Comment": "Project X POC workflow",
  "StartAt": "ValidateRequest",
  "States": {
    "ValidateRequest": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": {
        "FunctionName": "arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:project-x-poc-validator",
        "Payload": "{% $states.input %}"
      },
      "End": true
    }
  }
}

Don't worry about memorizing this.

This JSON is called Amazon States Language (ASL).

The important concepts are:

StartAt
   ↓
Which state starts first?

States
   ↓
What states exist?

Type: Task
   ↓
This state performs work.

Resource
   ↓
What AWS service/action is called?

End: true
   ↓
Workflow finishes here.

This becomes important later when we move the workflow into IaC/GitHub.

Step 3.6 — Create the state machine

Click Create.

Name it:

project-x-poc-workflow

For permissions, let Step Functions create a new execution role.

You may see something like:

Create new role

Select that.

Then create the state machine.

AWS will create something similar to:

project-x-poc-workflow

and an IAM role similar to:

StepFunctions-project-x-poc-workflow-role-xxxxx
Step 3.7 — Understand the IAM relationship

This is an important AWS concept.

In Step 2:

YOU
 ↓
Lambda
 ↓
Lambda Execution Role

Now:

YOU
 ↓
Step Functions
 ↓
Step Functions Execution Role
 ↓
Lambda
 ↓
Lambda Execution Role

There are two different roles.

Step Functions role

Needs permission to:

lambda:InvokeFunction

on:

project-x-poc-validator
Lambda role

Allows the Lambda itself to do things such as:

write CloudWatch logs

Think of it as:

Every AWS service needs permission to perform the next action.

This idea will become extremely important later:

EventBridge
   ↓ permission
Step Functions

Step Functions
   ↓ permission
Lambda

Lambda
   ↓ permission
AgentCore

AgentCore
   ↓ permission
Bedrock
Step 3.8 — Run your first workflow

Open:

project-x-poc-workflow

Click:

Start execution

For input, paste:

{
  "requestId": "REQ-3001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345",
  "newAddress": {
    "street": "123 Main Street",
    "city": "Jacksonville",
    "state": "FL",
    "zip": "32256"
  }
}

Click:

Start execution.

Step 3.9 — Watch the execution

This is one of the useful features of Step Functions.

You should see:

Start
   ↓
ValidateRequest
   ↓
Success

The ValidateRequest state should turn green.

Execution status:

Succeeded

Click ValidateRequest.

Look at its:

Input

Output

The input should contain your request.

The output will probably look somewhat different from what you expect.

You may see something like:

{
  "ExecutedVersion": "$LATEST",
  "Payload": {
    "requestId": "REQ-3001",
    "requestType": "CHANGE_ADDRESS",
    "validationStatus": "VALID",
    "message": "Project X request passed initial validation"
  },
  "SdkHttpMetadata": {
    ...
  },
  "StatusCode": 200
}

Notice this part:

"Payload": {
   ...
}

Your Lambda response is wrapped by the Step Functions Lambda integration.

We'll clean that up.

Step 3.10 — Make Lambda output cleaner

Go back to:

State machines
→ project-x-poc-workflow
→ Edit

Select:

ValidateRequest

Look for the output/result settings.

Depending on the current console UI, you may see options such as Output, Result selector, or a JSONata output expression.

We want the next state to receive only the Lambda's Payload, not all the Lambda invocation metadata.

Conceptually:

Lambda integration result

{
   Payload: {...},
   StatusCode: 200,
   metadata: ...
}

             ↓

Keep Payload

             ↓

{
   requestId: ...,
   validationStatus: "VALID"
}

If your Workflow Studio offers an Output expression for the Lambda task, set it to the Lambda response payload, commonly:

{% $states.result.Payload %}

Then save/update the state machine.

If your console presents a different input/output UI, don't get stuck here; the workflow succeeding is more important for this step.

Step 3.11 — Execute again

Start another execution:

{
  "requestId": "REQ-3002",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C99999"
}

Expected:

Start
  ↓
ValidateRequest
  ↓
Succeeded

And ideally the final workflow output is:

{
  "requestId": "REQ-3002",
  "requestType": "CHANGE_ADDRESS",
  "validationStatus": "VALID",
  "message": "Project X request passed initial validation"
}

Now we have a very clean pipeline:

INPUT

{
 requestId,
 requestType,
 customerId
}

       ↓

Step Functions

       ↓

ValidateRequest

       ↓

Lambda

       ↓

OUTPUT

{
 requestId,
 requestType,
 validationStatus
}
Step 3.12 — Now deliberately make it fail

This is important.

Start another execution with:

{
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

Notice:

requestId

is missing.

Remember our Lambda contains:

if not request_id:
    raise ValueError("requestId is required")

Run the workflow.

This time you should see:

Start
   ↓
ValidateRequest
   ↓
FAILED

The state should turn red.

Click the failed state.

You should find an error indicating:

ValueError

requestId is required

This is actually a successful test.

You've demonstrated:

VALID REQUEST

Step Functions
     ↓
Lambda
     ↓
VALID
     ↓
Workflow succeeds


INVALID REQUEST

Step Functions
     ↓
Lambda
     ↓
ValueError
     ↓
Workflow fails
Step 3.13 — Add error handling

Now let's make the workflow slightly more realistic.

Instead of:

ValidateRequest
     ↓
ERROR
     ↓
Entire execution crashes

we want:

ValidateRequest
       |
   +---+---+
   |       |
success   error
   |       |
   v       v
Complete  ValidationFailed

Edit your state machine.

Add a Fail state after/alongside the validation task.

Name it:

ValidationFailed

Select:

ValidateRequest

Look for:

Error handling

or Catch.

Add a Catch handler.

Use:

States.ALL

as the error type.

Set the fallback state to:

ValidationFailed

Conceptually the ASL will contain something similar to:

"Catch": [
  {
    "ErrorEquals": [
      "States.ALL"
    ],
    "Next": "ValidationFailed"
  }
]

This means:

If anything goes wrong in ValidateRequest, don't simply terminate unexpectedly. Route execution to ValidationFailed.

Step 3.14 — Test the failure again

Use:

{
  "requestType": "CHANGE_ADDRESS"
}

Now visually you should see something like:

          ValidateRequest
             /     \
            /       \
       Success      Error
          |           |
          v           v
       Complete   ValidationFailed

The workflow still ends in failure because ValidationFailed is a Fail state, but now you explicitly control how that failure is handled.

That's a major orchestration concept.

Later Project X might do:

Validation failed
       ↓
Determine failure type
       ↓
Business validation?
   YES / NO
    |     |
    v     v
Request   Technical
more info retry
    |       |
    v       v
Email     Retry
customer  system

This is one of the reasons Step Functions is valuable for your architecture.

Step 3.15 — Look at execution history

Open one successful execution.

Look for:

Execution event history

You'll see events somewhat like:

ExecutionStarted

TaskStateEntered

LambdaFunctionScheduled

LambdaFunctionStarted

LambdaFunctionSucceeded

TaskStateExited

ExecutionSucceeded

Don't memorize these.

The important idea is that Step Functions records what happened to the workflow.

This gives us an orchestration/audit trail.

For Project X, that eventually becomes very valuable when someone asks:

What happened to request REQ-58423?

We want to be able to reconstruct:

Request received
      ↓
Intent identified
      ↓
Data extracted
      ↓
Validation executed
      ↓
Agent invoked
      ↓
Tool called
      ↓
Transaction submitted
      ↓
Completed
Step 3.16 — Look at your state machine from CLI

Back on your Mac:

aws stepfunctions list-state-machines \
  --region us-east-1

You should see:

project-x-poc-workflow

You'll also see its ARN:

arn:aws:states:us-east-1:
YOUR_ACCOUNT:
stateMachine:project-x-poc-workflow

An ARN is the AWS resource identifier.

You'll see ARNs everywhere:

Lambda ARN
Step Functions ARN
IAM Role ARN
EventBridge ARN
AgentCore Runtime ARN
Step 3.17 — What you have built so far

After Steps 1–3, you now actually have this:

                    AWS ACCOUNT
                     us-east-1

                         |
                         |
                +----------------+
                | Step Functions |
                |                |
                | Project X POC  |
                +-------+--------+
                        |
                        |
                        v
              +--------------------+
              | Lambda             |
              |                    |
              | project-x-poc-     |
              | validator          |
              +---------+----------+
                        |
                        |
                        v
                CloudWatch Logs

And you've already touched four important AWS concepts:

AWS Service
     +
IAM Role
     +
ARN
     +
CloudWatch

These same concepts repeat throughout AWS.

Step 3 checklist

Before going further, make sure:

[ ] project-x-poc-workflow exists

[ ] State machine type = Standard

[ ] ValidateRequest invokes project-x-poc-validator

[ ] Valid request succeeds

[ ] Lambda output is visible

[ ] Invalid request fails

[ ] ValidationFailed/Catch is configured

[ ] Execution history makes sense

[ ] aws stepfunctions list-state-machines works

If those are working, Step 3 is complete.

## Next Step

Proceed to [Step 4 — Create EventBridge and trigger the Step Function](04-eventbridge.md).