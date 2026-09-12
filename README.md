# AWS Crash Course — POC

A hands-on proof-of-concept for building an end-to-end pipeline on AWS, from a single Lambda function to a fully automated CI/CD deployment with AgentCore.

## Documentation

All documentation lives in the [`docs/`](docs/) folder:

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Full POC roadmap with status tracking |
| [docs/steps/01-aws-setup.md](docs/steps/01-aws-setup.md) | Step 1 — Set up your laptop to access AWS ✅ |
| [docs/steps/02-lambda.md](docs/steps/02-lambda.md) | Step 2 — Create one Lambda manually and test it |
| [docs/steps/03-step-functions.md](docs/steps/03-step-functions.md) | Step 3 — Create a Step Function that calls Lambda |
| [docs/steps/04-eventbridge.md](docs/steps/04-eventbridge.md) | Step 4 — Create EventBridge and trigger the Step Function |
| [docs/steps/05-api-gateway.md](docs/steps/05-api-gateway.md) | Step 5 — Create API Gateway and send an HTTP request |
| [docs/steps/06-cdk-iac.md](docs/steps/06-cdk-iac.md) | Step 6 — Rebuild those resources using CDK/IaC |
| [docs/steps/07-mcp-server-local.md](docs/steps/07-mcp-server-local.md) | Step 7 — Create a simple MCP server locally |
| [docs/steps/08-mcp-server-agentcore.md](docs/steps/08-mcp-server-agentcore.md) | Step 8 — Deploy the MCP server to AgentCore Runtime |
| [docs/steps/09-agent-local.md](docs/steps/09-agent-local.md) | Step 9 — Create a simple agent locally |
| [docs/steps/10-agent-agentcore.md](docs/steps/10-agent-agentcore.md) | Step 10 — Deploy the agent to AgentCore Runtime |
| [docs/steps/11-agent-mcp.md](docs/steps/11-agent-mcp.md) | Step 11 — Make the agent call the MCP server |
| [docs/steps/12-stepfunctions-agent.md](docs/steps/12-stepfunctions-agent.md) | Step 12 — Make Step Functions call the agent |
| [docs/steps/13-github.md](docs/steps/13-github.md) | Step 13 — Move code to GitHub |
| [docs/steps/14-github-cicd.md](docs/steps/14-github-cicd.md) | Step 14 — Deploy automatically from GitHub |

> **Note:** AWS's current AgentCore CLI supports local testing, deployment, status checks, and invoking deployed agents. AgentCore Runtime can also host MCP servers.

## Current Status

- **Completed:** 1 of 14 steps
- **Current focus:** Step 2 — Create one Lambda manually and test it

## Security Notes

- **Never commit `.env`** — it is already in `.gitignore`.
- Use `.env.example` as a template for environment variables.
- **Rotate credentials immediately** if they are ever exposed (e.g., in a chat, screenshot, or commit).
- For production, use:
  - Least-privilege IAM roles
  - OIDC-based authentication (e.g., GitHub Actions OIDC)
  - AWS Secrets Manager or Parameter Store for secrets

## Repository Structure

```
.
├── .env.example          # Template for environment variables (never commit real values)
├── .gitignore            # Git ignore rules
├── LICENSE               # GPL-3.0 license
├── README.md             # This file
└── docs/
    ├── README.md         # Documentation index
    ├── ROADMAP.md        # Full POC roadmap with status tracking
    └── steps/            # Individual step specs
        ├── 01-aws-setup.md
        ├── 02-lambda.md
        ├── ...
        └── 14-github-cicd.md
```

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
