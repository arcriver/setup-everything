build-image:
    docker build -t act-with-gh .

test:
    act -W setup-trivy.yml -P ubuntu-latest=act-with-gh --pull=false -j setup-trivy -s GITHUB_TOKEN=$(gh auth token)
