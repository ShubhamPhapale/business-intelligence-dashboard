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
        return que_ans_df, voter_df, correct_answers_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None

def calculate_insights(voter_df, correct_answers_df, n):
    """Calculate various insights from the data"""
    insights = {}
    
    # Most Active Voters
    insights['active_voters'] = voter_df['voter_name'].value_counts().head(n)
    
    # Early Birds
    if 'response_time' in voter_df.columns:
        early_birds = voter_df.sort_values('response_time')\
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
    
    # Most Incorrectly Answered Questions
    incorrect_ratio = merged_df.groupby('question_text')\
        .agg(incorrect_ratio=('is_correct', lambda x: (~x).mean()))\
        .nlargest(n, 'incorrect_ratio')
    insights['incorrect_questions'] = incorrect_ratio
    
    # Best Performers
    good_performers = merged_df.groupby('voter_name')['is_correct']\
        .agg(['count', 'sum'])\
        .assign(accuracy=lambda x: (x['sum'] / x['count'] * 100))\
        .nlargest(n, 'accuracy')
    insights['good_performers'] = good_performers
    
    # Response Time Analysis
    if 'response_time' in voter_df.columns:
        avg_response_time = voter_df.groupby('question_text')['response_time']\
            .mean()\
            .sort_values()\
            .head(n)
        insights['response_times'] = avg_response_time
    
    return insights

def main():
    st.title("📊 Quiz Insights Dashboard")
    
    # Load data
    que_ans_df, voter_df, correct_answers_df = load_data()
    if que_ans_df is None:
        return
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    n = st.sidebar.slider("Number of records to show", 5, 50, 32)
    
    # Calculate insights
    insights = calculate_insights(voter_df, correct_answers_df, n)
    
    # Create dashboard layout with tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Participation Metrics",
        "⏱️ Response Analysis",
        "✅ Performance Metrics",
        "📊 Question Analysis"
    ])
    
    with tab1:
        st.header("Participation Metrics")
        
        # Active Voters Chart
        fig_active = px.bar(
            insights['active_voters'],
            title="Most Active Participants",
            labels={'value': 'Number of Votes', 'index': 'Voter Name'},
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig_active, use_container_width=True)
        
        # Show raw data in expander
        with st.expander("View Raw Data"):
            st.dataframe(insights['active_voters'])
    
    with tab2:
        st.header("Response Time Analysis")
        if 'response_times' in insights:
            # Response Times Chart
            fig_response = px.bar(
                insights['response_times'],
                title="Average Response Times by Question",
                labels={'value': 'Average Response Time (seconds)', 'index': 'Question'},
                color_discrete_sequence=['#2ca02c']
            )
            st.plotly_chart(fig_response, use_container_width=True)
            
            # Early Birds Chart
            fig_early = px.bar(
                insights['early_birds'],
                title="Early Birds (Quick Responders)",
                labels={'value': 'Number of Early Responses', 'index': 'Voter Name'},
                color_discrete_sequence=['#ff7f0e']
            )
            st.plotly_chart(fig_early, use_container_width=True)
    
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
        
        # Detailed performance metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Accuracy", 
                     f"{insights['good_performers']['accuracy'].mean():.1f}%")
        with col2:
            st.metric("Total Questions Answered", 
                     insights['good_performers']['count'].sum())
    
    with tab4:
        st.header("Question Analysis")
        
        # Incorrect Questions Chart
        fig_incorrect = px.bar(
            insights['incorrect_questions'],
            title="Most Challenging Questions",
            labels={'incorrect_ratio': 'Incorrect Answer Ratio', 'question_text': 'Question'},
            color_discrete_sequence=['#d62728']
        )
        st.plotly_chart(fig_incorrect, use_container_width=True)
        
        # Question difficulty distribution

        # Merge voter data with correct answers
        merged_df = pd.merge(
            voter_df, 
            correct_answers_df.rename(columns={'que_text': 'question_text'}),
            on='question_text'
        )
        merged_df['is_correct'] = merged_df['choice'] == merged_df['ans_text']

        question_difficulty = merged_df.groupby('question_text')['is_correct'].mean()
        fig_dist = px.histogram(
            question_difficulty,
            title="Question Difficulty Distribution",
            labels={'value': 'Correct Answer Ratio'},
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig_dist, use_container_width=True)

if __name__ == "__main__":
    main()