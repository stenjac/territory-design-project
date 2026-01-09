import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the accounts data
df = pd.read_csv('accounts.csv')

print("=" * 60)
print("TERRITORY ANALYSIS - CURRENT STATE")
print("=" * 60)
print()

# Group accounts by current owner
rep_analysis = df.groupby('current_owner').agg({
    'account_name': 'count',
    'estimated_annual_value': ['sum', 'mean']
}).round(0)

# Flatten column names
rep_analysis.columns = ['num_accounts', 'total_potential', 'avg_account_size']
rep_analysis = rep_analysis.sort_values('total_potential', ascending=False)

# Display individual rep metrics
print("INDIVIDUAL REP METRICS:")
print("-" * 60)
for rep, row in rep_analysis.iterrows():
    print(f"{rep}:")
    print(f"  • Number of accounts: {int(row['num_accounts'])}")
    print(f"  • Total potential: ${row['total_potential']:,.0f}")
    print(f"  • Average account size: ${row['avg_account_size']:,.0f}")
    print()

# Calculate team metrics
highest_rep = rep_analysis['total_potential'].idxmax()
lowest_rep = rep_analysis['total_potential'].idxmin()
highest_value = rep_analysis['total_potential'].max()
lowest_value = rep_analysis['total_potential'].min()
difference = highest_value - lowest_value
imbalance_ratio = highest_value / lowest_value
avg_potential = rep_analysis['total_potential'].mean()
total_potential = rep_analysis['total_potential'].sum()

# Print key findings
print("=" * 60)
print("KEY FINDINGS:")
print("=" * 60)
print(f"{highest_rep} has ${highest_value:,.0f} potential (HIGHEST)")
print(f"{lowest_rep} has ${lowest_value:,.0f} potential (LOWEST)")
print()
print(f"Imbalance: {imbalance_ratio:.1f}x difference")
print(f"Dollar difference: ${difference:,.0f}")
print(f"Average potential per rep: ${avg_potential:,.0f}")
print(f"Total team potential: ${total_potential:,.0f}")
print()

# Calculate distribution metrics
std_dev = rep_analysis['total_potential'].std()
coefficient_of_variation = (std_dev / avg_potential) * 100

# Calculate Balance Score
def calculate_balance_score(cv):
    """
    Calculate balance score based on coefficient of variation
    CV < 20%: Excellent balance (90-100)
    CV 20-30%: Good balance (70-89)
    CV 30-50%: Moderate imbalance (50-69)
    CV > 50%: Poor balance (0-49)
    """
    if cv < 20:
        # Excellent: 90-100 (linear scale from 100 at CV=0 to 90 at CV=20)
        score = 100 - (cv / 20) * 10
        rating = "Excellent Balance"
    elif cv < 30:
        # Good: 70-89 (linear scale from 89 at CV=20 to 70 at CV=30)
        score = 89 - ((cv - 20) / 10) * 19
        rating = "Good Balance"
    elif cv < 50:
        # Moderate: 50-69 (linear scale from 69 at CV=30 to 50 at CV=50)
        score = 69 - ((cv - 30) / 20) * 19
        rating = "Moderate Imbalance"
    else:
        # Poor: 0-49 (linear scale from 49 at CV=50, approaching 0 as CV increases)
        score = max(0, 49 - ((cv - 50) / 50) * 49)
        rating = "Poor Balance"

    return score, rating

balance_score, balance_rating = calculate_balance_score(coefficient_of_variation)

# Determine target recommendation
if coefficient_of_variation > 25:
    target_message = "Target: Get CV under 25% for good balance"
elif coefficient_of_variation > 20:
    target_message = "Target: Get CV under 20% for excellent balance"
else:
    target_message = "Target: Maintain CV under 20%"

print("=" * 60)
print("BALANCE SCORE")
print("=" * 60)
print(f"Current Balance Score: {balance_score:.0f}/100 ({balance_rating})")
print(f"Coefficient of Variation: {coefficient_of_variation:.1f}%")
print(f"{target_message}")
print()
print("Score Breakdown:")
print("  • CV < 20%: Excellent balance (90-100)")
print("  • CV 20-30%: Good balance (70-89)")
print("  • CV 30-50%: Moderate imbalance (50-69)")
print("  • CV > 50%: Poor balance (0-49)")
print()

print("DISTRIBUTION METRICS:")
print("-" * 60)
print(f"Standard deviation: ${std_dev:,.0f}")
print(f"Coefficient of variation: {coefficient_of_variation:.1f}%")
print()

# Show account count distribution
print("ACCOUNT COUNT DISTRIBUTION:")
print("-" * 60)
for rep, row in rep_analysis.iterrows():
    bar = '█' * int(row['num_accounts'] / 2)
    print(f"{rep}: {bar} ({int(row['num_accounts'])} accounts)")
print()

# Calculate workload analysis
print("=" * 60)
print("WORKLOAD ANALYSIS")
print("=" * 60)
print()

# Import capacity calculator functions
import sys
sys.path.append('.')
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MIN_UTILIZATION_PCT,
    MAX_UTILIZATION_PCT
)

# Calculate hours needed for each rep
workload_data = []
for rep in df['current_owner'].unique():
    rep_accounts = df[df['current_owner'] == rep]

    # Calculate total hours needed
    total_hours = 0
    for _, account in rep_accounts.iterrows():
        hours = calculate_account_hours(account['account_size'], account['customer_status'])
        total_hours += hours

    # Calculate utilization
    utilization_pct = (total_hours / AVAILABLE_SELLING_HOURS) * 100

    # Categorize workload
    if utilization_pct < 70:
        status = 'Underutilized'
    elif utilization_pct < 80:
        status = 'Light load'
    elif utilization_pct <= 95:
        status = 'Optimal'
    elif utilization_pct <= 110:
        status = 'Stretched'
    else:
        status = 'Overloaded'

    workload_data.append({
        'rep': rep,
        'accounts': len(rep_accounts),
        'hours_needed': total_hours,
        'capacity': AVAILABLE_SELLING_HOURS,
        'utilization_pct': utilization_pct,
        'status': status
    })

# Create DataFrame and sort by utilization
workload_df = pd.DataFrame(workload_data)
workload_df = workload_df.sort_values('utilization_pct', ascending=False)

# Print workload table
print("WORKLOAD BY REP:")
print("-" * 80)
print(f"{'Rep':<15} {'Accounts':>8} {'Hours Needed':>12} {'Capacity':>8} {'Utilization':>12} {'Status':<15}")
print("-" * 80)
for _, row in workload_df.iterrows():
    print(f"{row['rep']:<15} {row['accounts']:>8} {row['hours_needed']:>12.1f} {row['capacity']:>8.0f} "
          f"{row['utilization_pct']:>11.1f}% {row['status']:<15}")
print("-" * 80)
print(f"{'AVERAGE':<15} {workload_df['accounts'].mean():>8.1f} {workload_df['hours_needed'].mean():>12.1f} "
      f"{AVAILABLE_SELLING_HOURS:>8.0f} {workload_df['utilization_pct'].mean():>11.1f}%")
print()

# Categorize reps by status
status_counts = workload_df['status'].value_counts()
print("WORKLOAD STATUS BREAKDOWN:")
for status, count in sorted(status_counts.items()):
    print(f"  • {status}: {count} reps")
print()

# Key insights
optimal_range_start = MIN_UTILIZATION_PCT * 100
optimal_range_end = MAX_UTILIZATION_PCT * 100
reps_in_optimal = len(workload_df[
    (workload_df['utilization_pct'] >= optimal_range_start) &
    (workload_df['utilization_pct'] <= optimal_range_end)
])

print("KEY WORKLOAD INSIGHTS:")
print(f"  • Reps in optimal range (80-95%): {reps_in_optimal} of {len(workload_df)}")
print(f"  • Utilization range: {workload_df['utilization_pct'].min():.1f}% - {workload_df['utilization_pct'].max():.1f}%")
print(f"  • Utilization spread: {workload_df['utilization_pct'].max() - workload_df['utilization_pct'].min():.1f} percentage points")
print()

# Store workload_df for later use in visualizations
globals()['workload_df'] = workload_df

# Create bar chart
fig, ax = plt.subplots(figsize=(12, 6))

# Sort by total potential for better visualization
rep_analysis_sorted = rep_analysis.sort_values('total_potential', ascending=True)
reps = rep_analysis_sorted.index
values = rep_analysis_sorted['total_potential'] / 1000000  # Convert to millions

# Create color gradient (red for low, green for high)
colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(reps)))

bars = ax.barh(reps, values, color=colors, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars, values)):
    width = bar.get_width()
    ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
            f'${value:.2f}M',
            ha='left', va='center', fontweight='bold', fontsize=10)

# Add average line
ax.axvline(avg_potential / 1000000, color='blue', linestyle='--', linewidth=2,
           label=f'Average: ${avg_potential/1000000:.2f}M', alpha=0.7)

ax.set_xlabel('Total Potential Value (Millions $)', fontsize=12, fontweight='bold')
ax.set_ylabel('Sales Rep', fontsize=12, fontweight='bold')
ax.set_title('Current Territory Balance - Total Potential by Rep\n' +
             f'Imbalance Ratio: {imbalance_ratio:.1f}x | Range: ${lowest_value/1000000:.2f}M - ${highest_value/1000000:.2f}M',
             fontsize=14, fontweight='bold', pad=20)

ax.legend(loc='lower right', fontsize=10)
ax.grid(axis='x', alpha=0.3, linestyle='--')

# Format x-axis to show dollar values
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.1f}M'))

plt.tight_layout()
plt.savefig('current_balance.png', dpi=300, bbox_inches='tight')
print(f"Chart saved as 'current_balance.png'")
print()

# Create workload utilization chart
fig2, ax2 = plt.subplots(figsize=(12, 6))

# Sort workload data by utilization for visualization
workload_sorted = workload_df.sort_values('utilization_pct', ascending=True)
reps_wl = workload_sorted['rep']
utilization_vals = workload_sorted['utilization_pct']

# Color code based on workload status
def get_utilization_color(util_pct):
    if util_pct < 70:
        return '#e74c3c'  # Red - Underutilized
    elif util_pct < 80:
        return '#f39c12'  # Orange - Light load
    elif util_pct <= 95:
        return '#27ae60'  # Green - Optimal
    elif util_pct <= 110:
        return '#f39c12'  # Orange - Stretched
    else:
        return '#e74c3c'  # Red - Overloaded

colors_wl = [get_utilization_color(u) for u in utilization_vals]

bars2 = ax2.barh(reps_wl, utilization_vals, color=colors_wl, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars2, utilization_vals)):
    width = bar.get_width()
    label_x = width + 2 if width < 100 else width - 2
    ha = 'left' if width < 100 else 'right'
    color = 'black' if width < 100 else 'white'

    ax2.text(label_x, bar.get_y() + bar.get_height()/2,
            f'{value:.1f}%',
            ha=ha, va='center', fontweight='bold', fontsize=10, color=color)

# Add target range shading
optimal_min = MIN_UTILIZATION_PCT * 100  # 80%
optimal_max = MAX_UTILIZATION_PCT * 100  # 95%
ax2.axvspan(optimal_min, optimal_max, alpha=0.15, color='green', label=f'Optimal Range ({optimal_min:.0f}-{optimal_max:.0f}%)')

# Add vertical lines for boundaries
ax2.axvline(optimal_min, color='green', linestyle='--', linewidth=2, alpha=0.5)
ax2.axvline(optimal_max, color='green', linestyle='--', linewidth=2, alpha=0.5)
ax2.axvline(100, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='100% Capacity')

# Add average line
avg_util = workload_df['utilization_pct'].mean()
ax2.axvline(avg_util, color='blue', linestyle='--', linewidth=2,
           label=f'Average: {avg_util:.1f}%', alpha=0.7)

ax2.set_xlabel('Utilization (% of Available Selling Time)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Sales Rep', fontsize=12, fontweight='bold')
ax2.set_title('Current Workload Utilization by Rep\n' +
             f'Range: {workload_df["utilization_pct"].min():.1f}% - {workload_df["utilization_pct"].max():.1f}% | ' +
             f'Reps in Optimal Range: {reps_in_optimal}/{len(workload_df)}',
             fontsize=14, fontweight='bold', pad=20)

ax2.legend(loc='lower right', fontsize=9)
ax2.grid(axis='x', alpha=0.3, linestyle='--')
ax2.set_xlim(0, max(120, utilization_vals.max() + 10))

plt.tight_layout()
plt.savefig('workload_utilization.png', dpi=300, bbox_inches='tight')
print(f"Chart saved as 'workload_utilization.png'")
print()

# Additional insights
print("=" * 60)
print("ADDITIONAL INSIGHTS:")
print("=" * 60)

# Show customer vs prospect split by rep
customer_split = df.groupby(['current_owner', 'customer_status']).size().unstack(fill_value=0)
print("\nCUSTOMER vs PROSPECT DISTRIBUTION:")
print(customer_split)
print()

# Show account size distribution
size_dist = df.groupby(['current_owner', 'account_size']).size().unstack(fill_value=0)
print("\nACCOUNT SIZE DISTRIBUTION:")
print(size_dist)
print()

print("=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
