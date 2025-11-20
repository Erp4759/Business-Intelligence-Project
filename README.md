# 👔 VAESTA - Your Intelligent Fashion Companion

VAESTA is an intelligent fashion companion that blends meteorology with personal style. It analyzes upcoming weather patterns and your wardrobe to curate perfectly balanced outfits — practical, elegant, and trend-aware.

## ✨ Features

- 👤 **User Registration & Login** - Create your personal account with preferences
- 📍 **City-Based Weather** - Real weather data from OpenWeatherMap API
- 🌤️ **Weather Forecast** - Check current weather, 7-day, or 14-day forecasts
- 👗 **Smart Outfit Recommendations** - AI-powered suggestions based on real weather conditions
- 👕 **Digital Wardrobe** - Manage your clothing items with colors and seasons
- 🛍️ **Shopping Suggestions** - Temperature-aware fashion recommendations
- 🎨 **User Profile** - Customize style preferences, budget, and sizes
- 💾 **Data Persistence** - Your wardrobe and preferences are saved locally
- 🎨 **Beautiful UI** - Clean, modern design with gradient backgrounds and smooth interactions

## 🚀 Quick Start

### 1. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Set Up Weather API

To get real weather data, sign up for a free API key at [OpenWeatherMap](https://openweathermap.org/api):

1. Create account and get your API key
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Add your API key to `.env`:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   ```

**Note:** The app works without an API key using mock weather data.

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## 📱 How to Use

### First Time Setup

1. **Register** - Create your account with username, email, and city
2. **Set Preferences** - Choose your style and budget during registration
3. **Add Wardrobe Items** - Start building your digital wardrobe

### Daily Use

1. **Check Weather** - View current or forecast weather for your city
2. **Get Recommendations** - See outfit suggestions based on temperature and conditions
3. **Manage Wardrobe** - Add or remove clothing items
4. **Explore Shopping** - Find new pieces that match the weather and your style
5. **Update Profile** - Modify city, preferences, or sizes anytime

## 📱 How to Use

1. **Set Your Location** - Enter your city name in the sidebar
2. **Add Your Wardrobe** - Click "Add Clothing Item" to add items you own
3. **Check Weather** - Select forecast period (Today, 1 Week, 2 Weeks, or 1 Month)
4. **Get Recommendations** - View personalized outfit suggestions based on weather
5. **Explore Shopping** - Find new pieces that complement your wardrobe

## 🎨 Features Overview

### Weather Forecast
- Real-time weather display with icons
- Temperature and conditions
- Multi-period forecasting

### Outfit Recommendations
- Weather-appropriate suggestions
- Matches with your existing wardrobe
- Temperature and condition-based logic

### Wardrobe Management
- Add clothing items with type, name, and color
- Visual color picker
- Easy item removal

### Shopping Suggestions
- Style preference selection
- Budget filtering
- Occasion-based recommendations
- Match percentage for suggested items

## 🛠️ Tech Stack

- **Streamlit** - Web framework
- **Python 3.13** - Backend
- **Custom CSS** - Beautiful styling

## 📂 Project Structure

```
vaesta/
├── app.py                 # Main Streamlit application
├── data_manager.py        # User data and wardrobe persistence
├── weather_service.py     # Weather API integration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── data/                 # User data storage (auto-created)
└── README.md             # This file
```

## 🔧 Technical Details

### Components

- **Frontend**: Streamlit with custom CSS
- **Data Storage**: JSON-based local storage
- **Weather API**: OpenWeatherMap (with mock fallback)
- **Python Version**: 3.13+

### Key Modules

- `data_manager.py` - Handles user registration, wardrobe, and preferences
- `weather_service.py` - Fetches real weather data with fallback to mock data
- `app.py` - Main application with routing and UI

### Data Storage

User data is stored in `data/users.json` with the following structure:
- User profiles (email, city, creation date)
- Wardrobe items (type, name, color, season)
- Preferences (style, budget, sizes)

## 🎨 Features Breakdown

### Weather Forecast
- **Current Weather**: Real-time temperature, feels-like, humidity, wind
- **7-Day Forecast**: Daily predictions with temperatures and conditions
- **14-Day Forecast**: Extended planning for trips or events

### Outfit Recommendations
- Temperature-based suggestions (<10°C, 10-20°C, >20°C)
- Rain/weather condition awareness
- Integration with your wardrobe items

### Wardrobe Management
- Add items with type, name, color, and season tags
- Visual color picker for accurate representation
- Easy removal and organization
- Statistics dashboard

### User Profile
- Personal information management
- Style preference customization
- Budget range selection
- Size information storage

## 📝 Future Enhancements

- ✅ User registration and authentication *(DONE)*
- ✅ Real weather API integration *(DONE)*
- ✅ City selection and management *(DONE)*
- ✅ Data persistence *(DONE)*
- 📸 Photo upload for wardrobe items
- 🔗 Shopping links integration with real stores
- 📅 Calendar integration for outfit planning
- 🔔 Weather alerts and notifications
- 🤖 AI-powered style learning from user choices
- 👥 Social features and outfit sharing

## 🐛 Troubleshooting

### Weather API Not Working
- Check if API key is correctly set in `.env`
- Verify city name spelling
- App will use mock data as fallback

### Data Not Saving
- Ensure write permissions in the project directory
- Check if `data/` folder was created automatically

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

## 🤝 Contributing

Feel free to fork this project and submit pull requests with improvements!

## 📄 License

This project is open source and available for personal and educational use.

---

✨ **VAESTA** - Where meteorology meets personal style ✨
