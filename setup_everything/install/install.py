#!/usr/bin/env python3

import argparse
import shutil
import tarfile
import tempfile
import zipfile
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..utils import log_error, load_manifest, append_github_path


class Installer:
    @staticmethod
    def get_extract_patterns(manifest: Dict[str, Any]) -> Optional[List[str]]:
        extract_patterns = manifest.get("extract_patterns")

        if not extract_patterns:
            return None

        if isinstance(extract_patterns, list):
            return extract_patterns

        return None

    @staticmethod
    def should_extract_file(filename: str, patterns: Optional[List[str]]) -> bool:
        if not patterns:
            return True

        return any(pattern in filename for pattern in patterns)

    def extract_zip(
        self, zip_path: Path, temp_dir: str, patterns: Optional[List[str]]
    ) -> None:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                if self.should_extract_file(member, patterns):
                    zip_ref.extract(member, temp_dir)

    def extract_tar(
        self, tar_path: Path, temp_dir: str, patterns: Optional[List[str]]
    ) -> None:
        with tarfile.open(tar_path, "r:*") as tar_ref:
            for member in tar_ref.getmembers():
                if self.should_extract_file(member.name, patterns):
                    tar_ref.extract(member, temp_dir, filter="data")

    def install_asset(
        self, file_path, name, install_dir, manifest: Dict[str, Any]
    ) -> None:
        file_path = Path(file_path)
        name = Path(name)

        install_dir = Path(install_dir)
        install_dir.mkdir(parents=True, exist_ok=True)

        extract_patterns = self.get_extract_patterns(manifest)

        if zipfile.is_zipfile(file_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                self.extract_zip(file_path, temp_dir, extract_patterns)

                for item in Path(temp_dir).rglob("*"):
                    if item.is_file():
                        dest_path = install_dir / item.name
                        shutil.copy2(item, dest_path)
                        dest_path.chmod(0o755)

        elif tarfile.is_tarfile(file_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                self.extract_tar(file_path, temp_dir, extract_patterns)

                for item in Path(temp_dir).rglob("*"):
                    if item.is_file():
                        dest_path = install_dir / item.name
                        shutil.copy2(item, dest_path)
                        dest_path.chmod(0o755)

        else:
            dest_path = install_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            dest_path.chmod(0o755)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Install an asset by extracting or moving it."
    )
    parser.add_argument(
        "--file", required=True, help="Path to the asset file to install"
    )
    parser.add_argument("--name", required=True, help="Original filename of the asset")
    parser.add_argument(
        "--install-dir", required=True, help="Directory to install the asset"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path of application manifest to use for installation patterns",
    )

    return parser.parse_args()


def install_from_env(manifest_path: str) -> None:
    file_path = os.getenv("FILE", "")
    name = os.getenv("NAME", "")
    install_dir = os.getenv("INSTALL_DIR", "")

    if not all([file_path, name, install_dir]):
        log_error("Missing required environment variables")
        sys.exit(1)

    installer = Installer()
    manifest = load_manifest(manifest_path)
    installer.install_asset(file_path, name, install_dir, manifest)

    append_github_path(install_dir)


def main():
    args = parse_arguments()
    manifest = load_manifest(args.manifest)

    if all([args.file, args.install_dir]):
        installer = Installer()
        installer.install_asset(args.file, args.name, args.install_dir, manifest)
        print(f"Successfully installed asset to {args.install_dir}")
    else:
        install_from_env(args.manifest)

    append_github_path(args.install_dir)


if __name__ == "__main__":
    main()
