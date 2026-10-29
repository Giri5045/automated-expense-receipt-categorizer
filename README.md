# Automated Expense Receipt Categorizer & Ledger

## Project Overview

The Automated Expense Receipt Categorizer & Ledger is a serverless cloud application designed to simplify expense tracking. When a receipt image is uploaded to Amazon S3, an AWS Lambda function processes it, categorizes the expense, and stores the resulting record in Amazon DynamoDB.

## Objectives

- Automate receipt-processing workflows.
- Categorize expenses into Food, Transport, Healthcare, Shopping, and Other.
- Store expense records in a cloud-based ledger.
- Reduce manual expense-entry effort.
- Demonstrate an event-driven AWS serverless architecture.

## System Architecture

**Amazon S3 → AWS Lambda → Amazon Textract → Amazon DynamoDB**

1. **Amazon S3:** Stores uploaded receipt images privately.
2. **AWS Lambda:** Automatically runs when a new receipt is uploaded.
3. **Amazon Textract:** Intended to extract text from receipt images.
4. **Amazon DynamoDB:** Stores the expense record, including merchant, date, category, source file, and processing details.

### Current Implementation Status

S3 upload triggering, Lambda execution, expense categorization, and DynamoDB storage have been tested successfully.

Amazon Textract currently returns `SubscriptionRequiredException` for this AWS account. A clearly labelled filename-based fallback is implemented so the remaining workflow can be demonstrated without upgrading the account. In fallback mode, merchant, date, and amount are read from the filename rather than recognized from the image.

Example filename:

`BurgerKing_2026-10-29_416.86.jpg`

This produces a demo record for BurgerKing, dated 2026-10-29, with a total of INR 416.86 and the category Food.

**Limitation:** Actual image OCR is not yet verified because of the Textract access error.

## Technology Stack

- Amazon S3
- AWS Lambda (Python)
- Amazon Textract
- Amazon DynamoDB
- AWS IAM
- Amazon CloudWatch
- GitHub

## Expense Categories

| Category | Example keywords |
|---|---|
| Food | Restaurant, cafe, burger, grocery |
| Transport | Uber, fuel, railway, metro |
| Healthcare | Pharmacy, hospital, clinic |
| Shopping | Amazon, electronics, stationery |
| Other | Expenses that do not match the above categories |

## Setup and Demonstration

1. Create a private S3 bucket.
2. Create a DynamoDB table named `ExpenseLedger` with partition key `receipt_id` of type String.
3. Create a Python AWS Lambda function named `ExpenseReceiptProcessor`.
4. Configure an S3 object-created event notification to invoke the Lambda function.
5. Configure the Lambda execution role with the necessary S3, Textract, DynamoDB, and CloudWatch permissions.
6. Deploy the Lambda code.
7. Upload a supported receipt image to the S3 bucket.
8. Inspect the saved expense record in DynamoDB.
9. Check Lambda logs in CloudWatch if processing fails.

## Future Enhancements

- Resolve Textract access and enable verified OCR processing.
- Improve merchant, date, and total extraction.
- Add a web dashboard for viewing expenses.
- Generate category-wise spending reports.
- Integrate with accounting platforms such as QuickBooks or Xero.

## Project Status

The core S3-triggered processing and DynamoDB ledger workflow is working. Actual receipt-image OCR remains pending resolution of the Textract account-access issue.
