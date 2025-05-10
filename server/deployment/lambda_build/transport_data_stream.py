import boto3
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Key

class TransportDataService:
    def __init__(self, table_name):
        self.table = boto3.resource("dynamodb").Table(table_name)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.sns_client = boto3.client("sns")
        self.sns_topic_arn = "arn:aws:sns:us-east-1:851725323729:TransitAlertTopic"

    def log_prediction(self, bus_route, stop_id, prediction):
        try:
            required_keys = {"minutes_away", "stops_away", "arrival_time", "miles_away"}
            if not required_keys.issubset(prediction.keys()):
                self.logger.error(f"Prediction data missing required keys: {required_keys}")
                return

            self.logger.info(f"Updating prediction for route {bus_route} with stop_id {stop_id}")

            response = self.table.update_item(
                Key={"bus_route": bus_route},
                UpdateExpression="""
                    SET
                        stop_id = :stop_id,
                        minutes_away = :minutes,
                        stops_away = :stops,
                        miles_away = :miles,
                        arrival_time = :arrival,
                        #ts = :timestamp
                """,
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":stop_id": stop_id,
                    ":minutes": prediction["minutes_away"],
                    ":stops": prediction["stops_away"],
                    ":miles": prediction["miles_away"],
                    ":arrival": prediction["arrival_time"],
                    ":timestamp": datetime.utcnow().isoformat()
                }
            )
            self.logger.info(f"Successfully updated prediction for {bus_route}: {response}")
        except Exception as e:
            self.logger.error(f"Error logging prediction for route {bus_route}: {e}")

    def get_user_subscriptions(self):
        try:
            response = self.table.scan()
            return [
                item for item in response.get("Items", [])
                if "bus_route" in item and item["bus_route"] != "email"
            ]
        except Exception as e:
            self.logger.error(f"Error getting subscriptions: {e}")
            return []

    def get_user_subscription_arn(self, bus_route):
        try:
            response = self.table.get_item(Key={"bus_route": bus_route})
            item = response.get("Item")
            return item.get("subscription_arn") if item else None
        except Exception as e:
            self.logger.error(f"Error fetching ARN for route {bus_route}: {e}")
            return None

    def get_sns_subscriptions_by_email(self, email):
        try:
            response = self.sns_client.list_subscriptions_by_topic(TopicArn=self.sns_topic_arn)
            subscriptions = response.get("Subscriptions", [])
            matched_subs = [
                sub for sub in subscriptions
                if sub.get("Endpoint") == email and sub.get("SubscriptionArn") != "PendingConfirmation"
            ]
            return matched_subs
        except Exception as e:
            self.logger.error(f"Error fetching SNS subscriptions for email {email}: {e}")
            return []

    def get_all_unique_routes(self):
        try:
            response = self.table.scan(ProjectionExpression="bus_route")
            items = response.get("Items", [])
            return list(set(item["bus_route"] for item in items if "bus_route" in item))
        except Exception as e:
            self.logger.error(f"Error fetching unique routes: {e}")
            return []

    def unsubscribe_from_sns(self, subscription_arn):
        try:
            self.sns_client.unsubscribe(SubscriptionArn=subscription_arn)
            self.logger.info(f"Unsubscribed from SNS: {subscription_arn}")
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe ARN {subscription_arn}: {e}")

    def update_user_email(self, new_email):
        try:
            response = self.table.scan()
            items = response.get("Items", [])

            for item in items:
                old_arn = item.get("subscription_arn")
                bus_route = item.get("bus_route")

                if old_arn:
                    try:
                        self.sns_client.unsubscribe(SubscriptionArn=old_arn)
                    except Exception as e:
                        self.logger.warning(f"Failed to unsubscribe old ARN {old_arn}: {e}")

                try:
                    sns_response = self.sns_client.subscribe(
                        TopicArn=self.sns_topic_arn,
                        Protocol="email",
                        Endpoint=new_email,
                        ReturnSubscriptionArn=True
                    )
                    new_arn = sns_response.get("SubscriptionArn", "pending_confirmation")
                except Exception as e:
                    self.logger.error(f"Failed to subscribe new email {new_email}: {e}")
                    new_arn = None

                update_expression = "SET email = :email, email_status = :status"
                expression_values = {
                    ":email": new_email,
                    ":status": "pending_confirmation"
                }

                if new_arn:
                    update_expression += ", subscription_arn = :arn"
                    expression_values[":arn"] = new_arn

                self.table.update_item(
                    Key={"bus_route": bus_route},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating email and re-subscribing: {e}")
            return False

    def delete_subscription_record(self, route):
        try:
            self.table.delete_item(Key={"bus_route": route})
            self.logger.info(f"Deleted subscription for route {route}")
        except Exception as e:
            self.logger.error(f"Error deleting subscription for route {route}: {e}")
            raise

    def save_subscription_record(self, bus_route, stop_id, email, subscription_arn, email_status):
        try:
            self.table.put_item(Item={
                "bus_route": bus_route,
                "stop_id": stop_id,
                "email": email,
                "subscription_arn": subscription_arn,
                "email_status": email_status,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            self.logger.error(f"Error saving subscription for route {bus_route}: {e}")