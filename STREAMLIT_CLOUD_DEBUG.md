# Streamlit Cloud Debugging Guide

## 🔍 Problem: Users not saving to Supabase on Streamlit Cloud

### Step 1: Check Logs

1. Go to your Streamlit Cloud app
2. Click the **≡** menu (top right)
3. Click **"Manage app"**
4. Look at the **logs** section
5. Look for these messages:

**✅ Good (Working):**
```
[DEBUG] Using Streamlit secrets
✅ Connected to Supabase database
[INIT] ✅ Supabase connected!
📦 Active storage backend: SUPABASE
```

**❌ Bad (Not Working):**
```
⚠️  Supabase credentials not found
📦 Active storage backend: LOCAL_JSON
[DEBUG] Streamlit secrets failed: ...
```

### Step 2: Verify Secrets Format

Secrets in Streamlit Cloud **must be EXACTLY** in this format:

```toml
SUPABASE_URL = "https://xgvawonuusadqscxkuhu.supabase.co"
SUPABASE_KEY = "sb_publishable_x7d-PmEgpmQ0qv-SnRb_Rg_tlWGpt88"
OPENWEATHER_API_KEY = "740e29dafb7257ff7d140c183efe25e4"
OPENAI_API_KEY = "sk-proj-..."
```

**Common Mistakes:**
- ❌ Missing quotes: `SUPABASE_URL = https://...`
- ❌ Wrong format: `SUPABASE_URL: "https://..."`
- ❌ Extra spaces: `SUPABASE_URL = " https://... "`
- ❌ Comments in wrong place

### Step 3: Check Database Connection

After fixing secrets:
1. Click **"Reboot app"** in Manage app
2. Wait for restart
3. Register a new test user
4. Check logs for:
   ```
   Creating user: testuser, test@email.com, Seoul
   User created: {'email': 'test@email.com', ...
   ```
5. Go to Supabase dashboard
6. Check `users` table for the new user

### Step 4: Test Registration Flow

Try registering with these details:
- Username: `cloudtest`
- Email: `cloudtest@test.com`
- Password: `test123456`
- City: `Seoul`

Then check Supabase dashboard → Table Editor → `users` table

### Step 5: Common Issues

#### Issue: "local_json" backend on Streamlit Cloud
**Cause**: Secrets not loaded
**Fix**: 
1. Check secrets format (Step 2)
2. Reboot app
3. Check logs again

#### Issue: "403" or "Invalid API key"
**Cause**: Wrong Supabase key
**Fix**: 
1. Go to Supabase Dashboard → Settings → API
2. Copy **anon/public** key (not service_role!)
3. Update `SUPABASE_KEY` in secrets
4. Reboot app

#### Issue: "Connection refused"
**Cause**: Supabase project paused
**Fix**: 
1. Go to Supabase dashboard
2. Click "Restore project" if paused
3. Wait 1-2 minutes
4. Reboot Streamlit app

#### Issue: "Could not find the 'password_hash' column"
**Cause**: Database schema not updated
**Fix**: 
1. Go to Supabase SQL Editor
2. Run this SQL:
```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;
```
3. Test registration again

### Step 6: Force Connection Test

Add this temporarily to see connection status:

In your Streamlit Cloud app, after login page loads:
1. Look at the top of the page
2. Should see initialization logs
3. If you see "SUPABASE" - it's connected!

### Step 7: Manual Verification

1. **On Streamlit Cloud**: Register user `clouduser`
2. **In Supabase**: Check if `clouduser` appears in `users` table
3. **If NOT there**: Share the logs with me

### Quick Checklist

- [ ] Secrets added to Streamlit Cloud (Settings → Secrets)
- [ ] Secrets format is correct (TOML with quotes)
- [ ] App rebooted after adding secrets
- [ ] Supabase project is active (not paused)
- [ ] Database tables exist (run SUPABASE_SETUP.md SQL)
- [ ] `password_hash` column added to users table
- [ ] Logs show "✅ Connected to Supabase database"
- [ ] Logs show "📦 Active storage backend: SUPABASE"

---

## 📱 How to Share Logs

If still not working:
1. Go to Manage app → Logs
2. Copy the **entire startup section** (first 50 lines)
3. Copy the section when you **create a user**
4. Share both with me

Look for these specific lines:
```
============================================================
🚀 VAESTA STARTING - INITIALIZING DATABASE CONNECTION
============================================================
[INIT] Testing Supabase connection...
[DEBUG] Using Streamlit secrets / environment variables / file directly
```

---

## 🔧 Emergency Fallback

If Supabase still doesn't work on Streamlit Cloud:

The app will automatically fall back to local JSON storage (in cloud storage).
Users will still be created, but stored differently.

To fix permanently:
1. Download logs
2. Find the exact error message
3. Fix the issue
4. Reboot app
