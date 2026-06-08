# app.py
# A Simple SME Lending Management System

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

# ------------------- 1. Configuration & Session State -------------------
st.set_page_config(page_title="SME Lending System", layout="wide")
st.title("💰 SME Lending System")

# Initialize session state to store data (simulating a database)
if 'clients' not in st.session_state:
    # Sample data structure for clients
    st.session_state.clients = pd.DataFrame({
        'client_id': [],
        'company_name': [],
        'annual_revenue': [],
        'credit_score': [],
        'loan_amount_requested': [],
        'status': [],  # Pending, Approved, Rejected, Disbursed
        'interest_rate': [],
        'monthly_emi': [],
        'remaining_balance': []
    })

if 'loans' not in st.session_state:
    st.session_state.loans = pd.DataFrame({
        'loan_id': [],
        'client_id': [],
        'amount': [],
        'interest_rate': [],
        'start_date': [],
        'remaining_balance': [],
        'status': [] # Active, Closed
    })

# ------------------- 2. Helper Functions (Logic) -------------------

def calculate_credit_score(annual_revenue, requested_amount):
    """
    Simple rule-based credit scoring.
    High revenue relative to loan amount = higher score.
    """
    ratio = annual_revenue / requested_amount if requested_amount > 0 else 0
    if ratio >= 3:
        return 750  # Low Risk
    elif ratio >= 1.5:
        return 650  # Medium Risk
    else:
        return 550  # High Risk

def calculate_interest_and_emi(credit_score, principal, tenure_months=12):
    """
    Risk-based pricing.
    Higher credit score = lower interest rate.
    Calculates EMI using simple amortization.
    """
    if credit_score >= 700:
        rate = 0.08  # 8%
    elif credit_score >= 600:
        rate = 0.12  # 12%
    else:
        rate = 0.18  # 18% (High risk)
    
    # Monthly Interest Rate
    r = rate / 12
    # EMI Formula
    emi = principal * r * ((1+r)**tenure_months) / (((1+r)**tenure_months) - 1)
    return rate * 100, emi

def approve_loan(credit_score, requested_amount, annual_revenue):
    """Decision logic: Approve or Reject"""
    if credit_score < 600:
        return "Rejected", "Credit score below threshold (600)."
    
    max_loan_limit = annual_revenue * 0.5  # Bank lends max 50% of annual revenue
    if requested_amount > max_loan_limit:
        return "Rejected", f"Requested amount exceeds 50% of annual revenue (Max: ${max_loan_limit:,.2f})."
    
    return "Approved", "Eligible for loan."

# ------------------- 3. Sidebar Navigation -------------------
st.sidebar.header("Navigation")
menu = st.sidebar.selectbox("Select Module", 
    ["New Application", "Credit Scoring & Approval", "Disbursement", "Client List", "Outstanding Loans & Repayment"])

# ------------------- 4. Module Implementations -------------------

# --- MODULE 1: New Application ---
if menu == "New Application":
    st.header("📝 SME Loan Application")
    with st.form("application_form"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name")
            revenue = st.number_input("Annual Revenue (USD)", min_value=0, step=1000)
        with col2:
            request_amount = st.number_input("Loan Amount Requested (USD)", min_value=0, step=1000)
        
        submitted = st.form_submit_button("Submit Application")
        
        if submitted and company:
            # Auto-calculate credit score based on financials
            score = calculate_credit_score(revenue, request_amount)
            client_id = str(uuid.uuid4())[:8]
            
            new_client = pd.DataFrame([{
                'client_id': client_id,
                'company_name': company,
                'annual_revenue': revenue,
                'credit_score': score,
                'loan_amount_requested': request_amount,
                'status': 'Pending',
                'interest_rate': 0,
                'monthly_emi': 0,
                'remaining_balance': 0
            }])
            
            st.session_state.clients = pd.concat([st.session_state.clients, new_client], ignore_index=True)
            st.success(f"Application Submitted! Your Application ID: {client_id}")
            st.info(f"Calculated Credit Score: {score}. Proceed to Approval Module.")

# --- MODULE 2: Credit Scoring & Approval ---
elif menu == "Credit Scoring & Approval":
    st.header("⚖️ Underwriting & Decision")
    
    pending_clients = st.session_state.clients[st.session_state.clients['status'] == 'Pending']
    
    if pending_clients.empty:
        st.info("No pending applications.")
    else:
        for idx, row in pending_clients.iterrows():
            with st.expander(f"{row['company_name']} (Score: {row['credit_score']}) - Request: ${row['loan_amount_requested']:,.0f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Annual Revenue", f"${row['annual_revenue']:,.0f}")
                    st.metric("Credit Score", row['credit_score'])
                
                # Decision Logic
                status, reason = approve_loan(row['credit_score'], row['loan_amount_requested'], row['annual_revenue'])
                
                if status == "Approved":
                    interest, emi = calculate_interest_and_emi(row['credit_score'], row['loan_amount_requested'])
                    st.success(f"✅ Decision: {status}")
                    st.caption(reason)
                    st.metric("Proposed Interest Rate", f"{interest:.1f}%")
                    st.metric("Monthly EMI (12 Months)", f"${emi:,.2f}")
                    
                    if st.button(f"Approve {row['company_name']}", key=f"approve_{row['client_id']}"):
                        # Update records
                        st.session_state.clients.loc[idx, 'status'] = 'Approved'
                        st.session_state.clients.loc[idx, 'interest_rate'] = interest
                        st.session_state.clients.loc[idx, 'monthly_emi'] = emi
                        st.session_state.clients.loc[idx, 'remaining_balance'] = row['loan_amount_requested']
                        st.rerun()
                else:
                    st.error(f"❌ Decision: {status}")
                    st.warning(reason)
                    if st.button(f"Reject {row['company_name']}", key=f"reject_{row['client_id']}"):
                        st.session_state.clients.loc[idx, 'status'] = 'Rejected'
                        st.rerun()

# --- MODULE 3: Disbursement ---
elif menu == "Disbursement":
    st.header("💸 Disbursement")
    approved_clients = st.session_state.clients[st.session_state.clients['status'] == 'Approved']
    
    if approved_clients.empty:
        st.info("No approved loans waiting for disbursement.")
    else:
        for idx, row in approved_clients.iterrows():
            st.write(f"**{row['company_name']}** - Approved Amount: ${row['loan_amount_requested']:,.0f}")
            if st.button(f"Disburse to {row['company_name']}", key=f"disburse_{row['client_id']}"):
                st.session_state.clients.loc[idx, 'status'] = 'Disbursed'
                # Create loan record
                new_loan = pd.DataFrame([{
                    'loan_id': str(uuid.uuid4())[:8],
                    'client_id': row['client_id'],
                    'amount': row['loan_amount_requested'],
                    'interest_rate': row['interest_rate'],
                    'start_date': datetime.now().date(),
                    'remaining_balance': row['loan_amount_requested'],
                    'status': 'Active'
                }])
                st.session_state.loans = pd.concat([st.session_state.loans, new_loan], ignore_index=True)
                st.success(f"${row['loan_amount_requested']:,.0f} disbursed successfully!")
                st.rerun()

# --- MODULE 4: Client List View ---
elif menu == "Client List":
    st.header("📇 Client Portfolio")
    
    # Filter options
    status_filter = st.multiselect("Filter by Status", options=['Pending', 'Approved', 'Rejected', 'Disbursed'], default=['Disbursed'])
    
    filtered_df = st.session_state.clients[st.session_state.clients['status'].isin(status_filter)]
    
    # Display
    st.dataframe(filtered_df[['client_id', 'company_name', 'annual_revenue', 'credit_score', 'loan_amount_requested', 'status', 'interest_rate']], use_container_width=True)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    total_loans = st.session_state.clients[st.session_state.clients['status'] == 'Disbursed']['loan_amount_requested'].sum()
    col1.metric("Total Disbursed Portfolio", f"${total_loans:,.0f}")
    col2.metric("Avg Credit Score (Disbursed)", round(st.session_state.clients[st.session_state.clients['status'] == 'Disbursed']['credit_score'].mean(), 0))

# --- MODULE 5: Outstanding & Repayment ---
elif menu == "Outstanding Loans & Repayment":
    st.header("📊 Loan Repayment Tracker")
    
    active_loans = st.session_state.loans[st.session_state.loans['status'] == 'Active']
    
    if active_loans.empty:
        st.info("No active loans.")
    else:
        for idx, loan in active_loans.iterrows():
            # Get client name
            client_row = st.session_state.clients[st.session_state.clients['client_id'] == loan['client_id']]
            client_name = client_row['company_name'].values[0] if not client_row.empty else "Unknown"
            
            with st.container():
                st.subheader(f"🏢 {client_name}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Principal Left", f"${loan['remaining_balance']:,.2f}")
                col2.metric("Interest Rate", f"{loan['interest_rate']:.1f}%")
                
                # Simulate EMI calculation (Monthly)
                r_monthly = (loan['interest_rate'] / 100) / 12
                # Assume 12 months tenure left dynamically for simplicity, or fixed based on original loan
                emi = loan['remaining_balance'] * (r_monthly * (1+r_monthly)**12) / (((1+r_monthly)**12) - 1)
                col3.metric("Est. Monthly EMI", f"${emi:,.2f}")
                
                # Payment simulation
                payment = st.number_input(f"Payment Amount for {client_name}", min_value=0.0, step=100.0, key=f"pay_{loan['loan_id']}")
                if st.button("Record Payment", key=f"rec_{loan['loan_id']}"):
                    if payment >= emi * 0.9: # Accept payments close to EMI
                        new_balance = max(0, loan['remaining_balance'] - payment)
                        # Update Loans DF
                        st.session_state.loans.loc[idx, 'remaining_balance'] = new_balance
                        # Update Clients DF
                        st.session_state.clients.loc[st.session_state.clients['client_id'] == loan['client_id'], 'remaining_balance'] = new_balance
                        
                        if new_balance <= 0:
                            st.session_state.loans.loc[idx, 'status'] = 'Closed'
                            st.session_state.clients.loc[st.session_state.clients['client_id'] == loan['client_id'], 'status'] = 'Closed'
                            st.success("Loan fully repaid!")
                        else:
                            st.success(f"Payment of ${payment:,.2f} recorded. Remaining: ${new_balance:,.2f}")
                        st.rerun()
                    else:
                        st.error("Payment amount is less than the minimum EMI.")
