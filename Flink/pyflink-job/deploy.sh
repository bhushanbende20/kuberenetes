#!/bin/bash

# --- Configuration ---
JOB_FILE="word_count.py"
TARGET_DIR="/opt/flink/usrlib"  # <-- The directory that needs to be created
JOB_MANAGER_LABEL="app=flink,component=jobmanager"
# ---------------------

echo "🚀 Starting PyFlink Job Submission to Kubernetes Session Cluster..."

# 1. Find the name of your running JobManager pod
JOB_MANAGER_POD=$(kubectl get pods -l $JOB_MANAGER_LABEL -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$JOB_MANAGER_POD" ]; then
    echo "❌ Error: Flink JobManager pod not found with labels: $JOB_MANAGER_LABEL"
    exit 1
fi

echo "✅ JobManager Pod Name found: $JOB_MANAGER_POD"

if [ ! -f "$JOB_FILE" ]; then
    echo "❌ Error: Local job file '$JOB_FILE' not found."
    exit 1
fi

# 2. *** NEW STEP: Create the target directory inside the container ***
echo "📂 Creating target directory $TARGET_DIR inside the container..."
# Using 'mkdir -p' ensures the directory is created, and doesn't fail if it already exists.
if kubectl exec -it "$JOB_MANAGER_POD" -- mkdir -p "$TARGET_DIR"; then
    echo "✅ Directory created successfully."
else
    echo "❌ Error creating directory. Exiting."
    exit 1
fi

# 3. Copy the Python job file to the JobManager pod
echo "📦 Copying $JOB_FILE to $JOB_MANAGER_POD:$TARGET_DIR/..."
if kubectl cp "$JOB_FILE" "$JOB_MANAGER_POD":"$TARGET_DIR/$JOB_FILE"; then
    echo "✅ File successfully copied."
else
    echo "❌ Error copying file (This error should now be fixed). Check kubectl permissions or pod status."
    exit 1
fi

# 4. Submit the PyFlink job using the 'flink run' command
echo "🏃 Submitting PyFlink job to the Session Cluster..."
kubectl exec -it "$JOB_MANAGER_POD" -- \
/opt/flink/bin/flink run \
-py "$TARGET_DIR/$JOB_FILE"

echo "🎉 Job submission command executed."