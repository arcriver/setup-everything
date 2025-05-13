group "default" {
  targets = ["act-with-gh-amd64", "act-with-gh-arm64"]
}

target "act-with-gh-amd64" {
  context    = "."
  dockerfile = "Dockerfile"
  tags       = ["act-with-gh-amd64:latest"]
  platforms  = ["linux/amd64"]
}

target "act-with-gh-arm64" {
  context    = "."
  dockerfile = "Dockerfile"
  tags       = ["act-with-gh-arm64:latest"]
  platforms  = ["linux/arm64"]
}
