
import json
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

textract = boto3.client("textract")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = "ExpenseLedger"


def categorize_expense(text):
    text = text.lower()

    if any(word in text for word in [
        "restaurant", "cafe", "food", "burger", "pizza",
        "swiggy", "zomato", "grocery", "supermarket"
    ]):
        return "Food"

    if any(word in text for word in [
        "uber", "ola", "petrol", "fuel", "transport",
        "railway", "metro", "parking"
    ]):
        return "Transport"

    if any(word in text for word in [
        "pharmacy", "hospital", "medical", "clinic"
    ]):
        return "Healthcare"

    if any(word in text for word in [
        "amazon", "electronics", "computer", "stationery"
    ]):
        return "Shopping"

    return "Other"


def lambda_handler(event, context):
    results = []
    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        filename = key.rsplit("/", 1)[-1]
        stem = filename.rsplit(".", 1)[0]

        try:
            response = textract.detect_document_text(
                Document={
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": key
                    }
                }
            )

            lines = [
                block["Text"]
                for block in response.get("Blocks", [])
                if block.get("BlockType") == "LINE"
            ]
            full_text = "\n".join(lines)
            extraction_method = "Amazon Textract"

        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")

            if code != "SubscriptionRequiredException":
                raise

            # Transparent demo fallback: fields come from the filename.
            # Example: BurgerKing_2026-10-29_416.86.jpg
            parts = stem.split("_")
            merchant = parts[0].replace("-", " ")
            date = None
            total = None

            for part in parts[1:]:
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part):
                    date = part
                elif re.fullmatch(r"\d+(?:\.\d{1,2})?", part):
                    total = Decimal(part)

            lines = [merchant]
            full_text = f"Demo fallback from filename: {stem}"
            if total is not None:
                full_text += f"\nTotal: INR {total}"

            extraction_method = "Filename demo fallback"

        if extraction_method == "Amazon Textract":
            merchant = lines[0] if lines else "Unknown"
            date = None
            total = None

            for line in lines:
                if re.search(
                    r"\b(total|amount due|grand total)\b",
                    line, re.IGNORECASE
                ):
                    match = re.search(
                        r"(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
                        line, re.IGNORECASE
                    )
                    if match:
                        total = Decimal(
                            match.group(1).replace(",", "")
                        )

                match_date = re.search(
                    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                    line
                )
                if match_date and date is None:
                    date = match_date.group(1)

        category = categorize_expense(
            merchant + " " + full_text + " " + key
        )

        item = {
            "receipt_id": str(uuid.uuid4()),
            "merchant": merchant,
            "date": date or "Unknown",
            "category": category,
            "currency": "INR",
            "source_bucket": bucket,
            "source_key": key,
            "extracted_text": full_text,
            "extraction_method": extraction_method,
            "processed_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        if total is not None:
            item["total"] = total

        table.put_item(Item=item)

        results.append({
            "receipt_id": item["receipt_id"],
            "merchant": merchant,
            "date": item["date"],
            "total": str(total) if total is not None else None,
            "category": category,
            "extraction_method": extraction_method
        })

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
