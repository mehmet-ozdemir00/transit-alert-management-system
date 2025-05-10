import os
import json
import boto3
import logging
import re

from transit_alert_service import TransitAlertSystem
from transport_data_stream import TransportDataService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LambdaFunctionService:
    @staticmethod
    def response(status_code, body):
        return {
            "statusCode": status_code,
            "body": json.dumps(body) if isinstance(body, dict) else body,
            "headers": {"Content-Type": "application/json"}
        }

    @staticmethod
    def validate_user_route(user_id, route, stop_id):
        if not user_id or not isinstance(user_id, str):
            return "user_id is required and must be a string"
        if not route or not isinstance(route, str):
            return "route is required and must be a string"
        if not stop_id or not isinstance(stop_id, (str, int)):
            return "stop_id is required and must be a string or integer"
        return None

    @staticmethod
    def validate_email(email):
        if not email or not isinstance(email, str):
            return "email is required and must be a string"
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "email is not valid"
        return None

def lambda_handler(event, context):
    try:
        sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
        delay_threshold_minutes = int(os.environ.get("DELAY_THRESHOLD_MINUTES", "4"))
        vehicle_delay_threshold = int(os.environ.get("VEHICLE_DELAY_THRESHOLD", "5"))
        dynamodb_table_name = os.environ["DYNAMODB_TABLE_NAME"]
        max_subscriptions = int(os.environ.get("MAX_SUBSCRIPTIONS", "5"))
        max_retries = int(os.environ.get("MAX_RETRIES", "3"))
        retry_delay = int(os.environ.get("RETRY_DELAY", "5"))

        data_service = TransportDataService(dynamodb_table_name)
        alert_system = TransitAlertSystem(
            sns_client=boto3.client("sns"),
            sns_topic_arn=sns_topic_arn,
            delay_threshold_minutes=delay_threshold_minutes,
            vehicle_delay_threshold=vehicle_delay_threshold,
            data_service=data_service,
            max_subscriptions=max_subscriptions,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        # For now, fallback to a fixed user (or extract from query param/header if needed)
        user_id = "anonymous"

        http_method = event.get("httpMethod", "").upper()
        path = event.get("path", "").lower()

        if http_method == "POST" and path == "/subscribe":
            body = json.loads(event.get("body", "{}")) if event.get("body") else {}
            route = body.get("route")
            stop_id = body.get("stop_id")
            email = body.get("email")

            error = LambdaFunctionService.validate_user_route(user_id, route, stop_id)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            error = LambdaFunctionService.validate_email(email)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            if not alert_system.check_subscription_limit(user_id):
                return LambdaFunctionService.response(403, {"error": "Subscription limit reached."})

            result = alert_system.subscribe_user_to_sns(email, user_id, route, stop_id)
            if result:
                return LambdaFunctionService.response(200, {"message": "Subscription request sent. Please confirm your email."})
            else:
                return LambdaFunctionService.response(500, {"error": "Failed to subscribe the user to SNS."})

        elif http_method == "GET" and path == "/status":
            result = alert_system.get_user_status(user_id)
            return LambdaFunctionService.response(200, {"subscriptions": result})

        elif http_method == "GET" and path == "/delay":
            route = event.get("queryStringParameters", {}).get("route")
            if not route:
                return LambdaFunctionService.response(400, {"error": "Missing required query parameter: route"})
            alert_system.check_vehicle_delay(route)
            return LambdaFunctionService.response(200, {"message": f"Checked vehicle delay for route {route}. No significant delays detected at this time."})

        elif http_method == "GET" and path == "/prediction":
            query_params = event.get("queryStringParameters") or {}
            route = query_params.get("route")
            stop_id = query_params.get("stop_id")

            error = LambdaFunctionService.validate_user_route(user_id, route, stop_id)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            prediction = alert_system.get_prediction(route, stop_id)
            if prediction is None or "message" in prediction:
                return LambdaFunctionService.response(404, {"error": prediction.get("message", "No prediction data found")})

            data_service.log_prediction(user_id, route, stop_id, prediction)
            return LambdaFunctionService.response(200, prediction)

        elif http_method == "GET" and path == "/cancelled":
            cancelled_routes, active_routes = alert_system.get_cancelled_routes()
            if cancelled_routes is None:
                return LambdaFunctionService.response(404, {"error": "No cancelled routes found."})
            return LambdaFunctionService.response(200, {
                "cancelled_routes": cancelled_routes,
                "active_routes": active_routes,
                "count_cancelled": len(cancelled_routes),
                "count_active": len(active_routes),
                "message": "Cancelled and active routes retrieved successfully."
            })

        elif http_method == "PUT" and path == "/email":
            body = json.loads(event.get("body", "{}")) if event.get("body") else {}
            new_email = body.get("new_email")

            error = LambdaFunctionService.validate_email(new_email)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            result = alert_system.update_subscription_email(user_id, new_email)
            if result:
                return LambdaFunctionService.response(200, {"message": "Email updated successfully."})
            else:
                return LambdaFunctionService.response(500, {"error": "Failed to update email."})

        elif http_method == "DELETE" and path == "/unsubscribe":
            body = json.loads(event.get("body", "{}")) if event.get("body") else {}
            email = body.get("email")
            if not email:
                return LambdaFunctionService.response(400, {"error": "Email is required"})

            success = alert_system.unsubscribe_email_from_sns(email)
            if success:
                return LambdaFunctionService.response(200, {"message": f"{email} has been successfully unsubscribed from alerts."})
            else:
                return LambdaFunctionService.response(404, {"error": f"No active subscription found for {email}."})

        elif http_method == "DELETE" and path == "/subscription":
            query_params = event.get("queryStringParameters", {})
            route = query_params.get("route")
            if not route:
                return LambdaFunctionService.response(400, {"error": "Missing required query parameter: route"})

            deleted = alert_system.delete_dynamodb_only_subscription(user_id, route)
            if deleted:
                return LambdaFunctionService.response(200, {"message": "Subscription removed successfully from DynamoDB."})
            else:
                return LambdaFunctionService.response(404, {"error": f"No subscription found for route {route}."})

        else:
            return LambdaFunctionService.response(404, {"error": "Route not found"})

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return LambdaFunctionService.response(500, {"error": str(e)})