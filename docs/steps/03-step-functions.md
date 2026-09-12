# Step 3 — Create a Step Function that calls Lambda

**Status:** ✅ Complete

## Objective

Build a state machine that invokes the Lambda function from Step 2.

## Prerequisites

- [x] Step 2 complete — Lambda function created and tested

## Tasks

- [x] Create a Step Function state machine
- [x] Add a state that invokes the Lambda function
- [x] Test successful and failed executions
- [x] Add explicit error handling

## 3.1 Open AWS Step Functions

In the AWS Console, confirm the region is `us-east-1`. Open **AWS Step Functions → State machines → Create state machine**.

Choose **Create from blank** or **Build from scratch**, then select the **Standard** state machine type. Standard workflows are appropriate here because the eventual workflow is long-running, auditable, and may involve retries, waiting, or human and agent interactions.

Step 3 adds exactly one new AWS service. EventBridge is not added yet.

```text
Manual start
    ↓
Step Functions
    ↓
project-x-poc-validator Lambda
    ↓
Success
```

## 3.2 Build the workflow in Workflow Studio

In Workflow Studio, search for **Lambda** and drag **AWS Lambda — Invoke** between Start and End.

Select the Lambda state and choose `project-x-poc-validator` for **Function name**. Configure the payload so the Lambda receives the Step Functions state input unchanged. For example, this input:

```json
{
  "requestId": "REQ-3001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}
```

should arrive at Lambda as the same event object.

Rename the state from `Lambda Invoke` to `ValidateRequest`:

```text
Start
   ↓
ValidateRequest
   ↓
End
```

Use business-oriented state names. A future workflow might contain `IdentifyIntent`, `ExtractData`, `RunBusinessValidations`, `InvokeAgent`, `ExecuteTransaction`, and `Complete`.

## 3.3 Review the generated Amazon States Language

Open the **Code** view. You should see something similar to:

```json
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
```

This JSON is Amazon States Language (ASL). The important fields are:

- `StartAt`: the first state.
- `States`: the states in the workflow.
- `Type: Task`: a state that performs work.
- `Resource`: the AWS service or action called.
- `End: true`: the workflow finishes at this state.

## 3.4 Create the state machine and review IAM

Click **Create**, name the state machine `project-x-poc-workflow`, and let Step Functions create a new execution role if prompted.

The state machine role needs permission to invoke `project-x-poc-validator`:

```text
You
 ↓
Step Functions
 ↓  Step Functions execution role
Lambda
 ↓  Lambda execution role
AWS services and CloudWatch Logs
```

These are two different roles. Step Functions needs `lambda:InvokeFunction`; the Lambda execution role allows the function to write logs and call any services it requires.

## 3.5 Run the first workflow

Open `project-x-poc-workflow`, click **Start execution**, and use:

```json
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
```

The execution should show `Start → ValidateRequest → Success`, with status **Succeeded**. Inspect the state's Input and Output.

The Lambda integration may wrap the response like this:

```json
{
  "ExecutedVersion": "$LATEST",
  "Payload": {
    "requestId": "REQ-3001",
    "requestType": "CHANGE_ADDRESS",
    "validationStatus": "VALID",
    "message": "Project X request passed initial validation"
  },
  "StatusCode": 200
}
```

## 3.6 Keep only the Lambda payload

Edit the state machine, select `ValidateRequest`, and find the output or result settings. Depending on the console version, this may be called **Output**, **Result selector**, or a JSONata output expression.

Configure the task to pass only the Lambda response payload to the next state. A Workflow Studio output expression is commonly:

```text
{% $states.result.Payload %}
```

Save or update the state machine. If the console presents different controls, a successful workflow is the priority for this step.

Run another execution with:

```json
{
  "requestId": "REQ-3002",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C99999"
}
```

The final output should contain the request fields plus `validationStatus: "VALID"` and the validation message.

## 3.7 Test an invalid request

Start an execution without `requestId`:

```json
{
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}
```

The `ValidateRequest` state should fail with an error such as:

```text
ValueError: requestId is required
```

This demonstrates both paths:

```text
Valid request   → Lambda → VALID     → workflow succeeds
Invalid request → Lambda → ValueError → workflow fails
```

## 3.8 Add explicit error handling

Add a **Fail** state named `ValidationFailed`. On `ValidateRequest`, add a **Catch** handler with `States.ALL` and route it to `ValidationFailed`:

```json
"Catch": [
  {
    "ErrorEquals": ["States.ALL"],
    "Next": "ValidationFailed"
  }
]
```

The failure path is now explicit:

```text
ValidateRequest
    ├── success → Complete
    └── error   → ValidationFailed
```

Run the invalid request again. The execution should end at `ValidationFailed`, which is still a failed execution because it is a Fail state, but the workflow now controls how validation errors are handled.

## 3.9 Review execution history and the CLI

Open a successful execution and review **Execution event history**. You should see events such as `ExecutionStarted`, `TaskStateEntered`, `LambdaFunctionScheduled`, `LambdaFunctionStarted`, `LambdaFunctionSucceeded`, `TaskStateExited`, and `ExecutionSucceeded`.

This history provides an orchestration and audit trail for a request as it moves through the workflow.

From your Mac, run:

```bash
aws stepfunctions list-state-machines \
  --region us-east-1
```

You should see `project-x-poc-workflow` and its ARN, similar to:

```text
arn:aws:states:us-east-1:YOUR_ACCOUNT:stateMachine:project-x-poc-workflow
```

## Verification checklist

- [x] `project-x-poc-workflow` exists in `us-east-1`
- [x] State machine type is Standard
- [x] `ValidateRequest` invokes `project-x-poc-validator`
- [x] A valid request succeeds
- [x] Lambda output is visible
- [x] An invalid request fails with `requestId is required`
- [x] `ValidationFailed` and `Catch` are configured
- [x] Execution history is available
- [x] `aws stepfunctions list-state-machines` works

## Next Step

Proceed to [Step 4 — Create EventBridge and trigger the Step Function](04-eventbridge.md).
