#!/usr/bin/env python3

from urllib.error import URLError, HTTPError
from typing import Optional, Dict, Any

import hashlib
import urllib.request
import json
import sys
import os

from ..utils import log_error, log_notice, append_github_output, load_manifest


class Downloader:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self._default_os_map = {
            "Linux": "Linux",
            "Windows": "Windows",
            "macOS": "macOS",
        }

    @staticmethod
    def is_archive(file_path: str) -> bool:
        return file_path.endswith((".zip", ".tar.gz", ".tar.xz"))

    @staticmethod
    def map_arch(arch: str, custom_arch_map: Optional[Dict[str, str]] = None) -> str:
        arch_map = {}

        if custom_arch_map:
            arch_map.update(custom_arch_map)

        return arch_map.get(arch, arch)

    def map_os(
        self, os_name: str, custom_os_map: Optional[Dict[str, str]] = None
    ) -> str:
        os_map = self._default_os_map.copy()

        if custom_os_map:
            os_map.update(custom_os_map)

        return os_map.get(os_name, os_name)

    def fetch_release_data(self, repo: str, release: str) -> Dict[str, Any]:
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/{release}"

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        request = urllib.request.Request(api_url, headers=headers)

        print(f"Fetching releases from {api_url}")

        try:
            with urllib.request.urlopen(request) as response:
                if response.status != 200:
                    (
                        f"Failed to fetch release information: {response.status} {response.reason}"
                    )
                    sys.exit(1)

                return json.loads(response.read().decode())
        except HTTPError as e:
            (f"HTTP Error: {e.code} {e.reason}")
            sys.exit(1)
        except URLError as e:
            (f"URL Error: {e.reason}")
            sys.exit(1)

    def download_artifact(self, asset_url: str, output_file: str) -> None:
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        request = urllib.request.Request(asset_url, headers=headers)

        print(f"Downloading artifact from {asset_url}")

        try:
            with (
                urllib.request.urlopen(request) as response,
                open(output_file, "wb") as out_file,
            ):
                out_file.write(response.read())
        except HTTPError as e:
            (f"HTTP Error: {e.code} {e.reason}")
            sys.exit(1)
        except URLError as e:
            (f"URL Error: {e.reason}")
            sys.exit(1)

    @staticmethod
    def get_checksum(file_path: str) -> str:
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    @staticmethod
    def verify_checksum(file_path: str, expected_sha256: str) -> None:
        calculated_sha256 = Downloader.get_checksum(file_path)
        if calculated_sha256 != expected_sha256:
            os.remove(file_path)

            log_error(
                f"Checksum verification failed!\n"
                f"Expected: {expected_sha256.ljust(32)}\n"
                f"Got:      {calculated_sha256.ljust(32)}"
            )
            sys.exit(1)

        print("Checksum verification passed.")

    def get_release(
        self,
        arch: str,
        os_name: str,
        version: str,
        output_file: str,
        expected_sha256: str,
        manifest: str,
        release: Optional[str] = None,
    ) -> Any:
        if not release:
            release = f"v{version}"

        manifest_data = load_manifest(manifest)

        repo = manifest_data.get("repo")
        if not repo:
            ("Repository not specified in manifest")
            sys.exit(1)

        pattern = manifest_data.get("pattern")
        if not pattern:
            ("Pattern not specified in manifest")
            sys.exit(1)

        arch_mappings = manifest_data.get("mappings", {}).get("arch", {})
        os_mappings = manifest_data.get("mappings", {}).get("os", {})

        mapped_arch = self.map_arch(arch, arch_mappings)
        mapped_os = self.map_os(os_name, os_mappings)

        formatted_pattern = pattern.format(
            version=version, release=release, os=mapped_os, arch=mapped_arch
        )

        release_data = self.fetch_release_data(repo, release)
        asset = next(
            (
                a
                for a in release_data.get("assets", [])
                if formatted_pattern in a["name"] and self.is_archive(a["name"])
            ),
            None,
        )

        if not asset:
            (f"No matching asset found for pattern: {formatted_pattern}")
            sys.exit(1)

        return asset

    def download_release_artifact(
        self,
        arch: str,
        os_name: str,
        version: str,
        output_file: str,
        expected_sha256: str,
        manifest: str,
        release: Optional[str] = None,
    ) -> str:
        asset = self.get_release(
            arch, os_name, version, output_file, expected_sha256, manifest, release
        )

        filename = asset["name"]
        asset_url = asset["browser_download_url"]

        append_github_output("filename", filename)

        if os.path.exists(output_file):
            log_notice(f"File {output_file} already exists. Skipping download.")
        else:
            self.download_artifact(asset_url, output_file)

        self.verify_checksum(output_file, expected_sha256)

        return filename


def download_from_env(manifest: str) -> str:
    arch = os.getenv("ARCH", "")
    os_name = os.getenv("OS", "")
    version = os.getenv("VERSION", "")
    release = os.getenv("RELEASE")
    output_file = os.getenv("FILE", "")
    expected_sha256 = os.getenv("SHA256", "")
    github_token = os.getenv("GITHUB_TOKEN", "")

    if not all([arch, os_name, version, output_file, expected_sha256]):
        log_error("Missing required environment variables")
        sys.exit(1)

    downloader = Downloader(github_token)
    return downloader.download_release_artifact(
        arch=arch,
        os_name=os_name,
        version=version,
        output_file=output_file,
        expected_sha256=expected_sha256,
        manifest=manifest,
        release=release,
    )


def main():
    import argparse

    def parse_arguments():
        parser = argparse.ArgumentParser(
            description="Download a GitHub release artifact."
        )
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
            "--version",
            required=True,
            help="Version number of the release (e.g., 0.62.1)",
        )
        parser.add_argument(
            "--release",
            help="Release tag of the GitHub release (defaults to --version)",
        )
        parser.add_argument(
            "--file", required=True, help="Path to download the artifact"
        )
        parser.add_argument(
            "--sha256", required=True, help="Expected SHA256 checksum of the artifact"
        )
        parser.add_argument(
            "--github-token",
            help="GitHub token for authentication",
        )
        parser.add_argument(
            "--manifest",
            required=True,
            help="Path of application manifest to use for downloading the artifact",
        )

        return parser.parse_args()

    args = parse_arguments()

    if all([args.arch, args.os, args.version, args.file, args.sha256]):
        downloader = Downloader(args.github_token)
        downloader.download_release_artifact(
            arch=args.arch,
            os_name=args.os,
            version=args.version,
            output_file=args.file,
            expected_sha256=args.sha256,
            manifest=args.manifest,
            release=args.release,
        )
    else:
        download_from_env(args.manifest)
