import json
import argparse
import sys

from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader


class ActionGenerator:
    def __init__(
        self, manifest_dir: str = "manifests", template_dir: Optional[str] = None
    ):
        self.manifest_dir = Path(manifest_dir)
        self.template_dir = (
            Path(template_dir) if template_dir else Path(__file__).parent / "templates"
        )
        self._setup_jinja_env()

    def _setup_jinja_env(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            variable_start_string="{%",
            variable_end_string="%}",
            block_start_string="{%%",
            block_end_string="%%}",
            comment_start_string="{%#",
            comment_end_string="#%}",
        )

        self.jinja_env.filters["snake_case"] = self._to_snake_case
        self.jinja_env.filters["title_case"] = self._to_title_case

    def _to_snake_case(self, value: str) -> str:
        return value.lower().replace("-", "_").replace(" ", "_")

    def _to_title_case(self, value: str) -> str:
        return value.replace("-", " ").replace("_", " ").title()

    def load_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        with open(manifest_path, "r") as f:
            return json.load(f)

    def get_all_manifests(self) -> Dict[str, Dict[str, Any]]:
        manifests = {}
        for manifest_file in self.manifest_dir.glob("*/manifest.json"):
            tool_name = manifest_file.parent.name
            manifests[tool_name] = self.load_manifest(manifest_file)
        return manifests

    def generate_action(
        self,
        manifest: Dict[str, Any],
        tool_name: str,
        template_name: str = "action.yml.j2",
    ) -> str:
        template = self.jinja_env.get_template(template_name)

        context = {
            "tool_name": tool_name,
            "manifest": manifest,
            "name": manifest.get("name", tool_name),
            "repo": manifest["repo"],
            "assets": manifest["assets"],
            "extract_patterns": manifest["extract_patterns"],
            "platforms": list(manifest["assets"].keys()),
            "architectures": self._get_all_architectures(manifest["assets"]),
        }

        return template.render(**context)

    def _get_all_architectures(self, assets: Dict[str, Dict[str, str]]) -> List[str]:
        architectures = set()
        for platform_assets in assets.values():
            architectures.update(platform_assets.keys())
        return sorted(list(architectures))

    def generate_all_actions(
        self, template_name: str = "action.yml.j2"
    ) -> Dict[str, str]:
        manifests = self.get_all_manifests()
        actions = {}

        for tool_name, manifest in manifests.items():
            actions[tool_name] = self.generate_action(
                manifest, tool_name, template_name
            )

        return actions

    def generate_workflow(
        self,
        manifest: Dict[str, Any],
        tool_name: str,
        template_name: str = "workflow.yml.j2",
    ) -> str:
        template = self.jinja_env.get_template(template_name)

        context = {
            "tool_name": tool_name,
            "manifest": manifest,
            "name": manifest.get("name", tool_name),
            "repo": manifest["repo"],
            "assets": manifest["assets"],
            "extract_patterns": manifest["extract_patterns"],
            "platforms": list(manifest["assets"].keys()),
            "architectures": self._get_all_architectures(manifest["assets"]),
        }

        return template.render(**context)

    def generate_all_workflows(
        self, template_name: str = "workflow.yml.j2"
    ) -> Dict[str, str]:
        manifests = self.get_all_manifests()
        workflows = {}

        for tool_name, manifest in manifests.items():
            if "test" in manifest:
                workflows[tool_name] = self.generate_workflow(
                    manifest, tool_name, template_name
                )

        return workflows

    def write_action_files(
        self, output_dir: Path, template_name: str = "action.yml.j2"
    ):
        actions = self.generate_all_actions(template_name)

        for tool_name, action_content in actions.items():
            action_dir = output_dir / f"setup-{tool_name}"
            action_dir.mkdir(parents=True, exist_ok=True)

            action_file = action_dir / "action.yml"
            with open(action_file, "w") as f:
                f.write(action_content)

    def write_workflow_files(
        self, output_dir: Path, template_name: str = "workflow.yml.j2"
    ):
        workflows = self.generate_all_workflows(template_name)

        if not workflows:
            print("No manifests with test configuration found.")
            return

        for tool_name, workflow_content in workflows.items():
            output_dir.mkdir(parents=True, exist_ok=True)
            workflow_file = output_dir / f"setup-{tool_name}.yml"
            with open(workflow_file, "w") as f:
                f.write(workflow_content)


def generate_actions_from_manifests(
    manifest_dir: str = "manifests",
    output_dir: str = ".github/actions",
    template_dir: Optional[str] = None,
    template_name: str = "action.yml.j2",
) -> None:
    generator = ActionGenerator(manifest_dir, template_dir)
    output_path = Path(output_dir)
    generator.write_action_files(output_path, template_name)


def generate_workflows_from_manifests(
    manifest_dir: str = "manifests",
    output_dir: str = ".github/workflows",
    template_dir: Optional[str] = None,
    template_name: str = "workflow.yml.j2",
) -> None:
    generator = ActionGenerator(manifest_dir, template_dir)
    output_path = Path(output_dir)
    generator.write_workflow_files(output_path, template_name)


def main():
    parser = argparse.ArgumentParser(
        description="Generate GitHub Actions from manifest files"
    )
    parser.add_argument(
        "--manifest-dir",
        default="manifests",
        help="Directory containing manifest files (default: manifests)",
    )
    parser.add_argument("--template-dir", help="Custom template directory (optional)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show generated content without writing files",
    )
    parser.add_argument(
        "--action-output-dir",
        default=".github/actions",
        help="Output directory for generated actions (default: .github/actions)",
    )
    parser.add_argument(
        "--workflow-output-dir",
        default=".github/workflows",
        help="Output directory for generated workflows (default: .github/workflows)",
    )

    args = parser.parse_args()

    try:
        generator = ActionGenerator(args.manifest_dir, args.template_dir)

        if args.dry_run:
            workflows = generator.generate_all_workflows()
            for tool_name, workflow_content in workflows.items():
                print(f"Generated test workflow for {tool_name}")
                print(workflow_content)
                print()

            actions = generator.generate_all_actions()
            for tool_name, action_content in actions.items():
                print(f"Generated action for {tool_name}")
                print(action_content)
                print()
        else:
            generate_workflows_from_manifests(
                args.manifest_dir, args.workflow_output_dir, args.template_dir
            )
            print(f"Generated all test workflows in {args.workflow_output_dir}")

            generate_actions_from_manifests(
                args.manifest_dir, args.action_output_dir, args.template_dir
            )
            print(f"Generated all actions in {args.action_output_dir}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
