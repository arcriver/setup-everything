bake:
    docker buildx bake --load

clear-cache:
    rm -rf ~/.cache/actcache

test workflow:
    act \
        --pull=false \
        -W .github/workflows/{{workflow}}.yml \
        -P ubuntu-24.04=runner-amd64:latest \
        -P ubuntu-24.04-arm=runner-arm64:latest

test-all:
    just test setup-kubeconform
    just test setup-proto
    just test setup-trivy
