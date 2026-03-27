# Get the latest package name
LATEST=$(fission package list -n default | grep hello-py | sort -k4 -r | head -n1 | awk '{print $1}')

# Delete all other packages
for pkg in $(fission package list -n default | grep hello-py | awk '{print $1}'); do
    if [ "$pkg" != "$LATEST" ]; then
        fission package delete --name $pkg -n default --force
        echo "Deleted package: $pkg"
    fi
done