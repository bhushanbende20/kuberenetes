#!/bin/bash

NAMESPACE=default
FUNCTION_NAME=world-py
ROUTE_NAME=world-py-trigger
ENV_NAME=world
CODE_FILE=world.py

# Use Fission's open-source default images (from your release)
PYTHON_ENV_IMAGE="fission/python-env-3.9:latest"
PYTHON_BUILDER_IMAGE="fission/python-builder-3.9:latest"

echo "Checking if environment $ENV_NAME exists..."
EXISTING_ENV=$(fission env list -n $NAMESPACE | grep "^$ENV_NAME\b")

if [ -z "$EXISTING_ENV" ]; then
    echo "Environment $ENV_NAME does not exist. Creating..."
    fission env create \
      --name $ENV_NAME \
      --image $PYTHON_ENV_IMAGE \
      --builder $PYTHON_BUILDER_IMAGE \
      --poolsize 0 \
      --namespace $NAMESPACE
else
    echo "Environment $ENV_NAME already exists."
fi

echo "Deleting existing function, package, and route..."
fission function delete --name $FUNCTION_NAME -n $NAMESPACE --ignorenotfound
fission package delete --name $FUNCTION_NAME -n $NAMESPACE -f --ignorenotfound
fission route delete --name $ROUTE_NAME -n $NAMESPACE --ignorenotfound

echo "Creating new function $FUNCTION_NAME with newdeploy executor..."
fission function create \
  --name $FUNCTION_NAME \
  --env $ENV_NAME \
  --code $CODE_FILE \
  --entrypoint "main" \
  --executortype newdeploy \
  --minscale 0 \
  --maxscale 5 \
  -n $NAMESPACE

echo "Creating HTTP route for $FUNCTION_NAME..."
fission route create \
  --name $ROUTE_NAME \
  --method GET \
  --url /$FUNCTION_NAME \
  --function $FUNCTION_NAME \
  -n $NAMESPACE

echo "Function $FUNCTION_NAME created and accessible at /$FUNCTION_NAME"