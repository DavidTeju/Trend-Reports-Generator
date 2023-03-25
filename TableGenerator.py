import re
from datetime import datetime
import pandas as pd


class TableGenerator:
    full_data_frame: pd.DataFrame
    years: list[int]
    tables_config: list[dict]
    score_map: dict[str, int]
    by_year: dict[int, pd.DataFrame]
    full_questions: list[str]
    meta_data: list[str]

    @classmethod
    def configure_generator(cls, config):
        cls.full_data_frame = pd.read_csv("Graduating Student data/survey_data.csv")

        # Store MetaData and drop from table
        cls.full_questions, cls.meta_data = cls.full_data_frame.loc[0:1].values.tolist()
        cls.full_data_frame = cls.full_data_frame.drop([0, 1])

        # transform string dates to datetime dates
        cls.full_data_frame["RecordedDate"] = pd.to_datetime(cls.full_data_frame["RecordedDate"],
                                                             format="%Y-%m-%d %H:%M:%S")

        current_year = datetime.now().year
        cls.years = list(range(2019, current_year))
        # TODO Remember to add for date past August if program can be run past August
        cls.by_year = {year: cls.full_data_frame[cls.in_year(cls.full_data_frame, year)] for
                       year in cls.years}
        cls.tables_config = config["section_config"]
        cls.score_map = config["score_map"]

    @classmethod
    def generate_table(cls, table):
        function_dict = {"freq": cls.freq_frame_for_sub_question, "mean": cls.mean_frame_for_sub_question}

        table_frame = function_dict.get(table["type"], cls.table_type_error)(table)

        table_frame.name = table["question"]
        return table_frame

    @classmethod
    def generate_tables(cls):
        return [TableGenerator.generate_table(table) for table in cls.tables_config]

    @classmethod
    def mean_frame_for_sub_question(cls, table) -> pd.DataFrame:
        question_export_tags = table["sub_questions"]

        def passes_filter(x):
            if "filter" in table:
                return eval(f"x{table['filter']}")  # evaluate x with the filter attribute
            else:
                return [True for _ in x]

        def convert_to_score(value):
            return float(value) if isNum(value) else cls.score_map.get(value)

        def get_mean_values_for_sub_question(year_values, question_export_tag):
            return year_values[question_export_tag].map(convert_to_score).where(passes_filter).mean()

        def get_mean_values_for_year(year):
            return [get_mean_values_for_sub_question(cls.by_year[year], sub_question) for sub_question in
                    question_export_tags]

        all_vals = {year: get_mean_values_for_year(year) for year in cls.years}
        to_return = pd.DataFrame(all_vals,
                                 index=[cls.get_question(question_export_tag) for question_export_tag in
                                        question_export_tags]).round(2)
        to_return.columns.name = "Question"

        return to_return

    @classmethod
    def get_question(cls, tag):
        full_question = cls.full_questions[cls.full_data_frame.columns.get_loc(tag)]
        full_question = re.sub("\\(.*?\\)", "", full_question)  # Remove contextual info (in brackets like this)
        full_question = re.sub("[^a-zA-Z0-9]*$", "", full_question)  # Remove trailing punctuation.
        return full_question.split(" - ")[-1].strip()  # Split and get last member as that should be the relevant title

    @classmethod
    def freq_frame_for_sub_question(cls, table):
        table_data = [cls.freq_for_sub_question(question_export_tag, table["freq_keys"]) for question_export_tag in
                      table["sub_questions"]]
        table_frame: pd.DataFrame = pd.concat(table_data)
        table_frame.columns.names = [None, "Question"]
        return table_frame

    @classmethod
    def value_frequency_from_name_by_year(cls, year, name):
        percent_multiplier = 100
        frame_of_frequencies = cls.by_year[year][name].value_counts().to_frame()
        frame_of_frequency_rates = cls.by_year[year][name].value_counts(normalize=True) * percent_multiplier
        frame_of_frequency_rates = frame_of_frequency_rates.to_frame()
        return frame_of_frequencies.join(frame_of_frequency_rates, rsuffix="%").applymap(int)

    @classmethod
    def freq_for_sub_question(cls, question_export_tag: str, freq_keys: list[str]):
        def key_frequency_values_in_year(year):
            frequency_values = cls.value_frequency_from_name_by_year(year, question_export_tag)
            frequency_values.columns = [f"#'{cls.freq_keys_to_string(freq_keys)}'",
                                        f"%'{cls.freq_keys_to_string(freq_keys)}'"]
            yes_frequency_values: pd.Series = frequency_values.loc[freq_keys].sum()
            yes_frequency_values.name = cls.get_question(question_export_tag)
            transposed_frame = yes_frequency_values.to_frame().transpose()
            transposed_frame.columns = pd.MultiIndex.from_product([[year], transposed_frame.columns])
            return transposed_frame

        list_of_frequencies_by_year = [key_frequency_values_in_year(year) for year in cls.years]
        frequencies_by_year = pd.concat(list_of_frequencies_by_year, axis=1)
        return frequencies_by_year

    @staticmethod
    def freq_keys_to_string(freq_keys: list):
        if len(freq_keys) == 1:
            return freq_keys[0]
        else:
            return " or ".join(freq_keys)

    @staticmethod
    def table_type_error(table):
        return pd.DataFrame(
            {"": [f"Incorrect table type: '{table['type']}' for question: '{table['question']}'"]},
            index=["Error"])

    @staticmethod
    def in_year(dataframe, year):
        return (pd.to_datetime(f"{year}-08-01") <= dataframe["RecordedDate"]) & (
                dataframe["RecordedDate"] <= pd.to_datetime(f"{year + 1}-06-01"))


def isNum(v):
    try:
        float(v)
    except ValueError:
        return False
    return True
