import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime

def load_data():
    """
    Placeholder function to load data. 
    Replace with actual data loading in real implementation.
    """
    # Simulate loading DataFrames
    voters_df = pd.read_excel('Voter.xlsx')
    que_ans_df = pd.read_excel('Que_Ans.xlsx')
    correct_answers_df = pd.read_excel('Correct_Answers.xlsx')
    
    return voters_df, que_ans_df, correct_answers_df

def most_active_voters(voters_df, top_n=31):
    """Analyze most active voters"""
    active_voters = voters_df.groupby('voter_name')['question_text'].nunique().reset_index()
    active_voters.columns = ['voter_name', 'questions_answered']
    return active_voters.sort_values(by='questions_answered', ascending=False).head(top_n)

def least_active_voters(voters_df, top_n=31):
    """Analyze least active voters"""
    active_voters = voters_df.groupby('voter_name')['question_text'].nunique().reset_index()
    active_voters.columns = ['voter_name', 'questions_answered']
    return active_voters.sort_values(by='questions_answered', ascending=True).head(top_n)

def early_bird_analysis(voters_df, que_ans_df, top_n=31):
    """Analyze early bird voters"""
    voters_df['voting_time'] = pd.to_datetime(voters_df['voting_time'])
    que_ans_df['que_created_at'] = pd.to_datetime(que_ans_df['que_created_at'])
    
    merged_df = pd.merge(voters_df, que_ans_df[['que_text', 'que_created_at']], 
                         left_on='question_text', right_on='que_text')
    
    merged_df['time_diff'] = merged_df['voting_time'] - merged_df['que_created_at']
    merged_df = merged_df.sort_values(['que_text', 'time_diff'])
    early_birds_df = merged_df.groupby('que_text').first().reset_index()
    
    early_bird_counts = early_birds_df['voter_name'].value_counts().reset_index()
    early_bird_counts.columns = ['voter_name', 'early_bird_count']
    
    return early_bird_counts.head(top_n)

def ensure_list(x):
    """
    Convert input to a list of answers.
    Handles string, list, and other input types.
    """
    if pd.isna(x):
        return []
    if isinstance(x, str):
        return [ans.strip() for ans in x.split(',')]
    if isinstance(x, list):
        return [str(ans).strip() for ans in x]
    return [str(x).strip()]

def performance_analysis(voters_df, correct_answers_df, top_n=31):
    """Analyze voter performance"""
    # Ensure ans_text is a list of answers
    correct_answers_df['ans_text'] = correct_answers_df['ans_text'].apply(ensure_list)
    
    merged_df = voters_df.merge(correct_answers_df, 
                                 left_on='question_text', 
                                 right_on='que_text', 
                                 how='left')
    
    merged_df['is_correct'] = merged_df.apply(
        lambda row: row['choice'] in row['ans_text'], axis=1
    )
    
    correct_answers_per_voter = merged_df[merged_df['is_correct']].groupby('voter_name').size().reset_index(name='correct_count')
    
    return correct_answers_per_voter.sort_values(by='correct_count', ascending=False).head(top_n)

def incorrect_questions(voters_df, correct_answers_df, top_n=31):
    """Find questions with more incorrect than correct votes"""
    # Ensure ans_text is a list of answers
    correct_answers_df['ans_text'] = correct_answers_df['ans_text'].apply(ensure_list)
    
    merged_df = voters_df.merge(correct_answers_df, 
                                 left_on='question_text', 
                                 right_on='que_text', 
                                 how='left')
    
    merged_df['vote_category'] = merged_df.apply(
        lambda row: 'Correct' if row['choice'] in row['ans_text'] else 'Incorrect', 
        axis=1
    )
    
    vote_summary = merged_df.groupby(['question_text', 'vote_category']).size().unstack(fill_value=0)
    
    return vote_summary[vote_summary['Incorrect'] > vote_summary['Correct']].head(top_n)

def easy_questions(voters_df, correct_answers_df):
    """Find questions with zero incorrect votes"""
    # Ensure ans_text is a list of answers
    correct_answers_df['ans_text'] = correct_answers_df['ans_text'].apply(ensure_list)
    
    merged_df = voters_df.merge(correct_answers_df, 
                                 left_on='question_text', 
                                 right_on='que_text', 
                                 how='left')
    
    merged_df['vote_category'] = merged_df.apply(
        lambda row: 'Correct' if row['choice'] in row['ans_text'] else 'Incorrect', 
        axis=1
    )
    
    vote_summary = merged_df.groupby(['question_text', 'vote_category']).size().unstack(fill_value=0)
    
    return vote_summary[vote_summary['Incorrect'] == 0]

def inactive_voters_analysis(voters_df, current_date=datetime(2024, 10, 22, 11, 27), top_n=31):
    """Analyze voters inactive for the longest time"""
    voters_df['voting_time'] = pd.to_datetime(voters_df['voting_time'])
    last_vote_df = voters_df.groupby('voter_name')['voting_time'].max().reset_index()
    
    last_vote_df['time_since_last_vote'] = current_date - last_vote_df['voting_time']
    last_vote_df['days_since_last_vote'] = last_vote_df['time_since_last_vote'].dt.days
    
    return last_vote_df.sort_values(by='time_since_last_vote', ascending=False).head(top_n)

def difficult_questions(voters_df, top_n=31):
    """Identify questions with fewest votes"""
    question_vote_counts = voters_df.groupby('question_text').size().reset_index(name='vote_count')
    return question_vote_counts.sort_values(by='vote_count', ascending=True).head(top_n)

def response_time_analysis(voters_df, que_ans_df, fastest=True, top_n=31):
    """Analyze question response times"""
    voters_df['voting_time'] = pd.to_datetime(voters_df['voting_time'])
    que_ans_df['que_created_at'] = pd.to_datetime(que_ans_df['que_created_at'])
    
    que_ans_grouped = que_ans_df.groupby('que_text').first().reset_index()
    
    first_vote_time_df = voters_df.groupby('question_text')['voting_time'].min().reset_index()
    first_vote_time_df.columns = ['que_text', 'first_voting_time']
    
    merged_df = pd.merge(que_ans_grouped, first_vote_time_df, on='que_text', how='inner')
    merged_df['response_time'] = (merged_df['first_voting_time'] - merged_df['que_created_at']).dt.total_seconds() / 60
    
    return (merged_df.nsmallest if fastest else merged_df.nlargest)(top_n, 'response_time')[['que_text', 'response_time']]

def create_overview_dashboard(voters_df, que_ans_df, correct_answers_df):
    """Create comprehensive overview dashboard with summary statistics and insights"""
    st.header("📊 Voting Insights Dashboard Overview")
    
    # Overall Summary Statistics
    st.subheader("🔍 Key Metrics")
    
    # Calculate and display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_voters = len(voters_df['voter_name'].unique())
        st.metric("Total Voters", total_voters)
    
    with col2:
        total_questions = len(voters_df['question_text'].unique())
        st.metric("Total Questions", total_questions)
    
    with col3:
        total_votes = len(voters_df)
        st.metric("Total Votes Cast", total_votes)
    
    with col4:
        correct_answers = performance_analysis(voters_df, correct_answers_df)
        avg_correct_answers = correct_answers['correct_count'].mean()
        st.metric("Avg. Correct Answers", f"{avg_correct_answers:.2f}")
    
    # Engagement Analysis
    st.subheader("📈 Voter Engagement Insights")
    
    # Prepare engagement data
    active_voters = most_active_voters(voters_df)
    early_birds = early_bird_analysis(voters_df, que_ans_df)
    inactive_voters = inactive_voters_analysis(voters_df)
    
    # Engagement Columns
    col5, col6, col7 = st.columns(3)
    
    with col5:
        st.metric("Most Active Voter", 
                  active_voters.iloc[0]['voter_name'], 
                  f"{active_voters.iloc[0]['questions_answered']} questions")
    
    with col6:
        top_early_bird = early_birds.iloc[0]['voter_name']
        st.metric("Top Early Bird", 
                  top_early_bird, 
                  f"{early_birds.iloc[0]['early_bird_count']} first votes")
    
    with col7:
        top_inactive = inactive_voters.iloc[0]
        st.metric("Longest Inactive Voter", 
                  top_inactive['voter_name'], 
                  f"{top_inactive['days_since_last_vote']} days")
    
    # Performance and Difficulty Analysis
    st.subheader("🏆 Performance & Question Complexity")
    
    # Performance data
    top_performers = performance_analysis(voters_df, correct_answers_df)
    difficult_questions_list = difficult_questions(voters_df)
    incorrect_questions_list = incorrect_questions(voters_df, correct_answers_df)
    
    col8, col9, col10 = st.columns(3)
    
    with col8:
        top_performer = top_performers.iloc[0]
        st.metric("Top Performer", 
                  top_performer['voter_name'], 
                  f"{top_performer['correct_count']} correct answers")
    
    with col9:
        most_difficult_question = difficult_questions_list.iloc[0]
        st.metric("Most Difficult Question", 
                  f"Votes: {most_difficult_question['vote_count']}")
    
    with col10:
        most_incorrect_question = incorrect_questions_list.index[0]
        incorrect_count = incorrect_questions_list.loc[most_incorrect_question, 'Incorrect']
        st.metric("Question with Most Incorrect", 
                  f"Incorrect Votes: {incorrect_count}")
    
    # Response Time Analysis
    st.subheader("⏱️ Response Time Insights")
    
    fastest_questions = response_time_analysis(voters_df, que_ans_df, fastest=True)
    slowest_questions = response_time_analysis(voters_df, que_ans_df, fastest=False)
    
    col11, col12 = st.columns(2)
    
    with col11:
        fastest_question = fastest_questions.iloc[0]
        st.metric("Fastest Responded Question", 
                  f"Response Time: {fastest_question['response_time']:.2f} min")
    
    with col12:
        slowest_question = slowest_questions.iloc[0]
        st.metric("Slowest Responded Question", 
                  f"Response Time: {slowest_question['response_time']:.2f} min")
    
    # Additional Insights and Observations
    st.subheader("💡 Additional Insights")
    
    # Distribution of votes
    vote_distribution = voters_df.groupby('voter_name')['question_text'].count()
    
    # Visualize vote distribution
    fig_distribution = px.histogram(vote_distribution, 
                                    x=vote_distribution.values, 
                                    title='Distribution of Votes per Voter')
    st.plotly_chart(fig_distribution, use_container_width=True)
    
    # Observations
    observations = [
        f"Total unique voters: {total_voters}",
        f"Total questions voted on: {total_questions}",
        f"Average votes per question: {total_votes / total_questions:.2f}",
        f"Voter with most correct answers: {top_performers.iloc[0]['voter_name']}",
        f"Most inactive voter: {inactive_voters.iloc[0]['voter_name']}"
    ]
    
    st.write("🔹 Key Observations:")
    for obs in observations:
        st.write(f"- {obs}")

def create_advanced_visualizations(voters_df, que_ans_df, correct_answers_df):
    """Create more complex and interactive visualizations"""
    
    # Multi-dimensional Performance Analysis
    st.header("🔬 Advanced Performance Insights")
    
    # Interactive Scatter Plot: Performance vs Activity
    performance_df = performance_analysis(voters_df, correct_answers_df)
    active_voters = most_active_voters(voters_df)
    
    merged_performance = pd.merge(performance_df, active_voters, on='voter_name')
    
    # Scatter plot with hover information
    fig_performance_scatter = px.scatter(
        merged_performance, 
        x='questions_answered', 
        y='correct_count',
        hover_name='voter_name',
        labels={
            'questions_answered': 'Total Questions Answered', 
            'correct_count': 'Correct Answers'
        },
        title='Performance vs Voter Activity',
        color='correct_count',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_performance_scatter, use_container_width=True)
    
    # Time Series of Voting Patterns
    st.subheader("⏰ Voting Time Series")
    
    # Prepare time series data
    voters_df['voting_time'] = pd.to_datetime(voters_df['voting_time'])
    time_series_data = voters_df.groupby([pd.Grouper(key='voting_time', freq='H'), 'voter_name']).size().reset_index(name='vote_count')
    
    # Interactive time series plot
    fig_time_series = px.line(
        time_series_data, 
        x='voting_time', 
        y='vote_count', 
        color='voter_name',
        title='Hourly Voting Patterns by Voter',
        labels={'voting_time': 'Time', 'vote_count': 'Number of Votes'}
    )
    st.plotly_chart(fig_time_series, use_container_width=True)
    
    # Sankey Diagram: Question to Voter Flow
    st.subheader("🔀 Question-Voter Interaction Flow")
    
    # Prepare Sankey data
    sankey_data = voters_df.groupby(['question_text', 'voter_name']).size().reset_index(name='vote_count')
    
    # Create nodes
    questions = sankey_data['question_text'].unique()
    voters = sankey_data['voter_name'].unique()
    
    node_labels = list(questions) + list(voters)
    
    # Create links
    links = {
        'source': [list(node_labels).index(row['question_text']) for index, row in sankey_data.iterrows()],
        'target': [list(node_labels).index(row['voter_name']) for index, row in sankey_data.iterrows()],
        'value': sankey_data['vote_count']
    }
    
    # Sankey diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = node_labels,
          color = "blue"
        ),
        link = dict(
          source = links['source'], 
          target = links['target'],
          value = links['value']
        )
    )])
    
    fig_sankey.update_layout(title_text="Question-Voter Interaction Flow", font_size=10)
    st.plotly_chart(fig_sankey, use_container_width=True)

def create_interactive_filters(voters_df, que_ans_df, correct_answers_df):
    """Add more interactive and dynamic filtering options"""
    
    st.sidebar.header("🔍 Advanced Filters")
    
    # Date Range Filter
    st.sidebar.subheader("Date Range")
    voters_df['voting_time'] = pd.to_datetime(voters_df['voting_time'])
    
    min_date = voters_df['voting_time'].min()
    max_date = voters_df['voting_time'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range", 
        value=(min_date, max_date), 
        min_value=min_date, 
        max_value=max_date
    )
    
    # Voter Selection Multi-select
    st.sidebar.subheader("Voter Selection")
    voter_selection = st.sidebar.multiselect(
        "Select Specific Voters", 
        options=voters_df['voter_name'].unique(),
        default=None
    )
    
    # Performance Threshold
    st.sidebar.subheader("Performance Filters")
    min_correct_answers = st.sidebar.slider(
        "Minimum Correct Answers", 
        min_value=0, 
        max_value=int(performance_analysis(voters_df, correct_answers_df)['correct_count'].max()),
        value=0
    )
    
    # Apply Filters
    filtered_df = voters_df.copy()
    
    # Date Range Filter
    if date_range:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['voting_time'].dt.date >= start_date) & 
            (filtered_df['voting_time'].dt.date <= end_date)
        ]
    
    # Voter Selection Filter
    if voter_selection:
        filtered_df = filtered_df[filtered_df['voter_name'].isin(voter_selection)]
    
    # Performance Filter
    performance_df = performance_analysis(filtered_df, correct_answers_df)
    high_performers = performance_df[performance_df['correct_count'] >= min_correct_answers]['voter_name']
    
    if min_correct_answers > 0:
        filtered_df = filtered_df[filtered_df['voter_name'].isin(high_performers)]

    return filtered_df

def create_response_time_distribution(voters_df, que_ans_df):
    """Create a detailed response time distribution visualization"""
    st.header("⏱️ Response Time Distribution")
    
    # Calculate response times for all questions
    response_times = response_time_analysis(voters_df, que_ans_df, fastest=True)
    response_times['response_time'] = response_times['response_time']  # in minutes
    
    # Create histogram of response times
    fig_response_time = px.histogram(
        response_times, 
        x='response_time', 
        title='Distribution of Question Response Times',
        labels={'response_time': 'Response Time (minutes)'},
        marginal='box'  # Add a box plot for more detailed distribution
    )
    
    # Additional statistics
    mean_response_time = response_times['response_time'].mean()
    median_response_time = response_times['response_time'].median()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mean Response Time", f"{mean_response_time:.2f} min")
    with col2:
        st.metric("Median Response Time", f"{median_response_time:.2f} min")
    with col3:
        st.metric("Total Questions", len(response_times))
    
    st.plotly_chart(fig_response_time, use_container_width=True)
    
    # Optional: Detailed breakdown of response time quartiles
    quartiles = response_times['response_time'].quantile([0.25, 0.5, 0.75])
    st.subheader("Response Time Quartiles")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("25th Percentile", f"{quartiles[0.25]:.2f} min")
    with col2:
        st.metric("50th Percentile (Median)", f"{quartiles[0.5]:.2f} min")
    with col3:
        st.metric("75th Percentile", f"{quartiles[0.75]:.2f} min")

def create_dashboard():
    st.set_page_config(layout="wide", page_title="Comprehensive Voting Insights")
    
    # Load data
    voters_df, que_ans_df, correct_answers_df = load_data()
    
    st.title("🗳️ Comprehensive Voting Insights Dashboard")

    # Create tabs for different analyses
    tabs = [
        "📊 Dashboard Overview",  
        "🏆 Most Active Voters", 
        "😴 Least Active Voters", 
        "🐦 Early Birds", 
        "🌟 Top Performers",
        "⏳ Inactive Voters",
        "❓ Difficult Questions", 
        "❌ Incorrect Questions",
        "✅ Easy Questions",
        "⚡ Fast Responded Questions",
        "🐌 Slow Responded Questions",
        "⏱️ Response Time Distribution",
        "📈 Advanced Analytics"
    ]
    
    selected_tab = st.sidebar.radio("Choose Analysis", tabs)

    max_n = len(voters_df['voter_name'].unique())

    # Only show slider for tabs that are not Advanced Analytics
    if selected_tab != "📈 Advanced Analytics":
        n_value = st.sidebar.slider("N", min_value=1, max_value=max_n, value=10)
    else:
        n_value = 15
    
    # Render appropriate analysis based on selected tab
    if selected_tab == "📊 Dashboard Overview":
        create_overview_dashboard(voters_df, que_ans_df, correct_answers_df)

    elif selected_tab == "🏆 Most Active Voters":
        st.header("🏆 Top N Most Active Voters")
        most_active = most_active_voters(voters_df, top_n=n_value)
        fig = px.bar(most_active, x='voter_name', y='questions_answered')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "😴 Least Active Voters":
        st.header("😴 Top N Least Active Voters")
        least_active = least_active_voters(voters_df, top_n=n_value)
        fig = px.bar(least_active, x='voter_name', y='questions_answered')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "🐦 Early Birds":
        st.header("🐦 Top Early Bird Voters")
        early_birds = early_bird_analysis(voters_df, que_ans_df, top_n=n_value)
        fig = px.bar(early_birds, x='voter_name', y='early_bird_count')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "🌟 Top Performers":
        st.header("🌟 Top Performers by Correct Answers")
        top_performers = performance_analysis(voters_df, correct_answers_df, top_n=n_value)
        fig = px.bar(top_performers, x='voter_name', y='correct_count')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "⏳ Inactive Voters":
        st.header("⏳ Top Inactive Voters")
        inactive_voters = inactive_voters_analysis(voters_df, top_n=n_value)
        fig = px.bar(inactive_voters, x='voter_name', y='days_since_last_vote')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "❓ Difficult Questions":
        st.header("❓ Most Difficult Questions (Least Voted)")
        difficult_qs = difficult_questions(voters_df, top_n=n_value)
        fig = px.bar(difficult_qs, x='question_text', y='vote_count')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "❌ Incorrect Questions":
        st.header("❌ Questions with More Incorrect Votes")
        incorrect_qs = incorrect_questions(voters_df, correct_answers_df, top_n=n_value)
        fig = px.bar(incorrect_qs.reset_index(), x='question_text', y=['Correct', 'Incorrect'])
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "✅ Easy Questions":
        st.header("✅ Questions with Zero Incorrect Votes")
        easy_qs = easy_questions(voters_df, correct_answers_df)

        # Sort the easy questions by number of correct votes in descending order
        sorted_easy_qs = easy_qs.sort_values(by='Correct', ascending=False)

        fig = px.bar(sorted_easy_qs.reset_index(), x='question_text', y='Correct')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "⚡ Fast Responded Questions":
        st.header("⚡ Fastest Responded Questions")
        fast_qs = response_time_analysis(voters_df, que_ans_df, fastest=True, top_n=n_value)
        fig = px.bar(fast_qs, x='que_text', y='response_time')
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "🐌 Slow Responded Questions":
        st.header("🐌 Slowest Responded Questions")
        slow_qs = response_time_analysis(voters_df, que_ans_df, fastest=False, top_n=n_value)
        fig = px.bar(slow_qs, x='que_text', y='response_time')
        st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "⏱️ Response Time Distribution":
        create_response_time_distribution(voters_df, que_ans_df)

    elif selected_tab == "📈 Advanced Analytics":
        # Apply Interactive Filters
        filtered_df = create_interactive_filters(voters_df, que_ans_df, correct_answers_df)
        create_advanced_visualizations(filtered_df, que_ans_df, correct_answers_df)

def main():
    create_dashboard()

if __name__ == "__main__":
    main()