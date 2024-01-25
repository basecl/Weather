from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer


class KafkaManager:
    def __init__(self, bootstrap_servers, topic_name):
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = topic_name

    def topic_exists(self, admin_client):
        topic_metadata = admin_client.list_topics()
        return self.topic_name in topic_metadata

    def create_topic(self):
        admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)

        if not self.topic_exists(admin_client):
            topic_list = [NewTopic(name=self.topic_name, num_partitions=2, replication_factor=1)]
            admin_client.create_topics(new_topics=topic_list)
            print(f"Topic '{self.topic_name}' created successfully.")
        else:
            print(f"Topic '{self.topic_name}' already exists.")

    def consume_messages(self):
        consumer = KafkaConsumer(self.topic_name,
                                 bootstrap_servers=[self.bootstrap_servers],
                                 auto_offset_reset='earliest')

        for msg in consumer:
            print(msg.value.decode("utf-8"))


if __name__ == "__main__":
    kafka_bootstrap_servers = 'kafka:9092'
    kafka_topic = 'Belarus_Weather'

    try:
        kafka_manager = KafkaManager(kafka_bootstrap_servers, kafka_topic)
        kafka_manager.create_topic()
        kafka_manager.consume_messages()

    except Exception as e:
        print(f"Error: {e}")
