"""Simple test handler to verify Vercel Python function works."""
def handler(event, context):
    """Minimal test handler."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Test handler works!", "event": ' + str(event) + '}'
    }

