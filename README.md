# de101‑data‑pipeline
## 📖 Project Overview

`de101-data-pipeline` is a learning/proof‑of‑concept project to build batch ETL pipelines for multiple data domains such as stock market data and game logs. The goal is to practice and demonstrate:

- **Orchestration**: Using Apache Airflow to schedule and run workflows  
- **Data Validation**: Applying Great Expectations to validate data after extraction  
- **Transformation**: Using dbt to perform further modeling and transformations  
- **Scalable Deployment**: Containerization with Docker and eventual deployment to Kubernetes via Helm  

This project is ideal for anyone looking to build hands‑on experience in a full-fledged data engineering pipeline.

---

## 📂 Directory Structure
```
de101-data-pipeline/
├── dags/
│   ├── project1/
│   │   ├── etl/               # Airflow DAGs for ETL tasks
│   │   ├── ge_checks/         # DAGs for Great Expectations validations
│   │   └── dbt/models/        # dbt models for the project/domain
│   └── other_domain/          # Placeholder for future domains
├── plugins/                    # Custom Airflow Operators, Hooks, and Sensors
├── src/                        # ETL modules (extract / transform / load)
├── configs/                     # Configuration files per environment
│   ├── dev.yaml
│   └── prod.yaml
├── docker/                      # Dockerfiles & docker-compose for local setup
│   ├── Dockerfile.airflow
│   └── docker-compose.yaml
├── helm/airflow/                # Helm chart for Kubernetes deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── templates/
│   │   └── airflow-deployment.yaml
│   └── secrets/
│       └── airflow-connections.yaml
├── tests/                       # Unit tests for DAGs, src modules, plugins
├── requirements.txt
└── .env
```


---

## 🛠 Technology Stack
- **Orchestration**: Apache Airflow  
- **Validation**: Great Expectations  
- **Modeling / Transformation**: dbt  
- **Containerization**: Docker Compose  
- **Deployment (future)**: Kubernetes + Helm  
- **Storage / Targets**: S3 / MinIO, Databricks  

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose  
- (Optional) Access credentials for S3 / MinIO or Databricks  
- Python 3.9+ (for local dev)  

### Local Setup

1. Clone the repository  
   ```bash
   git clone https://github.com/your-username/de101-data-pipeline.git
   cd de101-data-pipeline


Create a .env file based on the example (or config):

AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
S3_ENDPOINT=http://localhost:9000


Build and start Airflow via Docker Compose:

docker-compose up --build


Open Airflow UI:
Navigate to http://localhost:8080 in your browser.

✅ Example Workflow

Airflow triggers an ETL DAG (e.g. stock/etl/daily)

ETL job extracts raw data, transforms it, and loads it into a staging location (S3 or Databricks)

Once loaded, a GE validation DAG runs to check data quality

If validation succeeds, a dbt DAG runs to model data and produce final tables

📦 Configuration

All environment-specific configurations are located in configs/:

configs/dev.yaml — for local development

configs/staging.yaml — for staging environment

configs/prod.yaml — for production

These config files define connections (S3, Databricks), credentials, and other environment variables.

👥 Contributing

Contributions are welcome! Here's how you can help:

Fork the repository

Create a new branch: git checkout -b feature/your-feature

Make your changes (add DAG, improve src, etc.)

Add / update tests under tests/

Commit your changes: git commit -m "feat: description of your change"

Push to your branch: git push origin feature/your-feature

Open a Pull Request

Please follow existing code style, and ensure new code is covered by tests.

📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

🔗 Links & Resources

Airflow Documentation

Great Expectations Documentation

dbt Documentation