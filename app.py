import json
import os
import re
from collections import defaultdict
from datetime import datetime

import io
import pandas as pd
from flask import Flask, render_template, request, send_file, make_response

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
    current_year = datetime.now().year
    return render_template("enter-config.jinja", config=config or {}, title=config_name or "New Config/Report",
                           datasources=datasources, current_year=current_year)


@app.route("/confirm-config")
def confirm_config(config: dict[str, list | int] = None):
    if config is not None:
        return render_template("confirm.jinja", config_name="Unsaved Config", config=config, is_new=True)

    config_name = request.args.get("config")
    with open(f"configs/{config_name}.json") as json_file:
        config = json.load(json_file)
        return render_template("confirm.jinja", config_name=config_name, config=config)


@app.route("/generate-report")
def generate_tables():
    config_str = request.args.get("config-string")

    generator = TableGenerator(config_str)
    tables = generator.generate_tables()

    to_html = lambda x: x.to_html(bold_rows=False).replace('<tr style="text-align: right;">', "<tr>")

    rendered_tables = {table.name: to_html(table) for table in tables}

    return render_template("generated.jinja", tables=rendered_tables)


@app.route("/download-excel")
def download_excel():
    config_str = request.args.get("config_string")

    generator = TableGenerator(config_str)
    tables: list[pd.DataFrame] = generator.generate_tables()

    # Create an in-memory binary stream to store the Excel data
    output = io.BytesIO()

    # Create a Pandas ExcelWriter object using the binary stream as the output file
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for i, table in enumerate(tables):
            safe_name = re.sub(r'[\\/*?:"<>|]', "", table.name)
            safe_name = f"({i}) {safe_name[:(30 - 4) - (i // 10)]}"  # Limit the length of the sheet name
            table.to_excel(writer, sheet_name=safe_name)
    # Set the position of the binary stream to the beginning
    output.seek(0)

    # Create a response with the binary stream as the Excel file
    response = make_response(
        send_file(io.BytesIO(output.getvalue()), as_attachment=True, download_name="report.xlsx", max_age=0))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    output.close()

    return response


def config_form_to_json(form_data: dict[str, str]):
    tables: defaultdict[str, int | dict[str, str | list]] = defaultdict(lambda: defaultdict(list))
    score_map = {}
    new_config = {"section_config": [],
                  "score_map": score_map,
                  "datasource": form_data["datasource"]}

    if form_data.get("year_start"):
        new_config["year_start"] = int(form_data["year_start"])
    if form_data.get("year_end"):
        new_config["year_end"] = int(form_data["year_end"])

    for key, value in form_data.items():
        key = key.replace("filter-type", "filterType")
        split_key = key.split("-")
        if len(split_key) == 1:
            if key in ["datasource", "year_start", "year_end"]:
                continue
            score_map[key] = int(value)
        elif len(split_key) == 2:
            i, key = split_key
            if "filter" in key:  # If this value is a filter, we need to add the filter type to the value
                if key == "filter":  # Ignore the filter type during iteration because it's already added to filter
                    if value := value.strip():
                        tables[i][key] = f'{form_data[f"{i}-filter-type"]} {value}'
                continue
            tables[i][key] = value
        elif len(split_key) == 3:
            i, j, key = split_key
            tables[i][f"{key}s"].append(value)

    for table in tables.values():
        new_config["section_config"].append(table)
    return new_config


@app.route("/process-entry", methods=["POST"])
def process_form():
    return confirm_config(config_form_to_json(request.form))


if __name__ == "__main__":
    app.run(port=3000, debug=True)
