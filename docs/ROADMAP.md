# POC Roadmap

This document tracks the full proof-of-concept roadmap for the AWS Crash Course.

We will do this in exactly this order:

| # | Step | Description | Status | Spec |
|---|------|-------------|--------|------|
| 1 | Set up your laptop to access AWS | Install/verify AWS CLI, create IAM user, configure credentials, test connectivity | ✅ Complete | [01-aws-setup.md](steps/01-aws-setup.md) |
| 2 | Create one Lambda manually and test it | Create a Lambda function in the AWS Console and invoke it | ⬜ Pending | [02-lambda.md](steps/02-lambda.md) |
| 3 | Create a Step Function that calls Lambda | Build a state machine that invokes the Lambda | ⬜ Pending | [03-step-functions.md](steps/03-step-functions.md) |
| 4 | Create EventBridge and trigger the Step Function | Schedule or event-trigger the Step Function | ⬜ Pending | [04-eventbridge.md](steps/04-eventbridge.md) |
| 5 | Create API Gateway and send an HTTP request | Expose the Step Function via a REST API | ⬜ Pending | [05-api-gateway.md](steps/05-api-gateway.md) |
| 6 | Rebuild those resources using CDK/IaC | Recreate everything as infrastructure-as-code | ⬜ Pending | [06-cdk-iac.md](steps/06-cdk-iac.md) |
| 7 | Create a simple MCP server locally | Build a Model Context Protocol server on your Mac | ⬜ Pending | [07-mcp-server-local.md](steps/07-mcp-server-local.md) |
| 8 | Deploy the MCP server to AgentCore Runtime | Host the MCP server on AgentCore Runtime | ⬜ Pending | [08-mcp-server-agentcore.md](steps/08-mcp-server-agentcore.md) |
| 9 | Create a simple agent locally | Build a basic agent on your Mac | ⬜ Pending | [09-agent-local.md](steps/09-agent-local.md) |
| 10 | Deploy the agent to AgentCore Runtime | Deploy the agent to AgentCore Runtime | ⬜ Pending | [10-agent-agentcore.md](steps/10-agent-agentcore.md) |
| 11 | Make the agent call the MCP server | Connect the agent to the MCP server | ⬜ Pending | [11-agent-mcp.md](steps/11-agent-mcp.md) |
| 12 | Make Step Functions call the agent | Have the Step Function invoke the deployed agent | ⬜ Pending | [12-stepfunctions-agent.md](steps/12-stepfunctions-agent.md) |
| 13 | Move code to GitHub | Push all source code to a GitHub repository | ⬜ Pending | [13-github.md](steps/13-github.md) |
| 14 | Deploy automatically from GitHub | Set up CI/CD for automatic deployments | ⬜ Pending | [14-github-cicd.md](steps/14-github-cicd.md) |

> **Note:** AWS's current AgentCore CLI supports local testing, deployment, status checks, and invoking deployed agents. AgentCore Runtime can also host MCP servers.

---

## Progress Summary

- **Completed:** 1 of 14 steps
- **Current focus:** Step 2 — Create one Lambda manually and test it
- **Next up:** Step 3 — Create a Step Function that calls Lambda

## Security Best Practices

1. **Never commit `.env`** — it is already in `.gitignore`.
2. **Rotate credentials** if they are ever exposed.
3. **Use least-privilege IAM roles** for production workloads.
4. **Use OIDC-based authentication** (e.g., GitHub Actions OIDC) instead of long-lived access keys.
5. **Use AWS Secrets Manager or Parameter Store** for secrets in production.