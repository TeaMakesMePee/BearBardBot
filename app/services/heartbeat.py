import boto3
import logging

logger = logging.getLogger(__name__)

def send_heartbeat():
    """Push a heartbeat metric to CloudWatch."""
    try:
        cloudwatch = boto3.client("cloudwatch", region_name="ap-southeast-1")
        cloudwatch.put_metric_data(
            Namespace="BearBard",
            MetricData=[
                {
                    "MetricName": "BotHeartbeat",
                    "Value": 1,
                    "Unit": "Count"
                }
            ]
        )
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {e}")
