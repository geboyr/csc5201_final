-- Initialize Ingredients Database
CREATE DATABASE IF NOT EXISTS ingredients_db;
USE ingredients_db;

CREATE TABLE ingredient (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL
);

-- Initialize Stats Database
CREATE DATABASE IF NOT EXISTS stats_db;
USE stats_db;

CREATE TABLE stat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(80) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    response_time FLOAT NOT NULL
);

