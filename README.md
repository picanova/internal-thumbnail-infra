# Internal Thumbnail Infrastructure

Infrastructure as Code (Pulumi/Python) for the `internal-thumbnail` AWS Lambda functions.

## Overview

This repository manages AWS Lambda infrastructure for the thumbnail generation service across multiple environments.

**Application Repository**: https://github.com/picanova/internal-thumbnail

## Environments

| Stack | Environment | Lambda Function | Purpose |
|-------|-------------|----------------|---------|
| `dev` | Development | `internal-thumbnail-dev` | Development testing |
| `stage` | Staging | `internal-thumbnail-stage` | Pre-production validation |
| `prod` | Production | `internal-thumbnail` | Production (managed separately) |

**Note**: Production Lambda (`internal-thumbnail`) already exists and is managed outside this repository.

## Architecture

### Lambda Function Configuration

```
Runtime: provided.al2023 (Custom Rust)
Handler: bootstrap
Memory: 1024 MB
Timeout: 900 seconds (15 minutes)
Architecture: x86_64
Package Type: Zip

VPC: vpc-2ef02a47
Subnets: subnet-db739ab3, subnet-0b1d232e1e5faf669, subnet-78bfba03
Security Groups: sg-07556e201ba83bc81
```

### Resources Managed

- AWS Lambda Functions (dev, stage)
- CloudWatch Log Groups
- IAM Role attachments (uses existing role)

**Not Managed Here**:
- IAM execution role (uses shared `euc-ops-os-sandbox-role-8x7vfw50`)
- VPC/Subnets/Security Groups (existing infrastructure)
- S3 bucket (uses shared `picanova-internal-thumbnail`)

## Prerequisites

### Required Tools

- [Pulumi](https://www.pulumi.com/docs/get-started/install/) >= 3.0
- Python >= 3.9
- AWS CLI configured with `prodwrite` profile
- AWS Account: 828118946681 (eu-central-1)

### AWS Credentials

```bash
export AWS_PROFILE=prodwrite
aws sts get-caller-identity  # Verify access
```

## Quick Start

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Select Stack

```bash
# Development
pulumi stack select dev

# Staging
pulumi stack select stage
```

### Deploy

```bash
# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# View outputs
pulumi stack output
```

## Stack Configuration

### Development (dev)

```yaml
aws:region: eu-central-1
aws:profile: prodwrite

lambda-function-name: internal-thumbnail-dev
environment: dev
log-retention-days: 7
```

### Staging (stage)

```yaml
aws:region: eu-central-1
aws:profile: prodwrite

lambda-function-name: internal-thumbnail-stage
environment: stage
log-retention-days: 14
```

## Deployment Guide

### Create New Environment

```bash
# Create stack
pulumi stack init dev

# Configure stack
pulumi config set aws:region eu-central-1
pulumi config set aws:profile prodwrite
pulumi config set lambda-function-name internal-thumbnail-dev
pulumi config set environment dev

# Deploy
pulumi up
```

### Update Existing Environment

```bash
# Select stack
pulumi stack select dev

# Preview changes
pulumi preview

# Apply changes
pulumi up
```

### Destroy Environment

```bash
pulumi stack select dev
pulumi destroy
```

## Infrastructure Details

### Lambda Function

Managed by `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
function_name = config.require("lambda-function-name")
environment = config.require("environment")

# Lambda function using existing IAM role and VPC config
lambda_function = aws.lambda_.Function(
    function_name,
    name=function_name,
    runtime="provided.al2023",
    handler="bootstrap",
    role="arn:aws:iam::828118946681:role/service-role/euc-ops-os-sandbox-role-8x7vfw50",
    # ... configuration
)
```

### Environment Variables

All Lambda functions use the same configuration:

```json
{
  "THUMBNAIL_BUCKET_CONFIG": {
    "ops-os-file-storage": {"": [150,300,600,800,1000]},
    "tcg-customer-images": {"": [300,600]},
    "tcg-order-items": {"": [300,600]},
    "euc-picanova-tcg-configurator-uploads": {"uploads/": [150,300,600,1000]}
  }
}
```

## CI/CD Integration

Deployment to Lambda functions is handled by GitHub Actions in the application repository:

```
Application Repo (internal-thumbnail):
  - Build Rust binary
  - Package as ZIP
  - Upload to S3
  - Deploy to Lambda

Infrastructure Repo (internal-thumbnail-infra):
  - Manage Lambda function definition
  - Manage CloudWatch logs
  - Manage IAM permissions
```

## Troubleshooting

### Common Issues

**Issue**: `pulumi up` fails with "role not found"
```bash
# Verify IAM role exists
aws iam get-role --role-name euc-ops-os-sandbox-role-8x7vfw50 --profile prodwrite
```

**Issue**: VPC configuration errors
```bash
# Verify VPC and subnets exist
aws ec2 describe-vpcs --vpc-ids vpc-2ef02a47 --profile prodwrite
aws ec2 describe-subnets --subnet-ids subnet-db739ab3 --profile prodwrite
```

**Issue**: Lambda code not updating
- This repository only manages Lambda _configuration_
- Lambda _code_ is deployed via GitHub Actions from the application repository
- To update code, push to the application repository

### View Current State

```bash
# List all resources in stack
pulumi stack

# View configuration
pulumi config

# Export stack state
pulumi stack export > stack-export.json
```

## Security

### IAM Permissions Required

Pulumi needs permissions to:
- Create/update/delete Lambda functions
- Create/update/delete CloudWatch log groups
- Read IAM roles (to verify execution role)
- Read VPC resources (to verify VPC configuration)

### Secrets Management

No secrets are stored in this repository. Pulumi config values are non-sensitive.

For sensitive values, use Pulumi secrets:
```bash
pulumi config set --secret my-secret-key my-secret-value
```

## Maintenance

### Updating Lambda Configuration

To change Lambda settings (memory, timeout, environment variables):

1. Update `__main__.py`
2. Run `pulumi preview` to see changes
3. Run `pulumi up` to apply

### Updating Dependencies

```bash
# Update Pulumi Python SDK
pip install --upgrade pulumi pulumi-aws

# Update requirements.txt
pip freeze > requirements.txt
```

## Support

**Issues**: https://github.com/picanova/internal-thumbnail-infra/issues
**Application Issues**: https://github.com/picanova/internal-thumbnail/issues

---

**Created**: 2026-06-24
**Maintained By**: DevOps Team
