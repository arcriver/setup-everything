#!/usr/bin/env python3

from urllib.error import URLError, HTTPError
from typing import Optional, Dict, Any

import hashlib
import urllib.request
import json
import sys
import os
import argparse

from http import HTTPStatus
from ..utils import log_error, log_notice, append_github_output, load_manifest


class Downloader:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token

    @staticmethod
    def is_archive(file_path: str) -> bool:
        return file_path.endswith((".zip", ".tar.gz", ".tar.xz"))

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
                return json.loads(response.read().decode())
        except HTTPError as e:
            if e.code == HTTPStatus.NOT_FOUND:
                log_error(f"Release {release} not found in repository {repo}")
                log_error(
                    "Please raise a bug report at https://github.com/arcriver/setup-everything if this is unexpected"
                )
                sys.exit(1)

            log_error(f"HTTP Error: {e.code} {e.reason}")
            sys.exit(1)
        except URLError as e:
            log_error(f"URL Error: {e.reason}")
            sys.exit(1)

    def download_asset(self, asset_url: str, output_file: str) -> None:
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        request = urllib.request.Request(asset_url, headers=headers)

        print(f"Downloading asset from {asset_url}")

        try:
            with (
                urllib.request.urlopen(request) as response,
                open(output_file, "wb") as out_file,
            ):
                out_file.write(response.read())
        except HTTPError as e:
            if e.code == HTTPStatus.NOT_FOUND:
                log_error(f"Asset not found: {asset_url}")
                sys.exit(1)

            log_error(f"HTTP Error: {e.code} {e.reason}")
            sys.exit(1)
        except URLError as e:
            log_error(f"URL Error: {e.reason}")
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
            log_error("Repository not specified in manifest")
            sys.exit(1)

        assets = manifest_data.get("assets")
        if not assets:
            log_error("Assets not specified in manifest")
            sys.exit(1)

        os_assets = assets.get(os_name)
        if not os_assets:
            log_error(f"No assets found for OS {os_name}")
            sys.exit(1)

        asset_url_template = os_assets.get(arch)
        if not asset_url_template:
            log_error(f"No assets found for ${os_name} {arch}")
            sys.exit(1)

        expected_filename = asset_url_template.format(version=version, release=release)

        release_data = self.fetch_release_data(repo, release)
        asset = next(
            (
                a
                for a in release_data.get("assets", [])
                if a["name"] == expected_filename
            ),
            None,
        )

        if not asset:
            log_error(f"No matching asset found for filename: {expected_filename}")
            sys.exit(1)

        return asset

    def download_release_asset(
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
            self.download_asset(asset_url, output_file)

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
    return downloader.download_release_asset(
        arch=arch,
        os_name=os_name,
        version=version,
        output_file=output_file,
        expected_sha256=expected_sha256,
        manifest=manifest,
        release=release,
    )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Download a GitHub release asset.")
    parser.add_argument(
        "--arch",
        required=True,
        help="Target architecture (e.g., X64, X86, ARM64, ARM)",
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
    parser.add_argument("--file", required=True, help="Path to download the asset")
    parser.add_argument(
        "--sha256", required=True, help="Expected SHA256 checksum of the asset"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token for authentication",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path of application manifest to use for downloading the asset",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    if all([args.arch, args.os, args.version, args.file, args.sha256]):
        downloader = Downloader(args.github_token)
        downloader.download_release_asset(
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
