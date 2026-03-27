# List and delete old package if needed
fission package list
# fission package delete --name <your-old-package-name>

# Create new package
fission package create \
  --sourcearchive my-function.zip \
  --env world \
  --buildcmd "./build.sh"

# Watch the build
fission package info --name $(fission package list | grep my-function | awk '{print $1}') --watch



zip -r my-function.zip *


 fission function update \
  --name my-function \
  --src my-function.zip \
  --entrypoint "function.main" \
  --executortype newdeploy \
  --minscale 0 \
  --maxscale 10 \
  --mincpu 5 \
  --maxcpu 10 \
  --minmemory 128 \
  --maxmemory 512 \
  --env world \
  --namespace default \
  --yolo true