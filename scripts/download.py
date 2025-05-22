#!/usr/bin/env python3

from urllib.error import URLError, HTTPError

import argparse
import hashlib
import urllib.request
import json
import sys
import os


def log_error(message):
    m = message.replace("\n", "%0A")
    print(f"::error::{m}")


def set_github_output(name, value):
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        return

    with open(github_output, "a") as f:
        f.write(f"{name}={value}\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Download a GitHub release artifact.")
    parser.add_argument(
        "--arch",
        required=True,
        help="Target architecture (e.g., X64, ARM64, ARM, IA32)",
    )
    parser.add_argument(
        "--os",
        required=True,
        help="Target operating system (e.g., Linux, Windows, macOS)",
    )
    parser.add_argument(
        "--version", required=True, help="Version number of the release (e.g., 0.62.1)"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version number of the release (e.g., 0.62.1)",
    )
    parser.add_argument(
        "--release",
        help="Release tag of the GitHub release (defaults to --version)",
    )
    parser.add_argument("--file", required=True, help="Path to download the artifact")
    parser.add_argument(
        "--sha256", required=True, help="Expected SHA256 checksum of the artifact"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token for authentication",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in the format owner/repo (e.g., aquasecurity/trivy)",
    )
    parser.add_argument(
        "--pattern",
        required=True,
        help="Pattern for the artifact filename, e.g., 'trivy_{version}_{os_name}-{arch}.tar.gz'",
    )
    parser.add_argument(
        "--map-arch",
        action="append",
        help="Custom architecture mapping in the format SOURCE=TARGET",
    )
    parser.add_argument(
        "--map-os",
        action="append",
        help="Custom OS mapping in the format SOURCE=TARGET",
    )

    args = parser.parse_args()

    if not args.release:
        args.release = f"v{args.version}"

    return args


def map_arch(arch, custom_arch_map):
    arch_map = {}

    for mapping in custom_arch_map:
        source, target = mapping.split("=")
        arch_map[source] = target

    return arch_map.get(arch, arch)


def map_os(os, custom_os_map):
    os_map = {"Linux": "Linux", "Windows": "Windows", "macOS": "macOS"}

    for mapping in custom_os_map:
        source, target = mapping.split("=")
        os_map[source] = target

    return os_map.get(os, os)


def map_ext(os):
    if os == "Windows":
        return "zip"
    if os == "Linux":
        return "tar.gz"
    if os == "macOS":
        return "tar.gz"

    log_error(f"Unsupported OS: {os}")
    sys.exit(1)


def fetch_release_data(repo, release, github_token):
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{release}"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    request = urllib.request.Request(api_url, headers=headers)

    print(f"Fetching releases from {api_url}")

    try:
        with urllib.request.urlopen(request) as response:
            if response.status != 200:
                log_error(
                    f"Failed to fetch release information: {response.status} {response.reason}"
                )
                sys.exit(1)

            return json.loads(response.read().decode())
    except HTTPError as e:
        log_error(f"HTTP Error: {e.code} {e.reason}")
        sys.exit(1)
    except URLError as e:
        log_error(f"URL Error: {e.reason}")
        sys.exit(1)


def download_artifact(asset_url, output_file, github_token):
    headers = {"Authorization": f"token {github_token}"}
    request = urllib.request.Request(asset_url, headers=headers)

    print(f"Downloading artifact from {asset_url}")

    try:
        with (
            urllib.request.urlopen(request) as response,
            open(output_file, "wb") as out_file,
        ):
            out_file.write(response.read())
    except HTTPError as e:
        log_error(f"HTTP Error: {e.code} {e.reason}")
        sys.exit(1)
    except URLError as e:
        log_error(f"URL Error: {e.reason}")
        sys.exit(1)


def verify_checksum(file_path, expected_sha256):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    calculated_sha256 = sha256_hash.hexdigest()
    if calculated_sha256 != expected_sha256:
        log_error(
            f"Checksum verification failed!\n"
            f"Expected: {expected_sha256.ljust(32)}\n"
            f"Got:      {calculated_sha256.ljust(32)}"
        )
        sys.exit(1)

    print("Checksum verification passed.")


def main():
    args = parse_arguments()

    arch = map_arch(args.arch, args.map_arch)
    os_name = map_os(args.os, args.map_os)
    ext = map_ext(args.os)

    pattern = args.pattern.format(
        version=args.version, release=args.release, os=os_name, arch=arch, ext=ext
    )

    release_data = fetch_release_data(args.repo, args.release, args.github_token)
    asset = next(
        (a for a in release_data.get("assets", []) if pattern in a["name"]), None
    )
    if not asset:
        log_error(f"No matching asset found for pattern: {pattern}")
        sys.exit(1)

    filename = asset["name"]
    asset_url = asset["browser_download_url"]

    set_github_output("filename", filename)

    download_artifact(asset_url, filename, args.github_token)
    verify_checksum(filename, args.sha256)


if __name__ == "__main__":
    main()
