"""Vercel serverless function handler for FastAPI app."""

import sys
import traceback

try:
    from mangum import Mangum
    from app.main import app

    # Create ASGI handler for Vercel
    # lifespan="off" because Vercel handles serverless lifecycle
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Log initialization errors for debugging
    error_msg = f"Failed to initialize handler: {e}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    
    # Create a minimal error handler
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": f"Initialization error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

