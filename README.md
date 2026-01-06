# de101‑data‑pipeline
## 📖 Project Overview

`de101-data-pipeline` is a data engineering project designed to build and manage
multiple batch ETL pipelines across different data domains using a shared,
scalable architecture.

The repository focuses on demonstrating production-oriented data engineering
practices, including workflow orchestration, data quality validation,
analytical data modeling, and containerized deployment.

The project is structured as a multi-pipeline platform where each data domain
is implemented as an independent Airflow DAG with reusable pipeline components.

---

## 🎯 Key Objectives

- Orchestrate batch data pipelines using **Apache Airflow**
- Enforce data quality standards with **Great Expectations**
- Model and transform data using **DBT**, **DuckDB**, **Apache Spark**
- Promote reusability and scalability through modular pipeline design
- Enable local and cloud-ready execution via **Docker-based environments**

---

## 📂 Repository Structure


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