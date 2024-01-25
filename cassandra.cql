CREATE KEYSPACE IF NOT EXISTS weather WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE weather;

CREATE TABLE IF NOT EXISTS r_city (
    city TEXT,
    date DATE,
    max_temp_c DOUBLE,
    max_temp_f DOUBLE,
    min_temp_c DOUBLE,
    min_temp_f DOUBLE,
    avg_temp_c DOUBLE,
    avg_temp_f DOUBLE,
    condition_text TEXT,
    wind_mph DOUBLE,
    wind_kph DOUBLE,
    precipitation_mm DOUBLE,
    precipitation_in DOUBLE,
    humidity DOUBLE,
    PRIMARY KEY (city, date)
) WITH compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_size': '30',
    'compaction_window_unit': 'DAYS'
};