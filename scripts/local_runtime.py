#!/usr/bin/env python3
"""Materialize an explicit local behavior; no provider, enrollment or server starts."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
CAPABILITY = 'good-teammate'

def runtime_data():
    if CAPABILITY == "good-teammate":
        data = yaml.safe_load((ROOT / "behaviors/teamwork.yaml").read_text())
        data["bundle"]["name"] = "good-teammate-local"
        for row in data.get("hooks", []) + data.get("tools", []):
            if row["module"] in {"hooks-teamwork", "tool-teamwork"}:
                row["source"] = str(ROOT / "modules/hooks-teamwork")
            if row["module"] == "tool-skills":
                row.setdefault("config", {})["skills"] = [str(ROOT / "skills")]
        data["context"] = {"include": [str(ROOT / "context/teamwork-awareness.md")]}
    else:
        generation = yaml.safe_load((ROOT / "behaviors/image-generation.yaml").read_text())
        data = {"bundle": {"name": "imagen-studio-local", "version": "2.0.0", "description": "Local MCP adapter, canonical portable image workflow, and unchanged native policy; no provider configuration."}, "tools": deepcopy(generation["tools"])}
        for row in data["tools"]:
            if row["module"] == "tool-imagen":row["source"] = str(ROOT / "modules/tool-imagen")
            if row["module"] == "tool-skills":row.setdefault("config", {})["skills"] = [str(ROOT / "skills")]
        data["context"] = {"include": [str(ROOT / "context/imagen-awareness.md"), str(ROOT / "context/image-production-policy.md")]}
    # This is an additive behavior for the user's configured host, never a new
    # provider/session or an instruction to connect an external service.
    if "providers" in data or "session" in data:raise ValueError("Local behavior must preserve host provider/session")
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument("--output", type=Path, required=True);parser.add_argument("--replace", action="store_true");args=parser.parse_args()
    output = args.output.resolve();local = (ROOT / ".capability-check").resolve()
    if not output.is_relative_to(local):parser.error("Generated machine-local paths must stay inside ignored .capability-check/")
    if output.suffix not in {".yaml", ".yml"}:parser.error("The native loader requires a YAML output filename")
    rendered = yaml.safe_dump(runtime_data(), sort_keys=False)
    if output.exists() and output.read_text()!=rendered and not args.replace:parser.error("Generated output differs; inspect it or choose --replace")
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(rendered)
    print(json.dumps({"written": str(output), "scope": "local behavior only", "activated": False, "provider_calls": 0, "enrolled": False}))
if __name__=="__main__":main()
