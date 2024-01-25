import pytest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timedelta
import requests
from producer import (
    load_last_downloaded_dates,
    save_last_downloaded_date,
    get_date_range,
    get_historical_weather_data,
    send_to_kafka,
    process_city,
    extract_main_weather_data,
)


@pytest.fixture
def mock_open():
    with patch("builtins.open", create=True) as mock_open:
        yield mock_open


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_kafka_producer():
    with patch("producer.KafkaProducer") as mock_producer:
        yield mock_producer


def test_load_last_downloaded_dates(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = '{"city": "date"}'
    assert load_last_downloaded_dates() == {"city": "date"}


def test_load_last_downloaded_dates_file_not_found(mock_open):
    mock_open.side_effect = FileNotFoundError
    assert load_last_downloaded_dates() == {}


def test_get_date_range():
    current_date = datetime.now()
    last_downloaded_date = (current_date - timedelta(days=5)).strftime('%Y-%m-%d')
    date_range = get_date_range(last_downloaded_date)
    assert len(date_range) == 5
    assert all(date < current_date for date in date_range)


def test_get_historical_weather_data(mock_requests_get):
    city = "Minsk"
    date = "2022-01-22"
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "weather_data"}
    mock_requests_get.return_value = mock_response
    result = get_historical_weather_data(city, date)
    assert result == {"data": "weather_data"}


def test_get_historical_weather_data_request_error(mock_requests_get):
    city = "Minsk"
    date = "2022-01-22"
    mock_requests_get.side_effect = requests.exceptions.RequestException("Error")
    result = get_historical_weather_data(city, date)
    assert result is None


def test_send_to_kafka(mock_kafka_producer):
    city = "Minsk"
    historical_data = {"data": "weather_data"}
    send_to_kafka(city, historical_data)
    mock_kafka_producer.assert_called_once_with(bootstrap_servers='kafka:9092', value_serializer=ANY)
    mock_kafka_producer.return_value.send.assert_called_once_with(topic='Belarus_Weather', value=historical_data)
    mock_kafka_producer.return_value.flush.assert_called_once()
    mock_kafka_producer.return_value.close.assert_called_once()


def test_extract_main_weather_data():
    historical_data = {
        'forecast': {
            'forecastday': [{
                'date': '2022-01-22',
                'day': {
                    'maxtemp_c': 10,
                    'maxtemp_f': 50,
                    'mintemp_c': 5,
                    'mintemp_f': 41,
                    'avgtemp_c': 7.5,
                    'avgtemp_f': 45.5,
                    'condition': {'text': 'Clear'},
                    'maxwind_mph': 10,
                    'maxwind_kph': 16,
                    'totalprecip_mm': 5,
                    'totalprecip_in': 0.2,
                    'avghumidity': 80
                }
            }]
        }
    }
    result = extract_main_weather_data("Minsk", historical_data)
    assert result == {
        'city': 'Minsk',
        'date': '2022-01-22',
        'max_temp_c': 10,
        'max_temp_f': 50,
        'min_temp_c': 5,
        'min_temp_f': 41,
        'avg_temp_c': 7.5,
        'avg_temp_f': 45.5,
        'condition_text': 'Clear',
        'wind_mph': 10,
        'wind_kph': 16,
        'precipitation_mm': 5,
        'precipitation_in': 0.2,
        'humidity': 80
    }


def test_extract_main_weather_data_missing_forecast():
    historical_data = {}
    result = extract_main_weather_data("Minsk", historical_data)
    assert result is None
