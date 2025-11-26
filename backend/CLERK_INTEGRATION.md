# Clerk Webhook Integration Setup

## ✅ What's Been Set Up

1. **SQLite Users Table** (`database/models/users.py`)
   - Stores Clerk user data
   - Fields: clerk_id, email, username, first_name, last_name, profile_image_url, email_verified
   - Automatic timestamps (created_at, updated_at)

2. **Webhook Endpoint** (`api/routes/clerk_webhook.py`)
   - Endpoint: `POST /webhooks/clerk`
   - Handles: user.created, user.updated, user.deleted events
   - Auto-syncs with local database

3. **Database Integration** (`main.py`)
   - Database initialized on server startup
   - Webhook route registered

## 🚀 Setup Instructions

### 1. Test Database Setup

```bash
cd /home/weed/senior/backend
python3 database/models/users.py
```

This will create the users table and run tests.

### 2. Configure Clerk Webhook (in Clerk Dashboard)

1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Navigate to **Webhooks** section
3. Click **Add Endpoint**
4. Set URL: `https://your-domain.com/webhooks/clerk`
   - For local testing: `http://localhost:8000/webhooks/clerk` (use ngrok for HTTPS)
5. Subscribe to events:
   - ✅ `user.created`
   - ✅ `user.updated`
   - ✅ `user.deleted`
6. Copy the **Signing Secret**

### 3. Add Webhook Secret to Environment

Add to your `.env` file or environment:

```bash
CLERK_WEBHOOK_SECRET=whsec_your_secret_here
```

Then uncomment the signature verification in `clerk_webhook.py` (lines 85-88).

### 4. Test the Webhook

**Option A: Using ngrok (for local development)**

```bash
# Terminal 1: Start your FastAPI server
cd /home/weed/senior/backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start ngrok
ngrok http 8000
```

Use the ngrok HTTPS URL in Clerk webhook settings.

**Option B: Test endpoint**

```bash
curl http://localhost:8000/webhooks/clerk/test
```

### 5. Verify Integration

When a user signs up via Clerk:
1. Clerk sends webhook to `/webhooks/clerk`
2. User data is automatically saved to SQLite
3. Check database:

```bash
python3 -c "from database.models.users import get_all_users; print(get_all_users())"
```

## 📋 User Data Stored

From Clerk webhook, we store:

| Field | Source | Type |
|-------|--------|------|
| `clerk_id` | `data.id` | Primary Key |
| `email` | `data.email_addresses[0].email_address` | Unique |
| `username` | `data.username` | Optional |
| `first_name` | `data.first_name` | Optional |
| `last_name` | `data.last_name` | Optional |
| `profile_image_url` | `data.profile_image_url` | Optional |
| `email_verified` | `data.email_addresses[].verification.status` | Boolean |
| `created_at` | Auto | Timestamp |
| `updated_at` | Auto | Timestamp |

## 🔧 Usage in Your API

### Get current user from Clerk token

```python
from fastapi import Depends, HTTPException
from database.models.users import get_user_by_clerk_id

# In your route
@router.get("/me")
async def get_current_user(clerk_user_id: str):  # Get from Clerk middleware
    user = get_user_by_clerk_id(clerk_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Use user_id in other tables

When creating portfolios, predictions, etc., use `clerk_id` as foreign key:

```python
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT,
    FOREIGN KEY (user_id) REFERENCES users(clerk_id) ON DELETE CASCADE
)
```

## 🔒 Security Notes

1. **Webhook Signature Verification**: Uncomment verification code after adding `CLERK_WEBHOOK_SECRET`
2. **HTTPS Required**: Clerk webhooks require HTTPS in production
3. **Rate Limiting**: Consider adding rate limiting to webhook endpoint
4. **Error Handling**: All webhook errors are logged but return 200 to Clerk (prevent retries)

## 📝 Next Steps

1. Add Clerk middleware to protect routes
2. Create user-specific tables (portfolios, watchlists, etc.)
3. Add user preferences/settings table
4. Implement user data deletion (GDPR compliance)

## 🧪 Testing Webhook Locally

Send test webhook:

```bash
curl -X POST http://localhost:8000/webhooks/clerk \
  -H "Content-Type: application/json" \
  -d '{
    "type": "user.created",
    "data": {
      "id": "user_test123",
      "email_addresses": [
        {
          "id": "email_123",
          "email_address": "test@example.com",
          "verification": {"status": "verified"}
        }
      ],
      "primary_email_address_id": "email_123",
      "username": "testuser",
      "first_name": "Test",
      "last_name": "User",
      "profile_image_url": "https://example.com/avatar.jpg"
    }
  }'
```

Check if user was created:

```bash
python3 -c "from database.models.users import get_user_by_email; print(get_user_by_email('test@example.com'))"
```
