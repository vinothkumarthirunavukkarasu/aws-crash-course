# Step 7 — Create a simple MCP server locally

**Status:** ✅ Complete

## Objective

Build and test a local Model Context Protocol (MCP) 2.x server with customer tools.

## Prerequisites

- [x] Python 3.10+ installed
- [x] A terminal and local project checkout

## Tasks

- [x] Create an isolated Python environment
- [x] Install MCP 2.x
- [x] Implement customer tools
- [x] Run the server over Streamable HTTP
- [x] Connect with an MCP client and call the tools

## Overview — Build a local MCP 2.x server

Target:

```text
Local MCP Client
      |
      | tools/list
      | tools/call
      v
Project X MCPServer
      |
      ├── get_customer
      ├── validate_address
└── update_customer_address
```

pip install mcp now installs the stable 2.x line. In v2, FastMCP was renamed to MCPServer; @mcp.tool() still works in the same general way.

## 7.1 Create a clean MCP folder

From your project root:

```bash
cd ~/github/aws-crash-course

mkdir -p mcp/customer-tools
cd mcp/customer-tools
```

Expected:

```text
aws-crash-course/
├── infrastructure/
└── mcp/
    └── customer-tools/
```
## 7.2 Create a dedicated virtual environment

Important because your earlier traceback showed Python using:

```text
aws-crash-course/.venv
```

We want:

```text
aws-crash-course/mcp/customer-tools/.venv
```

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify:

```bash
which python
```

You want something like:

```text
/Users/webmaster/github/aws-crash-course/mcp/customer-tools/.venv/bin/python
```

Check Python:

```bash
python --version
```

MCP 2.x requires Python 3.10+.

## 7.3 Install MCP 2.x

First:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Then:

```bash
pip install mcp
```

Verify:

```bash
pip show mcp
```

You should see:

```text
Name: mcp
Version: 2.x.x
```

Also verify the import:

```bash
python -c "from mcp.server import MCPServer; print('MCP 2.x OK')"
```

Expected:

```text
MCP 2.x OK
```
## 7.4 Create server.py

Create:

```bash
touch server.py
```

Use this:

```python
from mcp.server import MCPServer


mcp = MCPServer(
    "Project X Customer Tools"
)


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
    mcp.run("streamable-http")
```

In MCP 2.x, the high-level server is:

```python
from mcp.server import MCPServer
```

instead of the old:

```python
from mcp.server.fastmcp import FastMCP
```

The decorator-oriented API remains, so @mcp.tool() still exposes Python functions as MCP tools.

## 7.5 Start the server

Run:

```bash
python server.py
```

The server should start on port 8000, with MCP available at:

http://localhost:8000/mcp

That shape is useful for us because AgentCore Runtime expects MCP workloads at:

0.0.0.0:8000/mcp

and AWS recommends stateless Streamable HTTP for basic MCP servers.

Keep this terminal running.

## 7.6 Create the MCP client

Open a second terminal:

```bash
cd ~/github/aws-crash-course/mcp/customer-tools
source .venv/bin/activate
```

Create:

```bash
touch client.py
```

Use this first:

```python
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://localhost:8000/mcp"


async def main():

    async with streamablehttp_client(
        MCP_URL,
        {},
        timeout=120,
        terminate_on_close=False,
    ) as (
        read_stream,
        write_stream,
        _,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("\n=== AVAILABLE TOOLS ===")

            result = await session.list_tools()

            for tool in result.tools:
                print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())
```

AWS's current AgentCore local-testing documentation uses this same streamablehttp_client + ClientSession pattern.

## 7.7 Test tool discovery

Run:

```bash
python client.py
```

Expected:

```text
=== AVAILABLE TOOLS ===

- get_customer
- validate_address
- update_customer_address
```

You just performed:

```text
Client
  |
  | initialize
  |
  | tools/list
  v
MCPServer
  |
  ├─ get_customer
  ├─ validate_address
└─ update_customer_address
```

## 7.8 Inspect MCP-generated tool metadata

Change:

```python
for tool in result.tools:
    print(f"- {tool.name}")
```

to:

```python
for tool in result.tools:

    print("\nNAME:")
    print(tool.name)

    print("DESCRIPTION:")
    print(tool.description)

    print("INPUT SCHEMA:")
    print(tool.inputSchema)
```

Run again:

```bash
python client.py
```

You'll see MCP derive a schema from:

```python
def get_customer(customer_id: str) -> dict:
```

plus:

```python
"""Retrieve a customer by customer ID."""
```

This becomes important later because the agent sees approximately:

```text
Tool name
+ description
+ input schema
```

and uses those to decide when and how to call a tool.

## 7.9 Call get_customer

Replace your client with this expanded version:

```python
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://localhost:8000/mcp"


async def main():

    async with streamablehttp_client(
        MCP_URL,
        {},
        timeout=120,
        terminate_on_close=False,
    ) as (
        read_stream,
        write_stream,
        _,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("\n=== AVAILABLE TOOLS ===")

            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"- {tool.name}")

            print("\n=== GET CUSTOMER ===")

            result = await session.call_tool(
                "get_customer",
                {
                    "customer_id": "C12345"
                },
            )

            print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
python client.py
```

You should see data containing:

```text
C12345
John Smith
ACTIVE
100 Old Street
Jacksonville
```

Flow:

```text
MCP client
    |
    | tools/call
    | get_customer
    v
MCPServer
    |
    v
get_customer()
    |
    v
CUSTOMERS dictionary
```
## 7.10 Call validate_address

Add:

```python
print("\n=== VALIDATE ADDRESS ===")

result = await session.call_tool(
    "validate_address",
    {
        "street": "123 Main Street",
        "city": "Jacksonville",
        "state": "FL",
        "zip_code": "32256",
    },
)

print(result)
```

Run:

```bash
python client.py
```

Conceptual result:

```json
{
  "valid": true,
  "errors": [],
  "normalizedAddress": {
    "street": "123 Main Street",
    "city": "Jacksonville",
    "state": "FL",
    "zip": "32256"
  }
}
```
## 7.11 Test deterministic failure

Change:

```python
"zip_code": "32256"
```

to:

```python
"zip_code": "ABC"
```

Run:

```bash
python client.py
```

You should see something equivalent to:

```json
{
  "valid": false,
  "errors": [
    "zip code must contain 5 digits"
  ]
}
```

Important:

No LLM was involved.

The rule lives here:

```python
if len(zip_code) != 5 or not zip_code.isdigit():
```

That's exactly what we want for Project X deterministic validation.

```text
Agent
  |
  | chooses capability
  v
MCP tool
  |
  | calls deterministic implementation
  v
Business result
```

The LLM should not be responsible for remembering that ZIP codes have five digits.

## 7.12 Call the update tool

Restore:

```python
"zip_code": "32256"
```

Add:

```python
print("\n=== UPDATE CUSTOMER ADDRESS ===")

result = await session.call_tool(
    "update_customer_address",
    {
        "customer_id": "C12345",
        "street": "123 Main Street",
        "city": "Jacksonville",
        "state": "FL",
        "zip_code": "32256",
    },
)

print(result)
```

Then immediately call:

```python
print("\n=== GET CUSTOMER AFTER UPDATE ===")

result = await session.call_tool(
    "get_customer",
    {
        "customer_id": "C12345"
    },
)

print(result)
```

Run:

```bash
python client.py
```

You should now see:

```text
123 Main Street
```

instead of:

```text
100 Old Street
```
## 7.13 Important limitation of our mock storage

If you stop:

```bash
python server.py
```

and restart it, the address returns to:

100 Old Street

Why?

Because:

```python
CUSTOMERS = {...}
```

exists only in memory.

Eventually:

```text
MCP Tool
   |
   v
Business API

or:

MCP Tool
   |
   v
RDS

or:

MCP Tool
   |
   v
Pega API
```

will replace the dictionary.

We're intentionally avoiding databases in Step 7.

## 7.14 Understand MCP 2.x server structure

You now have:

```text
MCPServer
"Project X Customer Tools"
        |
        ├── Tool
        │    get_customer
        |
        ├── Tool
        │    validate_address
        |
        └── Tool
             update_customer_address
```

An MCP server is not the same thing as a tool.

One server can expose many related tools.

For your enterprise architecture, something like this is reasonable:

```text
Customer MCP Server
 ├─ get_customer
 ├─ validate_customer
 ├─ get_customer_history
 └─ update_customer

Policy MCP Server
 ├─ get_policy
 ├─ validate_policy
 ├─ calculate_eligibility
 └─ update_policy

Pega MCP Server
 ├─ create_case
 ├─ get_case
 ├─ update_case
 └─ close_case
```

You don't normally need:

```text
15 MCP tools
=
15 MCP servers
```
## 7.15 MCP is not an agent

Right now you have:

```text
client.py
     |
     v
MCPServer
     |
     v
Python functions

There is:

NO Claude
NO Bedrock model
NO reasoning
NO agent
```

MCP itself is a protocol for exposing capabilities to clients, including LLM applications.

Later we'll change:

```text
client.py

into something like:

Claude-powered Agent
        |
        | discovers
        v
    tools/list

        |
        | decides
        v
    tools/call
```

## 7.16 Understand what the future agent will do

Suppose the request is:

```json
{
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

An agent could reason:

```text
CHANGE_ADDRESS request
        ↓
I need the customer
        ↓
get_customer
        ↓
Customer exists
        ↓
Need to validate requested address
        ↓
validate_address
        ↓
valid=true
        ↓
Need to execute update
        ↓
update_customer_address
```

MCP gives the agent the standardized capability interface.

It does not determine the workflow by itself.

## 7.17 An important enterprise design lesson

Our current write tool will happily execute:

```text
update_customer_address
```

without requiring:

```text
validate_address
```

first.

That isn't strong enough for production.

Eventually your write operation should protect itself:

```text
update_customer_address
          |
          ├─ authenticate caller
          ├─ authorize transaction
          ├─ validate input
          ├─ validate customer state
          ├─ enforce business invariants
          ├─ check idempotency
          ├─ perform transaction
└─ audit
```

The agent can orchestrate:

validate → reason → execute

but the write capability must still protect the transaction.

For your hundreds of Project X validations, this distinction will become extremely important.

## 7.18 Why Streamable HTTP?

MCP supports multiple transports, but we're intentionally using:

```text
streamable-http
```

because that's where you're going next.

AWS AgentCore Runtime currently expects MCP server containers to expose:

```text
Host: 0.0.0.0
Port: 8000
Path: /mcp
```

and supports Streamable HTTP.

So our local development architecture is already conceptually aligned:

TODAY

```text
client.py
   |
   | HTTP
   v
localhost:8000/mcp
```

Later:

```text
AWS / Agent
   |
   | InvokeAgentRuntime
   v
AgentCore Runtime
   |
   v
0.0.0.0:8000/mcp
```
## 7.19 Don't add AgentCore yet

For Step 7, don't install or configure:

```text
AgentCore CLI
Docker
ECR
AgentCore Gateway
Bedrock model
Strands
LangGraph
OAuth
Entra ID
Pega
DataPower
```

They'll make it harder to understand what MCP itself is doing.

Our only objective right now is:

```text
Can I expose Python capabilities as MCP 2.x tools
and call them through MCP?
```
## Step 7 completion checklist

You're done with Step 7 when:

- [x] customer-tools/.venv exists

- [x] which python points to customer-tools/.venv

- [x] pip show mcp reports 2.x

- [x] MCPServer import works

- [x] server.py starts

- [x] localhost:8000/mcp is available

- [x] client.py connects

- [x] tools/list returns:
  - get_customer
  - validate_address
  - update_customer_address

- [x] get_customer("C12345") works

- [x] valid address returns valid=true

- [x] invalid ZIP returns valid=false

- [x] update_customer_address works

- [x] subsequent get_customer shows new address

Once this works, Step 8 will take this exact MCP 2.x server and make it deployable to Amazon Bedrock AgentCore Runtime, including the container/runtime requirements and local deployment testing. AgentCore currently requires an ARM64 container, port 8000, and /mcp for MCP workloads

## Next Step

Proceed to [Step 8 — Deploy the MCP server to AWS](08-mcp-server-aws.md).
