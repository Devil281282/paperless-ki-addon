import os
import time
import requests

PAPERLESS_URL = os.getenv("PAPERLESS_URL")
PAPERLESS_TOKEN = os.getenv("PAPERLESS_TOKEN")
HA_WEBHOOK_URL = os.getenv("HA_WEBHOOK_URL")
HEADERS = {"Authorization": f"Token {PAPERLESS_TOKEN}"}

CHECK_INTERVAL = 60
last_seen_id = None

def get_latest_document():
    r = requests.get(f"{PAPERLESS_URL}/api/documents/?ordering=-created&limit=1", headers=HEADERS)
    r.raise_for_status()
    return r.json()["results"][0]

def get_document_text(doc_id):
    r = requests.get(f"{PAPERLESS_URL}/api/documents/{doc_id}/content/", headers=HEADERS)
    r.raise_for_status()
    return r.text

def send_to_chatgpt(doc_text):
    return {
        "title": "Vodafone Mobilfunkrechnung März 2024",
        "document_type": 1,
        "tags": [2, 5]
    }

def update_document(doc_id, data):
    payload = {
        "title": data["title"],
        "tags": data["tags"],
        "document_type": data["document_type"]
    }
    r = requests.patch(f"{PAPERLESS_URL}/api/documents/{doc_id}/", headers=HEADERS, json=payload)
    r.raise_for_status()

def send_notification(message):
    if HA_WEBHOOK_URL:
        requests.post(HA_WEBHOOK_URL, json={"message": message})

while True:
    try:
        doc = get_latest_document()
        if doc["id"] != last_seen_id:
            print(f"Neues Dokument: {doc['title']}")
            text = get_document_text(doc["id"])
            analysis = send_to_chatgpt(text)
            update_document(doc["id"], analysis)
            send_notification(f"Dokument analysiert: {analysis['title']}")
            last_seen_id = doc["id"]
    except Exception as e:
        print(f"Fehler: {e}")
    time.sleep(CHECK_INTERVAL)
