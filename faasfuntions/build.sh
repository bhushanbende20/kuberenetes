#!/bin/bash

NAMESPACE=default
FUNCTION_NAME=hello-py
ROUTE_NAME=hello-py-trigger
ENV_NAME=python
CODE_FILE=hello.py

echo "Deleting existing function, package, and route..."
fission function delete --name $FUNCTION_NAME -n $NAMESPACE --ignorenotfound
fission package delete --name $FUNCTION_NAME -n $NAMESPACE -f --ignorenotfound
fission route delete --name $ROUTE_NAME -n $NAMESPACE --ignorenotfound

echo "Creating new function $FUNCTION_NAME..."
fission function create \
  --name $FUNCTION_NAME \
  --env $ENV_NAME \
  --code $CODE_FILE \
  --entrypoint "hello.main" \
  -n $NAMESPACE

echo "Creating HTTP route for $FUNCTION_NAME..."
fission route create \
  --name $ROUTE_NAME \
  --method GET \
  --url /$FUNCTION_NAME \
  --function $FUNCTION_NAME \
  -n $NAMESPACE

echo "Function $FUNCTION_NAME created and accessible at /$FUNCTION_NAME"