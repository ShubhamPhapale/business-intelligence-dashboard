import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="Quiz Insights Dashboard",
    page_icon="📊",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .stSlider > div > div > div > div {
        background-color: #1f77b4;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    """Load and prepare the data"""
    try:
        que_ans_df = pd.read_excel('Cleaned_Que_Ans.xlsx')
        voter_df = pd.read_excel('Cleaned_Voter.xlsx')
        correct_answers_df = pd.read_excel('Cleaned_Correct_Answers.xlsx')
        
        # Convert voting_time to datetime if it's not already
        if 'voting_time' in voter_df.columns:
            voter_df['voting_time'] = pd.to_datetime(voter_df['voting_time'], errors='coerce')
        
        # Calculate response_time as timedelta
        if 'que_created_at' in que_ans_df.columns:
            que_ans_df['que_created_at'] = pd.to_datetime(que_ans_df['que_created_at'], errors='coerce')
            voter_df = voter_df.merge(
                que_ans_df[['que_text', 'que_created_at']],
                left_on='question_text',
                right_on='que_text',
                how='left'
            )
            voter_df['response_time'] = (voter_df['voting_time'] - voter_df['que_created_at']).dt.total_seconds()
        
        return que_ans_df, voter_df, correct_answers_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None

def calculate_insights(voter_df, correct_answers_df, n):
    """Calculate various insights from the data"""
    insights = {}
    
    # 1. Most Active Voters
    insights['active_voters'] = voter_df['voter_name'].value_counts().head(n)
    
    # 2. Early Birds
    if 'response_time' in voter_df.columns:
        early_birds = voter_df[voter_df['response_time'].notna()]\
            .sort_values('response_time')\
            .drop_duplicates(['question_text'])\
            .groupby('voter_name').size()\
            .nlargest(n)
        insights['early_birds'] = early_birds
    
    # Merge voter data with correct answers
    merged_df = pd.merge(
        voter_df, 
        correct_answers_df.rename(columns={'que_text': 'question_text'}),
        on='question_text'
    )
    merged_df['is_correct'] = merged_df['choice'] == merged_df['ans_text']
    
    # 3. Most Incorrectly Answered Questions
    incorrect_ratio = merged_df.groupby('question_text')\
        .agg(incorrect_ratio=('is_correct', lambda x: (~x).mean()))\
        .nlargest(n, 'incorrect_ratio')
    insights['incorrect_questions'] = incorrect_ratio
    
    # 4. Easy Questions (zero incorrect answers)
    easy_questions = merged_df.groupby('question_text')\
        .agg(correct_ratio=('is_correct', 'mean'))\
        .query('correct_ratio == 1.0')\
        .head(n)
    insights['easy_questions'] = easy_questions
    
    # 5. Least Active Voters
    insights['least_active'] = voter_df['voter_name'].value_counts().tail(n)
    
    # 6. Inactive Followers
    if 'voting_time' in voter_df.columns:
        last_participation = voter_df.groupby('voter_name')['voting_time'].max()
        insights['inactive_followers'] = last_participation.nsmallest(n)
    
    # 7. Good Performers
    good_performers = merged_df.groupby('voter_name')['is_correct']\
        .agg(['count', 'sum'])\
        .assign(accuracy=lambda x: (x['sum'] / x['count'] * 100))\
        .nlargest(n, 'accuracy')
    insights['good_performers'] = good_performers
    
    # 8. Questions with Fewest Votes
    insights['least_voted'] = voter_df['question_text'].value_counts().nsmallest(n)
    
    # 9. Fast Responded Questions
    if 'response_time' in voter_df.columns:
        fast_responses = voter_df[voter_df['response_time'].notna()]\
            .groupby('question_text')['response_time'].min()\
            .nsmallest(n)
        insights['fast_responses'] = fast_responses
    
    # 10. Slow Responded Questions
    if 'response_time' in voter_df.columns:
        slow_responses = voter_df[voter_df['response_time'].notna()]\
            .groupby('question_text')['response_time'].max()\
            .nlargest(n)
        insights['slow_responses'] = slow_responses
    
    return insights

def main():
    st.title("📊 Quiz Insights Dashboard")
    
    # Load data
    que_ans_df, voter_df, correct_answers_df = load_data()
    if que_ans_df is None:
        return
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    n = st.sidebar.slider("Number of records to show", 5, 50, 20)
    
    # Calculate insights
    insights = calculate_insights(voter_df, correct_answers_df, n)
    
    # Create dashboard layout with tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Participation Metrics",
        "⏱️ Response Analysis",
        "✅ Performance Metrics",
        "📊 Question Analysis",
        "👥 User Engagement",
        "⚡ Speed Metrics"
    ])
    
    with tab1:
        st.header("Participation Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Active Voters Chart
            fig_active = px.bar(
                insights['active_voters'],
                title="Most Active Participants",
                labels={'value': 'Number of Votes', 'index': 'Voter Name'},
                color_discrete_sequence=['#1f77b4']
            )
            st.plotly_chart(fig_active, use_container_width=True)
        
        with col2:
            # Least Active Voters Chart
            fig_least_active = px.bar(
                insights['least_active'],
                title="Least Active Participants",
                labels={'value': 'Number of Votes', 'index': 'Voter Name'},
                color_discrete_sequence=['#ff7f0e']
            )
            st.plotly_chart(fig_least_active, use_container_width=True)
    
    with tab2:
        st.header("Response Time Analysis")
        
        if 'fast_responses' in insights and 'slow_responses' in insights:
            col1, col2 = st.columns(2)
            
            with col1:
                # Fast Responses Chart
                fig_fast = px.bar(
                    insights['fast_responses'],
                    title="Fastest Responded Questions",
                    labels={'value': 'Response Time (seconds)', 'index': 'Question'},
                    color_discrete_sequence=['#2ca02c']
                )
                st.plotly_chart(fig_fast, use_container_width=True)
            
            with col2:
                # Slow Responses Chart
                fig_slow = px.bar(
                    insights['slow_responses'],
                    title="Slowest Responded Questions",
                    labels={'value': 'Response Time (seconds)', 'index': 'Question'},
                    color_discrete_sequence=['#d62728']
                )
                st.plotly_chart(fig_slow, use_container_width=True)
        else:
            st.warning("Response time data is not available")
    
    with tab3:
        st.header("Performance Metrics")
        
        # Good Performers Chart
        fig_performers = px.bar(
            insights['good_performers']['accuracy'],
            title="Best Performers by Accuracy",
            labels={'value': 'Accuracy (%)', 'index': 'Voter Name'},
            color_discrete_sequence=['#9467bd']
        )
        st.plotly_chart(fig_performers, use_container_width=True)
        
        # Performance Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Accuracy", 
                     f"{insights['good_performers']['accuracy'].mean():.1f}%")
        with col2:
            st.metric("Total Questions Answered", 
                     insights['good_performers']['count'].sum())
        with col3:
            st.metric("Total Correct Answers",
                     insights['good_performers']['sum'].sum())
    
    with tab4:
        st.header("Question Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Incorrect Questions Chart
            fig_incorrect = px.bar(
                insights['incorrect_questions'],
                title="Most Challenging Questions",
                labels={'incorrect_ratio': 'Incorrect Answer Ratio', 'question_text': 'Question'},
                color_discrete_sequence=['#d62728']
            )
            st.plotly_chart(fig_incorrect, use_container_width=True)
        
        with col2:
            # Easy Questions Chart
            if not insights['easy_questions'].empty:
                fig_easy = px.bar(
                    insights['easy_questions'],
                    title="Easiest Questions (100% Correct)",
                    labels={'correct_ratio': 'Correct Answer Ratio', 'question_text': 'Question'},
                    color_discrete_sequence=['#2ca02c']
                )
                st.plotly_chart(fig_easy, use_container_width=True)
            else:
                st.info("No questions with 100% correct answers found")
    
    with tab5:
        st.header("User Engagement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Early Birds Chart
            if 'early_birds' in insights:
                fig_early = px.bar(
                    insights['early_birds'],
                    title="Early Birds (Quick Responders)",
                    labels={'value': 'Number of Early Responses', 'index': 'Voter Name'},
                    color_discrete_sequence=['#ff7f0e']
                )
                st.plotly_chart(fig_early, use_container_width=True)
            else:
                st.warning("Early birds data is not available")
        
        with col2:
            # Inactive Followers Chart
            if 'inactive_followers' in insights:
                fig_inactive = px.bar(
                    insights['inactive_followers'],
                    title="Inactive Followers (Last Participation)",
                    labels={'value': 'Last Activity Date', 'index': 'Voter Name'},
                    color_discrete_sequence=['#7f7f7f']
                )
                st.plotly_chart(fig_inactive, use_container_width=True)
            else:
                st.warning("Inactive followers data is not available")
    
    with tab6:
        st.header("Speed Metrics")
        
        # Questions with Fewest Votes
        fig_least_voted = px.bar(
            insights['least_voted'],
            title="Questions with Fewest Responses",
            labels={'value': 'Number of Votes', 'index': 'Question'},
            color_discrete_sequence=['#17becf']
        )
        st.plotly_chart(fig_least_voted, use_container_width=True)
        
        # Response Time Distribution
        if 'response_time' in voter_df.columns:
            response_times = voter_df[voter_df['response_time'].notna()]['response_time']
            if not response_times.empty:
                fig_response_dist = px.histogram(
                    response_times,
                    title="Response Time Distribution",
                    labels={'value': 'Response Time (seconds)', 'count': 'Frequency'},
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig_response_dist, use_container_width=True)
            else:
                st.warning("No valid response time data available")

if __name__ == "__main__":
    main()