import json
import os
from collections import defaultdict

from flask import Flask, render_template, request

from TableGenerator import TableGenerator

app = Flask(__name__, template_folder="templates")


# TODO: Replace query parameters with POST requests or path parameters
# TODO: add x buttons to remove questions or subquestions


@app.route("/")
def start_page():
    return render_template("index.jinja")


@app.route("/load-config")
def load_config():
    listdir = os.listdir("configs")
    listdir = [file.replace(".json", "") for file in listdir if file.endswith(".json")]
    return render_template("load-config.jinja", configs=listdir)


@app.route("/save-config", methods=["POST"])
def save_config():
    data = request.get_json()
    config = data["config"]
    config_name = data["config_name"]
    with open(f"configs/{config_name}.json", "w+") as json_file:
        json.dump(config, json_file, indent=4)
    return "Success"


@app.route("/create-config")
@app.route("/edit-config")
def create_config():
    config = 0
    config_name = request.args.get("config") if "config" in request.args else None
    if config_name is not None:
        with open(f"configs/{config_name}.json") as json_file:
            config = json.load(json_file)

    datasources = [file for file in os.listdir("data") if file.endswith(".csv")]
    return render_template("enter-config.jinja", config=config or {}, title=config_name or "New Config/Report",
                           datasources=datasources)


@app.route("/confirm-config")
def confirm_config(config: dict[str, list | int] = None):
    if config is None:
        config_name = request.args.get("config")
        with open(f"configs/{config_name}.json") as json_file:
            config = json.load(json_file)
            return render_template("confirm.jinja", config_name=config_name, config=config)
    else:
        return render_template("confirm.jinja", config_name="Unsaved Config", config=config, is_new=True)


@app.route("/generate-report")
def generate_tables():
    config = request.args.get("config-string")
    config = json.loads(config)

    TableGenerator.configure_generator(config)
    tables = TableGenerator.generate_tables()
    rendered_tables = {table.name: table.to_html(bold_rows=False) for table in tables}

    return render_template("generated.jinja", tables=rendered_tables)


def config_form_to_json(form_data: dict[str, str]):
    tables: defaultdict[str, int | dict[str, str | list]] = defaultdict(lambda: defaultdict(list))
    score_map = {}
    new_config = {"section_config": [],
                  "score_map": score_map,
                  "datasource": form_data["datasource"]}

    for key, value in form_data.items():
        key = key.replace("filter-type", "filterType")
        split_key = key.split("-")
        if len(split_key) == 1:
            if key == "datasource":
                continue
            score_map[key] = int(value)
        elif len(split_key) == 2:
            i, key = split_key
            if "filter" in key:  # If this value is a filter, we need to add the filter type to the value
                if key == "filter":  # Ignore the filter type during iteration because it's already added to filter
                    if value := value.strip():
                        tables[i][key] = form_data[f"{i}-filter-type"] + value
                continue
            tables[i][key] = value
        elif len(split_key) == 3:
            i, j, key = split_key
            tables[i][f"{key}s"].append(value)

    for table in tables.values():
        new_config["section_config"].append(table)
    print(json.dumps(new_config, indent=4))
    return new_config


@app.route("/process-entry", methods=["POST"])
def process_form():
    return confirm_config(config_form_to_json(request.form))


if __name__ == "__main__":
    app.run(port=3000, debug=True)
