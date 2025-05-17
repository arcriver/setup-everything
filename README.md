# setup-everything

A library of reusable GitHub Actions for securely setting up tools in workflows. This project consolidates various `setup-*` actions into a single repository, ensuring a consistent and secure approach to managing dependencies.

## Actions

### [Setup Kubeconform](.github/actions/setup-kubeconform/action.yml)
Installs a specific version of [Kubeconform](https://github.com/yannh/kubeconform).

### [Setup Proto](.github/actions/setup-proto/action.yml)
Installs a specific version of [Proto CLI](https://github.com/moonrepo/proto).

### [Setup Trivy](.github/actions/setup-trivy/action.yml)
Installs a specific version of [Trivy](https://github.com/aquasecurity/trivy).

## Usage

Each action requires the following inputs:
- `version`: The version of the tool to install.
- `sha256`: The SHA256 checksum of the artifact.

There are also optional inputs:
- `arch`: The architecture of the system in GitHub's `runner.arch` convention (e.g., `X64`, `ARM64`).
- `os`: The operating system of the system in GitHub's `runner.os` convention (e.g., `Linux`, `Windows`, `macOS`).
- `install-dir`: The directory where the tool will be installed.
- `github-token`: A GitHub token for authentication, defaulting to `${{ github.token }}`.

Example usage for setting up Kubeconform:

```yaml
- name: Setup Kubeconform
  uses: cedws/setup-everything/.github/actions/setup-kubeconform@main
  with:
    version: 0.7.0
    arch: X64
    sha256: c31518ddd122663b3f3aa874cfe8178cb0988de944f29c74a0b9260920d115d3
```

## Development

### Testing Locally

This project uses [act](https://github.com/nektos/act) for local testing. Build the Docker images and test workflows:

```bash
just bake
just test-all
```
