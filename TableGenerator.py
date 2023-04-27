import json
import re
from datetime import datetime
import pandas as pd


class TableGenerator:
    """
    A class to generate tables based on a given configuration.

    Attributes:
        full_data_frame (pd.DataFrame): A DataFrame containing the full dataset.
        full_questions (list): A list of full question texts.
        meta_data (list): A list of meta data.
        years (list): A list of years to filter data.
        by_year (dict): A dictionary containing DataFrames filtered by year.
        tables_config (list): A list of table configurations.
        score_map (dict): A mapping of scores to their corresponding values.
    """

    def __init__(self, config_str):
        """
        Initialize the TableGenerator with a configuration string.

        Args:
            config_str (str): JSON configuration string containing settings for data processing and table generation.
        """
        config: dict = json.loads(config_str.lower())
        to_lower_if_string = lambda s: s.lower() if type(s) == str else s
        self.full_data_frame = pd.read_csv(f"data/{config['datasource']}").applymap(
            to_lower_if_string
        )
        self.full_data_frame.columns = self.full_data_frame.columns.map(
            to_lower_if_string
        )

        # Store MetaData and drop from table
        self.full_questions, self.meta_data = self.full_data_frame.loc[:1].values.tolist()
        self.full_data_frame = self.full_data_frame.drop([0, 1])

        # transform string dates to datetime dates
        self.full_data_frame["recordeddate"] = pd.to_datetime(
            self.full_data_frame["recordeddate"], format="%Y-%m-%d %H:%M:%S"
        )

        current_year = datetime.now().year
        if datetime.now().month > 8:  # If the current month is past August, then generate for this year
            current_year += 1
        end_year = config.get("year_end", current_year - 1)
        start_year = config.get("year_start", 2019)
        self.years = list(range(start_year, end_year + 1))
        self.by_year = {
            year: self.full_data_frame[self.in_year(self.full_data_frame, year)]
            for year in self.years
        }
        self.tables_config = config["section_config"]
        self.score_map = config["score_map"]

    def generate_table(self, table):
        """
        Generates a table based on the given table configuration.

        Parameters
        -----------
        table : dict
            A dictionary containing the configuration for the table to be generated.

        Returns
        --------
        table_frame : pd.DataFrame
            The generated table as a pandas DataFrame.
        """
        function_dict = {
            "freq": self.freq_frame_for_sub_question,
            "mean": self.mean_frame_for_sub_question,
        }

        table_frame = function_dict.get(table["type"], self.table_type_error)(table)

        table_frame.name = table["question"]
        return table_frame

    def generate_tables(self):
        """
        Generates all the tables as specified in the tables_config.

        Returns
        --------
        list[pd.DataFrame]
            A list of generated tables as pandas DataFrames.
        """
        return [self.generate_table(table) for table in self.tables_config]

    def mean_frame_for_sub_question(self, table) -> pd.DataFrame:
        """
        Generates a mean frame for the given sub-question table configuration.

        Parameters
        -----------
        table : dict
            A dictionary containing the configuration for the sub-question table.

        Returns
        --------
        pd.DataFrame
            The generated mean frame as a pandas DataFrame.
        """
        question_export_tags = table["sub_questions"]

        def passes_filter(x):
            if "filter" not in table:
                return [True for _ in x]

            operator_map = {
                ">": (lambda a, b: a > b),
                "<": (lambda a, b: a < b),
                ">=": (lambda a, b: a >= b),
                "<=": (lambda a, b: a <= b),
                "==": (lambda a, b: a == b),
                "!=": (lambda a, b: a != b),
            }

            operator, operand = re.match(r"^([=!<>]{1,2})\s+(.*)$", table["filter"]).groups()
            operand = int(operand) if isNum(operand) else operand

            return [operator_map[operator](x_value, operand) for x_value in x]

        def convert_to_score(value):
            return float(value) if isNum(value) else self.score_map.get(value.lower())

        def get_mean_values_for_sub_question(year_values, question_export_tag):
            return (
                year_values.get(question_export_tag, default=pd.Series(dtype=float))
                .map(convert_to_score)
                .where(passes_filter)
                .mean()
            )

        def get_mean_values_for_year(year):
            return [
                get_mean_values_for_sub_question(self.by_year[year], sub_question)
                for sub_question in question_export_tags
            ]

        all_vals = {year: get_mean_values_for_year(year) for year in self.years}
        to_return = pd.DataFrame(
            all_vals,
            index=[
                self.get_question(question_export_tag.lower())
                for question_export_tag in question_export_tags
            ],
        ).round(2)
        to_return.columns.name = "Question"

        return to_return

    def get_question(self, tag):
        """
        Retrieves the full question text for the given question export tag.

        Parameters
        -----------
        tag : str
            The question export tag.

        Returns
        --------
        str
            The full question text.
        """
        try:
            full_question = self.full_questions[self.full_data_frame.columns.get_loc(tag)]
        except KeyError:
            return f"Not Found - {tag}"
        full_question = re.sub(
            "\\(.*?\\)", "", full_question
        )  # Remove contextual info (in brackets like this)
        full_question = re.sub(
            "[^a-zA-Z0-9]*$", "", full_question
        )  # Remove trailing punctuation.
        return full_question.split(" - ")[
            -1
        ].strip()  # Split and get last member as that should be the relevant title

    def freq_frame_for_sub_question(self, table):
        """
        Generates a frequency frame for the given sub-question table configuration.

        Parameters
        -----------
        table : dict
            A dictionary containing the configuration for the sub-question table.

        Returns
        --------
        pd.DataFrame
            The generated frequency frame as a DataFrame.
        """
        table_data = [
            self.freq_for_sub_question(question_export_tag.lower(), table["freq_keys"])
            for question_export_tag in table["sub_questions"]
        ]
        table_frame: pd.DataFrame = pd.concat(table_data)
        table_frame.columns.names = [None, "Question"]
        return table_frame

    def value_frequency_from_name_by_year(self, year, name):
        """
         Compute the frequency and percentage of values for the given freq_key in the specified year.

         Args:
             year (int): The year for which to compute the frequencies.
             name (str): The keyword for which to count the frequency.

         Returns:
             pd.DataFrame: A DataFrame containing the frequency and percentage of values for the given freq_key.
         """

        percent_multiplier = 100
        frame_of_frequencies = self.by_year[year][name].value_counts().to_frame()
        frame_of_frequency_rates = (
                self.by_year[year][name].value_counts(normalize=True) * percent_multiplier
        )
        frame_of_frequency_rates = frame_of_frequency_rates.to_frame()

        combined_frame = frame_of_frequencies.join(
            frame_of_frequency_rates, rsuffix="%"
        )
        combined_frame.loc["not found"] = [0, 0]
        combined_frame = combined_frame.applymap(int)

        return combined_frame

    def freq_for_sub_question(self, question_export_tag, freq_keys):
        """
        Generate a DataFrame containing the frequency data for the given sub_question and frequency keys.

        Args:
            question_export_tag (str): The tag associated with the sub_question.
            freq_keys (list[str]): A list of frequency keys.

        Returns:
            pd.DataFrame: A DataFrame containing the frequency data for the given sub_question and frequency keys.
        """

        def key_frequency_values_in_year(year):
            frequency_values = self.value_frequency_from_name_by_year(
                year, question_export_tag
            )
            frequency_values.columns = [
                f"#'{self.freq_keys_to_string(freq_keys)}'",
                f"%'{self.freq_keys_to_string(freq_keys)}'",
            ]

            try:
                yes_frequency_values: pd.Series = frequency_values.loc[freq_keys].sum()
            except KeyError:
                rows_to_remove = list(
                    set(frequency_values.index) - {*freq_keys, "not found"}
                )
                frequency_values.drop(rows_to_remove, inplace=True)
                yes_frequency_values: pd.Series = frequency_values.sum()

            yes_frequency_values.name = self.get_question(question_export_tag)
            transposed_frame = yes_frequency_values.to_frame().transpose()
            transposed_frame.columns = pd.MultiIndex.from_product(
                [[year], transposed_frame.columns]
            )
            return transposed_frame

        list_of_frequencies_by_year = [
            key_frequency_values_in_year(year) for year in self.years
        ]
        frequencies_by_year = pd.concat(list_of_frequencies_by_year, axis=1)
        return frequencies_by_year

    @staticmethod
    def freq_keys_to_string(freq_keys: list[str]):
        """Convert a list of frequency keys to a string representation."""
        return freq_keys[0] if len(freq_keys) == 1 else " or ".join(freq_keys)

    @staticmethod
    def table_type_error(table):
        return pd.DataFrame(
            {
                "": [
                    f"Incorrect table type: '{table['type']}' for question: '{table['question']}'"
                ]
            },
            index=["Error"],
        )

    @staticmethod
    def in_year(dataframe, year):
        return (pd.to_datetime(f"{year}-08-01") <= dataframe["recordeddate"]) & (
                dataframe["recordeddate"] <= pd.to_datetime(f"{year + 1}-06-01")
        )


def isNum(v):
    try:
        float(v)
    except ValueError:
        return False
    return True
