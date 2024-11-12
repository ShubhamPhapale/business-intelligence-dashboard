import pandas as pd
from datetime import datetime, timedelta

# Load the Excel files
que_ans_df = pd.read_excel('Que_Ans.xlsx')
voter_df = pd.read_excel('Voter.xlsx')
correct_answers_df = pd.read_excel('Correct_Answers.xlsx')

# Date Conversion for Que_Ans.xlsx
def convert_date(value):
    if value == "TODAY":
        return datetime(2024, 10, 22)
    elif value == "YESTERDAY":
        return datetime(2024, 10, 21)
    elif value == "SUNDAY":
        return datetime(2024, 10, 20)
    elif value == "FRIDAY":
        return datetime(2024, 10, 18)
    else:
        try:
            # Attempt to parse the date in case it’s already a standard date format
            # return pd.to_datetime(value)
            return pd.to_datetime(value, dayfirst=True, errors='coerce')
        except:
            return value

# Apply the conversion to the 'que_created_at' column
que_ans_df['que_created_at'] = que_ans_df['que_created_at'].apply(convert_date)

# Apply the conversion to the 'que_created_at' column
# voter_df['voting_time'] = voter_df['voting_time'].apply(convert_date)

# Clean 'vote_count' in Voter.xlsx
def convert_vote_count(value):
    if isinstance(value, str) and "votes" in value:
        return int(value.split()[0])  # Extracts the integer part before "votes"
    return value

voter_df['vote_count'] = voter_df['vote_count'].apply(convert_vote_count)

print(que_ans_df.columns)
print(voter_df.columns)

# Reconcile 'votes' column in Que_Ans.xlsx with 'vote_count' in Voter.xlsx
for idx, row in que_ans_df.iterrows():
    question_text = row['que_text']
    for choice in voter_df[voter_df['question_text'] == question_text]['choice'].unique():
        choice_voter_count = voter_df[(voter_df['question_text'] == question_text) & 
                                      (voter_df['choice'] == choice)].shape[0]
        que_ans_df.loc[(que_ans_df['que_text'] == question_text) & 
                       (que_ans_df['ans_text'] == choice), 'votes'] = choice_voter_count

# Save the cleaned files
# que_ans_df.to_excel('Cleaned_Que_Ans.xlsx', index=False)
# voter_df.to_excel('Cleaned_Voter.xlsx', index=False)
# correct_answers_df.to_excel('Cleaned_Correct_Answers.xlsx', index=False)
