NAMESPACE=default
FUNCTION_NAME=world-py
ROUTE_NAME=world-py-trigger
ENV_NAME=world

echo "Deleting HTTP route (if exists)..."
fission route delete --name $ROUTE_NAME -n $NAMESPACE --ignorenotfound

echo "Deleting function (if exists)..."
fission function delete --name $FUNCTION_NAME -n $NAMESPACE --ignorenotfound

echo "Deleting all packages for this function..."
# List all packages for the function name and delete them
fission package list -n $NAMESPACE | grep "$FUNCTION_NAME" | awk '{print $1}' | while read pkg; do
    fission package delete --name "$pkg" -n $NAMESPACE -f --ignorenotfound
done

echo "Deleting environment (if exists)..."
fission env delete --name $ENV_NAME -n $NAMESPACE --ignorenotfound