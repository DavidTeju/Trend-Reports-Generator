from datetime import datetime
from functools import reduce

import pandas as pd

hey = datetime.now().year
years = list(range(2019, hey))  # Remember to add for date past August if program can be run past August

frame = pd.read_csv("Graduating Student data/survey_data.csv")

# Store MetaData
full_question, meta_data = frame.loc[0:1].values.tolist()  # Consider converting to df.pop

# drop meta_data
frame = frame.drop([0, 1])

# transform string dates to datetime dates
frame["RecordedDate"] = pd.to_datetime(frame["RecordedDate"], format="%Y-%m-%d %H:%M:%S")

sections = {"Did you participate in the following types of programs?": ["clubs_Participate", "rec_Participate",
                                                                        "social_Participate", "leadership_Participate",
                                                                        "Q10_5_Participate"]}
# Q10_5_Quality : University Ministry

current_section: pd.DataFrame = frame[
    ["RecordedDate", *sections["Did you participate in the following types of programs?"]]]  # Fix this monstrosity


# Actual records start at label [2]
# Please rate the quality and level of availability of the following
# co/extra-curricular programs a... - Did you participate in the following types of programs? - Student clubs and
# organizations

def in_year(dataframe, year):
    return (pd.to_datetime(f"{year}-08-01") <= dataframe["RecordedDate"]) & (
            dataframe["RecordedDate"] <= pd.to_datetime(f"{year + 1}-06-01"))


by_year: dict[int, pd.DataFrame] = {year: current_section[in_year(current_section, year)] for year in years}

year19 = by_year[2019]

# year19.aggregate()
# print(by_year[2019])
the_name = "clubs_Participate"


def value_frequency_from_name_by_year(year, name):
    return by_year[year][name].value_counts().to_frame().join(
        by_year[year][name].value_counts(normalize=True), rsuffix="_%")


def from_name(name):
    def yes_frequency_values_in_year(year):
        frequency_values = value_frequency_from_name_by_year(year, name)
        frequency_values.columns = ["#", "%"]
        yes_frequency_values: pd.Series = frequency_values.loc["Yes"]
        yes_frequency_values.name = year
        return yes_frequency_values

    list_of_frequencies_by_year = [yes_frequency_values_in_year(year) for year in years]
    frequencies_by_year = pd.concat(list_of_frequencies_by_year, axis=1)
    print(frequencies_by_year)


# TODO convert list of this to dataframe with questions as records

from_name(the_name)

# print(combine())
# print(type(combine()))


# reduced = reduce(see, years, extract_participate(2019))

# print(reduced)

# print(reduced)
# print(again)
#
# print(pd.merge(frequency.transpose(), again.transpose(), left_index=True, right_index=True))

# frequency = .append)

# yes_frequency = frequency["Yes"]
# yes_rate = frequency["Yes"]

# print(frequency["Yes"])
# df()
# print(by_year[2020].head())
