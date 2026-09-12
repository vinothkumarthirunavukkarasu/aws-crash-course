# Step 6 — Rebuild those resources using CDK/IaC

**Status:** ⬜ Pending

## Objective

Recreate the Lambda, Step Function, EventBridge, and API Gateway resources as infrastructure-as-code using AWS CDK.

## Prerequisites

- [ ] Steps 2–5 complete — resources created manually in the AWS Console

## Tasks

- [ ] Set up an AWS CDK project
- [ ] Define the Lambda function in CDK
- [ ] Define the Step Function in CDK
- [ ] Define the EventBridge rule in CDK
- [ ] Define the API Gateway in CDK
- [ ] Deploy the stack
- [ ] Verify all resources work identically to the manual versions

## Verification

- [ ] CDK stack deploys successfully
- [ ] All resources exist in `us-east-1`
- [ ] End-to-end flow works via the CDK-deployed resources

## Next Step

Proceed to [Step 7 — Create a simple MCP server locally](07-mcp-server-local.md).