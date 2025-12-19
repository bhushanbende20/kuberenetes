FROM flink:1.18.1-scala_2.12-java11

# Install Python + deps
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install PyFlink + REQUIRED deps
RUN pip3 install \
    # apache-flink==1.18.1 \
    protobuf \
    google \
    cloudpickle

# Make python resolvable
RUN ln -sf /usr/bin/python3 /usr/local/bin/python

# Create dirs
RUN mkdir -p /opt/flink/jobs /opt/flink/data /opt/flink/output

# Copy job + data
COPY finance_csv_to_json.py /opt/flink/jobs/
COPY financial_data/ /opt/flink/data/

# Explicit Python config
ENV PYFLINK_CLIENT_EXECUTABLE=/usr/bin/python3
ENV PYFLINK_PYTHON_EXECUTABLE=/usr/bin/python3

WORKDIR /opt/flink
