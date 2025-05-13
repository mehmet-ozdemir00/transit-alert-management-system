import logging
import re

class TransitAlertSystem:
    def __init__(self, sns_client, sns_topic_arn, data_service, max_subscriptions, 
            delay_threshold_minutes=4, vehicle_delay_threshold=5, 
            max_retries=3, retry_delay=5):
        self.sns_client = sns_client
        self.sns_topic_arn = sns_topic_arn
        self.data_service = data_service
        self.max_subscriptions = max_subscriptions
        self.delay_threshold_minutes = delay_threshold_minutes
        self.vehicle_delay_threshold = vehicle_delay_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    # Validate the email format
    def is_valid_email(self, email):
        return isinstance(email, str) and re.match(r"[^@]+@[^@]+\.[^@]+", email)

    # Check if the user has reached the maximum number of subscriptions
    def check_subscription_limit(self, email):
        user_subscriptions = [
            sub for sub in self.data_service.get_user_subscriptions()
            if sub.get("email") == email
        ]
        return len(user_subscriptions) < self.max_subscriptions

    # Subscribe the user to the SNS topic
    def subscribe_user_to_sns(self, email, bus_route, stop_id):
        if not self.is_valid_email(email):
            self.logger.warning("Invalid email format")
            return False
        if not self.check_subscription_limit(email):
            self.logger.warning("Max subscription limit reached")
            return False
        try:
            response = self.sns_client.subscribe(
                TopicArn=self.sns_topic_arn,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True
            )
            arn = response.get("SubscriptionArn")
            status = "confirmed" if arn and arn != "PendingConfirmation" else "pending"

            self.data_service.save_subscription_record(
                bus_route=bus_route,
                stop_id=stop_id,
                email=email,
                subscription_arn=arn,
                email_status=status
            )

            if status == "confirmed":
                self.send_notification("You're subscribed to Transit Alerts!", subject="Subscription Confirmed")

            return True
        except Exception as e:
            self.logger.error(f"Error subscribing to SNS: {e}")
            return False

    # Send a notification to the user
    def send_notification(self, message, subject):
        try:
            self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Message=message,
                Subject=subject
            )
            self.logger.info(f"Notification sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")

    # Check the user's subscription status and send alerts if necessary
    def get_user_status(self):
        try:
            subscriptions = self.data_service.get_user_subscriptions()
            
            for sub in subscriptions:
                if sub.get("email_status") == "confirmed":
                    email = sub.get("email")
                    route = sub.get("bus_route")
                    message = (
                        f"⚠️ [ALERT] 🚍\n\n"
                        f"Dear Rider,\n\n"
                        f"We wanted to inform you of a service delay affecting your subscribed bus route.\n"
                        f"There is an anticipated **15-minute delay** on **Route {route}**.\n\n"
                        f"We recommend allowing extra travel time and adjusting your plans accordingly.\n\n"
                        f"Thank you for staying informed with PADCOM Transit Alerts.\n\n"
                        f"Best regards,\n"
                        f"──────────\n📬 The PADCOM Transit Alert Team"
                    )
                    self.send_notification(message, subject=f"Delay Alert for Route {route}")

            return subscriptions
        except Exception as e:
            self.logger.error(f"Error retrieving subscriptions: {e}")
            return []

    # Update the user's email address in the subscription
    def update_subscription_email(self, old_email, new_email):
        try:
            # Log the old and new email values
            self.logger.info(f"Attempting to update subscription for {old_email} to {new_email}")

            # Retrieve all subscriptions
            subscriptions = self.data_service.get_user_subscriptions()

            for sub in subscriptions:
                # Find the subscription that matches the old email
                if sub.get("email") == old_email:
                    self.logger.info(f"Found subscription for {old_email}")

                    # Proceed to update the subscription
                    return self.data_service.update_user_email(old_email, new_email)

            self.logger.warning(f"No subscription found for the old email: {old_email}")
            return False

        except Exception as e:
            self.logger.error(f"Error updating email: {e}")
            return False

    # Unsubscribe the user from the SNS topic
    def unsubscribe_email_from_sns(self, email):
        try:
            response = self.sns_client.list_subscriptions_by_topic(TopicArn=self.sns_topic_arn)
            for subscription in response.get("Subscriptions", []):
                if subscription.get("Endpoint") == email:
                    arn = subscription.get("SubscriptionArn")
                    if arn and arn != "PendingConfirmation":
                        self.sns_client.unsubscribe(SubscriptionArn=arn)
                        self.logger.info(f"Unsubscribed {email} from SNS")
                        return True
            self.logger.info(f"No confirmed subscription found for {email}")
            return False
        except Exception as e:
            self.logger.error(f"Error unsubscribing {email}: {e}")
            return False

    # Delete the subscription record from DynamoDB
    def delete_dynamodb_only_subscription(self, email, route):
        try:
            # Delete the subscription from DynamoDB using email and route
            self.data_service.delete_subscription_record(email, route)
            self.logger.info(f"Deleted subscription record for {email} on route {route}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting {email} / {route} from DynamoDB: {e}")
            return False