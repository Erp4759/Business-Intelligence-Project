import requests

API_KEY = ""   

def get_weather(city="Seoul"):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={API_KEY}&units=metric"
    )
    
    response = requests.get(url)
    data = response.json()

    print("API Response:", data)   

    if "main" not in data:
        print("ERROR: Weather data not returned.")
        print("This usually means: invalid key, key not activated, or wrong URL.")
        return

    temp = data["main"]["temp"]
    wind = data["wind"]["speed"]
    rain_1h = data.get("rain", {}).get("1h", 0)

    print("\nCity:", city)
    print("Temperature:", temp, "°C")
    print("Wind Speed:", wind, "m/s")
    print("Rain (last 1h):", rain_1h, "mm")

if __name__ == "__main__":
    get_weather("Seoul")
