import requests
import json
from datetime import datetime, timedelta
from kafka import KafkaProducer
import logging

REGIONAL_CITIES = ['Minsk', 'Vitsyebsk', 'Brest', 'Hrodna', 'Homyel']
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'Belarus_Weather'
API_KEY = '40d31e9b05a64bd5bf6124347241601'
DATA_FILE = 'last_downloaded_dates.json'
DATE_RANGE_DAYS = 25

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def load_last_downloaded_dates():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def save_last_downloaded_date(city, date):
    last_downloaded_dates = load_last_downloaded_dates()
    last_downloaded_dates[city] = date
    with open(DATA_FILE, 'w') as file:
        json.dump(last_downloaded_dates, file)


def get_date_range(last_downloaded_date):
    current_date = datetime.now()
    date_range = [current_date - timedelta(days=i) for i in range(1, DATE_RANGE_DAYS + 1)]

    if last_downloaded_date:
        last_downloaded_date = datetime.strptime(last_downloaded_date, '%Y-%m-%d')
        date_range = [date for date in date_range if date > last_downloaded_date]

    return date_range


def get_historical_weather_data(city, date):
    api_url = f'https://api.weatherapi.com/v1/history.json?q={city}&dt={date}&key={API_KEY}'

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for {city} on {date}: {e}")
        return None


def send_to_kafka(city, historical_data):
    try:
        producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        producer.send(topic=KAFKA_TOPIC, value=historical_data)
    except Exception as e:
        logger.error(f"Error sending data to Kafka for {city}: {e}")
    finally:
        producer.flush()
        producer.close()


def process_city(city):
    last_downloaded_dates = load_last_downloaded_dates()
    last_downloaded_date = last_downloaded_dates.get(city)
    date_range = get_date_range(last_downloaded_date)

    for date in date_range:
        historical_data = get_historical_weather_data(city, date)
        print(f"{city}:{date}")
        maine_weather_data = extract_main_weather_data(city, historical_data)
        if historical_data:
            send_to_kafka(city, maine_weather_data)
            save_last_downloaded_date(city, datetime.now().strftime('%Y-%m-%d'))


def extract_main_weather_data(city, historical_data):
    if historical_data and 'forecast' in historical_data:
        forecast = historical_data['forecast']['forecastday'][0]['day']
        main_weather_data = {
            'city': city,
            'date': historical_data['forecast']['forecastday'][0]['date'],
            'max_temp_c': forecast['maxtemp_c'],
            'max_temp_f': forecast['maxtemp_f'],
            'min_temp_c': forecast['mintemp_c'],
            'min_temp_f': forecast['mintemp_f'],
            'avg_temp_c': forecast['avgtemp_c'],
            'avg_temp_f': forecast['avgtemp_f'],
            'condition_text': forecast['condition']['text'],
            'wind_mph': forecast['maxwind_mph'],
            'wind_kph': forecast['maxwind_kph'],
            'precipitation_mm': forecast['totalprecip_mm'],
            'precipitation_in': forecast['totalprecip_in'],
            'humidity': forecast['avghumidity'],
        }
        return main_weather_data
    return None


def main():
    for city in REGIONAL_CITIES:
        process_city(city)


if __name__ == "__main__":
    main()
