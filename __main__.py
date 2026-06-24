"""
Internal Thumbnail Lambda Infrastructure

This Pulumi program manages AWS Lambda functions for the internal-thumbnail service.
It creates Lambda functions for dev and stage environments with identical configuration.
"""

import json
import pulumi
import pulumi_aws as aws

# Load configuration
config = pulumi.Config()
function_name = config.require("lambda-function-name")
environment = config.require("environment")
log_retention_days = config.get_int("log-retention-days") or 7

# AWS region from config
aws_config = pulumi.Config("aws")
region = aws_config.require("region")

# Shared configuration across all environments
RUNTIME = "provided.al2023"
HANDLER = "bootstrap"
MEMORY_SIZE = 1024
TIMEOUT = 900
ARCHITECTURE = "x86_64"

# Existing IAM role (shared across all Lambda functions)
EXECUTION_ROLE_ARN = "arn:aws:iam::828118946681:role/service-role/euc-ops-os-sandbox-role-8x7vfw50"

# VPC Configuration (existing infrastructure)
VPC_CONFIG = {
    "subnet_ids": [
        "subnet-db739ab3",
        "subnet-0b1d232e1e5faf669",
        "subnet-78bfba03"
    ],
    "security_group_ids": [
        "sg-07556e201ba83bc81"
    ]
}

# Environment Variables (shared configuration)
THUMBNAIL_BUCKET_CONFIG = {
    "ops-os-file-storage": {"": [150, 300, 600, 800, 1000]},
    "tcg-customer-images": {"": [300, 600]},
    "tcg-order-items": {"": [300, 600]},
    "euc-picanova-tcg-configurator-uploads": {"uploads/": [150, 300, 600, 1000]}
}

# S3 bucket for deployment artifacts
S3_ARTIFACT_BUCKET = "picanova-internal-thumbnail"

# Initial code location (placeholder - will be updated by CI/CD)
# Using latest artifact from the respective environment folder
INITIAL_CODE_S3_KEY = f"{environment}/deployments/placeholder/internal-thumbnail.zip"

# CloudWatch Log Group
log_group = aws.cloudwatch.LogGroup(
    f"{function_name}-logs",
    name=f"/aws/lambda/{function_name}",
    retention_in_days=log_retention_days,
    tags={
        "Environment": environment,
        "ManagedBy": "Pulumi",
        "Application": "internal-thumbnail"
    }
)

# Lambda Function
lambda_function = aws.lambda_.Function(
    function_name,
    name=function_name,
    runtime=RUNTIME,
    handler=HANDLER,
    role=EXECUTION_ROLE_ARN,
    timeout=TIMEOUT,
    memory_size=MEMORY_SIZE,
    architectures=[ARCHITECTURE],

    # VPC Configuration
    vpc_config=aws.lambda_.FunctionVpcConfigArgs(
        subnet_ids=VPC_CONFIG["subnet_ids"],
        security_group_ids=VPC_CONFIG["security_group_ids"]
    ),

    # Environment Variables
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "THUMBNAIL_BUCKET_CONFIG": json.dumps(THUMBNAIL_BUCKET_CONFIG)
        }
    ),

    # Code location (placeholder - CI/CD will update with actual code)
    # Note: This is required for initial creation but will be overwritten by GitHub Actions
    s3_bucket=S3_ARTIFACT_BUCKET,
    s3_key=INITIAL_CODE_S3_KEY,

    # Dependencies
    depends_on=[log_group],

    # Tags
    tags={
        "Environment": environment,
        "ManagedBy": "Pulumi",
        "Application": "internal-thumbnail",
        "Repository": "https://github.com/picanova/internal-thumbnail"
    },

    # Lifecycle
    opts=pulumi.ResourceOptions(
        # Protect against accidental deletion
        protect=False,  # Set to True in production
        # Ignore changes to code - managed by CI/CD
        ignore_changes=["s3_key", "source_code_hash", "last_modified"]
    )
)

# Outputs
pulumi.export("function_name", lambda_function.name)
pulumi.export("function_arn", lambda_function.arn)
pulumi.export("function_invoke_arn", lambda_function.invoke_arn)
pulumi.export("log_group_name", log_group.name)
pulumi.export("log_group_arn", log_group.arn)
pulumi.export("environment", environment)
pulumi.export("region", region)

# Export configuration for reference
pulumi.export("configuration", {
    "runtime": RUNTIME,
    "handler": HANDLER,
    "memory_mb": MEMORY_SIZE,
    "timeout_seconds": TIMEOUT,
    "architecture": ARCHITECTURE,
    "vpc_id": "vpc-2ef02a47",
    "execution_role": EXECUTION_ROLE_ARN,
    "artifact_bucket": S3_ARTIFACT_BUCKET
})
