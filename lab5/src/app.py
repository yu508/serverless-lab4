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
translate = boto3.client("translate", region_name="eu-central-1")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def get_http_method(event):
    return event.get("requestContext", {}).get("http", {}).get("method")


def get_raw_path(event):
    return event.get("rawPath", "")


def get_order_id(event):
    path_params = event.get("pathParameters") or {}
    return path_params.get("id")


def get_query_lang(event):
    query_params = event.get("queryStringParameters") or {}
    return query_params.get("lang", "en")


def parse_body(event):
    raw_body = event.get("body")
    if not raw_body:
        return {}
    return json.loads(raw_body)


def log_to_s3(key_prefix, payload):
    timestamp = datetime.utcnow().isoformat()
    key = f"{key_prefix}/{timestamp}.json"

    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json"
    )


def update_order_status(order_id, new_status):
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

    log_to_s3(
        key_prefix=f"orders/{order_id}",
        payload={
            "event": "order_status_updated",
            "order_id": order_id,
            "new_status": new_status,
            "updated_at": now
        }
    )

    return item


def get_order(order_id):
    result = table.get_item(Key={"id": order_id})
    return result.get("Item")


def translate_notification_text(source_text, target_lang):
    try:
        result = translate.translate_text(
            Text=source_text,
            SourceLanguageCode="en",
            TargetLanguageCode=target_lang
        )
        return result.get("TranslatedText", source_text)
    except Exception as e:
        print(f"Translate error: {str(e)}")
        return source_text


def notify_order(order_id, lang):
    item = get_order(order_id)

    if not item:
        return response(404, {"message": "Замовлення не знайдено"})

    status = item.get("status", "unknown")
    source_text = f"Your order #{order_id} status has been updated to {status}."

    translated_text = translate_notification_text(source_text, lang)

    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=f"Order {order_id} notification",
        Message=translated_text
    )

    now = datetime.utcnow().isoformat()

    table.update_item(
        Key={"id": order_id},
        UpdateExpression=(
            "SET translated_notification = :translated_notification, "
            "notification_lang = :notification_lang, "
            "notification_sent_at = :notification_sent_at"
        ),
        ExpressionAttributeValues={
            ":translated_notification": translated_text,
            ":notification_lang": lang,
            ":notification_sent_at": now
        }
    )

    log_to_s3(
        key_prefix=f"notifications/{order_id}",
        payload={
            "event": "translated_notification_sent",
            "order_id": order_id,
            "language": lang,
            "source_text": source_text,
            "translated_notification": translated_text,
            "notification_sent_at": now
        }
    )

    return response(200, {
        "message": "Сповіщення перекладено та надіслано",
        "order_id": order_id,
        "language": lang,
        "translated_notification": translated_text
    })


def handler(event, context):
    try:
        http_method = get_http_method(event)
        raw_path = get_raw_path(event)
        order_id = get_order_id(event)

        if http_method != "PUT":
            return response(405, {"message": "Метод не дозволено"})

        if not order_id:
            return response(400, {"message": "Не вказано order id"})

        if raw_path.endswith(f"/orders/{order_id}/status"):
            body = parse_body(event)
            new_status = body.get("status")

            if not new_status:
                return response(400, {"message": "Поле 'status' є обов'язковим"})

            item = update_order_status(order_id, new_status)

            return response(200, {
                "message": "Статус замовлення успішно оновлено",
                "item": item
            })

        if raw_path.endswith(f"/orders/{order_id}/notify"):
            lang = get_query_lang(event)
            return notify_order(order_id, lang)

        return response(404, {"message": "Not Found"})

    except ClientError as e:
        print(f"AWS error: {str(e)}")
        return response(500, {"message": "Помилка AWS"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {"message": "Внутрішня помилка сервера"})