#!/bin/bash
set -e

# Wait for the ClickHouse server to be ready
until clickhouse-client --host click_server --query "SELECT 1"; do
    >&2 echo "ClickHouse server is unavailable - sleeping"
    sleep 1
done

# Create database and table if they don't exist
clickhouse-client --host click_server --query "CREATE DATABASE IF NOT EXISTS default"
clickhouse-client --host click_server --query "CREATE TABLE IF NOT EXISTS default.resend_notifications (id UUID, event_date Date, sender String, recipient String, status String, payload String) ENGINE = MergeTree(event_date, (id), 8192)"

echo "Initialization completed."