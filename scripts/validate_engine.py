from pathlib import Path
import sys

import yaml


ENGINE = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def main() -> int:
    errors = []
    registry_path = ENGINE / "registry.yaml"
    registry = load_yaml(registry_path).get("components", {})
    for name, relative in registry.items():
        if not (ENGINE / relative).is_file():
            errors.append(f"registry {name}: missing path {relative}")

    workflows = {}
    for path in (ENGINE / "workflows").glob("*.yaml"):
        data = load_yaml(path)
        workflows[data["name"]] = data
        for stage in data.get("stages", []):
            if not (ENGINE / "stages" / f"{stage}.yaml").is_file():
                errors.append(f"workflow {data['name']}: missing stage {stage}")

    for path in (ENGINE / "stages").glob("*.yaml"):
        stage = load_yaml(path)
        gate = stage.get("exit_gate")
        if not gate or not (ENGINE / "gates" / f"{gate}.yaml").is_file():
            errors.append(f"stage {stage.get('name')}: missing gate {gate}")
        context = stage.get("context")
        if not context or not (ENGINE / context).is_file():
            errors.append(f"stage {stage.get('name')}: missing context {context}")

    selector = load_yaml(ENGINE / "selector.yaml").get("task_types", {})
    for task_type, workflow in selector.items():
        if workflow not in workflows:
            errors.append(f"selector {task_type}: unknown workflow {workflow}")

    if errors:
        print("Engine validation failed:")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print(f"Engine valid: {len(registry)} registry entries, {len(workflows)} workflow(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
