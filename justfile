bake:
    docker buildx bake --load

clear-cache:
    rm -rf ~/.cache/act

test workflow:
    act \
        --container-architecture linux/amd64 \
        --pull=false \
        -W .github/workflows/{{workflow}}.yml \
        -P ubuntu-latest=runner-amd64:latest

test-all:
    just test setup-kubeconform
    just test setup-proto
    just test setup-trivy
