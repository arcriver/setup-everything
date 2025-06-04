# setup-everything

A library of reusable GitHub Actions for securely setting up tools in workflows. This project replaces various `setup-*` actions into a single repository, ensuring a consistent and secure approach to managing dependencies. All Actions perform mandatory SHA256 checksum verification to ensure the integrity of downloaded artifacts and reduce the risk of supply chain attacks.

## Usage

All of the Actions take the same inputs and work in the same way. They will download the specific version of the app, verify the SHA256 checksum, and install it to a specified directory.

> [!NOTE]
> It's recommended that you fork this repo into your own GitHub account or organisation and use the forked version in your workflows. This is more secure than referencing a tag or branch in the main repository, as it allows you to carefully control changes.

| Input          | Type   | Required | Default                  | Description                                            |
| -------------- | ------ | -------- | ------------------------ | ------------------------------------------------------ |
| `version`      | string | Yes      | -                        | Version of application to install (without 'v' prefix) |
| `arch`         | string | No       | `${{ runner.arch }}`     | Target architecture (e.g. X64, X86, ARM64, ARM)        |
| `os`           | string | No       | `${{ runner.os }}`       | Target operating system (e.g. Linux, Windows, macOS)   |
| `sha256`       | string | Yes      | -                        | SHA256 checksum to verify the downloaded artifact      |
| `install-dir`  | string | No       | `${{ runner.temp }}/bin` | Directory to install application                       |
| `github-token` | string | No       | `${{ github.token }}`    | GitHub token for authentication                        |

Example usage for setting up Kubeconform:

```yaml
- name: Setup Kubeconform
  uses: cedws/setup-everything/.github/actions/setup-kubeconform@{...}
  with:
    version: 0.7.0
    arch: X64
    sha256: c31518ddd122663b3f3aa874cfe8178cb0988de944f29c74a0b9260920d115d3
```

See [here](./docs/actions.md) for a list of available Actions.

## Development

### Prerequisites

Please ensure you have installed the pre-commit hooks and have validated your changes before submitting a pull request.

### Testing Locally

This project uses [act](https://github.com/nektos/act) for local testing. Build the Docker images and test workflows:

```bash
just bake
just test-all
```
