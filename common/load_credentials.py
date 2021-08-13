
from .common import *


def load_gsheets():
    gsheets = pygsheets.authorize(service_account_env_var='CREDENTIALS')

    return gsheets


def load_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(os.environ['CREDENTIALS']))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    return db


def load_storage():
    cred = json.loads(os.environ['CREDENTIALS'])
    storage_client = storage.Client.from_service_account_info(cred)
    bucket = storage_client.get_bucket(f'{cred["project_id"]}.appspot.com')

    return bucket
