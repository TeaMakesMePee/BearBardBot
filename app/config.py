import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

def get_secret(param_name: str, env_fallback: str) -> str:
    try:
        import boto3
        ssm = boto3.client("ssm", region_name="ap-southeast-1")
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except Exception as e:
        logger.warning(f"Could not read {param_name} from Parameter Store: {e}")
        value = os.environ.get(env_fallback)
        if not value:
            raise ValueError(f"No value for {param_name} or {env_fallback}")
        return value

BOT_TOKEN = get_secret("/bearbard/bot-token", "BOT_TOKEN")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "leveling")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "botuser")
POSTGRES_PASSWORD = get_secret("/bearbard/postgres-password", "POSTGRES_PASSWORD")

EXP_PER_MESSAGE = 10
EXP_COOLDOWN_SECONDS = 5

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Singapore")
