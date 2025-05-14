bake:
    docker buildx bake --load

test workflow:
    act \
        --container-architecture linux/amd64 \
        --pull=false \
        -W .github/workflows/{{workflow}}.yml \
        -P ubuntu-latest=act-with-gh-amd64:latest

test-all:
    just test setup-trivy
