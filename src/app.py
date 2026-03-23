import json
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["TABLE_NAME"]
TOPIC_ARN = os.environ["TOPIC_ARN"]
LOG_BUCKET = os.environ["LOG_BUCKET"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
sns = boto3.client("sns")
s3 = boto3.client("s3")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def handler(event, context):
    try:
        http_method = event.get("requestContext", {}).get("http", {}).get("method")
        path_params = event.get("pathParameters") or {}
        order_id = path_params.get("id")

        if http_method != "PUT":
            return response(405, {"message": "Method Not Allowed"})

        if not order_id:
            return response(400, {"message": "Order ID is required in path"})

        raw_body = event.get("body")
        if not raw_body:
            return response(400, {"message": "Request body is empty"})

        body = json.loads(raw_body)
        new_status = body.get("status")

        if not new_status:
            return response(400, {"message": "Field 'status' is required"})

        now = datetime.utcnow().isoformat()

        update_result = table.update_item(
            Key={"id": order_id},
            UpdateExpression="SET #st = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":status": new_status,
                ":updated_at": now
            },
            ReturnValues="ALL_NEW"
        )

        item = update_result.get("Attributes", {})

        message = {
            "order_id": order_id,
            "status": new_status,
            "updated_at": now
        }

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"Order {order_id} status updated",
            Message=json.dumps(message, ensure_ascii=False)
        )

        log_key = f"orders/{order_id}/{now}.json"
        s3.put_object(
            Bucket=LOG_BUCKET,
            Key=log_key,
            Body=json.dumps({
                "event": "order_status_updated",
                "payload": message
            }, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json"
        )

        return response(200, {
            "message": "Status updated and notification sent",
            "notified": True,
            "item": item
        })

    except ClientError as e:
        print(f"AWS error: {str(e)}")
        return response(500, {"message": "AWS operation failed"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {"message": "Internal Server Error"})