# Step 6 — Rebuild those resources using CDK/IaC

**Status:** ✅ Complete

## Objective

Recreate the Lambda, Step Function, EventBridge, and API Gateway resources as infrastructure-as-code using AWS CDK.

## Prerequisites

- [x] Steps 2–5 complete — resources created manually in the AWS Console

## Tasks

- [x] Set up an AWS CDK project
- [x] Define the Lambda function in CDK
- [x] Define the Step Function in CDK
- [x] Define the EventBridge rule in CDK
- [x] Define the API Gateway in CDK
- [x] Deploy the stack
- [x] Verify all resources work identically to the manual versions

## Verification

- [x] CDK stack deploys successfully
- [x] All resources exist in `us-east-1`
- [x] End-to-end flow works via the CDK-deployed resources

Step 6 is our transition from “clicking in the AWS Console” to Infrastructure as Code.

However, I want to make one change from the earlier roadmap: we will not immediately recreate all four existing resources in CDK. That risks name conflicts with the Lambda, Step Functions, EventBridge bus/rule, and API Gateway you already created manually.

We'll learn CDK safely first.

Steps 1–5                         Step 6+
──────────                        ──────────
AWS Console                      Python code
    ↓                                ↓
Create resources                 AWS CDK
                                     ↓
                                CloudFormation
                                     ↓
                                AWS resources

AWS CDK ultimately synthesizes CloudFormation templates and uses CloudFormation to provision the infrastructure.

Step 6 goal

For this step only, we'll:

1. Install CDK
2. Create a Python CDK project
3. Understand CDK structure
4. Bootstrap your AWS account
5. Define ONE new Lambda using code
6. Run cdk synth
7. Run cdk diff
8. Run cdk deploy
9. Verify AWS created it
10. Delete this temporary learning Lambda

Then Step 6B will convert the actual Project X architecture into CDK.

This keeps the learning manageable.

6.1 — Check prerequisites

From your Mac:

node --version
python3 --version
aws --version

You already used AWS CLI successfully, so credentials should be configured.

Also confirm:

aws sts get-caller-identity

and:

aws configure get region

Region should be:

us-east-1

Python CDK currently requires Python 3.9+, and AWS documents Python as a fully supported CDK language.

6.2 — Install AWS CDK

AWS recommends installing the CDK CLI through npm.

Run:

npm install -g aws-cdk

Then:

cdk --version

You should get a version number.

Don't worry if your exact version differs from examples you find online.

6.3 — Create a separate CDK folder

You currently have something like:

project-x-poc/

Let's keep our infrastructure code separate.

From inside project-x-poc:

mkdir infrastructure
cd infrastructure

Your structure becomes:

project-x-poc/
│
├── README.md
├── event.json
├── eventbridge-request.json
│
└── infrastructure/

Now initialize CDK:

cdk init app --language python

AWS's standard Python CDK initialization command is cdk init app --language python.

6.4 — Activate Python virtual environment

CDK should have created:

infrastructure/
├── .venv/
├── app.py
├── cdk.json
├── requirements.txt
├── README.md
└── infrastructure/
    └── infrastructure_stack.py

Activate the virtual environment:

source .venv/bin/activate

Your Terminal prompt may now show:

(.venv)

Install dependencies:

python -m pip install -r requirements.txt

AWS recommends activating the virtual environment whenever you're working with the Python CDK project.

6.5 — Understand the files

Don't modify anything yet.

There are three files I want you to understand.

app.py

Open:

cat app.py

You'll see something similar to:

#!/usr/bin/env python3

import aws_cdk as cdk

from infrastructure.infrastructure_stack import InfrastructureStack

app = cdk.App()

InfrastructureStack(
    app,
    "InfrastructureStack"
)

app.synth()

Think:

app.py
   ↓
starts CDK application
   ↓
loads our stack
infrastructure_stack.py

This is where we'll define AWS resources:

Lambda
EventBridge
Step Functions
API Gateway
IAM
etc.
cdk.json

This tells the CDK CLI how to run your application.

For now, don't change it.

6.6 — Understand App → Stack → Construct

Three important CDK words:

CDK App
   │
   └── Stack
         │
         ├── Lambda
         ├── IAM Role
         ├── EventBridge
         ├── Step Functions
         └── API Gateway
App

Your overall CDK program.

Stack

A group of AWS resources deployed together through CloudFormation.

Construct

A building block representing AWS infrastructure.

For example:

lambda_.Function(...)

is a construct representing Lambda infrastructure.

You will see these concepts repeatedly.

6.7 — Configure our environment explicitly

Open:

app.py

I want us to make the account and region explicit using your currently configured AWS environment.

Change it to:

#!/usr/bin/env python3

import os

import aws_cdk as cdk

from infrastructure.infrastructure_stack import InfrastructureStack


app = cdk.App()

InfrastructureStack(
    app,
    "ProjectXPocStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

app.synth()

Notice:

ProjectXPocStack

That's going to become our CloudFormation stack name.

6.8 — Bootstrap your AWS environment

This is a one-time important CDK setup.

Run:

cdk bootstrap

Because our stack has an environment configured, CDK can determine the target account/region.

Alternatively, the explicit form is:

cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1

You can retrieve your account number using:

aws sts get-caller-identity

Bootstrapping prepares an AWS account/region for CDK deployments. AWS creates a CloudFormation stack called:

CDKToolkit

along with deployment resources such as an S3 asset bucket, ECR repository, and IAM roles used by CDK deployments.

You should eventually see something like:

Environment aws://123456789012/us-east-1 bootstrapped.
6.9 — Look at what bootstrap created

Open AWS Console:

CloudFormation
→ Stacks

You should see:

CDKToolkit

This is important.

You didn't manually create it.

You ran:

cdk bootstrap

and:

CDK
 ↓
CloudFormation
 ↓
created CDKToolkit

You've just performed your first IaC infrastructure operation.

Don't delete CDKToolkit.

6.10 — Create our first CDK Lambda

Now let's create one temporary learning Lambda.

We deliberately will not call it:

project-x-poc-validator

because that already exists from Step 2.

We'll call this:

project-x-cdk-learning

Open:

infrastructure/infrastructure_stack.py

Replace its contents with:

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
)
from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        lambda_.Function(
            self,
            "LearningLambda",
            function_name="project-x-cdk-learning",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_inline(
                """
def lambda_handler(event, context):
    print("Project X CDK Lambda invoked")

    return {
        "message": "Hello from Project X CDK",
        "status": "SUCCESS"
    }
"""
            ),
        )

Save it.

6.11 — Understand this code

This:

lambda_.Function(...)

means:

CDK, I want a Lambda function.

This:

function_name="project-x-cdk-learning"

means:

Give the physical AWS Lambda this name.

This:

runtime=lambda_.Runtime.PYTHON_3_12

means:

Use Python 3.12.

And:

code=lambda_.Code.from_inline(...)

means:

Put this tiny Python function directly into the Lambda package.

We're only using inline code because this is a tiny learning exercise.

Later we'll have proper directories such as:

lambda/
  validator/
     lambda_function.py
6.12 — Run cdk list

Run:

cdk list

Expected:

ProjectXPocStack

This tells you:

CDK recognizes one deployable stack.

6.13 — Run cdk synth

Now run:

cdk synth

This is a very important command.

It means:

Python CDK code
       ↓
    synth
       ↓
CloudFormation template

CDK should output a large YAML CloudFormation template.

You'll see things involving:

AWS::IAM::Role

AWS::Lambda::Function

Don't try to understand the whole generated template.

The important idea is:

You write Python. CDK generates CloudFormation.

AWS describes synthesis as the step that creates the CloudFormation template and deployment artifacts used during deployment.

6.14 — Look at cdk.out

Run:

ls

You'll now see:

cdk.out

Inside it:

ls cdk.out

CDK generated deployment artifacts there.

Again:

Python
 ↓
CDK
 ↓
cdk.out
 ↓
CloudFormation

Normally you don't manually edit anything inside cdk.out.

6.15 — Run cdk diff

Before deploying, run:

cdk diff

This command is one of your best friends.

You should see changes indicating CDK wants to create something like:

IAM Role
+ AWS::IAM::Role

Lambda
+ AWS::Lambda::Function

The + essentially means:

AWS resource will be added

This lets you inspect infrastructure changes before deployment.

Eventually your workflow will frequently be:

change code
   ↓
cdk synth
   ↓
cdk diff
   ↓
review
   ↓
cdk deploy
6.16 — Deploy

Now run:

cdk deploy

Because IAM resources are involved, CDK may show a security/IAM change approval.

Review it.

You'll get something like:

Do you wish to deploy these changes (y/n)?

Enter:

y

CDK then:

CDK
 ↓
CloudFormation
 ↓
creates IAM role
 ↓
creates Lambda

AWS documents cdk deploy as the command that submits the synthesized infrastructure through CloudFormation to provision AWS resources.

6.17 — Verify CloudFormation

Now go to:

AWS Console
→ CloudFormation
→ Stacks

You should have:

CDKToolkit

ProjectXPocStack

Open:

ProjectXPocStack

Look at:

Resources

You should see resources including:

AWS::IAM::Role

AWS::Lambda::Function

This is a very important conceptual change from Steps 1–5.

Previously:

YOU
 ↓
AWS Console
 ↓
Lambda

Now:

YOU
 ↓
Python
 ↓
CDK
 ↓
CloudFormation
 ↓
Lambda

CloudFormation now owns/manages the resources created by this stack.

6.18 — Verify Lambda

Go to:

AWS Console
→ Lambda
→ Functions

You should now see both:

project-x-poc-validator

from Step 2, and:

project-x-cdk-learning

from Step 6.

That distinction is intentional.

6.19 — Invoke your CDK Lambda

From your Mac:

aws lambda invoke \
  --function-name project-x-cdk-learning \
  --payload '{}' \
  cdk-response.json

Then:

cat cdk-response.json

Expected:

{
  "message": "Hello from Project X CDK",
  "status": "SUCCESS"
}

Congratulations — this Lambda was created entirely from infrastructure code.

6.20 — Make a change

Now let's experience the real power of IaC.

Change:

"message": "Hello from Project X CDK"

to:

"message": "Project X infrastructure is now managed by CDK"

Save.

Run:

cdk diff

You should see that the Lambda will change.

Then:

cdk deploy

Invoke again:

aws lambda invoke \
  --function-name project-x-cdk-learning \
  --payload '{}' \
  cdk-response.json

cat cdk-response.json

Expected:

{
  "message": "Project X infrastructure is now managed by CDK",
  "status": "SUCCESS"
}

You didn't open the Lambda console.

That's the mindset change we're after.

6.21 — Delete the temporary Lambda properly

Here's another major IaC lesson.

Don't delete project-x-cdk-learning manually from the Lambda console.

Because CloudFormation owns it.

Instead run:

cdk destroy

You'll see something like:

Are you sure you want to delete: ProjectXPocStack (y/n)?

Enter:

y

CDK/CloudFormation will remove resources belonging to ProjectXPocStack.

AWS's CDK tutorial similarly uses cdk destroy to remove resources created by the CDK stack.

Afterward:

project-x-cdk-learning

should disappear.

But your manually-created Step 1–5 infrastructure should remain:

project-x-poc-api              ← remains

project-x-poc-bus              ← remains

project-x-request-received-rule ← remains

project-x-poc-workflow         ← remains

project-x-poc-validator        ← remains

And leave:

CDKToolkit

alone.

## The most important lesson from Step 6

You now know two fundamentally different approaches.

Console-managed
AWS Console
    ↓
click
    ↓
resource
IaC-managed
Python source
    ↓
AWS CDK
    ↓
CloudFormation
    ↓
AWS resource

For your enterprise Project X, we ultimately want:

GitLab / GitHub
       ↓
Infrastructure code
       ↓
CI/CD
       ↓
CDK
       ↓
CloudFormation
       ↓
AWS DEV
       ↓
AWS QA
       ↓
AWS PROD

Not engineers manually configuring production resources through the console.

## Step 6 checklist

Complete these before we continue:

- [x] npm install -g aws-cdk

- [x] cdk --version works

- [x] infrastructure/ CDK project created

- [x] Python .venv activated

- [x] cdk bootstrap completed

- [x] CDKToolkit visible in CloudFormation

- [x] project-x-cdk-learning defined in Python

- [x] cdk list shows ProjectXPocStack

- [x] cdk synth works

- [x] cdk diff works

- [x] cdk deploy creates ProjectXPocStack

- [x] project-x-cdk-learning appears in Lambda

- [x] CLI invocation succeeds

- [x] Change + redeploy succeeds

- [x] cdk destroy removes ProjectXPocStack

- [x] Original Steps 1–5 resources still work
## What happens in Step 6B

Once this works, don't manually recreate anything yet. Tell me “Step 6 complete.”

Then we'll tackle the more interesting problem: turning your existing working architecture into a proper Project X CDK application:

CDK
 │
 ├── API Gateway
 │
 ├── IAM
 │
 ├── EventBridge Bus
 │
 ├── EventBridge Rule
 │
 ├── Step Functions
 │
 └── Lambda

We'll also decide whether to import/adopt the manually-created resources or build a parallel CDK-managed POC and then retire the manual resources. For a learning environment, I strongly favor the second approach because it gives you a clean IaC ownership boundary and teaches you how the entire architecture is actually assembled.

Step 6B will rebuild your full working POC as CDK-managed infrastructure.

We will not touch the resources you created manually in Steps 1–5. Instead, we’ll create parallel resources with -cdk- in their names.

Your target becomes:

curl / Postman
      │
      ▼
API Gateway
project-x-cdk-api
      │
      ▼
EventBridge
project-x-cdk-bus
      │
      ▼
EventBridge Rule
      │
      ▼
Step Functions
project-x-cdk-workflow
      │
      ▼
Lambda
project-x-cdk-validator

CDK currently has native constructs for EventBridge→Step Functions and HTTP API→EventBridge PutEvents, so we can define these relationships directly in Python rather than manually creating IAM roles.

Step 6B.1 — Create the Lambda source folder

From your CDK project root:

pwd

You should be inside something like:

.../aws-crash-course/infrastructure

Create:

mkdir -p lambda/validator

Your structure should become:

infrastructure/
│
├── app.py
├── cdk.json
├── requirements.txt
│
├── infrastructure/
│   └── infrastructure_stack.py
│
└── lambda/
    └── validator/
        └── index.py

Create:

touch lambda/validator/index.py
Step 6B.2 — Move our validator code into index.py

Put this into:

lambda/validator/index.py
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

Notice we're no longer using:

Code.from_inline(...)

We're packaging actual source files.

That's much closer to how your enterprise project will work. CDK supports packaging Lambda code from a directory using Code.from_asset.

Step 6B.3 — Replace the CDK stack

Open:

infrastructure/infrastructure_stack.py

Replace it with this:

import os

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)

from aws_cdk.aws_apigatewayv2_integrations import (
    HttpEventBridgeIntegration,
)

from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        #
        # 1. Lambda
        #

        validator = lambda_.Function(
            self,
            "ValidatorFunction",
            function_name="project-x-cdk-validator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "lambda",
                    "validator",
                )
            ),
            timeout=Duration.seconds(30),
        )

        #
        # 2. Step Functions
        #

        validation_failed = sfn.Fail(
            self,
            "ValidationFailed",
            error="ValidationError",
            cause="Request validation failed",
        )

        validate_request = tasks.LambdaInvoke(
            self,
            "ValidateRequest",
            lambda_function=validator,
            payload=sfn.TaskInput.from_json_path_at("$"),
            output_path="$.Payload",
        )

        validate_request.add_catch(
            validation_failed,
            result_path="$.error",
        )

        workflow = sfn.StateMachine(
            self,
            "ProjectXWorkflow",
            state_machine_name="project-x-cdk-workflow",
            definition_body=sfn.DefinitionBody.from_chainable(
                validate_request
            ),
            timeout=Duration.minutes(5),
        )

        #
        # 3. EventBridge custom bus
        #

        event_bus = events.EventBus(
            self,
            "ProjectXEventBus",
            event_bus_name="project-x-cdk-bus",
        )

        #
        # 4. EventBridge rule
        #

        request_rule = events.Rule(
            self,
            "RequestReceivedRule",
            rule_name="project-x-cdk-request-received-rule",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["projectx.requests"],
                detail_type=["RequestReceived"],
            ),
        )

        request_rule.add_target(
            targets.SfnStateMachine(
                workflow,
                input=events.RuleTargetInput.from_event_path(
                    "$.detail"
                ),
            )
        )

        #
        # 5. API Gateway HTTP API
        #

        http_api = apigwv2.HttpApi(
            self,
            "ProjectXHttpApi",
            api_name="project-x-cdk-api",
            description="Project X CDK POC API",
        )

        #
        # API Gateway -> EventBridge integration
        #

        parameter_mapping = (
            apigwv2.ParameterMapping()
            .custom("Detail", "$request.body")
            .custom("DetailType", "RequestReceived")
            .custom("Source", "projectx.requests")
        )

        eventbridge_integration = HttpEventBridgeIntegration(
            "ProjectXEventBridgeIntegration",
            event_bus_ref=event_bus.event_bus_ref,
            parameter_mapping=parameter_mapping,
        )

        http_api.add_routes(
            path="/requests",
            methods=[apigwv2.HttpMethod.POST],
            integration=eventbridge_integration,
        )

        #
        # 6. Outputs
        #

        CfnOutput(
            self,
            "ApiEndpoint",
            value=http_api.api_endpoint,
        )

        CfnOutput(
            self,
            "EventBusName",
            value=event_bus.event_bus_name,
        )

        CfnOutput(
            self,
            "WorkflowArn",
            value=workflow.state_machine_arn,
        )

This uses CDK's native HttpEventBridgeIntegration, which supports API Gateway HTTP APIs forwarding requests to EventBridge using PutEvents. Custom parameter mapping allows us to send the HTTP body as Detail, while assigning our fixed source and detail type.

Step 6B.4 — Understand what CDK is creating

Don't deploy yet.

Look at this relationship:

validator
   ↓
Lambda construct


validate_request
   ↓
LambdaInvoke Step Functions task


workflow
   ↓
State Machine


event_bus
   ↓
EventBridge custom event bus


request_rule
   ↓
EventBridge rule


targets.SfnStateMachine(...)
   ↓
Connects EventBridge → Step Functions


HttpEventBridgeIntegration(...)
   ↓
Connects API Gateway → EventBridge

This part is particularly important:

request_rule.add_target(
    targets.SfnStateMachine(workflow)
)

CDK knows:

EventBridge
needs permission
to call
states:StartExecution

and can create the appropriate IAM relationship. EventBridge's CDK target library specifically supports Step Functions state machines.

Similarly:

HttpEventBridgeIntegration(...)

understands that API Gateway must call EventBridge PutEvents. This is one of the big advantages of higher-level CDK constructs.

Step 6B.5 — Verify app.py

Your app.py should now look like:

#!/usr/bin/env python3

import os

import aws_cdk as cdk

from infrastructure.infrastructure_stack import InfrastructureStack


app = cdk.App()

InfrastructureStack(
    app,
    "ProjectXPocCdkStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()

Important:

ProjectXPocCdkStack

is now our CloudFormation stack.

Step 6B.6 — Check dependencies

Activate your environment:

source .venv/bin/activate

Then:

python -m pip install -r requirements.txt

Your requirements.txt should contain something similar to:

aws-cdk-lib==...
constructs>=10.0.0,<11.0.0

Since you just created the CDK project, don't manually change versions unless you get an import error.

Step 6B.7 — Run cdk synth

Because you're using npx, run:

npx aws-cdk@latest synth

Expected:

Successfully synthesized ...

You will get a large CloudFormation template.

Search for:

AWS::Lambda::Function
AWS::StepFunctions::StateMachine
AWS::Events::EventBus
AWS::Events::Rule
AWS::ApiGatewayV2::Api

For example:

npx aws-cdk@latest synth | grep "AWS::"

You should see several AWS resources.

Step 6B.8 — Inspect the generated IAM

This is worth doing.

Run:

npx aws-cdk@latest synth > template.yaml

Then:

grep -n "states:StartExecution" template.yaml

You should find permission associated with EventBridge.

Also try:

grep -n "events:PutEvents" template.yaml

You should find permission associated with API Gateway.

This is the important difference from Step 5.

Previously you manually created:

API Gateway role
     ↓
events:PutEvents

Now CDK constructs can generate those permissions from the infrastructure relationship.

Step 6B.9 — Run cdk diff

Now:

npx aws-cdk@latest diff

You should see a sizeable change set.

Expect resources including:

+ Lambda
+ Lambda IAM role

+ Step Functions state machine
+ Step Functions IAM role

+ EventBridge bus

+ EventBridge rule
+ EventBridge target IAM role

+ API Gateway HTTP API
+ API Gateway integration
+ API Gateway route

+ API Gateway/EventBridge IAM permissions

This is an excellent place to stop and inspect.

You're essentially seeing the infrastructure equivalent of:

git diff

before deploying.

Step 6B.10 — Deploy

If the diff looks reasonable:

npx aws-cdk@latest deploy

Approve IAM changes if prompted.

Eventually you should see something similar to:

Outputs:

ProjectXPocCdkStack.ApiEndpoint =
https://xxxxxxxx.execute-api.us-east-1.amazonaws.com

ProjectXPocCdkStack.EventBusName =
project-x-cdk-bus

ProjectXPocCdkStack.WorkflowArn =
arn:aws:states:...

Copy your API endpoint.

Step 6B.11 — Verify CloudFormation first

Go to:

AWS Console
→ CloudFormation
→ Stacks
→ ProjectXPocCdkStack

Status should be:

CREATE_COMPLETE

Open:

Resources

You'll see the components CDK created.

This is now your ownership hierarchy:

ProjectXPocCdkStack
       │
       ├── Lambda
       ├── IAM roles
       ├── Step Functions
       ├── EventBridge bus
       ├── EventBridge rule
       ├── API Gateway
       ├── integration
       └── route

CloudFormation owns all of these.

Step 6B.12 — Verify Lambda

Go to:

Lambda
→ Functions

You should now have:

project-x-poc-validator

Your manually-created one.

And:

project-x-cdk-validator

Your CDK-managed one.

Do not confuse the two.

Step 6B.13 — Verify Step Functions

Go to:

Step Functions

You should see:

project-x-poc-workflow

manual.

And:

project-x-cdk-workflow

CDK.

Step 6B.14 — Verify EventBridge

Go to:

EventBridge
→ Event buses

You should see:

project-x-poc-bus

manual.

And:

project-x-cdk-bus

CDK.

Then:

EventBridge
→ Rules
→ project-x-cdk-bus

You should see:

project-x-cdk-request-received-rule
Step 6B.15 — Verify API Gateway

Go to:

API Gateway

You should see:

project-x-poc-api

manual.

And:

project-x-cdk-api

CDK.

Inside it:

POST /requests

should exist.

The API Gateway→EventBridge first-class integration uses EventBridge-PutEvents; AWS supports $request.body for passing the complete HTTP request body as EventBridge Detail.

Step 6B.16 — End-to-end test

Take the API endpoint printed by CDK.

Suppose it is:

https://abc123.execute-api.us-east-1.amazonaws.com

Run:

curl -i -X POST \
  'YOUR_CDK_API_ENDPOINT/requests' \
  -H 'Content-Type: application/json' \
  -d '{
    "requestId": "REQ-CDK-1001",
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }'

Then immediately go to:

Step Functions
→ project-x-cdk-workflow
→ Executions

You should see a new execution.

Step 6B.17 — Verify the workflow input

Open the execution.

Input should be:

{
  "requestId": "REQ-CDK-1001",
  "requestType": "CHANGE_ADDRESS",
  "customerId": "C12345"
}

That is because this line:

input=events.RuleTargetInput.from_event_path(
    "$.detail"
)

means:

EventBridge envelope
       ↓
take only $.detail
       ↓
Step Functions

So:

EventBridge receives
{
  source,
  detail-type,
  detail: {...}
}

            ↓ $.detail

Step Functions receives
{
  requestId,
  requestType,
  customerId
}
Step 6B.18 — Verify success

Your state machine should show:

Start
  ↓
ValidateRequest
  ↓
Succeeded

And the output should look similar to:

{
  "requestId": "REQ-CDK-1001",
  "requestType": "CHANGE_ADDRESS",
  "validationStatus": "VALID",
  "message": "Project X request passed initial validation"
}

CDK's Step Functions library supports building workflows using constructs such as LambdaInvoke, Fail, and DefinitionBody.from_chainable.

Step 6B.19 — Test failure

Now:

curl -i -X POST \
  'YOUR_CDK_API_ENDPOINT/requests' \
  -H 'Content-Type: application/json' \
  -d '{
    "requestType": "CHANGE_ADDRESS",
    "customerId": "C12345"
  }'

No requestId.

Expected:

API Gateway
     ↓
EventBridge
     ↓
rule matches
     ↓
Step Functions
     ↓
ValidateRequest
     ↓
Lambda ValueError
     ↓
Catch
     ↓
ValidationFailed

State machine execution should be:

FAILED

but failed intentionally through your defined Fail state.

Step 6B.20 — Look at IAM roles CDK generated

This is an important learning exercise.

Open:

IAM
→ Roles

Search for:

ProjectXPocCdkStack

You'll probably see several generated role names.

For example conceptually:

ProjectXPocCdkStack-
    ValidatorFunctionServiceRole...

and roles for workflow/integrations.

Don't worry about the ugly generated names.

Open them and inspect permissions.

You'll see relationships such as:

Lambda role
    ↓
CloudWatch Logs
Step Functions role
    ↓
lambda:InvokeFunction
EventBridge target role
    ↓
states:StartExecution
API Gateway integration role
    ↓
events:PutEvents

CDK is not eliminating IAM.

It is generating IAM from your architecture.

That's a very important distinction.

Step 6B.21 — Understand what we've achieved

Originally you manually built:

Console
   ↓
API Gateway

Console
   ↓
IAM role

Console
   ↓
EventBridge

Console
   ↓
IAM role

Console
   ↓
Step Functions

Console
   ↓
IAM role

Console
   ↓
Lambda

Now you have:

infrastructure_stack.py
          │
          ▼
         CDK
          │
          ▼
    CloudFormation
          │
    ┌─────┼──────────────┐
    ▼     ▼              ▼
   API  EventBridge   Step Functions
                         │
                         ▼
                       Lambda

That Python file has become your infrastructure blueprint.

Step 6B.22 — Prove reproducibility

Don't actually destroy it yet.

But conceptually you could run:

npx aws-cdk@latest destroy

and CDK would delete the entire CDK-managed POC.

Then:

npx aws-cdk@latest deploy

would recreate it.

That's the core IaC principle:

The infrastructure is reproducible from source code.

Your architecture now

After Step 6B you'll temporarily have two architectures:

             MANUAL VERSION

project-x-poc-api
      ↓
project-x-poc-bus
      ↓
project-x-request-received-rule
      ↓
project-x-poc-workflow
      ↓
project-x-poc-validator

and:

              CDK VERSION

project-x-cdk-api
      ↓
project-x-cdk-bus
      ↓
project-x-cdk-request-received-rule
      ↓
project-x-cdk-workflow
      ↓
project-x-cdk-validator

That's intentional.

Do not delete the manual version yet

We'll keep it temporarily because it's useful to compare:

Manual configuration
        VS
CDK configuration

Later we'll delete the manual version and make CDK the authoritative infrastructure definition.

Step 6B completion checklist
- [x] lambda/validator/index.py created

- [x] CDK stack replaced with full Project X architecture

- [x] project-x-cdk-validator defined

- [x] project-x-cdk-workflow defined

- [x] ValidationFailed Catch defined

- [x] project-x-cdk-bus defined

- [x] project-x-cdk-request-received-rule defined

- [x] project-x-cdk-api defined

- [x] POST /requests defined

- [x] API → EventBridge integration defined

- [x] EventBridge → Step Functions target defined

- [x] npx aws-cdk@latest synth succeeds

- [x] npx aws-cdk@latest diff succeeds

- [x] npx aws-cdk@latest deploy succeeds

- [x] ProjectXPocCdkStack CREATE_COMPLETE

- [x] curl POST succeeds

- [x] EventBridge receives event

- [x] Step Functions starts automatically

- [x] Valid request succeeds

- [x] Invalid request reaches ValidationFailed

## Next Step

Proceed to [Step 7 — Create a simple MCP server locally](07-mcp-server-local.md).
