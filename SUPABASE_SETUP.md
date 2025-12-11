# Supabase Database Setup for VAESTA

This guide will help you set up Supabase as the database backend for VAESTA.

## 🚀 Quick Start

### Step 1: Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"** and sign up (GitHub login recommended)
3. Create a new organization (if prompted)

### Step 2: Create a New Project

1. Click **"New Project"**
2. Fill in:
   - **Name**: `vaesta` (or any name you prefer)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose the closest to your users
3. Click **"Create new project"**
4. Wait 1-2 minutes for the project to be provisioned

### Step 3: Get Your API Credentials

1. Go to **Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL** → This is your `SUPABASE_URL`
   - **anon/public key** → This is your `SUPABASE_KEY`

### Step 4: Create Storage Bucket for Images

**Why:** All clothing images need cloud storage to persist across Streamlit Cloud restarts.

1. In your Supabase dashboard, go to **Storage** (left sidebar)

2. Click **"Create a new bucket"** or **"New bucket"**

3. Fill in the details:
   - **Name:** `wardrobe-images`
   - **Public bucket:** ✅ **YES** (Enable public access so images can be displayed)
   - **File size limit:** 10MB (optional)
   - **Allowed MIME types:** `image/jpeg,image/png,image/jpg` (optional)

4. Click **"Create bucket"**

**Direct link to your Storage:**
👉 https://supabase.com/dashboard/project/xgvawonuusadqscxkuhu/storage/buckets

---

### Step 5: Create Database Tables
http://supabase.com/dashboard/project/xgvawonuusadqscxkuhu

1. Go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy and paste the SQL below, then click **"Run"**

```sql
-- ============================================
-- VAESTA Database Schema for Supabase
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    city TEXT DEFAULT 'London',
    gender TEXT DEFAULT 'Female',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster username lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================
-- PREFERENCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    style TEXT DEFAULT 'Minimalist Chic',
    budget TEXT DEFAULT '$$',
    top_size TEXT DEFAULT 'M',
    bottom_size TEXT DEFAULT 'M',
    shoes_size TEXT DEFAULT '42',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================
-- MEASUREMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS measurements (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    height_cm NUMERIC DEFAULT 170,
    weight_kg NUMERIC DEFAULT 70,
    shoulder_cm NUMERIC DEFAULT 44,
    chest_cm NUMERIC DEFAULT 96,
    waist_cm NUMERIC DEFAULT 80,
    hips_cm NUMERIC DEFAULT 95,
    inseam_cm NUMERIC DEFAULT 80,
    shoe_size TEXT DEFAULT '42',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================
-- WARDROBE TABLE (Manual entries)
-- ============================================
CREATE TABLE IF NOT EXISTS wardrobe (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#667eea',
    season TEXT[] DEFAULT ARRAY['Spring', 'Fall'],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster user wardrobe lookups
CREATE INDEX IF NOT EXISTS idx_wardrobe_user_id ON wardrobe(user_id);

-- ============================================
-- AI WARDROBE TABLE (AI-analyzed items)
-- ============================================
CREATE TABLE IF NOT EXISTS ai_wardrobe (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id TEXT UNIQUE NOT NULL,
    image_path TEXT,
    item_type TEXT,
    warmth_level INTEGER DEFAULT 3,
    color TEXT,
    material TEXT,
    season TEXT[],
    style TEXT,
    thickness TEXT,
    waterproof BOOLEAN DEFAULT FALSE,
    windproof BOOLEAN DEFAULT FALSE,
    ai_analyzed BOOLEAN DEFAULT TRUE,
    confidence NUMERIC DEFAULT 0.8,
    notes TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster user AI wardrobe lookups
CREATE INDEX IF NOT EXISTS idx_ai_wardrobe_user_id ON ai_wardrobe(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_wardrobe_item_id ON ai_wardrobe(item_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS) - Optional but recommended
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE wardrobe ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_wardrobe ENABLE ROW LEVEL SECURITY;

-- Create policies that allow all operations (for service role)
-- These allow the anon key to perform all operations
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on preferences" ON preferences FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on measurements" ON measurements FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on wardrobe" ON wardrobe FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on ai_wardrobe" ON ai_wardrobe FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables with updated_at column
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_measurements_updated_at
    BEFORE UPDATE ON measurements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

4. Verify tables were created: Go to **Table Editor** (left sidebar) and you should see:
   - `users`
   - `preferences`
   - `measurements`
   - `wardrobe`
   - `ai_wardrobe`

### Step 5: Configure Your Environment

1. Create/edit your `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key

# Existing configurations
OPENWEATHER_API_KEY=your_openweather_key
GEMINI_API_KEY=your_gemini_key
```

2. Replace the placeholder values with your actual Supabase credentials

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Test the Connection

Run the app:
```bash
streamlit run app.py
```

Try creating a new account - if it works, you're connected to Supabase! 🎉

---

## 📊 Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         VAESTA Database                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐      ┌──────────────────┐                      │
│  │   users     │──────│   preferences    │                      │
│  │─────────────│      │──────────────────│                      │
│  │ id (PK)     │      │ id (PK)          │                      │
│  │ username    │      │ user_id (FK)     │                      │
│  │ email       │      │ style            │                      │
│  │ city        │      │ budget           │                      │
│  │ gender      │      │ top_size         │                      │
│  │ created_at  │      │ bottom_size      │                      │
│  └─────────────┘      │ shoes_size       │                      │
│         │             └──────────────────┘                      │
│         │                                                        │
│         │             ┌──────────────────┐                      │
│         ├─────────────│   measurements   │                      │
│         │             │──────────────────│                      │
│         │             │ id (PK)          │                      │
│         │             │ user_id (FK)     │                      │
│         │             │ height_cm        │                      │
│         │             │ weight_kg        │                      │
│         │             │ shoulder_cm      │                      │
│         │             │ chest_cm, etc... │                      │
│         │             └──────────────────┘                      │
│         │                                                        │
│         │             ┌──────────────────┐                      │
│         ├─────────────│    wardrobe      │                      │
│         │             │──────────────────│                      │
│         │             │ id (PK)          │                      │
│         │             │ user_id (FK)     │                      │
│         │             │ item_type        │                      │
│         │             │ name             │                      │
│         │             │ color            │                      │
│         │             │ season[]         │                      │
│         │             └──────────────────┘                      │
│         │                                                        │
│         │             ┌──────────────────┐                      │
│         └─────────────│   ai_wardrobe    │                      │
│                       │──────────────────│                      │
│                       │ id (PK)          │                      │
│                       │ user_id (FK)     │                      │
│                       │ item_id          │                      │
│                       │ image_path       │                      │
│                       │ item_type        │                      │
│                       │ warmth_level     │                      │
│                       │ color, etc...    │                      │
│                       └──────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### "Could not find table" Error
- Make sure you ran the SQL script in Step 4
- Check that you're connected to the correct project

### "Invalid API Key" Error
- Verify your `SUPABASE_KEY` in `.env` is the **anon/public** key
- Make sure there are no extra spaces or newlines

### "Connection Refused" Error
- Check your `SUPABASE_URL` is correct
- Make sure your Supabase project is active (not paused)

### App Falls Back to Local Storage
- If Supabase credentials are missing or invalid, the app automatically uses local JSON storage
- Check the console output for connection status messages

### Paused Project
- Free tier projects pause after 1 week of inactivity
- Go to your Supabase dashboard and click "Restore project"

---

## 🔒 Security Best Practices

1. **Never commit `.env` to git** - it's already in `.gitignore`
2. **Use environment variables in production** (Streamlit Cloud, Heroku, etc.)
3. **Consider using Row Level Security (RLS)** for multi-tenant apps
4. **Rotate your API keys** if you suspect they've been compromised

---

## 📦 Storage Architecture

### Image Storage with Supabase

**All clothing images** are now stored in **Supabase Storage** (bucket: `wardrobe-images`)

### Why Supabase Storage?

- ✅ **Persistent:** Images survive Streamlit Cloud restarts
- ✅ **Backed up:** Included in database backups
- ✅ **Fast:** CDN-powered delivery worldwide
- ✅ **Scalable:** No local disk dependency

### How it works:

1. **User uploads image** → Temporarily saved to `data/uploads/`
2. **Upload to cloud** → Image sent to Supabase Storage bucket
3. **Get public URL** → `https://...supabase.co/storage/v1/object/public/wardrobe-images/username/uuid.jpg`
4. **Store URL in database** → Only the URL is saved in `ai_wardrobe` table
5. **Display image** → Load directly from cloud URL

### File Organization:

```
wardrobe-images/
├── username1/
│   ├── uuid1.jpg
│   ├── uuid2.png
│   └── uuid3.jpg
├── username2/
│   ├── uuid4.jpg
│   └── uuid5.jpg
```

### Storage Limits (Supabase Free Tier):

- **Storage:** 1 GB total
- **Bandwidth:** 2 GB/month
- **File uploads:** 50 MB max per file

For most users, this is more than enough! (~200-500 clothing images)

---

## 📱 Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Streamlit Cloud settings:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```

---

## 🆘 Need Help?

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord](https://discord.supabase.com)
- [Python Client Docs](https://supabase.com/docs/reference/python/introduction)
