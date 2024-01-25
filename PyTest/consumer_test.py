import pytest
from unittest.mock import MagicMock
from consumer import KafkaManager


@pytest.fixture
def kafka_manager():
    return KafkaManager(bootstrap_servers='kafka:9092', topic_name='Belarus_Weather')


def test_topic_exists_true(kafka_manager):
    admin_client_mock = MagicMock()
    admin_client_mock.list_topics.return_value = ['Belarus_Weather', 'Other_Topic']

    assert kafka_manager.topic_exists(admin_client_mock)


def test_topic_exists_false(kafka_manager):
    admin_client_mock = MagicMock()
    admin_client_mock.list_topics.return_value = ['Other_Topic']

    assert not kafka_manager.topic_exists(admin_client_mock)


def test_create_topic_already_exists(capfd, kafka_manager):
    admin_client_mock = MagicMock()
    admin_client_mock.list_topics.return_value = ['Belarus_Weather']

    kafka_manager.create_topic()

    out, _ = capfd.readouterr()
    assert "already exists" in out
