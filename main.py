import pandas as pd
from datetime import datetime, date

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
                                                                        "Q10_5_Quality"]}
# Q10_5_Quality : University Ministry

current_section: pd.DataFrame = frame[
    ["RecordedDate", *sections["Did you participate in the following types of programs?"]]]  # Fix this monstrosity


# Actual records start at label [2]
# Please rate the quality and level of availability of the following
# co/extra-curricular programs a... - Did you participate in the following types of programs? - Student clubs and
# organizations

def in_year(year):
    return (pd.to_datetime(f"{year}-08-01") <= current_section["RecordedDate"]) & (
            current_section["RecordedDate"] <= pd.to_datetime(f"{year + 1}-06-01"))


by_year = {year: current_section[in_year(year)] for year in years}
