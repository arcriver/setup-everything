#!/usr/bin/env python3

import os
import json
import sys
from typing import Dict, Any


def log_notice(message: str) -> None:
    if not os.getenv("CI"):
        print(f"Notice: {message}")
        return

    message = message.replace("\n", "%0A")
    print(f"::notice::{message}")


def log_error(message: str) -> None:
    if not os.getenv("CI"):
        print(f"Error: {message}")
        return

    message = message.replace("\n", "%0A")
    print(f"::error::{message}")


def append_github_output(name: str, value: str) -> None:
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        return

    with open(github_output, "a") as f:
        f.write(f"{name}={value}\n")


def append_github_path(path: str) -> None:
    github_path = os.getenv("GITHUB_PATH")
    if not github_path:
        return

    with open(github_path, "a") as f:
        f.write(f"{path}\n")


def validate_manifest_schema(manifest: Dict[str, Any]) -> None:
    required_fields = ["repo", "assets"]

    for field in required_fields:
        if field not in manifest:
            log_error(f"Missing required field '{field}' in manifest")
            sys.exit(1)

    if not isinstance(manifest["repo"], str):
        log_error("Field 'repo' must be a string")
        sys.exit(1)

    if not isinstance(manifest["assets"], dict):
        log_error("Field 'assets' must be a dictionary")
        sys.exit(1)

    if "mappings" in manifest and not isinstance(manifest["mappings"], dict):
        log_error("Field 'mappings' must be a dictionary")
        sys.exit(1)

    if "extract_patterns" in manifest:
        if not isinstance(manifest["extract_patterns"], list):
            log_error("Field 'extract_patterns' must be a list")
            sys.exit(1)

        for pattern in manifest["extract_patterns"]:
            if not isinstance(pattern, str):
                log_error("All extract patterns must be strings")
                sys.exit(1)


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        log_error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in manifest file: {e}")
        sys.exit(1)

    validate_manifest_schema(manifest)
    return manifest
