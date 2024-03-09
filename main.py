from datetime import date
import json
from clickhouse_driver import Client
from fastapi import FastAPI, HTTPException, Request
from typing import Optional, List

import redis


from tasks import process_webhook_payload

app = FastAPI()
clickhouse_client = Client(host='localhost')
redis_client = redis.from_url("redis://default:eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81@localhost:6379/0")

# Include other imports and configurations as necessary
@app.post("/webhook/resend")
async def receive_resend_notification(request: Request):
    payload = await request.json()
    process_webhook_payload.delay(payload)  # Forward payload to Celery for processing
    return {"status": "received"}




@app.get("/query/email-events")
async def query_email_events(
    sender: str,
    recipient: Optional[str] = None,
    status: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None
):
    # Generate a unique cache key based on function parameters to identify the cached results.
    cache_key = f"email_events:{sender}:{recipient}:{status}:{date_start}:{date_end}"
    
    # Attempt to fetch the result from Redis cache using the generated key.
    cached_result = redis_client.get(cache_key)
    if cached_result:
        # If a cached result is found, return it immediately without querying the database.
        return {"data": json.loads(cached_result)}
    
    # Build the SQL query dynamically, starting with a base query.
    query = "SELECT id, event_date, sender, recipient, status, payload FROM resend_notifications WHERE sender = %(sender)s"
    query_params = {"sender": sender}

    # Append optional filters to the query if they are provided.
    if recipient:
        query += " AND recipient = %(recipient)s"
        query_params["recipient"] = recipient

    if status:
        query += " AND status = %(status)s"
        query_params["status"] = status

    if date_start:
        query += " AND event_date >= %(date_start)s"
        query_params["date_start"] = str(date_start)

    if date_end:
        query += " AND event_date <= %(date_end)s"
        query_params["date_end"] = str(date_end)

    try:
        # Execute the query with the dynamically built conditions.
        records = clickhouse_client.execute(query, query_params)
        # Process the records into a list of dictionaries for JSON serialization.
        results = [{
            "id": str(record[0]),
            "event_date": record[1].isoformat(),
            "sender": record[2],
            "recipient": record[3],
            "status": record[4],
            "full_payload": record[5]
        } for record in records]

        # Cache the query results in Redis with an expiration time of 1 hour.
        redis_client.set(cache_key, json.dumps(results), ex=3600)
        return {"data": results}
    except Exception as e:
        # Handle exceptions from the database query, such as connectivity issues or syntax errors.
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
