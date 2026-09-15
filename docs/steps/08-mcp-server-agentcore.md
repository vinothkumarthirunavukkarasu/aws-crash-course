# Step 8 — Deploy the MCP server to AgentCore Runtime

**Status:** ⬜ Pending

## Objective

Host the MCP server from Step 7 on AgentCore Runtime.

## Prerequisites

- [ ] Step 7 complete — MCP server created and tested locally
- [ ] Node.js 20+ installed (verified in Step 1)

## Tasks

- [ ] Install the AgentCore CLI
- [ ] Deploy the MCP server to AgentCore Runtime
- [ ] Verify the deployment status
- [ ] Test invoking the deployed MCP server

## Verification

- [ ] MCP server is deployed to AgentCore Runtime
- [ ] Deployment status shows healthy
- [ ] MCP server responds to invocations


## Deployment guide

Project X — Step 8: Deploy MCP 2.x Customer Tools to Amazon Bedrock AgentCore Runtime.

| Item | Value |
| --- | --- |
| Status | Ready to start |
| Region | `us-east-1` |
| Documentation verified | 2026-09-13 |
| Previous step | Step 7 — Local MCP 2.x server with `MCPServer` |
| Goal | Take the working local MCP 2.x customer-tools server and make it deployable to Amazon Bedrock AgentCore Runtime. |

---

## 1. What Step 8 accomplishes

At the end of Step 8, the architecture will be:

```text
Local laptop
    |
    | AWS SigV4 / InvokeAgentRuntime
    v
Amazon Bedrock AgentCore Runtime
    |
    | Streamable HTTP
    | 0.0.0.0:8000/mcp
    v
Project X Customer MCP Server
    |
    +-- get_customer
    +-- validate_address
    +-- update_customer_address
```

This is still **not an LLM agent**.

We are deploying a tool server first.

Later:

```text
Claude / Bedrock Agent
        |
        v
AgentCore Gateway / MCP
        |
        v
Customer MCP Server
        |
        +-- get_customer
        +-- validate_address
        +-- update_customer_address
```

---

## 2. Important MCP 2.x note

The current MCP Python SDK 2.x uses:

```python
from mcp.server import MCPServer
```

rather than the older:

```python
from mcp.server.fastmcp import FastMCP
```

Likewise, the MCP 2.x low-level HTTP client helper is:

```python
from mcp.client.streamable_http import streamable_http_client
```

not:

```python
streamablehttp_client
```

The AWS AgentCore MCP documentation still contains some older SDK examples using `FastMCP` / `streamablehttp_client`.

For Project X we will keep the **current MCP 2.x SDK**, while following the AgentCore **protocol/runtime contract**:

- Streamable HTTP
- host `0.0.0.0`
- port `8000`
- MCP path `/mcp`
- ARM64-compatible runtime/container
- `tools/list`
- `tools/call`

The current MCP 2.x SDK also supports the modern MCP protocol while retaining compatibility with earlier protocol-era clients.

---

## 3. AgentCore MCP Runtime contract

Amazon Bedrock AgentCore Runtime expects an MCP workload to satisfy:

```text
Protocol: Streamable HTTP
Host:     0.0.0.0
Port:     8000
Path:     /mcp
Platform: ARM64
```

Conceptually:

```text
InvokeAgentRuntime
       |
       v
AgentCore Runtime
       |
       | forwards MCP JSON-RPC
       v
0.0.0.0:8000/mcp
       |
       +-- tools/list
       |
       +-- tools/call
```

For a simple tool server, stateless operation is preferred:

```python
stateless_http=True
```

We are intentionally using that for this POC.

---

## 4. Step 8A — Verify prerequisites

We are using:

```text
AWS Region: us-east-1
```

First verify AWS:

```bash
aws sts get-caller-identity
```

Expected:

```json
{
  "UserId": "...",
  "Account": "...",
  "Arn": "arn:aws:iam::...:user/project-x-admin"
}
```

Check region:

```bash
aws configure get region
```

Expected:

```text
us-east-1
```

### 4.1 Verify Node.js

The current AgentCore CLI requires Node.js 20+.

Run:

```bash
node --version
npm --version
```

You want approximately:

```text
Node v20+
```

Node 22 is fine.

Because this Mac is on macOS Catalina and current Homebrew no longer supports it, **do not try to repair Homebrew for Step 8**.

If Node already works from Step 6/CDK, keep using that installation.

### 4.2 Verify Python environment

From:

```bash
cd ~/github/aws-crash-course/mcp/customer-tools
```

activate the MCP environment:

```bash
source .venv/bin/activate
```

Verify:

```bash
which python
python --version
```

The Python executable should be under:

```text
.../aws-crash-course/mcp/customer-tools/.venv/
```

and Python should be 3.10+.

Verify MCP:

```bash
python -c "import mcp; print(mcp.__file__)"
pip show mcp
```

The MCP path should also point into:

```text
mcp/customer-tools/.venv
```

and the version should be:

```text
2.x
```

---

## 5. Step 8B — Make `server.py` AgentCore-compatible

Use this version of:

```text
mcp/customer-tools/server.py
```

```python
from mcp.server import MCPServer


mcp = MCPServer("Project X Customer Tools")


CUSTOMERS = {
    "C12345": {
        "customerId": "C12345",
        "name": "John Smith",
        "status": "ACTIVE",
        "address": {
            "street": "100 Old Street",
            "city": "Jacksonville",
            "state": "FL",
            "zip": "32256",
        },
    },
    "C67890": {
        "customerId": "C67890",
        "name": "Mary Jones",
        "status": "ACTIVE",
        "address": {
            "street": "500 Bay Street",
            "city": "Jacksonville",
            "state": "FL",
            "zip": "32202",
        },
    },
}


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Retrieve a customer by customer ID."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "found": False,
            "customerId": customer_id,
        }

    return {
        "found": True,
        "customer": customer,
    }


@mcp.tool()
def validate_address(
    street: str,
    city: str,
    state: str,
    zip_code: str,
) -> dict:
    """Validate basic requirements for a US address."""

    errors = []

    street = street.strip()
    city = city.strip()
    state = state.strip().upper()
    zip_code = zip_code.strip()

    if not street:
        errors.append("street is required")

    if not city:
        errors.append("city is required")

    if len(state) != 2:
        errors.append("state must be a 2-letter code")

    if len(zip_code) != 5 or not zip_code.isdigit():
        errors.append("zip code must contain 5 digits")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "normalizedAddress": {
            "street": street,
            "city": city,
            "state": state,
            "zip": zip_code,
        },
    }


@mcp.tool()
def update_customer_address(
    customer_id: str,
    street: str,
    city: str,
    state: str,
    zip_code: str,
) -> dict:
    """Update the address for an existing customer."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "updated": False,
            "reason": "CUSTOMER_NOT_FOUND",
            "customerId": customer_id,
        }

    # Production note:
    # The write capability itself must eventually enforce
    # authorization, deterministic validations, invariants,
    # idempotency and auditing.

    customer["address"] = {
        "street": street.strip(),
        "city": city.strip(),
        "state": state.strip().upper(),
        "zip": zip_code.strip(),
    }

    return {
        "updated": True,
        "customerId": customer_id,
        "address": customer["address"],
    }


if __name__ == "__main__":
    mcp.run(
        "streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
    )
```

The critical part is:

```python
mcp.run(
    "streamable-http",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
)
```

This explicitly matches the AgentCore MCP runtime contract.

---

## 6. Step 8C — Retest the AgentCore-compatible server locally

Terminal 1:

```bash
cd ~/github/aws-crash-course/mcp/customer-tools
source .venv/bin/activate
python server.py
```

Expected endpoint:

```text
http://localhost:8000/mcp
```

Terminal 2:

```bash
cd ~/github/aws-crash-course/mcp/customer-tools
source .venv/bin/activate
python client.py
```

Expected tool discovery:

```text
get_customer
validate_address
update_customer_address
```

Do not continue to AWS until this still works.

---

## 7. Step 8D — Add deployment dependency metadata

Create:

```text
requirements.txt
```

with:

```text
mcp>=2,<3
```

This is intentional.

It keeps this project on:

```text
MCP 2.x
```

rather than accidentally receiving an incompatible future major version.

Directory now:

```text
customer-tools/
├── .venv/
├── server.py
├── client.py
└── requirements.txt
```

Optional verification:

```bash
cat requirements.txt
```

---

## 8. Step 8E — Install the current AgentCore CLI

AWS now provides the AgentCore CLI as an npm package.

Official installation:

```bash
npm install -g @aws/agentcore
```

Then:

```bash
agentcore --version
```

If a global npm permission error occurs, do **not** use `sudo npm install`.

We will fix the npm prefix or use an isolated execution path instead.

Also check:

```bash
which agentcore
```

The current CLI is the Node-based AgentCore CLI.

If an old Python `agentcore` executable shadows it, AWS recommends removing the older Python starter-toolkit command.

---

## 9. Step 8F — Understand what the AgentCore CLI will do

The deployment path is:

```text
server.py
   +
Python dependencies
   |
   v
AgentCore CLI
   |
   +-- prepares deployment
   +-- uses CDK underneath
   +-- provisions runtime resources
   +-- configures CloudWatch
   |
   v
AgentCore Runtime
```

This is why we are **not manually creating ECR, ECS, EKS or Lambda** for this MCP server.

For this POC:

```text
MCP tools
    |
    v
AgentCore Runtime
```

is enough.

Later, Jenkins can run this same deployment flow from the enterprise pipeline.

---

## 10. Step 8G — Create an AgentCore project

Do not place AgentCore-generated files directly into the original `customer-tools` folder yet.

From:

```bash
cd ~/github/aws-crash-course/mcp
```

create a separate deployment project:

```bash
agentcore create \
  --project-name ProjectXCustomerTools \
  --no-agent
```

Then:

```bash
cd ProjectXCustomerTools
```

Expected structure is conceptually:

```text
ProjectXCustomerTools/
├── agentcore/
│   ├── agentcore.json
│   ├── aws-targets.json
│   └── cdk/
└── ...
```

The generated configuration becomes the Infrastructure-as-Code representation of the AgentCore project.

---

## 11. Step 8H — Add our MCP runtime

For the first POC, prefer **IAM / SigV4 inbound access** instead of immediately introducing Cognito or Entra ID.

Why?

We are currently learning:

```text
Can AgentCore host our MCP server?
```

not:

```text
Can we complete enterprise OAuth architecture?
```

AgentCore Runtime supports IAM SigV4 as its default inbound authentication mechanism.

Use the AgentCore CLI to add an MCP-protocol runtime.

Because the AgentCore CLI command surface is evolving, inspect the exact current options first:

```bash
agentcore add agent --help
```

We want a runtime with approximately these properties:

```text
Name:     CustomerTools
Language: Python
Protocol: MCP
Inbound:  IAM / default SigV4
```

If the CLI offers IAM/default inbound auth, select it.

**Do not configure Cognito for this first POC unless the CLI requires it for the MCP scaffolding path.**

Production Project X will ultimately need the enterprise identity design, likely Microsoft Entra ID / OAuth for end-user identity plus IAM for AWS workload identity.

---

## 12. Step 8I — Put the MCP 2.x code into the generated runtime

The current AgentCore CLI project layout generally places runtime source under:

```text
app/<runtime-name>/
```

For example:

```text
ProjectXCustomerTools/
└── app/
    └── CustomerTools/
        ├── main.py
        └── pyproject.toml
```

Copy our Step 7/8 server:

```bash
cp ../customer-tools/server.py app/CustomerTools/main.py
```

Open:

```text
app/CustomerTools/main.py
```

and verify it still contains:

```python
from mcp.server import MCPServer
```

and:

```python
mcp.run(
    "streamable-http",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
)
```

Do not replace it with an automatically generated old `FastMCP` sample.

---

## 13. Step 8J — Add MCP 2.x dependency to the AgentCore project

If the generated project uses `uv` / `pyproject.toml`, run from the generated runtime folder:

```bash
cd app/CustomerTools
uv add "mcp>=2,<3"
cd ../..
```

Then inspect:

```bash
cat app/CustomerTools/pyproject.toml
```

You should see MCP as a dependency.

If your generated project instead uses `requirements.txt`, use:

```text
mcp>=2,<3
```

The principle is the same:

```text
Deployment environment
        |
        v
must explicitly install MCP 2.x
```

---

## 14. Step 8K — Preview deployment before creating AWS resources

From the AgentCore project root:

```bash
agentcore deploy --dry-run
```

This is an important habit.

Think of it like:

```text
cdk diff
```

or:

```text
terraform plan
```

Conceptually:

```text
Source code
    |
    v
agentcore deploy --dry-run
    |
    v
"Here is what I intend to create/change"
```

Review for unexpected resources.

---

## 15. Step 8L — Deploy to AWS

When dry-run looks correct:

```bash
agentcore deploy
```

The CLI deploy flow provisions the required AgentCore infrastructure.

The first deployment may also perform CDK bootstrap-related setup if required.

After deployment:

```bash
agentcore status
```

Capture:

```text
Runtime name
Runtime ARN
Region
Status
Endpoint / qualifier
```

The runtime ARN looks conceptually like:

```text
arn:aws:bedrock-agentcore:us-east-1:<account-id>:runtime/<runtime-id>
```

---

## 16. Step 8M — Understand what was created

Before:

```text
Mac
 |
 v
localhost:8000/mcp
```

After:

```text
AWS Account
   |
   v
Amazon Bedrock AgentCore Runtime
   |
   | managed compute / isolation
   |
   v
Project X Customer Tools
   |
   +-- /mcp
       |
       +-- tools/list
       +-- tools/call
```

You are no longer responsible for running:

```bash
python server.py
```

on your Mac for the AWS-hosted copy.

---

## 17. Step 8N — Invoke the deployed MCP runtime using AWS IAM

For the learning POC, IAM SigV4 is easier than adding Cognito.

The caller needs:

```text
bedrock-agentcore:InvokeAgentRuntime
```

The current AWS SDK exposes:

```python
boto3.client("bedrock-agentcore")
```

and:

```python
invoke_agent_runtime(...)
```

For an MCP runtime, the payload itself is the MCP protocol message.

Create:

```text
remote_client.py
```

Start with a tool-list request:

```python
import json
import uuid

import boto3


REGION = "us-east-1"

AGENT_RUNTIME_ARN = "REPLACE_WITH_RUNTIME_ARN"


client = boto3.client(
    "bedrock-agentcore",
    region_name=REGION,
)


payload = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list",
}


response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    runtimeSessionId=str(uuid.uuid4()) + "-project-x-session",
    payload=json.dumps(payload).encode("utf-8"),
    qualifier="DEFAULT",
)


chunks = []

for chunk in response.get("response", []):
    if isinstance(chunk, bytes):
        chunks.append(chunk.decode("utf-8"))
    else:
        chunks.append(str(chunk))


print("".join(chunks))
```

Note:

AgentCore's MCP protocol/version behavior continues to evolve. If the deployed runtime expects modern MCP 2026 request metadata rather than the legacy JSON-RPC-only form, we will use the MCP 2.x client transport against the AgentCore invocation endpoint or add the required MCP protocol headers.

The goal of this first remote test is:

```text
AWS credentials
     |
     v
InvokeAgentRuntime
     |
     v
AgentCore-hosted MCP server
     |
     v
tools/list
```

---

## 18. Step 8O — Call `get_customer` remotely

After `tools/list` works, send:

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/call",
  "params": {
    "name": "get_customer",
    "arguments": {
      "customer_id": "C12345"
    }
  }
}
```

Expected business payload contains:

```text
C12345
John Smith
ACTIVE
100 Old Street
```

Then test:

```text
validate_address
```

and finally:

```text
update_customer_address
```

---

## 19. Step 8P — CloudWatch observability

AgentCore deployment integrates with AWS observability.

After deployment, inspect:

```text
AWS Console
  |
  +-- Amazon Bedrock AgentCore
  |
  +-- CloudWatch
```

Look for:

```text
runtime startup
requests
errors
tool executions
exceptions
```

This matters for Project X because eventually each transaction will require:

```text
request ID
business intent
tool calls
validation results
decision
transaction result
audit correlation ID
```

Application/business auditing will still belong in our own audit design; CloudWatch is operational telemetry, not the entire business audit record.

---

## 20. Step 8Q — What happens to the in-memory customer data?

Our POC currently has:

```python
CUSTOMERS = {...}
```

This is **not durable storage**.

In AgentCore:

```text
Runtime instance starts
        |
        v
CUSTOMERS dictionary exists in memory
        |
        v
runtime/session lifecycle ends
        |
        v
data can disappear
```

Therefore:

```text
DO NOT treat AgentCore process memory as enterprise state.
```

Production:

```text
MCP tool
  |
  +--> enterprise REST/SOAP API
  |
  +--> Pega
  |
  +--> RDS
```

The tool server should be a capability layer, not the source of truth for customer records.

---

## 21. Step 8R — Do we need Docker locally?

Not yet.

AgentCore's runtime contract ultimately requires an ARM64-compatible deployment environment, but the current AgentCore CLI can package/build/deploy the runtime for us.

Therefore Step 8 uses:

```text
AgentCore CLI
```

rather than forcing:

```text
Docker Desktop
ECR push
manual ARM64 build
manual create-agent-runtime
```

Later we should learn the explicit container path because it matters for enterprise CI/CD and debugging.

That later path looks like:

```text
GitLab
   |
Jenkins
   |
docker buildx --platform linux/arm64
   |
ECR
   |
AgentCore Runtime
```

but we do not need it to understand the first deployment.

---

## 22. Step 8S — Authentication: POC vs enterprise

### POC

Use:

```text
AWS IAM
   |
SigV4
   |
InvokeAgentRuntime
```

Benefits:

- no Cognito setup
- no OAuth token management
- works naturally with AWS CLI / boto3
- keeps Step 8 focused on deployment

### Enterprise Project X

Likely:

```text
Microsoft Entra ID
        |
        | OAuth/JWT
        v
Enterprise caller / agent
        |
        v
AgentCore ingress / gateway
```

plus:

```text
AWS IAM / workload role
```

for AWS service-to-service authorization.

These are different identity layers:

```text
Human/business identity
        !=
AWS workload identity
```

Do not mix them.

---

## 23. Step 8T — Runtime vs AgentCore Gateway

At this point:

```text
Client
   |
   v
AgentCore Runtime
   |
   v
Customer MCP Server
```

We **do not need AgentCore Gateway yet**.

Gateway becomes useful when we want:

```text
Agent
 |
 v
AgentCore Gateway
 |
 +-- Customer MCP runtime
 +-- Pega MCP runtime
 +-- Policy MCP runtime
 +-- Lambda tools
 +-- REST/OpenAPI tools
```

Gateway can provide:

- MCP aggregation
- inbound authorization
- policy enforcement
- semantic tool discovery
- interceptors
- unified governance

We will add it only after we understand a single runtime.

---

## 24. Step 8U — Runtime vs MCP server vs tool

Keep these layers distinct:

```text
AgentCore Runtime
    |
    | hosts compute
    v
MCP Server
    |
    | exposes capabilities
    v
MCP Tools
```

Example:

```text
AgentCore Runtime
"CustomerToolsRuntime"
        |
        v
MCPServer
"Project X Customer Tools"
        |
        +-- get_customer
        +-- validate_address
        +-- update_customer_address
```

One runtime does not need to equal one tool.

---

## 25. Step 8V — Enterprise deployment direction

Our laptop deployment:

```text
Developer
   |
agentcore deploy
   |
AWS
```

will eventually become:

```text
GitLab
   |
   v
Jenkins Pipeline
   |
   +-- checkout
   +-- unit tests
   +-- MCP contract tests
   +-- security scan
   +-- package/build
   +-- assume AWS deployment role
   +-- agentcore deploy / controlled IaC
   |
   v
AWS AgentCore Runtime
```

Do not store permanent AWS access keys in Jenkins.

Enterprise CI/CD should use short-lived credentials / federation / AssumeRole.

---

## 26. Step 8W — Production hardening items we intentionally postpone

Do not add all of these during the first deployment:

```text
Entra ID
OAuth propagation
AgentCore Gateway
AgentCore Policy
RDS
Pega
DataPower
Secrets Manager
VPC networking
PrivateLink/VPC endpoints
mTLS
tool-level RBAC
idempotency database
business audit database
distributed tracing
multi-runtime routing
```

They are important, but Step 8 has one purpose:

> Can we take an MCP 2.x server that works locally and deploy it successfully to AgentCore Runtime?

---

## 27. Step 8 completion checklist

- [ ] Step 7 MCP 2.x server still works locally
- [ ] `server.py` uses `from mcp.server import MCPServer`
- [ ] Server uses `streamable-http`, host `0.0.0.0`, port `8000`, and `stateless_http=True`
- [ ] Requirements pin MCP 2.x with `mcp>=2,<3`
- [ ] Node.js 20+ is available
- [ ] AWS CLI identity works
- [ ] AWS Region is `us-east-1`
- [ ] AgentCore CLI is installed
- [ ] `agentcore --version` works
- [ ] AgentCore project is created
- [ ] MCP runtime is added
- [ ] Generated runtime uses the MCP 2.x `server.py`
- [ ] Dependency configuration contains MCP 2.x
- [ ] `agentcore deploy --dry-run` succeeds
- [ ] `agentcore deploy` succeeds
- [ ] `agentcore status` shows a healthy runtime
- [ ] Runtime ARN is captured
- [ ] Remote `tools/list` works
- [ ] Remote `get_customer` works
- [ ] Remote `validate_address` works
- [ ] CloudWatch logs are visible

---

## 28. Step 8 architecture after completion

```text
                     AWS ACCOUNT
                         |
                         |
             +-----------v-----------+
             | Amazon Bedrock        |
             | AgentCore Runtime     |
             |                       |
             | MCP : 0.0.0.0:8000   |
             | Path: /mcp            |
             +-----------+-----------+
                         |
                         v
              +---------------------+
              | Project X Customer  |
              | MCPServer 2.x       |
              +----------+----------+
                         |
              +----------+----------+
              |          |          |
              v          v          v
             get_     validate_   update_
           customer    address   customer
                                  address
```

---

## 29. What comes next — Step 9

Once Step 8 works, Step 9 should introduce the first actual agent:

```text
User request
    |
    v
Claude / Bedrock-powered Agent
    |
    | decides which capability is needed
    v
Customer MCP tools
```

Example reasoning:

```text
"Change C12345's address"

        |
        v
get_customer
        |
        v
validate_address
        |
        v
reason / decide
        |
        v
update_customer_address
```

That is the point where we clearly separate:

```text
Step Functions = deterministic workflow
LLM/Agent     = semantic reasoning
MCP           = capability interface
Tools         = deterministic actions
```

---

## 30. Current source references

### AWS

1. [Deploy MCP servers in AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html)
2. [MCP protocol contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp-protocol-contract.html)
3. [Get started with the AgentCore CLI](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-cli.html)
4. [Invoke an AgentCore Runtime agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html)
5. [Authentication and authorization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html)

### MCP Python SDK

1. [Official Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
2. [ASGI and Streamable HTTP deployment](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/asgi.md)
3. [MCP Python SDK v2 changes](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md)

---

## 31. First command to run when starting Step 8

Do **only this first**:

```bash
node --version
npm --version
aws sts get-caller-identity
aws configure get region
```

Expected:

```text
Node >= 20
AWS identity returned
Region = us-east-1
```

Then continue to installing/verifying the AgentCore CLI.

---

> **Project X learning rule:** One infrastructure concept at a time. Do not add Gateway, Cognito, Entra ID, VPC networking, RDS, or the LLM agent until the single MCP Runtime deployment is understood and working.

## Next Step

Proceed to [Step 9 — Create a simple agent locally](09-agent-local.md).
