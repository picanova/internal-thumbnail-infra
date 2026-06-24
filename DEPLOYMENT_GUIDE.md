# Deployment Guide - Internal Thumbnail Infrastructure

## Overview

This guide covers deploying and managing Lambda infrastructure for the internal-thumbnail service using Pulumi.

**Important**: This repository manages Lambda _infrastructure_ (function configuration, IAM, CloudWatch logs). Lambda _code_ is deployed separately via GitHub Actions from the application repository.

---

## Prerequisites

### 1. Install Tools

```bash
# Install Pulumi
curl -fsSL https://get.pulumi.com | sh

# Verify installation
pulumi version

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
# Use prodwrite profile
export AWS_PROFILE=prodwrite

# Verify access
aws sts get-caller-identity

# Expected output:
# Account: 828118946681
# Region: eu-central-1
```

### 3. Login to Pulumi

```bash
# Login to Pulumi Cloud (or self-hosted backend)
pulumi login

# Or use local backend
pulumi login --local
```

---

## Initial Setup

### Development Environment

```bash
# Initialize dev stack (if not exists)
pulumi stack init dev

# Stack is already configured via Pulumi.dev.yaml
# Verify configuration
pulumi config

# Expected output:
# KEY                                            VALUE
# aws:profile                                    prodwrite
# aws:region                                     eu-central-1
# internal-thumbnail-infra:environment           dev
# internal-thumbnail-infra:lambda-function-name  internal-thumbnail-dev
# internal-thumbnail-infra:log-retention-days    7
```

### Staging Environment

```bash
# Initialize stage stack
pulumi stack init stage

# Configuration is in Pulumi.stage.yaml
pulumi config

# Expected output shows staging configuration
```

---

## Deployment

### Deploy Development

```bash
# Select dev stack
pulumi stack select dev

# Preview changes
pulumi preview

# Deploy
pulumi up

# Review changes and confirm with 'yes'
```

### Deploy Staging

```bash
# Select stage stack
pulumi stack select stage

# Preview and deploy
pulumi preview
pulumi up
```

### Expected Output

```
Previewing update (dev)

View in Browser: https://app.pulumi.com/...

     Type                            Name                                    Plan
 +   pulumi:pulumi:Stack             internal-thumbnail-infra-dev            create
 +   ├─ aws:cloudwatch:LogGroup      internal-thumbnail-dev-logs             create
 +   └─ aws:lambda:Function          internal-thumbnail-dev                  create

Outputs:
    configuration  : {
        architecture   : "x86_64"
        artifact_bucket: "picanova-internal-thumbnail"
        execution_role : "arn:aws:iam::828118946681:role/service-role/euc-ops-os-sandbox-role-8x7vfw50"
        handler        : "bootstrap"
        memory_mb      : 1024
        runtime        : "provided.al2023"
        timeout_seconds: 900
        vpc_id         : "vpc-2ef02a47"
    }
    environment    : "dev"
    function_arn   : "arn:aws:lambda:eu-central-1:828118946681:function:internal-thumbnail-dev"
    function_name  : "internal-thumbnail-dev"
    log_group_arn  : "arn:aws:logs:eu-central-1:828118946681:log-group:/aws/lambda/internal-thumbnail-dev"
    log_group_name : "/aws/lambda/internal-thumbnail-dev"
    region         : "eu-central-1"

Resources:
    + 3 to create

Do you want to perform this update? yes
```

---

## Important Notes

### Lambda Code Deployment

**This Pulumi stack does NOT deploy Lambda code.** Code deployment is handled by GitHub Actions:

```
Application Repo Workflow:
1. Build Rust binary
2. Package as ZIP
3. Upload to S3: s3://picanova-internal-thumbnail/{env}/deployments/...
4. Update Lambda code via AWS CLI
```

**What Pulumi Manages**:
- Lambda function configuration (memory, timeout, VPC, etc.)
- CloudWatch log groups
- Environment variables
- IAM role attachments (references existing role)

**What Pulumi Does NOT Manage**:
- Lambda function code (managed by GitHub Actions)
- IAM execution role (pre-existing shared role)
- VPC/Subnets/Security Groups (pre-existing infrastructure)
- S3 artifact bucket (pre-existing)

### Ignore Changes to Code

The Pulumi program uses `ignore_changes` to prevent conflicts with CI/CD:

```python
opts=pulumi.ResourceOptions(
    ignore_changes=["s3_key", "source_code_hash", "last_modified"]
)
```

This ensures Pulumi doesn't overwrite code deployed by GitHub Actions.

---

## Updating Configuration

### Change Lambda Memory

```bash
# Edit __main__.py
MEMORY_SIZE = 2048  # Change from 1024 to 2048

# Preview and apply
pulumi preview
pulumi up
```

### Change Timeout

```bash
# Edit __main__.py
TIMEOUT = 600  # Change from 900 to 600

pulumi preview
pulumi up
```

### Update Environment Variables

```bash
# Edit __main__.py
THUMBNAIL_BUCKET_CONFIG = {
    "ops-os-file-storage": {"": [150, 300, 600]},  # Modify sizes
    # ... other buckets
}

pulumi preview
pulumi up
```

### Change Log Retention

```bash
# Edit Pulumi.dev.yaml or Pulumi.stage.yaml
internal-thumbnail-infra:log-retention-days: "30"

# Or via CLI
pulumi config set log-retention-days 30

pulumi preview
pulumi up
```

---

## Verification

### Check Stack Outputs

```bash
pulumi stack output

# Get specific output
pulumi stack output function_arn
pulumi stack output log_group_name
```

### Verify Lambda Function

```bash
aws lambda get-function \
  --function-name internal-thumbnail-dev \
  --region eu-central-1 \
  --profile prodwrite
```

### Check CloudWatch Logs

```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/internal-thumbnail-dev \
  --region eu-central-1 \
  --profile prodwrite
```

---

## Troubleshooting

### Error: Function Already Exists

If Lambda function already exists (created manually or by other means):

**Option 1: Import Existing Resource**

```bash
pulumi import aws:lambda/function:Function internal-thumbnail-dev internal-thumbnail-dev
```

**Option 2: Delete and Recreate**

```bash
# WARNING: This will delete the function
pulumi destroy
pulumi up
```

**Recommended**: Import the existing function to avoid disruption.

### Error: Role Not Found

```bash
# Verify IAM role exists
aws iam get-role \
  --role-name euc-ops-os-sandbox-role-8x7vfw50 \
  --profile prodwrite

# If role doesn't exist, update __main__.py with correct role ARN
```

### Error: VPC Configuration Failed

```bash
# Verify VPC and subnets
aws ec2 describe-vpcs --vpc-ids vpc-2ef02a47 --profile prodwrite
aws ec2 describe-subnets --subnet-ids subnet-db739ab3 --profile prodwrite

# Verify security group
aws ec2 describe-security-groups --group-ids sg-07556e201ba83bc81 --profile prodwrite
```

### Error: S3 Bucket Not Found

The initial deployment uses a placeholder S3 key. If S3 bucket doesn't have the file:

**Option 1**: Deploy code first via GitHub Actions
**Option 2**: Upload a placeholder zip file

```bash
# Create minimal placeholder
echo "placeholder" > bootstrap
zip /tmp/placeholder.zip bootstrap

# Upload to S3
aws s3 cp /tmp/placeholder.zip \
  s3://picanova-internal-thumbnail/dev/deployments/placeholder/internal-thumbnail.zip \
  --profile prodwrite

# Then run pulumi up
```

---

## Maintenance

### View Resource State

```bash
# List all resources
pulumi stack --show-urns

# Export state
pulumi stack export > stack-export.json
```

### Refresh State

```bash
# Sync state with AWS
pulumi refresh
```

### Destroy Environment

```bash
# WARNING: This will delete all resources in the stack
pulumi stack select dev
pulumi destroy

# Confirm with 'yes'
```

---

## CI/CD Integration (Future)

Currently, this repository is deployed manually. Future enhancements:

### GitHub Actions Workflow (Proposed)

```yaml
name: Deploy Infrastructure

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pulumi/actions@v4
        with:
          command: preview
          stack-name: dev

  deploy-dev:
    needs: preview
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pulumi/actions@v4
        with:
          command: up
          stack-name: dev
```

---

## Security Best Practices

### 1. Protect Production Stacks

```python
# In __main__.py, set protect=True for production
opts=pulumi.ResourceOptions(
    protect=True,  # Prevents accidental deletion
    ignore_changes=["s3_key", "source_code_hash", "last_modified"]
)
```

### 2. Use Secrets for Sensitive Data

```bash
# Store secrets in Pulumi
pulumi config set --secret db-password mySecretPassword

# Access in code
db_password = config.require_secret("db-password")
```

### 3. Least Privilege IAM

Ensure Pulumi execution has minimal required permissions:
- `lambda:CreateFunction`, `lambda:UpdateFunctionConfiguration`
- `logs:CreateLogGroup`, `logs:PutRetentionPolicy`
- `iam:PassRole` (for Lambda execution role)

---

## Stack Management

### List Stacks

```bash
pulumi stack ls

# Output:
# NAME   LAST UPDATE     RESOURCE COUNT  URL
# dev    2 minutes ago   3               https://app.pulumi.com/...
# stage  1 hour ago      3               https://app.pulumi.com/...
```

### Switch Between Stacks

```bash
pulumi stack select dev
pulumi stack select stage
```

### Remove Stack

```bash
# Destroy resources first
pulumi destroy

# Then remove stack
pulumi stack rm dev
```

---

## Support

**Issues**: https://github.com/picanova/internal-thumbnail-infra/issues
**Pulumi Docs**: https://www.pulumi.com/docs/
**AWS Lambda Docs**: https://docs.aws.amazon.com/lambda/

---

**Created**: 2026-06-24
**Last Updated**: 2026-06-24
**Maintained By**: DevOps Team
