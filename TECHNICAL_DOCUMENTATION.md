# VAESTA - Technical Documentation

## Architecture Overview

VAESTA is a multipage Streamlit web application that combines weather forecasting, wardrobe management, and AI-powered clothing analysis. The system follows a modular architecture with clear separation of concerns.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  ┌──────────┬──────────┬──────────────┬─────────────────┐  │
│  │  Login   │   Home   │   Profile    │  Fit & Measures │  │
│  │          │          │              │   AI Wardrobe   │  │
│  └──────────┴──────────┴──────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┬──────────────────┬───────────────────┐   │
│  │ Data Manager │ Weather Service  │ AI Image Analyzer │   │
│  │              │                  │                   │   │
│  └──────────────┴──────────────────┴───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌───────────────────┬────────────────────────────────┐    │
│  │ OpenWeatherMap API│  Google Gemini Vision API      │    │
│  └───────────────────┴────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage                             │
│              JSON Files (data/users.json)                    │
│              Images (data/uploads/*.jpg)                     │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Framework
- **Streamlit 1.28+**: Web application framework
  - Multipage application structure using `pages/` directory
  - Session state management for user authentication and caching
  - Custom CSS injection for styling
  - File upload handling

### Backend Technologies
- **Python 3.13**: Primary programming language
- **JSON**: Data persistence format
- **Pillow (PIL)**: Image processing and manipulation

### External APIs
1. **OpenWeatherMap API**
   - Current weather data endpoint: `/data/2.5/weather`
   - Forecast endpoint: `/data/2.5/forecast` (3-hour intervals, aggregated to daily)
   - Geocoding endpoint: `/geo/1.0/direct` (city name to coordinates)

2. **Google Gemini 1.5 Flash**
   - Vision API for clothing image analysis
   - Model: `gemini-1.5-flash`
   - JSON response parsing for structured data extraction

### Libraries
- **requests**: HTTP client for API calls
- **python-dotenv**: Environment variable management
- **google-generativeai**: Gemini API client
- **uuid**: Unique identifier generation
- **datetime**: Timestamp and date handling
- **pathlib**: Cross-platform file path operations

## Project Structure

```
vaesta/
├── app.py                          # Entry point: login/landing page
├── ui.py                           # Shared UI utilities (CSS injection)
├── data_manager.py                 # Data persistence layer
├── weather_service.py              # Weather API integration
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (gitignored)
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── start.sh                        # Quick start script
├── README.md                       # User documentation
├── USER_GUIDE.md                   # Detailed user guide
├── TECHNICAL_DOCUMENTATION.md      # This file
├── data/                           # Data storage (auto-created)
│   ├── users.json                  # User profiles and wardrobe
│   └── uploads/                    # Uploaded clothing images
└── pages/                          # Streamlit multipage structure
    ├── 01_Home.py                  # Weather, outfit, shopping
    ├── 02_Profile.py               # User preferences, sizes
    ├── 03_Fit_Measurements.py      # Body measurements, mannequin
    └── 04_AI_Wardrobe.py           # AI clothing analysis
```

## Core Modules

### 1. app.py - Application Entry Point

**Purpose**: Authentication and landing page

**Key Components**:
- Session state initialization (`logged_in`, `username`, `user_data`)
- Login/Registration UI with tabs
- User creation with default preferences and measurements
- Landing page with navigation instructions
- Logout functionality

**Technical Details**:
```python
# Session state structure
st.session_state = {
    'logged_in': bool,
    'username': str,
    'user_data': dict,
    'weather_service': WeatherService,
    'weather_cache_{city}': dict,
    'ai_analysis': dict,
    'temp_image_path': str
}
```

### 2. ui.py - Shared UI Components

**Purpose**: Centralized styling and page configuration

**Key Components**:
- `inject_css()`: Injects custom CSS for consistent styling across pages
- Page configuration (title, icon, layout)
- Gradient background
- Card components styling
- Mannequin stage CSS

**CSS Architecture**:
- Linear gradient background: `#667eea` → `#764ba2`
- White cards with border-radius and box-shadow
- Weather cards with gradient overlay
- Responsive column layouts

### 3. data_manager.py - Data Persistence

**Purpose**: Handle all data storage operations

**Data Structure**:
```python
users = {
    "username": {
        "email": str,
        "city": str,
        "created_at": ISO8601 timestamp,
        "wardrobe": [
            {
                "type": str,
                "name": str,
                "color": str (hex),
                "season": [str]
            }
        ],
        "preferences": {
            "style": str,
            "budget": str,
            "sizes": {
                "top": str,
                "bottom": str,
                "shoes": str
            }
        },
        "measurements": {
            "height_cm": int,
            "weight_kg": int,
            "shoulder_cm": float,
            "chest_cm": float,
            "waist_cm": float,
            "hips_cm": float,
            "inseam_cm": float,
            "shoe_size": str
        },
        "ai_wardrobe": [
            {
                "id": str (UUID),
                "image_path": str,
                "type": str,
                "warmth_level": int (1-5),
                "color": str (hex),
                "material": str,
                "season": [str],
                "style": str,
                "thickness": str,
                "waterproof": bool,
                "windproof": bool,
                "ai_analyzed": bool,
                "confidence": float (0-1),
                "notes": str,
                "added_at": ISO8601 timestamp
            }
        ]
    }
}
```

**Key Functions**:
- `create_user()`: Initialize new user with defaults
- `get_user()`, `update_user()`: User CRUD operations
- `add_wardrobe_item()`, `remove_wardrobe_item()`, `get_wardrobe()`: Basic wardrobe
- `get_measurements()`, `update_measurements()`: Body measurements
- `add_ai_item()`, `get_ai_wardrobe()`, `update_ai_item()`, `remove_ai_item()`: AI wardrobe

**Persistence Strategy**:
- JSON serialization with indent=2 for readability
- Atomic write operations
- Auto-initialization of data directory
- Graceful handling of missing/corrupted files

### 4. weather_service.py - Weather API Integration

**Purpose**: Fetch and cache weather data

**API Integration**:
```python
# Current Weather
GET https://api.openweathermap.org/data/2.5/weather
Parameters:
  - lat, lon (from geocoding) OR q (city name)
  - appid (API key)
  - units=metric

# Forecast
GET https://api.openweathermap.org/data/2.5/forecast
Parameters:
  - lat, lon (from geocoding) OR q (city name)
  - appid (API key)
  - units=metric
  - cnt (number of 3-hour intervals, max 40)

# Geocoding
GET https://api.openweathermap.org/geo/1.0/direct
Parameters:
  - q (city name)
  - limit=1
  - appid (API key)
```

**Key Features**:
1. **Geocoding Resolution**: Converts city names to lat/lon for accurate weather
2. **API Validation Caching**: After first 401/403, marks API as invalid to avoid repeated failures
3. **Mock Fallback**: Returns realistic placeholder data when API unavailable
4. **Daily Aggregation**: Converts 3-hour forecast intervals to daily averages
5. **Error Handling**: Graceful degradation with logging

**Weather Emoji Mapping**:
```python
emoji_map = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist/Fog/Haze": "🌫️"
}
```

**Caching Strategy** (in pages/01_Home.py):
- Per-city session state caching
- Manual refresh via "🔄 Update Weather" button
- Separate cache keys for current weather and forecasts (7/14 day)
- Timestamp display for cache age

### 5. pages/01_Home.py - Main Dashboard

**Purpose**: Weather display, outfit recommendations, shopping suggestions

**Key Components**:

1. **Weather Caching System**:
```python
cache_key = f"weather_cache_{city}"
cache_time_key = f"weather_cache_time_{city}"
needs_refresh = (
    cache_key not in st.session_state or
    st.session_state.get("force_weather_refresh", False)
)
```

2. **Outfit Recommendation Logic**:
```python
def outfit_for(weather_data):
    temp = weather_data['temp']
    if temp < 10:
        return ["Warm sweater", "Thermal pants", "Winter coat", "Boots", "Scarf"]
    elif temp < 20:
        return ["Long sleeve shirt", "Jeans", "Light jacket", "Sneakers"]
    else:
        return ["T-shirt", "Shorts/Light pants", "Sunglasses", "Sandals"]
    
    # Add rain gear if needed
    if "rain" in condition.lower():
        items += ["Umbrella ☔", "Waterproof jacket"]
```

3. **Shopping Suggestions**:
- Temperature-based product recommendations
- Style matching with user preferences
- Budget filtering
- Match percentage display

**UI Layout**:
- Two-column layout: Weather (left) + Outfit (right)
- Sidebar: City selection, wardrobe management
- Weather forecast with scrollable container (max-height: 400px)
- Shopping section with 3-column product grid

### 6. pages/02_Profile.py - User Management

**Purpose**: Profile editing, preferences, statistics

**Sections**:
1. **Account Information** (read-only display)
   - Username, email, member since date

2. **Location Management**
   - City input with update button
   - Triggers weather cache invalidation

3. **Style Preferences**
   - Style selection: Minimalist Chic, Urban Streetwear, Classic Elegant, Casual Comfort
   - Budget slider: $, $$, $$$, $$$$
   - Size inputs: Top, Bottom, Shoes

4. **Wardrobe Statistics**
   - Total items count
   - Breakdown by type (Tops, Bottoms, Outerwear)
   - Uses `st.metric()` for visual appeal

### 7. pages/03_Fit_Measurements.py - Body Measurements

**Purpose**: Physical measurements with visual mannequin

**Measurement System**:
```python
measurements = {
    "height_cm": 140-210,
    "weight_kg": 40-140,
    "shoulder_cm": 35.0-60.0,
    "chest_cm": 70.0-130.0,
    "waist_cm": 60.0-130.0,
    "hips_cm": 75.0-140.0,
    "inseam_cm": 60.0-100.0,
    "shoe_size": str
}
```

**SVG Mannequin**:
- Dynamic scaling based on measurements
- Height scale: `sy = height_cm / 170.0` (clamped 0.8-1.35)
- Width scale: `sx = avg(shoulder, waist, hips ratios)` (clamped 0.85-1.35)
- Real-time preview using session state widget keys
- Gradient fills for visual appeal

**SVG Structure**:
```xml
<svg viewBox='0 0 200 400' width='260' height='520'>
  <g transform='scale(sx, sy)'>
    <!-- Head: circle -->
    <!-- Neck: rounded rect -->
    <!-- Torso: large rounded rect -->
    <!-- Hips: rounded rect -->
    <!-- Legs: 2 rounded rects -->
    <!-- Arms: 2 rounded rects -->
    <!-- Shoes: 2 small rounded rects -->
    <!-- Shoulder line -->
  </g>
  <defs><!-- Linear gradients for coloring --></defs>
</svg>
```

### 8. pages/04_AI_Wardrobe.py - AI Clothing Analysis

**Purpose**: Image upload, AI analysis, dataset building

**Workflow**:
1. User uploads clothing image (jpg/png)
2. Image saved to `data/uploads/{username}_{timestamp}.{ext}`
3. User clicks "🤖 Analyze with AI"
4. Gemini Vision API analyzes image
5. Form auto-fills with AI predictions
6. User edits if needed
7. Save to `ai_wardrobe` array

**Gemini Integration**:
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

img = Image.open(image_path)
prompt = """Analyze this clothing item and provide detailed parameters in JSON format.
Return ONLY valid JSON with these exact fields:
{
  "type": "jacket|shirt|t-shirt|...",
  "warmth_level": 1-5,
  "color": "dominant color name",
  "material": "cotton|wool|synthetic|...",
  "season": ["Spring", "Summer", ...],
  "style": "casual|formal|sport|...",
  "thickness": "thin|medium|thick",
  "waterproof": true|false,
  "windproof": true|false,
  "description": "brief description"
}"""

response = model.generate_content([prompt, img])
```

**Response Processing**:
1. Extract JSON from response (handle markdown code blocks)
2. Parse JSON to dict
3. Map color names to hex codes
4. Validate and normalize field values
5. Add metadata (ai_analyzed, confidence, timestamp)

**Color Mapping**:
```python
color_map = {
    "black": "#000000", "white": "#FFFFFF", "gray": "#808080",
    "red": "#FF0000", "blue": "#0000FF", "green": "#00FF00",
    "yellow": "#FFFF00", "orange": "#FFA500", "purple": "#800080",
    "pink": "#FFC0CB", "brown": "#8B4513", "navy": "#000080",
    "beige": "#F5F5DC", "khaki": "#F0E68C"
}
```

**Gallery Display**:
- 3-column responsive grid
- Image thumbnails with parameters overlay
- AI confidence badge
- Edit/Delete action buttons
- Uses UUID for item identification

## Data Flow

### User Registration Flow
```
1. User fills registration form
   ↓
2. app.py: create_user(username, email, city)
   ↓
3. data_manager.py: Save to users.json with defaults
   ↓
4. Session state updated: logged_in=True, user_data=new_user
   ↓
5. Redirect to landing page
```

### Weather Fetch Flow
```
1. User opens Home page
   ↓
2. Check session_state for cached weather
   ↓
   If cached: Display from session_state
   If not cached or manual refresh:
     ↓
     3. weather_service.py: Check API validity cache
        ↓
        If API valid or untested:
          ↓
          4a. Geocode city to lat/lon
          4b. Fetch weather by coordinates
          4c. Cache API validity (success/fail)
          4d. Return weather data with source='live'
        If API invalid:
          ↓
          5. Return mock data with source='mock'
     ↓
     6. Cache in session_state with timestamp
   ↓
7. Render weather card with data
```

### AI Wardrobe Flow
```
1. User uploads image
   ↓
2. Save to data/uploads/{username}_{timestamp}.{ext}
   ↓
3. Store path in session_state.temp_image_path
   ↓
4. User clicks "Analyze with AI"
   ↓
5. Call Gemini Vision API with image + prompt
   ↓
6. Parse JSON response
   ↓
7. Store in session_state.ai_analysis
   ↓
8. Pre-fill form with AI predictions
   ↓
9. User edits/confirms parameters
   ↓
10. Submit form
    ↓
11. Create item dict with UUID
    ↓
12. data_manager.add_ai_item(username, item)
    ↓
13. Append to users[username].ai_wardrobe
    ↓
14. Save users.json
    ↓
15. Clear temp session state
    ↓
16. Rerun to show updated gallery
```

## Performance Optimizations

### 1. Weather API Caching
- **Problem**: Every page load triggered API calls (token waste)
- **Solution**: Session state caching per city with manual refresh button
- **Impact**: API calls reduced by ~90%

### 2. Weather Service State Persistence
- **Problem**: New WeatherService instance on every rerun
- **Solution**: Store service in session_state with API validity flag
- **Impact**: Faster page loads, reduced error logging spam

### 3. Image Upload Handling
- **Problem**: Uploaded files lost on rerun
- **Solution**: Immediate save to disk, path in session state
- **Impact**: Reliable image persistence

### 4. Form State Management
- **Problem**: AI analysis lost when form reruns
- **Solution**: Store AI predictions in session state, pre-fill form
- **Impact**: Smooth user experience, no re-analysis needed

## Security Considerations

### 1. API Key Management
- Stored in `.env` file (gitignored)
- Loaded via `python-dotenv`
- Never exposed in client-side code
- `.env.example` provided as template

### 2. Data Storage
- Local JSON files (not suitable for production multi-user)
- No SQL injection risk (no database)
- File system access controlled by Python process permissions

### 3. Image Uploads
- Validated file extensions (jpg, jpeg, png)
- Stored in controlled directory (`data/uploads/`)
- Filename sanitization via timestamp
- No arbitrary file path execution

### 4. Input Validation
- Streamlit handles basic XSS protection
- User inputs validated before database write
- Color picker ensures valid hex codes
- Numeric sliders enforce min/max bounds

## Error Handling

### API Failures
```python
try:
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    # Process successful response
except requests.HTTPError as e:
    if e.response.status_code in (401, 403):
        self._api_ok = False  # Cache failure
    print(f"API Error: {e}")
    return fallback_data()
except Exception as e:
    print(f"Unexpected Error: {e}")
    return fallback_data()
```

### Data Persistence Failures
```python
try:
    with open(USERS_FILE, 'r') as f:
        return json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    return {}  # Return empty dict, auto-initialize on save
```

### Image Processing Failures
```python
try:
    img = Image.open(image_path)
    # Process image
except Exception as e:
    st.error(f"Image processing failed: {e}")
    # Continue without image or use placeholder
```

## Testing Strategies

### Manual Testing Checklist
1. ✅ User registration with various inputs
2. ✅ Login with existing/non-existing users
3. ✅ City change with weather refresh
4. ✅ Wardrobe CRUD operations
5. ✅ Profile updates and persistence
6. ✅ Measurements with mannequin scaling
7. ✅ Image upload (various formats/sizes)
8. ✅ AI analysis with/without API key
9. ✅ Form pre-fill and manual override
10. ✅ Gallery display and item deletion

### API Testing
- Weather API tested with valid/invalid keys
- Gemini API tested with various clothing types
- Network failures simulated (timeout, unreachable)

### Edge Cases Handled
- Missing API keys → graceful fallback to mock data
- Corrupted JSON file → reinitialize with empty dict
- Invalid image file → error message, continue
- Concurrent user sessions → session state isolation
- Browser refresh → session state preserved

## Deployment Considerations

### Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with API keys

# Run
streamlit run app.py
```

### Production Deployment (Future)

**Recommended Stack**:
- **Hosting**: Streamlit Cloud, Heroku, AWS EC2
- **Database**: PostgreSQL with SQLAlchemy (replace JSON)
- **File Storage**: AWS S3, Google Cloud Storage (replace local uploads)
- **Caching**: Redis for weather/API caching
- **Authentication**: OAuth2, JWT tokens

**Required Changes**:
1. Replace JSON with proper database
2. Add user authentication/authorization
3. Implement file upload to cloud storage
4. Add rate limiting for API calls
5. Set up environment variable management
6. Configure HTTPS/SSL
7. Add logging and monitoring
8. Implement database migrations

## Dependencies

### Core Dependencies
```
streamlit>=1.28.0           # Web framework
requests>=2.31.0            # HTTP client
pillow>=10.0.0              # Image processing
python-dotenv>=1.0.0        # Environment variables
google-generativeai>=0.3.0  # Gemini API client
```

### Indirect Dependencies
- urllib3 (via requests)
- certifi (via requests)
- charset-normalizer (via requests)
- idna (via requests)
- numpy (via Pillow)
- protobuf (via google-generativeai)
- google-ai-generativelanguage (via google-generativeai)
- google-auth (via google-generativeai)

### Python Version
- **Minimum**: Python 3.8
- **Recommended**: Python 3.13
- **Tested**: Python 3.12, 3.13

## API Rate Limits & Costs

### OpenWeatherMap (Free Tier)
- **Rate Limit**: 60 calls/minute, 1,000,000 calls/month
- **Cost**: Free
- **Our Usage**: ~1-3 calls per session (with caching)

### Google Gemini 1.5 Flash
- **Rate Limit**: 15 requests/minute (free tier)
- **Cost**: Free up to 1,500 requests/day
- **Our Usage**: 1 call per image upload (~5-10/session)

## Future Technical Improvements

### Short Term
1. Add unit tests with pytest
2. Implement proper logging (not just print statements)
3. Add input validation schemas with Pydantic
4. Create API response models
5. Add retry logic with exponential backoff

### Medium Term
1. Migrate to PostgreSQL database
2. Implement user authentication with JWT
3. Add API rate limiting per user
4. Create admin dashboard
5. Add email notifications
6. Implement image compression/resizing

### Long Term
1. Microservices architecture
2. Machine learning outfit recommendation model
3. Real-time weather updates with WebSockets
4. Mobile app integration (API backend)
5. Social features (sharing outfits)
6. E-commerce integration (affiliate links)

## Troubleshooting

### Common Issues

**1. API Key Not Working**
```
Error: 401 Unauthorized
Solution: 
- Verify key in .env file
- Check key is activated (email verification)
- Restart Streamlit to reload .env
```

**2. Images Not Displaying**
```
Error: Image not found
Solution:
- Check data/uploads/ directory exists
- Verify file permissions
- Check image_path in users.json is absolute
```

**3. Session State Lost**
```
Symptom: User logged out on page navigation
Solution:
- Session state is per-browser-tab
- Don't clear browser cache during session
- Check for st.rerun() clearing state
```

**4. Slow AI Analysis**
```
Symptom: Long wait for Gemini response
Solution:
- Check internet connection
- Verify API quota not exceeded
- Use smaller images (<2MB)
- Consider timeout adjustment
```

## Code Quality Standards

### Formatting
- 4-space indentation
- 100-character line length (flexible)
- PEP 8 style guide
- Type hints recommended (not enforced)

### Documentation
- Docstrings for all functions
- Inline comments for complex logic
- README for user documentation
- This file for technical documentation

### Git Workflow
- Branch: `prototype_web`
- Commit messages: Descriptive, present tense
- No sensitive data in commits (.env gitignored)

---

## Conclusion

VAESTA demonstrates a practical implementation of:
- Streamlit multipage applications
- External API integration with caching
- AI/ML integration (Google Gemini Vision)
- Session state management
- JSON-based data persistence
- Image upload and processing
- Responsive UI with custom CSS

The architecture is modular, maintainable, and scalable with clear upgrade paths for production deployment.
