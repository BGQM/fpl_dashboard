import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import requests
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="FPL Electric Bills Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title
st.title("⚡ FPL Electric Bills Dashboard")
st.markdown("Analysis of Florida Power & Light monthly bills")

@st.cache_data
def load_fpl_data():
    """Load FPL data from GitHub repository"""
    try:
        url = "https://raw.githubusercontent.com/BGQM/fpl/refs/heads/main/FPL_Bills.csv"
        response = requests.get(url)
        response.raise_for_status()
        
        # Read CSV data
        df = pd.read_csv(StringIO(response.text))
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Calculate unit cost ($/kWh)
        df['Unit_Cost'] = df['Total'] / df['kWh']
        
        # Extract year and month for filtering
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Month_Name'] = df['Date'].dt.strftime('%B')
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Load data
with st.spinner("Loading FPL data from GitHub..."):
    df = load_fpl_data()

if df is not None:
    # Sidebar for year selection
    st.sidebar.header("Filter Options")
    
    available_years = sorted(df['Year'].unique())
    selected_year = st.sidebar.selectbox(
        "Select Year:", 
        available_years,
        index=len(available_years)-1  # Default to most recent year
    )
    
    # Filter data for selected year
    year_df = df[df['Year'] == selected_year].copy()
    year_df = year_df.sort_values('Date')
    
    # Display summary statistics
    st.sidebar.markdown("### Year Summary")
    total_kwh = year_df['kWh'].sum()
    total_cost = year_df['Total'].sum()
    avg_unit_cost = year_df['Unit_Cost'].mean()
    num_bills = len(year_df)
    
    st.sidebar.metric("Total kWh", f"{total_kwh:,.0f}")
    st.sidebar.metric("Total Cost", f"${total_cost:,.2f}")
    st.sidebar.metric("Avg Unit Cost", f"${avg_unit_cost:.4f}/kWh")
    st.sidebar.metric("Number of Bills", num_bills)
    
    # Main dashboard
    if len(year_df) > 0:
        # Create three columns for the main charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly kWh Consumption Chart
            st.subheader(f"Monthly Electricity Consumption ({selected_year})")
            fig_kwh = px.bar(
                year_df, 
                x='Month_Name', 
                y='kWh',
                title=f"Monthly kWh Usage - {selected_year}",
                color='kWh',
                color_continuous_scale='Blues'
            )
            fig_kwh.update_layout(
                xaxis_title="Month",
                yaxis_title="kWh",
                showlegend=False
            )
            fig_kwh.update_xaxes(categoryorder='array', categoryarray=[
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ])
            st.plotly_chart(fig_kwh, width='stretch')
        
        with col2:
            # Monthly Cost Chart
            st.subheader(f"Monthly Electricity Cost ({selected_year})")
            fig_cost = px.bar(
                year_df, 
                x='Month_Name', 
                y='Total',
                title=f"Monthly Bill Amount - {selected_year}",
                color='Total',
                color_continuous_scale='Reds'
            )
            fig_cost.update_layout(
                xaxis_title="Month",
                yaxis_title="Cost ($)",
                showlegend=False
            )
            fig_cost.update_xaxes(categoryorder='array', categoryarray=[
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ])
            st.plotly_chart(fig_cost, width='stretch')
        
        # Unit Cost Chart (full width)
        st.subheader(f"Unit Cost per kWh ({selected_year})")
        fig_unit = px.line(
            year_df, 
            x='Month_Name', 
            y='Unit_Cost',
            title=f"Cost per kWh - {selected_year}",
            markers=True
        )
        fig_unit.update_layout(
            xaxis_title="Month",
            yaxis_title="Cost per kWh ($)"
        )
        fig_unit.update_xaxes(categoryorder='array', categoryarray=[
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ])
        st.plotly_chart(fig_unit, width='stretch')
        
        # Data table
        st.subheader(f"Detailed Data - {selected_year}")
        
        # Format the dataframe for display
        display_df = year_df[['Date', 'kWh', 'Total', 'Unit_Cost']].copy()
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
        display_df['Total'] = display_df['Total'].apply(lambda x: f"${x:.2f}")
        display_df['Unit_Cost'] = display_df['Unit_Cost'].apply(lambda x: f"${x:.4f}")
        
        st.dataframe(display_df, width='stretch')
        
        # Historical comparison (bonus feature)
        if len(available_years) > 1:
            st.subheader("Year-over-Year Comparison")
            
            # Annual summary by year
            annual_summary = df.groupby('Year').agg({
                'kWh': 'sum',
                'Total': 'sum',
                'Unit_Cost': 'mean'
            }).reset_index()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fig_annual_kwh = px.bar(
                    annual_summary, 
                    x='Year', 
                    y='kWh',
                    title="Annual kWh Consumption"
                )
                st.plotly_chart(fig_annual_kwh, width='stretch')
            
            with col2:
                fig_annual_cost = px.bar(
                    annual_summary, 
                    x='Year', 
                    y='Total',
                    title="Annual Total Cost"
                )
                st.plotly_chart(fig_annual_cost, width='stretch')
            
            with col3:
                fig_annual_unit = px.line(
                    annual_summary, 
                    x='Year', 
                    y='Unit_Cost',
                    title="Average Unit Cost",
                    markers=True
                )
                st.plotly_chart(fig_annual_unit, width='stretch')
    
    else:
        st.warning(f"No data available for {selected_year}")
        
else:
    st.error("Failed to load data. Please check the GitHub repository URL.")

# Footer
st.markdown("---")
st.markdown("Data source: [BGQM/fpl GitHub Repository](https://github.com/BGQM/fpl)")
