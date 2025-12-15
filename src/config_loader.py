import os
import yaml
import json
from pathlib import Path

CONFIG_DIR = os.environ.get("CONFIG_PATH", "configs")

def load_yaml(path: str):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def get_templates():
    templates_dir = Path(CONFIG_DIR) / "templates"
    templates = []
    if templates_dir.exists():
        for f in templates_dir.glob("*.yaml"):
            templates.append(load_yaml(str(f)))
    return templates

def get_template(template_id: str):
    templates = get_templates()
    for t in templates:
        if t.get('template_id') == template_id:
            return t
    return None

def get_rubrics():
    rubrics_dir = Path(CONFIG_DIR) / "rubrics"
    rubrics = []
    if rubrics_dir.exists():
        for f in rubrics_dir.glob("*.yaml"):
            rubrics.append(load_yaml(str(f)))
    return rubrics

def get_rubric(rubric_id: str):
    rubrics = get_rubrics()
    for r in rubrics:
        if r.get('rubric_id') == rubric_id:
            return r
    return None

def get_schema(schema_name: str):
    # schema_name can be "loan_output" (without ext)
    schema_path = Path(CONFIG_DIR) / "schemas" / f"{schema_name}.json"
    if schema_path.exists():
        return load_json(str(schema_path))
    return None
