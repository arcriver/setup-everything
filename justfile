bake:
    docker buildx bake --load -f test/docker/docker-bake.hcl

clear-cache:
    rm -rf ~/.cache/actcache

test workflow:
    act \
        --pull=false \
        -W .github/workflows/{{workflow}}.yml \
        -P ubuntu-24.04=runner-amd64:latest \
        -P ubuntu-24.04-arm=runner-arm64:latest
