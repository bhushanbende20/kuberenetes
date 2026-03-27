#!/bin/bash

# Namespace
NAMESPACE=default
FUNC_NAME=ne-py
ZIP_FILE=ne.zip
PY_FILE=ne_fn.py
REQ_FILE=requirements.txt
ENTRY_POINT="ne_fn.main"
URL_PATH="/ne-py"
ENV_NAME=python

echo "==== Deleting existing function, package, and route if any ===="

# Delete HTTP trigger (route)
EXISTING_ROUTE=$(fission route list -n $NAMESPACE | grep $URL_PATH | awk '{print $1}')
if [ ! -z "$EXISTING_ROUTE" ]; then
    echo "Deleting existing route $EXISTING_ROUTE"
    fission route delete --name $EXISTING_ROUTE -n $NAMESPACE
fi

# Delete function
fission function delete --name $FUNC_NAME -n $NAMESPACE --ignorenotfound

# Delete package
EXISTING_PKG=$(fission package list -n $NAMESPACE | grep $FUNC_NAME | awk '{print $1}')
if [ ! -z "$EXISTING_PKG" ]; then
    echo "Deleting existing package $EXISTING_PKG"
    fission package delete --name $EXISTING_PKG -n $NAMESPACE
fi

echo "==== Creating zip package ===="
# Recreate zip file with correct structure
zip -r $ZIP_FILE $PY_FILE $REQ_FILE

echo "==== Creating function package ===="
fission package create \
    --name $FUNC_NAME \
    --source $ZIP_FILE \
    --env $ENV_NAME \
    -n $NAMESPACE

echo "==== Creating function ===="
fission function create \
    --name $FUNC_NAME \
    --env $ENV_NAME \
    --pkgname $FUNC_NAME \
    --entrypoint $ENTRY_POINT \
    -n $NAMESPACE

echo "==== Creating HTTP route ===="
fission route create \
    --method GET \
    --url $URL_PATH \
    --function $FUNC_NAME \
    -n $NAMESPACE

echo "==== Done ===="
# echo "Test with: curl http://localhost:8080$URL_PATH"