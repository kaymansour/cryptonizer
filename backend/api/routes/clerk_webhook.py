"""
Clerk Webhook Handler
Syncs Clerk authentication events with local SQLite database
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import json
import hmac
import hashlib

from database.models.users import (
    insert_user,
    update_user,
    delete_user,
    user_exists
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_clerk_webhook(payload: bytes, signature: str, webhook_secret: str) -> bool:
    """
    Verify Clerk webhook signature
    
    Args:
        payload: Raw request body
        signature: Svix signature from header
        webhook_secret: Clerk webhook secret
    
    Returns:
        True if signature is valid
    """
    # Clerk uses Svix for webhook signatures
    # The signature header contains multiple signatures, we need to verify one matches
    
    if not signature:
        return False
    
    # Parse signature header (format: v1,signature v1,signature2 ...)
    signatures = {}
    for sig in signature.split(" "):
        if "," in sig:
            version, sig_value = sig.split(",", 1)
            signatures[version] = sig_value
    
    # Get v1 signature
    expected_signature = signatures.get("v1")
    if not expected_signature:
        return False
    
    # Compute HMAC
    computed_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, expected_signature)


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None),
    svix_timestamp: Optional[str] = Header(None),
    svix_signature: Optional[str] = Header(None)
):
    """
    Handle Clerk webhook events
    
    Webhook events:
    - user.created: Create user in database
    - user.updated: Update user in database
    - user.deleted: Delete user from database
    
    Setup in Clerk Dashboard:
    1. Go to Webhooks
    2. Add endpoint: https://your-domain.com/api/webhooks/clerk
    3. Subscribe to: user.created, user.updated, user.deleted
    4. Copy the webhook secret to your .env file
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # TODO: Uncomment when you have CLERK_WEBHOOK_SECRET in environment
    # from core.config import settings
    # if not verify_clerk_webhook(body, svix_signature or "", settings.CLERK_WEBHOOK_SECRET):
    #     raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse the webhook payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = payload.get("type")
    data = payload.get("data", {})
    
    # Extract user information
    clerk_id = data.get("id")
    email_addresses = data.get("email_addresses", [])
    primary_email = next(
        (e["email_address"] for e in email_addresses if e.get("id") == data.get("primary_email_address_id")),
        email_addresses[0]["email_address"] if email_addresses else None
    )
    
    if not clerk_id or not primary_email:
        raise HTTPException(status_code=400, detail="Missing required user data")
    
    # Handle different event types
    try:
        if event_type == "user.created":
            # Extract user data from Clerk payload
            user_data = {
                "clerk_id": clerk_id,
                "email": primary_email,
                "username": data.get("username"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "profile_image_url": data.get("profile_image_url") or data.get("image_url"),
                "email_verified": any(e.get("verification", {}).get("status") == "verified" for e in email_addresses)
            }
            
            insert_user(**user_data)
            print(f"✓ User created: {clerk_id} ({primary_email})")
            
        elif event_type == "user.updated":
            # Update user data
            update_data = {
                "clerk_id": clerk_id,
                "email": primary_email,
                "username": data.get("username"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "profile_image_url": data.get("profile_image_url") or data.get("image_url"),
                "email_verified": any(e.get("verification", {}).get("status") == "verified" for e in email_addresses)
            }
            
            # Check if user exists, create if not (in case webhook was missed)
            if not user_exists(clerk_id):
                insert_user(**update_data)
                print(f"✓ User created (from update event): {clerk_id}")
            else:
                update_user(**update_data)
                print(f"✓ User updated: {clerk_id}")
            
        elif event_type == "user.deleted":
            # Delete user
            if delete_user(clerk_id):
                print(f"✓ User deleted: {clerk_id}")
            else:
                print(f"⚠ User not found for deletion: {clerk_id}")
        
        else:
            print(f"⚠ Unhandled event type: {event_type}")
    
    except Exception as e:
        print(f"❌ Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return {"success": True, "event": event_type}


@router.get("/clerk/test")
async def test_webhook():
    """
    Test endpoint to verify webhook route is accessible
    """
    return {
        "status": "ok",
        "message": "Clerk webhook endpoint is ready",
        "endpoint": "/api/webhooks/clerk"
    }
