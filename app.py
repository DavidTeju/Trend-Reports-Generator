import json
import os

from flask import Flask, render_template, request

from TableGenerator import TableGenerator

app = Flask(__name__, template_folder="templates")


@app.route("/")
def start_page():
    return render_template("index.jinja")


@app.route("/load-config")
def load_config():
    listdir = os.listdir("configs")
    listdir = [file[0:-5] for file in listdir if file.endswith(".json")]
    return render_template("load-config.jinja", configs=listdir)


@app.route("/confirm-config")
def confirm_config():
    config_name = request.args.get("config")
    with open(f"configs/{config_name}.json") as json_file:
        config = json.load(json_file)
    return render_template("confirm.jinja", config_name=config_name, config=config)


@app.route("/generate-report")
def generate_tables():
    config = request.args.get("config-string")
    config = json.loads(config)

    TableGenerator.configure_generator(config)
    tables = TableGenerator.generate_tables()
    string = ""
    table_dict = {table.name: table.to_html(bold_rows=False) for table in tables}
    for table in tables:
        string += f"<h2>{table.name}</h2>\n{table.to_html(bold_rows=False)}\n"

    return render_template("any.html", content=string)


@app.route("/test")
def test():
    return render_template("single-config.jinja", index=1, table={
        "question": "Satisfaction with the quality of the programs",
        "type": "mean",
        "sub_questions": [
            "clubs_Quality",
            "rec_Quality",
            "social_Quality",
            "leadership_Quality",
            "Q10_5_Quality"
        ]
    })


if __name__ == "__main__":
    app.run(port=3000, debug=True)
