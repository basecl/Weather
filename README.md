# Weather Data Analysis Project

This project fetches weather data from an API for regional cities of Belarus, processes it, and performs analysis on it. It utilizes Docker and Docker Compose to orchestrate the services needed for the project.

## Prerequisites

Ensure you have Docker and Docker Compose installed on your system.

## Getting Started

1. Clone this repository to your local machine.
2. Navigate to the project directory.

## Usage

To run the project, execute the following command:

```bash
docker-compose up
```

This will start the services defined in the `docker-compose.yml` file.

## Services

### Kafka

- **Image**: bitnami/kafka:3.5.1
- **Purpose**: Message broker for handling streaming data.
- **Healthcheck**: Verifies if Kafka topics are accessible.

### Cassandra

- **Image**: cassandra:4.1.3
- **Purpose**: NoSQL database for storing processed weather data.
- **Healthcheck**: Checks if Cassandra keyspaces are accessible.

### Spark

- **Build Context**: ./ETL/Load_and_Transform/
- **Purpose**: Data processing and transformation.
- **Healthcheck**: Verifies if Spark application is running.

### Consumer

- **Build Context**: ./ETL/Extract/consumer/
- **Purpose**: Extracts data from Kafka for processing.
- **Dependency**: Depends on Kafka service being healthy.

### Download

- **Build Context**: ./ETL/Extract/producer/
- **Purpose**: Extracts data from the API.
- **Dependency**: Depends on Spark service being healthy.

### Analysis

- **Build Context**: ./Analys/
- **Purpose**: Performs analysis on processed data.
- **Dependency**: Depends on Cassandra keyspace being loaded successfully.

### Test

- **Build Context**: .
- **Purpose**: Runs tests for the project.
- **Dependency**: Depends on Cassandra keyspace being loaded successfully.

## Environment Variables

- `KAFKA_CFG_NODE_ID`: Kafka configuration.
- `CASSANDRA_CLUSTER_NAME`: Cassandra configuration.
- `NGINX_WORKER_PROCESSES`: Environment variable for NGINX worker processes in the analysis service.

## Ports

- **Cassandra**: 9042
- **Spark**: 4040
- **Analysis**: 8080

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
