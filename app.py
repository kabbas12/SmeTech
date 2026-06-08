# future_value_calculator.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="Future Value Calculator",
    page_icon="💰",
    layout="wide"
)

# Title and description
st.title("💰 Future Value Calculator")
st.markdown("### Calculate the future value of your investment with interactive charts")
st.markdown("---")

# Create sidebar for inputs
st.sidebar.header("Investment Parameters")

# Input parameters
current_investment = st.sidebar.number_input(
    "Current Investment ($)",
    min_value=0.0,
    value=10000.0,
    step=1000.0,
    format="%0.2f"
)

monthly_contribution = st.sidebar.number_input(
    "Monthly Contribution ($)",
    min_value=0.0,
    value=500.0,
    step=100.0,
    format="%0.2f"
)

interest_rate = st.sidebar.number_input(
    "Annual Interest Rate (%)",
    min_value=0.0,
    max_value=30.0,
    value=8.0,
    step=0.5,
    format="%0.1f"
)

tenure_years = st.sidebar.number_input(
    "Investment Tenure (Years)",
    min_value=1,
    max_value=50,
    value=10,
    step=1
)

compounding_frequency = st.sidebar.selectbox(
    "Compounding Frequency",
    ["Annually", "Semi-Annually", "Quarterly", "Monthly"]
)

# Advanced options
st.sidebar.markdown("---")
st.sidebar.subheader("Advanced Options")
inflation_rate = st.sidebar.number_input(
    "Expected Inflation Rate (%)",
    min_value=0.0,
    max_value=20.0,
    value=2.0,
    step=0.5,
    format="%0.1f"
)

tax_rate = st.sidebar.number_input(
    "Tax Rate on Returns (%)",
    min_value=0.0,
    max_value=50.0,
    value=0.0,
    step=5.0,
    format="%0.1f"
)

# Calculate compounding periods per year
compounding_map = {
    "Annually": 1,
    "Semi-Annually": 2,
    "Quarterly": 4,
    "Monthly": 12
}
n_per_year = compounding_map[compounding_frequency]

# Convert annual rate to periodic rate
periodic_rate = (interest_rate / 100) / n_per_year
total_periods = tenure_years * n_per_year

# Calculate future value
def calculate_future_value(principal, monthly_contrib, rate_per_period, n_periods, n_per_year, monthly_contrib_flag=True):
    """
    Calculate future value with monthly contributions
    """
    # Future value of initial investment
    fv_principal = principal * (1 + rate_per_period) ** n_periods
    
    if monthly_contrib_flag and monthly_contrib > 0:
        # Convert monthly contribution to periodic contribution
        periodic_contrib = monthly_contrib / (n_per_year / 12)
        
        # Future value of periodic contributions
        if rate_per_period == 0:
            fv_contributions = periodic_contrib * n_periods
        else:
            fv_contributions = periodic_contrib * ((1 + rate_per_period) ** n_periods - 1) / rate_per_period
    else:
        fv_contributions = 0
    
    total_fv = fv_principal + fv_contributions
    return total_fv, fv_principal, fv_contributions

# Calculate future value
fv_total, fv_principal, fv_contributions = calculate_future_value(
    current_investment, 
    monthly_contribution, 
    periodic_rate, 
    total_periods, 
    n_per_year
)

# Calculate future value with inflation adjustment
fv_real = fv_total / ((1 + inflation_rate/100) ** tenure_years)

# Calculate after-tax future value
if tax_rate > 0:
    total_gain = fv_total - current_investment - (monthly_contribution * 12 * tenure_years)
    tax_amount = total_gain * (tax_rate / 100)
    fv_after_tax = fv_total - tax_amount
else:
    fv_after_tax = fv_total
    tax_amount = 0

# Create arrays for year-by-year calculation
years = np.arange(0, tenure_years + 1)
fv_yearly = []
principal_yearly = []
contributions_yearly = []

for year in years:
    periods = year * n_per_year
    fv_year, fv_principal_year, fv_contrib_year = calculate_future_value(
        current_investment, 
        monthly_contribution, 
        periodic_rate, 
        periods, 
        n_per_year
    )
    fv_yearly.append(fv_year)
    principal_yearly.append(fv_principal_year)
    contributions_yearly.append(fv_contrib_year)

# Create DataFrame for plotting
df_growth = pd.DataFrame({
    'Year': years,
    'Principal Value': principal_yearly,
    'Contributions Value': contributions_yearly,
    'Total Value': fv_yearly
})

# Melt dataframe for stacked area chart
df_melted = df_growth.melt(id_vars=['Year'], 
                           value_vars=['Principal Value', 'Contributions Value'],
                           var_name='Component', 
                           value_name='Value')

# Main content area - Key Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📈 Future Value (Before Tax)",
        value=f"${fv_total:,.2f}",
        delta=f"+${fv_total - current_investment:,.2f}"
    )

with col2:
    st.metric(
        label="💰 Total Contributions",
        value=f"${(current_investment + monthly_contribution * 12 * tenure_years):,.2f}",
        delta=f"${monthly_contribution * 12 * tenure_years:,.0f} from contributions"
    )

with col3:
    st.metric(
        label="📊 Total Returns",
        value=f"${fv_total - current_investment - (monthly_contribution * 12 * tenure_years):,.2f}"
    )

with col4:
    st.metric(
        label="🏦 Real Value (After Inflation)",
        value=f"${fv_real:,.2f}",
        delta=f"{(1 - fv_real/fv_total)*100:.1f}% lost to inflation"
    )

if tax_rate > 0:
    col5, col6 = st.columns(2)
    with col5:
        st.metric(
            label="💰 After-Tax Value",
            value=f"${fv_after_tax:,.2f}",
            delta=f"-${tax_amount:,.2f} in taxes"
        )

st.markdown("---")

# Create tabs for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["📊 Growth Chart", "📈 Year-by-Year Analysis", "💰 Contribution Impact", "📋 Detailed Report"])

with tab1:
    st.subheader("Investment Growth Over Time")
    
    # Create interactive line chart with Plotly
    fig1 = go.Figure()
    
    fig1.add_trace(go.Scatter(
        x=df_growth['Year'],
        y=df_growth['Total Value'],
        mode='lines+markers',
        name='Total Value',
        line=dict(color='green', width=3),
        marker=dict(size=8),
        hovertemplate='Year: %{x}<br>Value: $%{y:,.2f}<extra></extra>'
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_growth['Year'],
        y=df_growth['Principal Value'],
        mode='lines',
        name='Initial Investment Growth',
        line=dict(color='blue', width=2, dash='dash'),
        hovertemplate='Year: %{x}<br>Value: $%{y:,.2f}<extra></extra>'
    ))
    
    fig1.update_layout(
        title='Future Value Projection',
        xaxis_title='Year',
        yaxis_title='Value ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Stacked area chart
    st.subheader("Investment Composition Over Time")
    fig2 = px.area(df_melted, x='Year', y='Value', color='Component',
                   title='Composition of Investment Value',
                   template='plotly_white',
                   color_discrete_map={'Principal Value': 'blue', 'Contributions Value': 'orange'})
    fig2.update_layout(height=450)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Detailed Year-by-Year Growth")
    
    # Add annual return rate column
    df_growth['Annual Return'] = df_growth['Total Value'].pct_change() * 100
    df_growth['Annual Return'] = df_growth['Annual Return'].fillna(0)
    
    # Display table
    display_df = df_growth.copy()
    display_df['Total Value'] = display_df['Total Value'].apply(lambda x: f"${x:,.2f}")
    display_df['Principal Value'] = display_df['Principal Value'].apply(lambda x: f"${x:,.2f}")
    display_df['Contributions Value'] = display_df['Contributions Value'].apply(lambda x: f"${x:,.2f}")
    display_df['Annual Return'] = display_df['Annual Return'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Bar chart of annual growth
    df_growth['Growth'] = df_growth['Total Value'].diff().fillna(0)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_growth['Year'][1:],
        y=df_growth['Growth'][1:],
        name='Annual Growth',
        marker_color='lightgreen',
        hovertemplate='Year: %{x}<br>Growth: $%{y:,.2f}<extra></extra>'
    ))
    
    fig3.update_layout(
        title='Annual Growth in Investment Value',
        xaxis_title='Year',
        yaxis_title='Growth ($)',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Impact of Monthly Contributions")
    
    # Calculate scenarios with different contribution amounts
    contribution_scenarios = [0, monthly_contribution/2, monthly_contribution, monthly_contribution*2]
    scenario_labels = ['No Contribution', '50% Contribution', 'Base Contribution', 'Double Contribution']
    
    fig4 = go.Figure()
    
    for contrib, label in zip(contribution_scenarios, scenario_labels):
        fv_scenario = []
        for year in years:
            periods = year * n_per_year
            fv_year, _, _ = calculate_future_value(
                current_investment, 
                contrib, 
                periodic_rate, 
                periods, 
                n_per_year
            )
            fv_scenario.append(fv_year)
        
        fig4.add_trace(go.Scatter(
            x=years,
            y=fv_scenario,
            mode='lines',
            name=label,
            hovertemplate='Year: %{x}<br>Value: $%{y:,.2f}<extra></extra>'
        ))
    
    fig4.update_layout(
        title='Impact of Monthly Contributions on Future Value',
        xaxis_title='Year',
        yaxis_title='Future Value ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    st.plotly_chart(fig4, use_container_width=True)
    
    # Contribution vs Returns pie chart at end of tenure
    total_principal = current_investment
    total_contributions = monthly_contribution * 12 * tenure_years
    total_returns = fv_total - total_principal - total_contributions
    
    fig5 = go.Figure(data=[go.Pie(
        labels=['Initial Investment', 'Monthly Contributions', 'Investment Returns'],
        values=[total_principal, total_contributions, total_returns],
        hole=.3,
        marker_colors=['blue', 'orange', 'green']
    )])
    
    fig5.update_layout(
        title='Final Value Composition',
        height=450,
        template='plotly_white'
    )
    
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    st.subheader("Detailed Investment Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Investment Summary")
        st.markdown(f"""
        - **Initial Investment:** ${current_investment:,.2f}
        - **Monthly Contribution:** ${monthly_contribution:,.2f}
        - **Total Contributions:** ${(current_investment + monthly_contribution * 12 * tenure_years):,.2f}
        - **Investment Tenure:** {tenure_years} years
        - **Annual Interest Rate:** {interest_rate}%
        - **Compounding Frequency:** {compounding_frequency}
        """)
    
    with col2:
        st.markdown("### Returns Summary")
        st.markdown(f"""
        - **Total Future Value:** ${fv_total:,.2f}
        - **Total Returns:** ${fv_total - current_investment - (monthly_contribution * 12 * tenure_years):,.2f}
        - **Real Value (Inflation Adj.):** ${fv_real:,.2f}
        - **Annualized Return:** {((fv_total / (current_investment + monthly_contribution * 12 * tenure_years)) ** (1/tenure_years) - 1) * 100:.2f}%
        """)
    
    if tax_rate > 0:
        st.markdown("### Tax Impact")
        st.markdown(f"""
        - **Tax Rate:** {tax_rate}%
        - **Tax Amount:** ${tax_amount:,.2f}
        - **After-Tax Value:** ${fv_after_tax:,.2f}
        """)
    
    # Download button for data
    csv = df_growth.to_csv(index=False)
    st.download_button(
        label="📥 Download Growth Data (CSV)",
        data=csv,
        file_name=f"investment_growth_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("### 📝 Notes")
st.markdown("""
- This calculator assumes contributions are made at the beginning of each period
- Returns are reinvested and compounded according to the selected frequency
- Inflation adjustment shows the purchasing power of your future value in today's dollars
- Tax calculation is simplified and may not reflect your actual tax situation
""")
