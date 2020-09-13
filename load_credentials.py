
from common import *


def load_gsheets():
    gsheets = pygsheets.authorize(service_account_env_var='CREDENTIALS')

    return gsheets


def load_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(os.environ['CREDENTIALS']))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    return db
