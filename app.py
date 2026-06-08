import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import optimize
import warnings
warnings.filterwarnings('ignore')

# Set beautiful styling
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class AdvancedEMICalculator:
    """Advanced EMI Calculator using multiple scientific libraries"""
    
    def __init__(self, principal, annual_rate, tenure_years):
        self.principal = principal
        self.annual_rate = annual_rate
        self.tenure_years = tenure_years
        self.tenure_months = int(tenure_years * 12)
        self.monthly_rate = (annual_rate / 100) / 12
        
    def calculate_emi(self):
        """Calculate EMI"""
        if self.monthly_rate == 0:
            return self.principal / self.tenure_months
        else:
            return self.principal * self.monthly_rate * \
                   (1 + self.monthly_rate)**self.tenure_months / \
                   ((1 + self.monthly_rate)**self.tenure_months - 1)
    
    def create_amortization_dataframe(self):
        """Create full amortization schedule as DataFrame"""
        emi = self.calculate_emi()
        
        data = {
            'Month': np.arange(1, self.tenure_months + 1),
            'EMI': np.full(self.tenure_months, emi),
            'Interest': np.zeros(self.tenure_months),
            'Principal': np.zeros(self.tenure_months),
            'Balance': np.zeros(self.tenure_months)
        }
        
        balance = self.principal
        for month in range(self.tenure_months):
            interest = balance * self.monthly_rate
            principal_paid = emi - interest if month < self.tenure_months - 1 else balance
            data['Interest'][month] = interest
            data['Principal'][month] = principal_paid
            data['Balance'][month] = balance
            balance -= principal_paid
        
        df = pd.DataFrame(data)
        df['Cumulative_Interest'] = df['Interest'].cumsum()
        df['Cumulative_Principal'] = df['Principal'].cumsum()
        
        return df.round(2)
    
    def create_dashboard(self):
        """Create comprehensive dashboard with all visualizations"""
        df = self.create_amortization_dataframe()
        emi = self.calculate_emi()
        
        # Create figure with GridSpec for complex layout
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main title
        fig.suptitle(f'Loan EMI Analysis Dashboard\n'
                    f'₹{self.principal:,.0f} at {self.annual_rate}% for {self.tenure_years} years',
                    fontsize=16, fontweight='bold')
        
        # 1. Loan Balance Over Time (top left)
        ax1 = fig.add_subplot(gs[0, :2])
        ax1.plot(df['Month'], df['Balance'], 'b-', linewidth=2, label='Remaining Balance')
        ax1.fill_between(df['Month'], 0, df['Balance'], alpha=0.3)
        ax1.set_xlabel('Months')
        ax1.set_ylabel('Balance (₹)')
        ax1.set_title('Loan Amortization Schedule')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Key Metrics (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        metrics = {
            'EMI': f'₹{emi:,.0f}',
            'Total Payment': f'₹{df["EMI"].sum():,.0f}',
            'Total Interest': f'₹{df["Interest"].sum():,.0f}',
            'Interest Ratio': f'{(df["Interest"].sum()/self.principal)*100:.1f}%'
        }
        ax2.axis('off')
        y_pos = 0.8
        for key, value in metrics.items():
            ax2.text(0.1, y_pos, f'{key}:', fontsize=11, fontweight='bold')
            ax2.text(0.5, y_pos, value, fontsize=11)
            y_pos -= 0.15
        ax2.set_title('Key Metrics', fontsize=12, fontweight='bold')
        
        # 3. Monthly Breakdown (middle left)
        ax3 = fig.add_subplot(gs[1, :2])
        ax3.bar(df['Month'][:24], df['Principal'][:24], label='Principal', 
                alpha=0.7, color='#2ecc71', width=0.8)
        ax3.bar(df['Month'][:24], df['Interest'][:24], bottom=df['Principal'][:24],
                label='Interest', alpha=0.7, color='#e74c3c', width=0.8)
        ax3.set_xlabel('Months')
        ax3.set_ylabel('Amount (₹)')
        ax3.set_title('Monthly Payment Breakdown (First 24 months)')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Cumulative Payments (middle right)
        ax4 = fig.add_subplot(gs[1, 2])
        ax4.stackplot(df['Month'], df['Cumulative_Principal'], df['Cumulative_Interest'],
                     labels=['Principal', 'Interest'], alpha=0.7,
                     colors=['#2ecc71', '#e74c3c'])
        ax4.set_xlabel('Months')
        ax4.set_ylabel('Cumulative Amount (₹)')
        ax4.set_title('Cumulative Payments')
        ax4.legend(loc='upper left')
        ax4.grid(True, alpha=0.3)
        
        # 5. Heatmap of Interest Payment (bottom)
        ax5 = fig.add_subplot(gs[2, :])
        
        # Create heatmap data (reshape into years)
        years = self.tenure_months // 12
        if years > 0:
            heatmap_data = df['Interest'].values[:years*12].reshape(years, 12)
            sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd',
                       xticklabels=[f'M{i+1}' for i in range(12)],
                       yticklabels=[f'Year {i+1}' for i in range(years)],
                       ax=ax5, cbar_kws={'label': 'Interest Payment (₹)'})
            ax5.set_title('Interest Payment Heatmap (Monthly)', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.show()
        
        return df
    
    def sensitivity_analysis(self):
        """Perform sensitivity analysis on interest rates"""
        rates = np.linspace(max(0, self.annual_rate - 5), 
                           self.annual_rate + 5, 11)
        
        results = []
        for rate in rates:
            calc = AdvancedEMICalculator(self.principal, rate, self.tenure_years)
            emi = calc.calculate_emi()
            df = calc.create_amortization_dataframe()
            results.append({
                'Rate (%)': rate,
                'EMI': emi,
                'Total Interest': df['Interest'].sum(),
                'Total Payment': df['EMI'].sum()
            })
        
        sensitivity_df = pd.DataFrame(results)
        
        # Plot sensitivity
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        axes[0].plot(sensitivity_df['Rate (%)'], sensitivity_df['EMI'], 
                    'bo-', linewidth=2, markersize=8)
        axes[0].set_xlabel('Interest Rate (%)')
        axes[0].set_ylabel('Monthly EMI (₹)')
        axes[0].set_title('EMI Sensitivity to Interest Rate')
        axes[0].grid(True, alpha=0.3)
        
        axes[1].plot(sensitivity_df['Rate (%)'], sensitivity_df['Total Interest'], 
                    'ro-', linewidth=2, markersize=8)
        axes[1].set_xlabel('Interest Rate (%)')
        axes[1].set_ylabel('Total Interest (₹)')
        axes[1].set_title('Total Interest Sensitivity')
        axes[1].grid(True, alpha=0.3)
        
        plt.suptitle('Sensitivity Analysis (±5% from base rate)', fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        return sensitivity_df

def main():
    print("\n" + "="*70)
    print("     ADVANCED EMI CALCULATOR WITH SCIENTIFIC LIBRARIES")
    print("     (NumPy, Pandas, Matplotlib, Seaborn, SciPy)")
    print("="*70)
    
    # Get inputs
    principal = float(input("\nEnter loan amount (₹): "))
    annual_rate = float(input("Enter annual interest rate (%): "))
    tenure_years = float(input("Enter loan tenure (in years): "))
    
    # Create calculator instance
    calc = AdvancedEMICalculator(principal, annual_rate, tenure_years)
    
    # Calculate EMI
    emi = calc.calculate_emi()
    df = calc.create_amortization_dataframe()
    
    # Display summary
    print("\n" + "-"*70)
    print(f"📊 LOAN SUMMARY")
    print("-"*70)
    print(f"Loan Amount:     ₹{principal:,.2f}")
    print(f"Interest Rate:   {annual_rate}%")
    print(f"Tenure:          {tenure_years} years ({calc.tenure_months} months)")
    print(f"Monthly EMI:     ₹{emi:,.2f}")
    print(f"Total Payment:   ₹{df['EMI'].sum():,.2f}")
    print(f"Total Interest:  ₹{df['Interest'].sum():,.2f}")
    print(f"Interest Ratio:  {(df['Interest'].sum()/principal)*100:.1f}%")
    print("-"*70)
    
    # Show options
    print("\n📈 AVAILABLE ANALYSES:")
    print("1. Show Amortization Table")
    print("2. Show Dashboard Visualizations")
    print("3. Show Sensitivity Analysis")
    print("4. Export Data to CSV")
    print("5. All of the above")
    
    choice = input("\nSelect option (1-5): ")
    
    if choice in ['1', '5']:
        pd.set_option('display.max_rows', 20)
        print("\n" + df.to_string(index=False))
        
        # Show statistics
        print("\n📊 STATISTICAL SUMMARY:")
        print(df[['Interest', 'Principal']].describe())
    
    if choice in ['2', '5']:
        calc.create_dashboard()
    
    if choice in ['3', '5']:
        sensitivity_df = calc.sensitivity_analysis()
        print("\n📊 SENSITIVITY ANALYSIS RESULTS:")
        print(sensitivity_df.to_string(index=False))
    
    if choice in ['4', '5']:
        filename = f"emi_analysis_{principal}_{annual_rate}_{tenure_years}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ Data exported to {filename}")

if __name__ == "__main__":
    main()
