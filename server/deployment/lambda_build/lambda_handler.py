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
    def validate_user_route(route, stop_id):
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

    logger.info("Lambda function triggered")
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Load environment variables
        sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
        dynamodb_table_name = os.environ["DYNAMODB_TABLE_NAME"]
        delay_threshold_minutes = int(os.environ.get("DELAY_THRESHOLD_MINUTES", "4"))
        vehicle_delay_threshold = int(os.environ.get("VEHICLE_DELAY_THRESHOLD", "5"))
        max_subscriptions = int(os.environ.get("MAX_SUBSCRIPTIONS", "5"))
        max_retries = int(os.environ.get("MAX_RETRIES", "3"))
        retry_delay = int(os.environ.get("RETRY_DELAY", "5"))

        # Initialize services
        data_service = TransportDataService(dynamodb_table_name, sns_topic_arn)
        alert_system = TransitAlertSystem(
            sns_client=boto3.client("sns"),
            sns_topic_arn=sns_topic_arn,
            data_service=data_service,
            delay_threshold_minutes=delay_threshold_minutes,
            vehicle_delay_threshold=vehicle_delay_threshold,
            max_subscriptions=max_subscriptions,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        http_method = event.get("httpMethod", "").upper()
        path = event.get("path", "").lower()

        # Post request to subscribe user
        if http_method == "POST" and path == "/subscribe":
            body = json.loads(event.get("body", "{}"))
            route = body.get("route")
            stop_id = body.get("stop_id")
            email = body.get("email")

            error = LambdaFunctionService.validate_user_route(route, stop_id)
            if error:
                return LambdaFunctionService.response(400, {"error": error})
            error = LambdaFunctionService.validate_email(email)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            if not alert_system.check_subscription_limit(email):
                return LambdaFunctionService.response(403, {"error": "Subscription limit reached."})

            success = alert_system.subscribe_user_to_sns(email, route, stop_id)
            if success:
                return LambdaFunctionService.response(200, {"message": "Subscription request sent. Please confirm your email."})
            else:
                return LambdaFunctionService.response(500, {"error": "Failed to subscribe user."})

        # Get request to check user status
        elif http_method == "GET" and path == "/status":
            subscriptions = alert_system.get_user_status()
            return LambdaFunctionService.response(200, {"subscriptions": subscriptions})

        # Put request to update user email
        elif http_method == "PUT" and path == "/update":
            body = json.loads(event.get("body", "{}"))
            old_email = body.get("old_email")
            new_email = body.get("new_email")

            if not old_email:
                return LambdaFunctionService.response(400, {"error": "old_email is required"})

            if not new_email:
                return LambdaFunctionService.response(400, {"error": "new_email is required"})
            
            error = LambdaFunctionService.validate_email(new_email)
            if error:
                return LambdaFunctionService.response(400, {"error": error})

            success = alert_system.update_subscription_email(old_email, new_email)
            if success:
                return LambdaFunctionService.response(200, {"message": "Email updated successfully."})
            else:
                return LambdaFunctionService.response(500, {"error": "Failed to update email."})

        # Delete request to unsubscribe user
        elif http_method == "DELETE" and path == "/unsubscribe":
            body = json.loads(event.get("body", "{}"))
            email = body.get("email")
            if not email:
                return LambdaFunctionService.response(400, {"error": "Email is required"})

            success = alert_system.unsubscribe_email_from_sns(email)
            if success:
                return LambdaFunctionService.response(200, {"message": f"{email} successfully unsubscribed."})
            else:
                return LambdaFunctionService.response(404, {"error": f"No active subscription found for {email}."})

        # Delete request to delete subscription from DynamoDB
        elif http_method == "DELETE" and path == "/subscription":
            # Read the body of the request
            body = json.loads(event.get("body", "{}"))
            
            # Get the email from the request body
            email = body.get("email")
            
            # Get the route from query parameters
            query_params = event.get("queryStringParameters", {})
            route = query_params.get("route")
            
            # If route or email is missing, return an error response
            if not route or not email:
                return LambdaFunctionService.response(400, {"error": "Missing route or email"})
            
            # Attempt to delete the subscription from DynamoDB
            deleted = alert_system.delete_dynamodb_only_subscription(email, route)

            if deleted:
                return LambdaFunctionService.response(200, {"message": "Subscription deleted from DynamoDB."})
            else:
                return LambdaFunctionService.response(404, {"error": f"No subscription found for route {route}."})

        else:
            return LambdaFunctionService.response(404, {"error": "Endpoint not found"})

    # Handle any exceptions that occur during the execution
    except Exception as e:
        logger.error(f"Lambda execution error: {e}")
        return LambdaFunctionService.response(500, {"error": "Internal server error"})