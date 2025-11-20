# Base Airflow image with Python 3.12
FROM apache/airflow:3.1.3-python3.12

# Set working directory inside container
WORKDIR /opt/airflow

# Intall airflow requirements 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========================
# Create necessary directories
# ========================
RUN mkdir -p /opt/airflow/logs /opt/airflow/plugins /opt/airflow/config /opt/airflow/dags \
    && chown -R airflow:0 /opt/airflow/logs /opt/airflow/plugins /opt/airflow/config /opt/airflow/dags

# copy dag and necessary files
COPY --chown=airflow:airflow airflow/dags/ /opt/airflow/dags/
COPY --chown=airflow:airflow src/ /opt/airflow/src/

# ========================
# Set PYTHONPATH to include src
# ========================
ENV PYTHONPATH="/opt/airflow/src:$PYTHONPATH"

# ========================
# Switch to non-root user
# ========================
USER airflow

# ========================
# Entrypoint and default command
# ========================
ENTRYPOINT ["/entrypoint"]
CMD ["webserver"]
