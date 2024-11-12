import pandas as pd
import os
from datetime import datetime, timedelta

# Load cleaned datasets
que_ans_df = pd.read_excel('Cleaned_Que_Ans.xlsx')
voter_df = pd.read_excel('Cleaned_Voter.xlsx')
correct_answers_df = pd.read_excel('Cleaned_Correct_Answers.xlsx')

# Clean que_ans_df to ensure unique `que_text` entries (add this block)
que_ans_df = que_ans_df.drop_duplicates(subset=['que_text'])

# Alternative aggregation (if `que_text` entries are not unique)
# que_ans_df = que_ans_df.groupby('que_text')['que_created_at'].min().reset_index()

# Now proceed with mapping and response time calculation
voter_df['response_time'] = voter_df['voting_time'] - voter_df['question_text'].map(que_ans_df.set_index('que_text')['que_created_at'])

# Set the value of N
N = 32  # or any other number of top records you want

# Output directory for insights
output_dir = 'insights/'
os.makedirs(output_dir, exist_ok=True)

# Custom function to handle non-standard date formats
def parse_custom_date(date_str):
    if isinstance(date_str, pd.Timestamp):
        return date_str  # If already a Timestamp, return as is
    if "Today" in date_str:
        time_part = date_str.split("at")[-1].strip()
        today = datetime.now().strftime("%d/%m/%Y")
        date_str = f"{today} {time_part}"
    elif "Yesterday" in date_str:
        time_part = date_str.split("at")[-1].strip()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        date_str = f"{yesterday} {time_part}"

    parsed_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')  # Set dayfirst=True
    print(f"Original: {date_str} | Parsed: {parsed_date}")  # Debug print
    return parsed_date

# Apply the custom parsing function to voting_time and que_created_at columns
voter_df['voting_time'] = voter_df['voting_time'].apply(parse_custom_date)

voter_df.to_excel('Cleaned_Voter.xlsx', index=False)
print("Voter data cleaned and saved to 'Cleaned_Voter.xlsx'")

# que_ans_df['que_created_at'] = que_ans_df['que_created_at'].apply(parse_custom_date)

# Proceed with analysis as before
voter_df['response_time'] = voter_df['voting_time'] - voter_df['question_text'].map(que_ans_df.set_index('que_text')['que_created_at'])

# 1. Top N most active followers/voters
active_voters = voter_df['voter_name'].value_counts().head(N)
active_voters.to_excel(f'{output_dir}Top_{N}_Most_Active_Followers.xlsx')

# 2. Top N early birds (users who answered questions earliest after creation)
early_birds = voter_df.sort_values('response_time').drop_duplicates(['question_text']).groupby('voter_name').size().nlargest(N)
early_birds.to_excel(f'{output_dir}Top_{N}_Early_Birds.xlsx')

# 3. Top N questions with more incorrect than correct answers

# Rename 'que_text' to 'question_text' in correct_answers_df
correct_answers_df.rename(columns={'que_text': 'question_text'}, inplace=True)

# Now merge the DataFrames
merged_df = pd.merge(voter_df, correct_answers_df, on='question_text')

# After merging the DataFrames, print the column names
print("Columns in merged_df:", merged_df.columns)

# Then, proceed with the logic assuming the correct column exists
# merged_df['is_correct'] = merged_df['choice'] == merged_df['correct_answer']

# Check if 'choice' matches 'ans_text' (assuming 'ans_text' represents the correct answer)
merged_df['is_correct'] = merged_df['choice'] == merged_df['ans_text']

incorrect_counts = merged_df.groupby('question_text')['is_correct'].apply(lambda x: (~x).sum())
correct_counts = merged_df.groupby('question_text')['is_correct'].sum()
incorrectly_voted_questions = (incorrect_counts > correct_counts).nlargest(N)
incorrectly_voted_questions.to_excel(f'{output_dir}Top_{N}_Incorrectly_Voted_Questions.xlsx')

# 4. Top N easy questions (where zero incorrect options were voted)
easy_questions = incorrect_counts[incorrect_counts == 0].nlargest(N)
easy_questions.to_excel(f'{output_dir}Top_{N}_Easy_Questions.xlsx')

# 5. Top N least active followers/voters
least_active_voters = voter_df['voter_name'].value_counts().tail(N)
least_active_voters.to_excel(f'{output_dir}Top_{N}_Least_Active_Followers.xlsx')

# 6. Top N voters who haven't participated since long
last_participation = voter_df.groupby('voter_name')['voting_time'].max()
oldest_participants = last_participation.nsmallest(N)
oldest_participants.to_excel(f'{output_dir}Top_{N}_Inactive_Followers.xlsx')

# 7. Top N good performers (answered correct answers the most)
correct_answers_by_voter = merged_df[merged_df['is_correct']].groupby('voter_name').size().nlargest(N)
correct_answers_by_voter.to_excel(f'{output_dir}Top_{N}_Good_Performers.xlsx')

# 8. Top N difficult questions (with the fewest votes, correct or incorrect)
question_vote_counts = voter_df['question_text'].value_counts().nsmallest(N)
question_vote_counts.to_excel(f'{output_dir}Top_{N}_Difficult_Questions.xlsx')

# 9. Top N fast responded questions
question_response_times = voter_df.groupby('question_text')['response_time'].min().nsmallest(N)
question_response_times.to_excel(f'{output_dir}Top_{N}_Fast_Responded_Questions.xlsx')

# 10. Top N slowest responded questions
slowest_questions = voter_df.groupby('question_text')['response_time'].max().nlargest(N)
slowest_questions.to_excel(f'{output_dir}Top_{N}_Slowest_Responded_Questions.xlsx')

print("Insight files generated in the directory:", output_dir)