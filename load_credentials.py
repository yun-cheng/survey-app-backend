
from common import *


# TODO 移到設定
def load_credentials():
    with open('credentials.json', 'r') as file:
        credentials_dict = json.load(file)
    os.environ['CREDENTIALS'] = str(json.dumps(credentials_dict))


def load_gsheets():
    gsheets = pygsheets.authorize(service_account_env_var='CREDENTIALS')

    return gsheets


def load_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(os.environ['CREDENTIALS']))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    return db