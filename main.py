import json
import re
from datetime import datetime

import pandas as pd


def in_year(dataframe, year):
    return (pd.to_datetime(f"{year}-08-01") <= dataframe["RecordedDate"]) & (
            dataframe["RecordedDate"] <= pd.to_datetime(f"{year + 1}-06-01"))


def mean_frame_for_sub_question(section) -> pd.DataFrame:
    question_export_tags = section["sub_questions"]

    def get_mean_values_for_sub_question(year_values, question_export_tag):
        return year_values[question_export_tag].map(score_map.get).mean()

    def get_mean_values_for_year(year):
        return [get_mean_values_for_sub_question(by_year[year], sub_question) for sub_question in question_export_tags]

    all_vals = {year: get_mean_values_for_year(year) for year in years}
    to_return = pd.DataFrame(all_vals,
                             index=[get_question(question_export_tag) for question_export_tag in
                                    question_export_tags]).round(2)
    to_return.columns.name = "Question"

    return to_return


def get_question(tag):
    full_question = full_questions[full_data_frame.columns.get_loc(tag)]
    full_question = re.sub("\\(.*?\\)", "", full_question)  # Remove contextual info (in brackets like this)
    full_question = re.sub("[^a-zA-Z0-9]*$", "", full_question)  # Remove trailing punctuation.
    return full_question.split(" - ")[-1].strip()  # Split and get last member as that should be the relevant title


def section_type_error(section):
    return pd.DataFrame({"": [f"Incorrect section type: '{section['type']}' for question: '{section['question']}'"]},
                        index=["Error"])


def freq_frame_for_sub_question(section):
    section_data = [freq_for_sub_question(question_export_tag, section["freq_keys"]) for question_export_tag in
                    section["sub_questions"]]
    section_frame: pd.DataFrame = pd.concat(section_data)
    section_frame.columns.names = [None, "Question"]
    return section_frame


def value_frequency_from_name_by_year(year, name):
    percent_multiplier = 100
    frame_of_frequencies = by_year[year][name].value_counts().to_frame()
    frame_of_frequency_rates = by_year[year][name].value_counts(normalize=True) * percent_multiplier
    frame_of_frequency_rates = frame_of_frequency_rates.to_frame()
    return frame_of_frequencies.join(frame_of_frequency_rates, rsuffix="%").applymap(int)


def freq_for_sub_question(question_export_tag: str, freq_keys: list[str]):
    def key_frequency_values_in_year(year):
        frequency_values = value_frequency_from_name_by_year(year, question_export_tag)
        frequency_values.columns = [f"#'{freq_keys_to_string(freq_keys)}'", f"%'{freq_keys_to_string(freq_keys)}'"]
        yes_frequency_values: pd.Series = frequency_values.loc[freq_keys].sum()
        yes_frequency_values.name = get_question(question_export_tag)
        transposed_frame = yes_frequency_values.to_frame().transpose()
        transposed_frame.columns = pd.MultiIndex.from_product([[year], transposed_frame.columns])
        return transposed_frame

    list_of_frequencies_by_year = [key_frequency_values_in_year(year) for year in years]
    frequencies_by_year = pd.concat(list_of_frequencies_by_year, axis=1)
    return frequencies_by_year


def freq_keys_to_string(freq_keys: list):
    if len(freq_keys) == 1:
        return freq_keys[0]
    else:
        return " or ".join(freq_keys)


def run_for_section(section):
    function_dict = {"freq": freq_frame_for_sub_question, "mean": mean_frame_for_sub_question}

    section_frame = function_dict.get(section["type"], section_type_error)(section)

    section_frame.name = section["question"]
    return section_frame


def main(sections):
    sections_tables = [run_for_section(section) for section in sections]
    with open("output.html", "w") as html:
        for table in sections_tables:
            print(table)
            html.write(f"<h2>{table.name}</h2>")
            html.write(table.to_html(bold_rows=False))


full_data_frame = pd.read_csv("Graduating Student data/survey_data.csv")

# Store MetaData
full_questions: list[str]
meta_data: list[str]
full_questions, meta_data = full_data_frame.loc[0:1].values.tolist()  # Consider converting to df.pop

# drop meta_data from table
full_data_frame = full_data_frame.drop([0, 1])

# transform string dates to datetime dates
full_data_frame["RecordedDate"] = pd.to_datetime(full_data_frame["RecordedDate"], format="%Y-%m-%d %H:%M:%S")

current_year = datetime.now().year
years = list(range(2019, current_year))  # TODO Remember to add for date past August if program can be run past August
by_year: dict[int, pd.DataFrame] = {year: full_data_frame[in_year(full_data_frame, year)] for year in years}

with open("config.json") as file:
    config = json.load(file)
    sections_config = config["section_config"]
    score_map: dict[str, int] = config["score_map"]

main(sections_config)
