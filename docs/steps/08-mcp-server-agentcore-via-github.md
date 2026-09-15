# Step 8 — Deploy MCP 2.x to AgentCore using GitHub Actions

## 8.0 Goal

Your Mac becomes only the development/git machine:

```text
Your Mac
   │
   │ git push
   ▼
GitHub Repository
   │
   ▼
GitHub Actions
ubuntu-latest
   │
   ├── Node 22
   ├── Python 3.12
   ├── AgentCore CLI
   ├── AWS CLI
   └── MCP deployment
   │
   │ GitHub OIDC
   ▼
AWS IAM Role
   │
   ▼
Amazon Bedrock AgentCore Runtime
   │
   ▼
Project X MCP 2.x Server
   │
   ├── get_customer
   ├── validate_address
   └── update_customer_address
```

The major improvement is:

**OLD**

```text
Mac Catalina
    ↓
AgentCore CLI
    ↓
AWS
```

becomes:

**NEW**

```text
Mac
 ↓ git push
GitHub
 ↓
Linux GitHub Runner
 ↓ AgentCore CLI
AWS
```

Your Mac no longer needs AgentCore CLI, modern npm, Docker, ARM64 tooling, CDK, or a working Homebrew installation.

## Step 8A — Prepare the GitHub repository

Your current structure is approximately:

```text
aws-crash-course/
├── infrastructure/
└── mcp/
    └── customer-tools/
        ├── .venv/
        ├── server.py
        ├── client.py
        └── requirements.txt
```

Make sure:

```text
.venv/
```

is not committed.

At the root of aws-crash-course, add/update .gitignore:

```gitignore
.venv/
__pycache__/
*.pyc
.DS_Store
.env
node_modules/
cdk.out/
```

Your requirements.txt should contain:

```text
mcp>=2,<3
```

## Step 8B — Commit your Step 7 MCP server

From:

```bash
cd ~/github/aws-crash-course
```

check:

```bash
git status
```

Then:

```bash
git add mcp/customer-tools
git add .gitignore
git commit -m "Add Project X MCP 2.x customer tools"
```

If your repository is already connected to GitHub:

```bash
git push
```

At this point:

```text
Mac
 │
 │ git push
 ▼
GitHub
 │
 └── mcp/customer-tools/server.py
```

Do not proceed until you can see server.py in GitHub.

## Step 8C — Understand GitHub → AWS authentication

We are not going to put these into GitHub Secrets:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Instead:

```text
GitHub Actions
      │
      │ requests OIDC token
      ▼
GitHub OIDC
      │
      │ AssumeRoleWithWebIdentity
      ▼
AWS STS
      │
      ▼
Temporary credentials
      │
      ▼
AWS
```

GitHub explicitly recommends this approach because OIDC avoids storing long-lived AWS credentials.

## Step 8D — Create GitHub OIDC provider in AWS

This is a one-time AWS account setup.

Go to:

```text
AWS Console
   ↓
IAM
   ↓
Identity providers
```

Choose:

```text
Add provider
```

Select:

```text
OpenID Connect
```

Provider URL:

```text
https://token.actions.githubusercontent.com
```

Audience:

```text
sts.amazonaws.com
```

Then create the provider.

These are GitHub's documented AWS OIDC values.

You should end up with:

```text
AWS IAM
   │
   └── Identity Provider
          │
          └── token.actions.githubusercontent.com
```

## Step 8E — Create the GitHub deployment role

Now create:

```text
IAM
 ↓
Roles
 ↓
Create role
```

Trusted entity:

```text
Web identity
```

Identity provider:

```text
token.actions.githubusercontent.com
```

Audience:

```text
sts.amazonaws.com
```

Name the role:

```text
project-x-github-deploy-role
```

Conceptually:

```text
GitHub Actions
      │
      │ OIDC
      ▼
project-x-github-deploy-role
      │
      ▼
AgentCore deployment
```

## Step 8F — Restrict the role to YOUR repository

This is important.

Don't create:

```text
Any GitHub repo
     ↓
AWS
```

We want:

```text
YOUR GitHub repo
      ↓
main branch
      ↓
AWS
```

GitHub recommends restricting the IAM trust policy using the OIDC sub claim rather than allowing arbitrary repositories to assume the role.

Your trust relationship will conceptually contain:

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub":
        "repo:YOUR_GITHUB_USERNAME/YOUR_REPOSITORY:ref:refs/heads/main"
    }
  }
}
```

### Important 2026 GitHub detail

GitHub changed OIDC subject behavior for repositories created after July 15, 2026. New repositories can include immutable organization/repository IDs in the sub claim.

Therefore, don't blindly paste my example trust policy yet.

When we reach this point, we'll use your actual GitHub repository information and build the correct trust policy.

## Step 8G — Give the deployment role permissions

For our isolated learning AWS account, we can initially give the deployment role broader permissions to prove the pipeline.

Conceptually the role needs permission for AgentCore deployment plus resources created by its CDK deployment process.

AWS says the deploying identity needs AgentCore API permissions and permission to assume the CDK bootstrap roles used during deployment.

For the POC:

```text
project-x-github-deploy-role
        │
        ├── AgentCore
        ├── CloudFormation/CDK
        ├── IAM PassRole/create supporting roles
        ├── S3
        └── CloudWatch
```

We'll tighten this later.

Do not copy this broad POC model into the enterprise environment.

## Step 8H — Create the first GitHub Actions workflow

Create:

```text
.github/
└── workflows/
    └── agentcore-deploy.yml
```

Initially, don't deploy anything.

We first prove:

```text
GitHub Runner
      ↓
OIDC
      ↓
AWS
```

Use:

```yaml
name: Project X AgentCore Deployment

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:

  verify-aws:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v6.2.4
        with:
          role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/project-x-github-deploy-role
          aws-region: us-east-1

      - name: Verify AWS identity
        run: |
          aws sts get-caller-identity

      - name: Verify AWS region
        run: |
          aws configure get region
```

The important part is:

```yaml
permissions:
  id-token: write
  contents: read
```

id-token: write lets the workflow obtain an OIDC token; it does not itself grant AWS resource permissions. The AWS IAM role determines what the workflow can actually do.

## Step 8I — Run the workflow manually

Commit:

```bash
git add .github/workflows/agentcore-deploy.yml

git commit -m "Add GitHub AWS OIDC workflow"

git push
```

Then open:

```text
GitHub
 ↓
aws-crash-course
 ↓
Actions
 ↓
Project X AgentCore Deployment
 ↓
Run workflow
```

Expected result:

- [x] Checkout repository

- [x] Configure AWS credentials

- [x] Verify AWS identity

- [x] Verify AWS region

The AWS identity should look approximately like:

```text
arn:aws:sts::<account-id>:assumed-role/project-x-github-deploy-role/...
```

This is a major milestone.

You have:

```text
GitHub
   ↓
OIDC
   ↓
AWS STS
   ↓
Temporary AWS credentials
```

with zero permanent AWS keys stored in GitHub.

## Step 8J — Add Node to the runner

Now extend the workflow:

```yaml
- name: Setup Node
  uses: actions/setup-node@v6
  with:
    node-version: '22'

- name: Verify Node
  run: |
    node --version
    npm --version
```

Expected:

```text
Node 22.x
```

AWS currently requires Node 20+ for the AgentCore CLI.

This is exactly what your Catalina Mac couldn't comfortably provide.

## Step 8K — Install AgentCore CLI on the runner

Add:

```yaml
- name: Install AgentCore CLI
  run: |
    npm install -g @aws/agentcore
    agentcore --version
```

Now:

```text
GitHub Ubuntu Runner
       │
       ├── Node 22
       │
       └── AgentCore CLI
```

Your Mac has none of this responsibility.

AWS's current installation command is npm install -g @aws/agentcore.

## Step 8L — Add Python

Add:

```yaml
- name: Setup Python
  uses: actions/setup-python@v6
  with:
    python-version: '3.12'

- name: Verify Python
  run: |
    python --version
    pip --version
```

Now the runner contains:

```text
Ubuntu
 ├── Node 22
 ├── npm
 ├── AgentCore CLI
 ├── Python 3.12
 └── AWS credentials
```

This becomes our clean AWS development/build machine.

## Step 8M — Install and test MCP 2.x

Add:

```yaml
- name: Install MCP dependencies
  working-directory: mcp/customer-tools
  run: |
    pip install -r requirements.txt
```

Then:

```yaml
- name: Verify MCP 2.x
  working-directory: mcp/customer-tools
  run: |
    python -c "import mcp; print(mcp.__file__)"
    pip show mcp
```

This proves your code can build on Linux.

## Step 8N — Why CodeZip helps us

AgentCore currently supports:

```text
CodeZip
Container
```

The default CodeZip deployment packages the application into a ZIP and uploads it through the deployment flow.

AWS explicitly says:

```text
CodeZip → Docker NOT required

Container → Docker required
```

For this POC, therefore:

```text
GitHub Runner
      │
      ├── Python
      ├── MCP
      ├── AgentCore CLI
      │
      X Docker unnecessary
      │
      v
CodeZip
      │
      v
AgentCore Runtime
```

That's much simpler.

## Step 8O — Create the AgentCore project on Linux

This is where we'll move from pipeline setup into AgentCore deployment.

The runner can execute:

```bash
agentcore create \
  --project-name ProjectXCustomerTools \
  --no-agent
```

AWS documents --no-agent as a supported way to create the project structure first and add a workload afterward.

Conceptually:

```text
GitHub checkout

aws-crash-course/
     │
     ├── mcp/customer-tools
     │
     └── ProjectXCustomerTools/
             │
             ├── agentcore/
             └── app/
```

We will then configure the MCP workload.

## Step 8P — MCP 2.x server contract

Our deployed server must remain:

```python
from mcp.server import MCPServer
```

and expose Streamable HTTP on:

```text
0.0.0.0
8000
/mcp
```

Our three tools remain:

```text
Project X Customer Tools

├── get_customer
├── validate_address
└── update_customer_address
```

No LLM is involved yet.

## Step 8Q — Preview before deploying

Once the AgentCore project is configured:

```bash
agentcore deploy --dry-run
```

This is analogous to:

```text
Terraform
   ↓
terraform plan
```

or:

```text
CDK
 ↓
cdk diff
```

AWS documents agentcore deploy --dry-run specifically for previewing deployment changes.

## Step 8R — Deploy from GitHub

Then the runner executes:

```bash
agentcore deploy
```

AgentCore CLI will:

```text
MCP source
   ↓
package CodeZip
   ↓
S3 artifact
   ↓
CDK
   ↓
AWS resources
   ↓
AgentCore Runtime
   ↓
CloudWatch
```

AWS says agentcore deploy packages the application, uses CDK underneath, creates the Runtime endpoint, and configures CloudWatch observability.

Then:

```bash
agentcore status
```

## Step 8S — Final GitHub Actions architecture

Our workflow eventually becomes approximately:

```yaml
name: Deploy Project X MCP

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:

  deploy:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout
        uses: actions/checkout@v6

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v6.2.4
        with:
          role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/project-x-github-deploy-role
          aws-region: us-east-1

      - name: Setup Node
        uses: actions/setup-node@v6
        with:
          node-version: '22'

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Install AgentCore CLI
        run: |
          npm install -g @aws/agentcore
          agentcore --version

      - name: Verify AWS
        run: |
          aws sts get-caller-identity

      - name: Install MCP dependencies
        working-directory: mcp/customer-tools
        run: |
          pip install -r requirements.txt

      # AgentCore project/configuration steps go here

      - name: Preview deployment
        run: |
          agentcore deploy --dry-run

      - name: Deploy
        run: |
          agentcore deploy

      - name: Runtime status
        run: |
          agentcore status
```

Don't create this entire final workflow yet.

We're going to build it incrementally so when something fails, we know exactly which layer failed.

## Step 8T — Why this is better for Project X

This isn't merely a workaround for Catalina.

You're learning:

```text
Developer
    ↓
Source Control
    ↓
CI/CD Runner
    ↓
Federated AWS identity
    ↓
Build
    ↓
Deploy
    ↓
AWS Runtime
```

Your enterprise architecture will eventually be:

```text
                    POC

Mac
 ↓
GitHub
 ↓
GitHub Actions
 ↓ OIDC
AWS deployment role
 ↓
AgentCore
```

and later:

```text
                 ENTERPRISE

Developer
 ↓
On-prem GitLab
 ↓
On-prem Jenkins
 ↓ federation / AssumeRole
AWS deployment role
 ↓
AgentCore
```

So most of the concepts transfer directly.

## Step 8 completion target

```text
Mac
 │
 │ git push
 ▼
GitHub
 │
 ▼
GitHub Actions / Ubuntu
 │
 ├── Node 22 ✓
 ├── Python 3.12 ✓
 ├── MCP 2.x ✓
 ├── AgentCore CLI ✓
 │
 │ OIDC
 ▼
AWS deployment role ✓
 │
 ▼
AgentCore Runtime ✓
 │
 ▼
MCP 2.x
 │
 ├── tools/list ✓
 ├── get_customer ✓
 ├── validate_address ✓
 └── update_customer_address ✓
```
