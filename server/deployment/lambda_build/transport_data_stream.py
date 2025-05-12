import boto3
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

class TransportDataService:
    def __init__(self, table_name, sns_topic_arn):
        self.table = boto3.resource("dynamodb").Table(table_name)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.sns_client = boto3.client("sns")
        self.sns_topic_arn = sns_topic_arn

    # Save subscription record to DynamoDB
    def save_subscription_record(self, bus_route, stop_id, email, subscription_arn, email_status):
        try:
            self.table.put_item(Item={
                "email": email,
                "bus_route": bus_route,
                "stop_id": stop_id,
                "subscription_arn": subscription_arn,
                "email_status": email_status,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.logger.info(f"Saved subscription for {email} on route {bus_route}.")
        except Exception as e:
            self.logger.error(f"Error saving subscription for {email} on route {bus_route}: {e}")

    # Retrieve all subscriptions from DynamoDB
    def get_user_subscriptions(self):
        try:
            # Retrieve all subscriptions from DynamoDB
            response = self.table.scan()
            subscriptions = response.get("Items", [])
            
            # Log retrieved subscriptions for debugging purposes
            self.logger.info(f"Retrieved subscriptions: {subscriptions}")
            
            if not subscriptions:
                self.logger.warning("No subscriptions found in the database.")
            
            return subscriptions
        except Exception as e:
            self.logger.error(f"Error retrieving subscriptions: {e}")
            return []

    # Update the user's email address in the subscription
    def update_user_email(self, old_email, new_email):
        try:
            # Use scan with filter since email may not be the primary key
            response = self.table.scan(
                FilterExpression=Attr("email").eq(old_email)
            )
            items = response.get("Items", [])
            if not items:
                self.logger.warning(f"No records found for old email: {old_email}")
                return False

            for item in items:
                bus_route = item["bus_route"]
                stop_id = item.get("stop_id")
                old_arn = item.get("subscription_arn")

                # Unsubscribe old ARN
                if old_arn and old_arn != "PendingConfirmation":
                    self.unsubscribe_from_sns(old_arn)

                # Subscribe new email
                response = self.sns_client.subscribe(
                    TopicArn=self.sns_topic_arn,
                    Protocol="email",
                    Endpoint=new_email,
                    ReturnSubscriptionArn=True
                )
                new_arn = response.get("SubscriptionArn", "PendingConfirmation")

                # Set status to pending — manual email confirmation is required
                status = "pending"
                if new_arn == "PendingConfirmation":
                    self.logger.info(f"Subscription for {new_email} is pending confirmation. Please check your email.")
                else:
                    self.logger.info(f"Subscription ARN for {new_email}: {new_arn}")

                # Save new subscription record
                self.save_subscription_record(bus_route, stop_id, new_email, new_arn, status)

                # Delete old record from DynamoDB
                self.table.delete_item(Key={"email": item["email"], "bus_route": bus_route})

            return True
        except Exception as e:
            self.logger.error(f"Error updating email: {e}")
            return False

    # Unsubscribe the user from the SNS topic
    def unsubscribe_from_sns(self, subscription_arn):
        try:
            self.sns_client.unsubscribe(SubscriptionArn=subscription_arn)
            self.logger.info(f"Unsubscribed from SNS: {subscription_arn}")
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe ARN {subscription_arn}: {e}")

    # Delete the subscription record from DynamoDB
    def delete_subscription_record(self, email, route):
        try:
            self.table.delete_item(Key={"email": email, "bus_route": route})
            self.logger.info(f"Deleted subscription for {email} and route {route}.")
        except Exception as e:
            self.logger.error(f"Error deleting subscription for {email} and route {route}: {e}")