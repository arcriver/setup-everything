bake:
    docker buildx bake --load

test workflow arch:
    act \
        --container-architecture linux/{{arch}} \
        --pull=false \
        -W test/{{workflow}}.yml \
        -P ubuntu-latest=act-with-gh-{{arch}}:latest

test-workflow workflow:
    just test {{workflow}} amd64
    just test {{workflow}} arm64

test-all:
    just test-workflow setup-trivy
