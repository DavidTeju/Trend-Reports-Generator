import json
import sys
from datetime import datetime

import pandas as pd


def main(sections):
    sections_tables = [run_for_section(section) for section in sections]
    for table in sections_tables:
        print(table)
        # with open(f"{table.name}.csv", "w+") as csv:
        #     csv.write(table.to_csv())


full_data_frame = pd.read_csv("Graduating Student data/survey_data.csv")

# Store MetaData
full_question, meta_data = full_data_frame.loc[0:1].values.tolist()  # Consider converting to df.pop

# drop meta_data from table
full_data_frame = full_data_frame.drop([0, 1])

# transform string dates to datetime dates
full_data_frame["RecordedDate"] = pd.to_datetime(full_data_frame["RecordedDate"], format="%Y-%m-%d %H:%M:%S")

with open("section_config.json") as file:
    sections_config = json.load(file)


def in_year(dataframe, year):
    return (pd.to_datetime(f"{year}-08-01") <= dataframe["RecordedDate"]) & (
            dataframe["RecordedDate"] <= pd.to_datetime(f"{year + 1}-06-01"))


current_year = datetime.now().year
years = list(range(2019, current_year))  # TODO Remember to add for date past August if program can be run past August
by_year: dict[int, pd.DataFrame] = {year: full_data_frame[in_year(full_data_frame, year)] for year in years}
with open("satisfied_map.json", "r") as json_file:
    satisfied_map: dict[str, int] = json.load(json_file)


# Q10_5_Quality : University Ministry


# Actual records start at label [2]
# Please rate the quality and level of availability of the following
# co/extra-curricular programs a... - Did you participate in the following types of programs? - Student clubs and
# organizations


def mean_frame_for_sub_question(section) -> pd.DataFrame:
    sub_questions = section["sub_questions"]

    def get_mean_values_for_subquestion(year_values, sub_question):
        return year_values[sub_question].dropna().map(satisfied_map.get).mean()

    def get_mean_values_for_year(year):
        return [get_mean_values_for_subquestion(by_year[year], sub_question) for sub_question in sub_questions]

    all_vals = {year: get_mean_values_for_year(year) for year in years}
    to_return = pd.DataFrame(all_vals, index=sub_questions).round(2)
    to_return.columns.name = "Question"

    return to_return


def run_for_section(section):
    function_dict = {"freq": freq_frame_for_subquestion, "mean": mean_frame_for_sub_question}

    section_frame = function_dict.get(section["type"], sys.exit)(section)

    section_frame.name = section["question"]
    return section_frame


def freq_frame_for_subquestion(section):
    section_data = [freq_for_sub_question(sub_question, section["freq_keys"]) for sub_question in
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


def freq_for_sub_question(sub_question: str, freq_keys: list[str]):
    def key_frequency_values_in_year(year):
        frequency_values = value_frequency_from_name_by_year(year, sub_question)
        frequency_values.columns = [f"#'{freq_keys_to_string(freq_keys)}'", f"%'{freq_keys_to_string(freq_keys)}'"]
        yes_frequency_values: pd.Series = frequency_values.loc[freq_keys].sum()
        yes_frequency_values.name = sub_question
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


main(sections_config)
