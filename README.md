# Decoupled Serverless Pipeline

> **Infrastructure as Code · Real-time Ingestion · Privacy by Design**

A production-ready serverless data pipeline built entirely with Terraform. Records flow from a producer into **Amazon Kinesis**, get processed and **PII-masked** by **AWS Lambda**, then land in **DynamoDB** — all within the AWS Free Tier.

---

## Architecture

```
![Architecture Screenshot](./images/infrastructure.drawio.svg)
!
---

## Why I Built This

This project demonstrates three cloud engineering fundamentals that I wanted to prove in practice, not just theory:

| Principle | Implementation |
|---|---|
| **Infrastructure as Code** | 100% Terraform — no console clicks, full drift detection |
| **Data Security** | PII masked *before* persistence — plaintext never touches the database |
| **Decoupled Architecture** | Producer and consumer are fully independent via Kinesis as the contract |

---

## Project Structure

```
serverless-pipeline/
├── main.tf                  # Root module — wires everything together
├── variables.tf             # Input variables with validation
├── outputs.tf               # Exposed resource names and ARNs
├── terraform.tfvars.example # Safe-to-commit variable template
│
├── modules/
│   ├── kinesis/             # Stream, shard config
│   ├── lambda/              # Function, event source mapping, log group
│   ├── dynamodb/            # Table schema, PITR, billing mode
│   └── iam/                 # Least-privilege role + inline policies
│
├── lambda_src/
│   └── handler.py           # Masking logic + DynamoDB persistence
│
├── scripts/
│   └── producer.py          # CLI tool to send test records
│
└── tests/
    └── test_masking.py      # Unit tests for all masking functions
```

---

## Free Tier Coverage

This project is designed to run at **$0** during development and testing.

| Service | Free Tier Allowance | This Project |
|---|---|---|
| Kinesis | 1 shard-month, 1M PUT records/mo | 1 shard stream |
| Lambda | 1M requests, 400K GB-sec/mo | ~128 MB · event-driven only |
| DynamoDB | 25 WCU / 25 RCU, 25 GB storage | `PAY_PER_REQUEST` mode |
| CloudWatch Logs | 5 GB ingestion/mo | 7-day retention |

> ⚠️ **Important:** Kinesis charges **$0.015 per shard-hour** after your free period expires. Always run `terraform destroy` when you finish testing.

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.6
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured (`aws configure`)
- Python 3.12 (for producer script and tests)
- An AWS account with Free Tier active

---

## Quick Start

### 1 — Clone the repo

```bash
git clone https://github.com/MuigaiEdwin/serverless-pipeline.git
cd serverless-pipeline
```

### 2 — Configure variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if you want a different region or project name
```

### 3 — Deploy

```bash
terraform init
terraform plan
terraform apply
```

Terraform will output the resource names on completion:

```
Outputs:
  dynamodb_table_name  = "serverless-pipeline-records"
  kinesis_stream_name  = "serverless-pipeline-stream"
  lambda_function_name = "serverless-pipeline-processor"
  lambda_log_group     = "/aws/lambda/serverless-pipeline-processor"
```

### 4 — Send test records

```bash
pip install boto3

python scripts/producer.py \
  --stream serverless-pipeline-stream \
  --count 10 \
  --region us-east-1
```

### 5 — Verify masking in DynamoDB

Open the AWS Console → DynamoDB → Tables → `serverless-pipeline-records` → Explore items.

You should see records like:

```json
{
  "record_id":    "f3a1c2d4-...",
  "ingested_at":  "2024-11-01T10:23:45+00:00",
  "email":        "al****@***.com",
  "phone":        "+25***5678",
  "name":         "A**** W*****",
  "product":      "laptop",
  "price_usd":    299.99
}
```

### 6 — Watch Lambda logs

```bash
aws logs tail /aws/lambda/serverless-pipeline-processor --follow
```

### 7 — Tear down when done

```bash
terraform destroy
```

---

## Data Masking Rules

The Lambda applies field-level masking based on key name matching — no schema required.

| Field | Input | Masked Output |
|---|---|---|
| `email` | `alice@example.com` | `al****@***.com` |
| `phone` / `mobile` | `+254712345678` | `+254***5678` |
| `ssn` / `national_id` | `123-45-6789` | `***-**-6789` |
| `name` / `full_name` | `Alice Wanjiru` | `A**** W******` |

All other fields pass through unchanged.

---

## IAM Security Design

The Lambda execution role follows **least-privilege** — it has exactly the permissions it needs and nothing more.

```
Lambda Role
├── kinesis:GetRecords          ← on this stream ARN only
├── kinesis:GetShardIterator
├── kinesis:DescribeStream
├── kinesis:ListShards
├── dynamodb:PutItem            ← on this table ARN only
├── logs:CreateLogGroup         ← AWSLambdaBasicExecutionRole
├── logs:CreateLogStream
└── logs:PutLogEvents
```

No `*` actions. No `*` resources.

---

## Running Tests

```bash
pip install pytest boto3
python -m pytest tests/ -v
```

Expected output:

```
tests/test_masking.py::TestMaskEmail::test_basic_email        PASSED
tests/test_masking.py::TestMaskEmail::test_empty_string       PASSED
tests/test_masking.py::TestMaskPhone::test_kenyan_number      PASSED
tests/test_masking.py::TestMaskSSN::test_standard_ssn         PASSED
tests/test_masking.py::TestMaskName::test_full_name           PASSED
tests/test_masking.py::TestApplyMasking::test_masks_known_fields  PASSED
...
```

---

## CI/CD Pipeline

GitHub Actions runs automatically on every push and pull request:

| Job | What it checks |
|---|---|
| **Lambda Unit Tests** | All masking functions pass pytest |
| **Terraform Validate** | `terraform fmt` and `terraform validate` |
| **tfsec Security Scan** | Static analysis for IaC misconfigurations |

---

## Possible Extensions

- **Remote state** — add an S3 backend + DynamoDB state lock for team use
- **Encryption** — enable KMS CMK on the Kinesis stream and DynamoDB table
- **Dead-letter queue** — route failed Lambda records to an SQS DLQ
- **Monitoring** — CloudWatch alarms on Lambda error rate and iterator age
- **Schema validation** — JSON Schema check in Lambda before masking

---

## Tech Stack

![Terraform](https://img.shields.io/badge/Terraform-1.6+-7B42BC?logo=terraform&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-Python_3.12-FF9900?logo=awslambda&logoColor=white)
![Amazon Kinesis](https://img.shields.io/badge/Amazon_Kinesis-Data_Stream-FF9900?logo=amazonaws)
![DynamoDB](https://img.shields.io/badge/DynamoDB-On--Demand-FF9900?logo=amazondynamodb&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI-2088FF?logo=githubactions&logoColor=white)

---

## Author

Built as part of a hands-on cloud engineering portfolio to demonstrate Infrastructure as Code, serverless design patterns, and data privacy implementation on AWS.

---

## License

MIT
