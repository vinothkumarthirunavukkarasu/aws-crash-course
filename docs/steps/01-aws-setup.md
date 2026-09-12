# Step 1 — Prepare your Mac for AWS

**Status:** ✅ Complete

## Objective

Your Mac should be able to authenticate to your AWS account. Nothing else.

## 1.1 Choose the AWS Region

For this POC use:

```
us-east-1
```

Don't worry about VPCs, AZs, subnets, NAT gateways, etc. yet.

## 1.2 Check Python

```bash
python3 --version
```

**Required:** Python 3.10 or later (AgentCore's MCP documentation requires 3.10+).

**Installed:** `Python 3.12.1` ✅

## 1.3 Check Node.js

```bash
node --version
npm --version
```

**Required:** Node.js 20+ (current AgentCore CLI requires Node.js 20+).

**Installed:** `v22.13.1` and `10.9.2` ✅

## 1.4 Install AWS CLI

```bash
aws --version
```

**Installed:** `aws-cli/2.2.5` ✅

If not installed, use Homebrew:

```bash
brew install awscli
```

## 1.5 Do NOT Create Root Access Keys

- **Never** use the root account with access keys for development.
- Use an IAM administrator/developer identity instead.

## 1.6 Create an IAM User for the POC

- **User name:** `project-x-admin`
- **Policy:** `AdministratorAccess`

> ⚠️ This is acceptable for an isolated learning/POC account. For enterprise implementations, use least-privilege IAM roles.

## 1.7 Create CLI Credentials

- IAM → Users → `project-x-admin` → Security credentials
- Create an access key for **Command Line Interface (CLI)**
- Store the Access Key ID and Secret Access Key securely

**Never put credentials in:**
- GitHub
- Source code
- README
- Python files
- `.env` committed to Git

## 1.8 Configure AWS CLI

```bash
aws configure
```

```
AWS Access Key ID: ************
AWS Secret Access Key: ************
Default region name: us-east-1
Default output format: json
```

## 1.9 Test AWS Connectivity

```bash
aws sts get-caller-identity
```

**Expected output:**

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/project-x-admin"
}
```

**Actual output:**

```json
{
    "UserId": "AIDAQH2QMDZUK6BMFOEZ7",
    "Account": "016811564648",
    "Arn": "arn:aws:iam::016811564648:user/project-x-admin"
}
```

## Verification Checklist

- [x] Python 3.10+ installed
- [x] Node.js 20+ installed
- [x] AWS CLI v2 installed
- [x] IAM user `project-x-admin` created
- [x] CLI credentials configured
- [x] `aws sts get-caller-identity` returns valid identity

## Next Step

Proceed to [Step 2 — Create one Lambda manually and test it](02-lambda.md).