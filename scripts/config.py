"""Configuração compartilhada: lê o .env da raiz do projeto e monta os clientes do Google."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

KEY_PATH = str(ROOT / os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
MCC_ID = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
ADS_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v25")
GA_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def ads_client():
    from google.ads.googleads.client import GoogleAdsClient

    # Sem developer_token: descontinuado em 09/09/2026 (acesso agora é por projeto do Cloud).
    return GoogleAdsClient.load_from_dict(
        {
            "json_key_file_path": KEY_PATH,
            "login_customer_id": MCC_ID,
            "use_proto_plus": True,
        },
        version=ADS_VERSION,
    )


def ga_credentials():
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_file(KEY_PATH, scopes=GA_SCOPES)
