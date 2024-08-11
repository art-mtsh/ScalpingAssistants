import firebase_admin
from firebase_admin import credentials, db

# Path to your service account key file
SERVICE_ACCOUNT_KEY = 'tgbots-8fc9c-firebase-adminsdk-d19h9-c54020bf1d.json'

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://tgbots-8fc9c-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Reference to your Realtime Database
ref = db.reference('chat_ids')

def get_existed_chat_ids():
    return ref.get() or []

def save_new_chat_id(new_chat_id=None):
    existed_chat_ids = get_existed_chat_ids()
    if new_chat_id and new_chat_id not in existed_chat_ids:
        existed_chat_ids.append(new_chat_id)
    ref.set(existed_chat_ids)

