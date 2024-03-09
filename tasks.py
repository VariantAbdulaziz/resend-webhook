import uuid
from celery import Celery
from clickhouse_driver import Client
from datetime import date

# Set Redis as the broker
app = Celery('tasks', broker='redis://default:eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81@localhost:6379/0')
clickhouse_client = Client(host='localhost')


@app.task
def process_webhook_payload(payload):
    # Example payload processing; adapt based on actual payload structure
    event_id = payload.get('id', str(uuid.uuid4()))
    event_date = date.fromisoformat(payload.get('event_date', date.today().isoformat()))
    sender = payload.get('from')
    recipient = payload.get('to')
    status = payload.get('status')

    print(payload)
    # Convert payload to a string or structured form as needed for ClickHouse
    payload_str = str(payload)
    
    clickhouse_client.execute(
        "INSERT INTO resend_notifications (id, event_date, payload, sender, recipient, status) VALUES",
        [(event_id, event_date, payload_str, sender, recipient, status)]
    )
