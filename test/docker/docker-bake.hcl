group "default" {
  targets = ["runner-amd64", "runner-arm64"]
}

target "runner-amd64" {
  context    = "."
  dockerfile = "test/docker/Dockerfile"
  tags       = ["runner-amd64:latest"]
  platforms  = ["linux/amd64"]
}

target "runner-arm64" {
  context    = "."
  dockerfile = "test/docker/Dockerfile"
  tags       = ["runner-arm64:latest"]
  platforms  = ["linux/arm64"]
}
