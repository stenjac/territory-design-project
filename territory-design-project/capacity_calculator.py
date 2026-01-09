import pandas as pd

"""
CAPACITY CALCULATOR
Estimates time requirements for managing sales accounts based on size and status.

TIME PER ACCOUNT (per quarter):
- Enterprise accounts: 15 hours
  * Quarterly business reviews, strategy sessions, multiple touchpoints
- Large accounts: 8 hours
  * Regular check-ins, some strategic work
- Medium accounts: 4 hours
  * Monthly touchpoints, basic relationship management
- Small accounts: 2 hours
  * Quarterly check-in, mostly email communication

MULTIPLIERS:
- Customer status: 1.3x (requires upsell/renewal work, account management)
- Prospect status: 1.0x (standard prospecting effort)

REP CAPACITY (per quarter):
- Starting hours: 40 hours/week × 13 weeks = 520 hours
- Subtract non-selling time:
  * Meetings/admin: 25% (130 hours)
  * Internal work: 15% (78 hours)
  * PTO/holidays: 10% (52 hours)
  * Deal paperwork: 10% (52 hours)
- Available selling time: 208 hours per quarter
- Target utilization: 80-95% (166-198 hours used)
  * 80% (166 hours) = minimum for efficiency
  * 95% (198 hours) = maximum before burnout
"""

# Base hours per account size (per quarter)
BASE_HOURS = {
    'Enterprise': 15,
    'Large': 8,
    'Medium': 4,
    'Small': 2
}

# Status multipliers
STATUS_MULTIPLIERS = {
    'Customer': 1.3,  # Existing customers need upsell/renewal work
    'Prospect': 1.0   # Prospects require standard effort
}

# Rep capacity constants
TOTAL_HOURS_PER_QUARTER = 520  # 40 hours/week × 13 weeks
NON_SELLING_TIME = {
    'Meetings/Admin': 0.25,      # 25% = 130 hours
    'Internal Work': 0.15,       # 15% = 78 hours
    'PTO/Holidays': 0.10,        # 10% = 52 hours
    'Deal Paperwork': 0.10       # 10% = 52 hours
}
TOTAL_NON_SELLING_PCT = sum(NON_SELLING_TIME.values())  # 60%
AVAILABLE_SELLING_HOURS = TOTAL_HOURS_PER_QUARTER * (1 - TOTAL_NON_SELLING_PCT)  # 208 hours

# Target utilization range
MIN_UTILIZATION_PCT = 0.80  # 80% of available selling time (166 hours)
MAX_UTILIZATION_PCT = 0.95  # 95% of available selling time (198 hours)
MIN_TARGET_HOURS = AVAILABLE_SELLING_HOURS * MIN_UTILIZATION_PCT  # 166 hours
MAX_TARGET_HOURS = AVAILABLE_SELLING_HOURS * MAX_UTILIZATION_PCT  # 198 hours


def rep_capacity():
    """
    Returns the available selling hours per rep per quarter.

    Returns:
    --------
    float
        Available selling hours per quarter (208 hours)
    """
    return AVAILABLE_SELLING_HOURS

def calculate_account_hours(account_size, customer_status):
    """
    Calculate quarterly hours required for a single account.

    Parameters:
    -----------
    account_size : str
        Size of the account ('Enterprise', 'Large', 'Medium', 'Small')
    customer_status : str
        Status of the account ('Customer' or 'Prospect')

    Returns:
    --------
    float
        Estimated hours per quarter for this account
    """
    base_hours = BASE_HOURS[account_size]
    multiplier = STATUS_MULTIPLIERS[customer_status]
    return base_hours * multiplier


def calculate_rep_capacity(df, rep_name):
    """
    Calculate total quarterly hours required for a specific rep's territory.

    Parameters:
    -----------
    df : DataFrame
        Accounts dataframe with columns: account_size, customer_status, current_owner
    rep_name : str
        Name of the rep to calculate capacity for

    Returns:
    --------
    dict
        Dictionary containing capacity metrics for the rep
    """
    rep_accounts = df[df['current_owner'] == rep_name].copy()

    # Calculate hours for each account
    rep_accounts['quarterly_hours'] = rep_accounts.apply(
        lambda row: calculate_account_hours(row['account_size'], row['customer_status']),
        axis=1
    )

    total_hours = rep_accounts['quarterly_hours'].sum()
    num_accounts = len(rep_accounts)
    avg_hours_per_account = total_hours / num_accounts if num_accounts > 0 else 0

    # Break down by account size
    hours_by_size = rep_accounts.groupby('account_size')['quarterly_hours'].sum().to_dict()

    # Break down by customer status
    hours_by_status = rep_accounts.groupby('customer_status')['quarterly_hours'].sum().to_dict()

    return {
        'rep_name': rep_name,
        'total_quarterly_hours': total_hours,
        'num_accounts': num_accounts,
        'avg_hours_per_account': avg_hours_per_account,
        'hours_by_size': hours_by_size,
        'hours_by_status': hours_by_status,
        'accounts_detail': rep_accounts
    }


def analyze_team_capacity(df, available_hours_per_quarter=None):
    """
    Analyze capacity requirements for entire sales team.

    Parameters:
    -----------
    df : DataFrame
        Accounts dataframe
    available_hours_per_quarter : float, optional
        Available selling hours per rep per quarter (default: uses AVAILABLE_SELLING_HOURS = 208)

    Returns:
    --------
    DataFrame
        Summary of capacity metrics by rep
    """
    if available_hours_per_quarter is None:
        available_hours_per_quarter = AVAILABLE_SELLING_HOURS

    reps = df['current_owner'].unique()

    capacity_data = []

    for rep in reps:
        metrics = calculate_rep_capacity(df, rep)

        # Calculate capacity utilization (as % of available selling time)
        utilization_pct = (metrics['total_quarterly_hours'] / available_hours_per_quarter) * 100

        # Determine capacity status based on target utilization (80-95%)
        if utilization_pct < MIN_UTILIZATION_PCT * 100:  # < 80%
            capacity_status = 'Under-utilized'
        elif utilization_pct <= MAX_UTILIZATION_PCT * 100:  # 80-95%
            capacity_status = 'Optimal'
        elif utilization_pct <= 110:  # 95-110%
            capacity_status = 'Over-capacity'
        else:  # > 110%
            capacity_status = 'Severely over-capacity'

        capacity_data.append({
            'rep': rep,
            'num_accounts': metrics['num_accounts'],
            'total_hours': metrics['total_quarterly_hours'],
            'available_hours': available_hours_per_quarter,
            'utilization_pct': utilization_pct,
            'capacity_status': capacity_status,
            'hours_over_under': metrics['total_quarterly_hours'] - available_hours_per_quarter,
            'target_min_hours': MIN_TARGET_HOURS,
            'target_max_hours': MAX_TARGET_HOURS
        })

    capacity_df = pd.DataFrame(capacity_data)
    capacity_df = capacity_df.sort_values('utilization_pct', ascending=False)

    return capacity_df


def print_capacity_report(df, available_hours=None):
    """
    Print a detailed capacity analysis report.

    Parameters:
    -----------
    df : DataFrame
        Accounts dataframe
    available_hours : float, optional
        Available selling hours per rep per quarter (default: uses AVAILABLE_SELLING_HOURS = 208)
    """
    if available_hours is None:
        available_hours = AVAILABLE_SELLING_HOURS

    print("=" * 70)
    print("SALES CAPACITY ANALYSIS")
    print("=" * 70)
    print()
    print("REP CAPACITY MODEL (per quarter):")
    print("-" * 70)
    print(f"Total hours per quarter: {TOTAL_HOURS_PER_QUARTER} hrs (40 hrs/week × 13 weeks)")
    print()
    print("Non-selling time deductions:")
    for category, pct in NON_SELLING_TIME.items():
        hours = TOTAL_HOURS_PER_QUARTER * pct
        print(f"  • {category}: {pct*100:.0f}% ({hours:.0f} hrs)")
    print(f"  • TOTAL NON-SELLING: {TOTAL_NON_SELLING_PCT*100:.0f}% ({TOTAL_HOURS_PER_QUARTER * TOTAL_NON_SELLING_PCT:.0f} hrs)")
    print()
    print(f"Available selling time: {available_hours:.0f} hours per quarter")
    print()
    print("TARGET UTILIZATION:")
    print(f"  • Minimum (80%): {MIN_TARGET_HOURS:.0f} hours - Below this = under-utilized")
    print(f"  • Optimal (80-95%): {MIN_TARGET_HOURS:.0f}-{MAX_TARGET_HOURS:.0f} hours - Ideal range")
    print(f"  • Maximum (95%): {MAX_TARGET_HOURS:.0f} hours - Above this = over-capacity")
    print()

    capacity_df = analyze_team_capacity(df, available_hours)

    print("CAPACITY BY REP:")
    print("-" * 70)
    for _, row in capacity_df.iterrows():
        print(f"{row['rep']}:")
        print(f"  • Accounts: {row['num_accounts']}")
        print(f"  • Required hours: {row['total_hours']:.1f} hrs/quarter")
        print(f"  • Utilization: {row['utilization_pct']:.1f}% of available selling time")
        print(f"  • Status: {row['capacity_status']}")

        # Show distance from target range
        if row['total_hours'] < row['target_min_hours']:
            gap = row['target_min_hours'] - row['total_hours']
            print(f"  • Below optimal range by: {gap:.1f} hours (need {row['target_min_hours']:.0f}-{row['target_max_hours']:.0f} hrs)")
        elif row['total_hours'] > row['target_max_hours']:
            gap = row['total_hours'] - row['target_max_hours']
            print(f"  • Above optimal range by: {gap:.1f} hours (target: {row['target_min_hours']:.0f}-{row['target_max_hours']:.0f} hrs)")
        else:
            print(f"  • Within optimal range: {row['target_min_hours']:.0f}-{row['target_max_hours']:.0f} hrs ✓")
        print()

    print("=" * 70)
    print("TEAM SUMMARY:")
    print("-" * 70)
    print(f"Average utilization: {capacity_df['utilization_pct'].mean():.1f}%")
    print(f"Highest utilization: {capacity_df['utilization_pct'].max():.1f}% ({capacity_df.iloc[0]['rep']})")
    print(f"Lowest utilization: {capacity_df['utilization_pct'].min():.1f}% ({capacity_df.iloc[-1]['rep']})")
    print(f"Utilization range: {capacity_df['utilization_pct'].max() - capacity_df['utilization_pct'].min():.1f} percentage points")
    print()

    # Count reps by status
    status_counts = capacity_df['capacity_status'].value_counts()
    print("CAPACITY STATUS BREAKDOWN:")
    for status, count in status_counts.items():
        print(f"  • {status}: {count} reps")
    print()

    return capacity_df


# Main execution
if __name__ == "__main__":
    # Load accounts data
    df = pd.read_csv('accounts.csv')

    # Run capacity analysis
    capacity_df = print_capacity_report(df)

    # Additional detailed breakdown for a sample rep
    print("=" * 70)
    print("DETAILED EXAMPLE: Rep_1 Breakdown")
    print("-" * 70)

    rep1_metrics = calculate_rep_capacity(df, 'Rep_1')

    print(f"Total accounts: {rep1_metrics['num_accounts']}")
    print(f"Total quarterly hours: {rep1_metrics['total_quarterly_hours']:.1f}")
    print()

    print("Hours by Account Size:")
    for size, hours in sorted(rep1_metrics['hours_by_size'].items()):
        pct = (hours / rep1_metrics['total_quarterly_hours']) * 100
        print(f"  • {size}: {hours:.1f} hrs ({pct:.1f}%)")
    print()

    print("Hours by Customer Status:")
    for status, hours in sorted(rep1_metrics['hours_by_status'].items()):
        pct = (hours / rep1_metrics['total_quarterly_hours']) * 100
        print(f"  • {status}: {hours:.1f} hrs ({pct:.1f}%)")
    print()

    print("=" * 70)
    print("TIME MODEL REFERENCE:")
    print("-" * 70)
    print("Base Hours per Account (per quarter):")
    for size, hours in BASE_HOURS.items():
        print(f"  • {size}: {hours} hours")
    print()
    print("Customer Status Multipliers:")
    for status, mult in STATUS_MULTIPLIERS.items():
        print(f"  • {status}: {mult}x")
    print()
    print("Examples:")
    print(f"  • Enterprise Customer: 15 × 1.3 = {calculate_account_hours('Enterprise', 'Customer'):.1f} hrs")
    print(f"  • Enterprise Prospect: 15 × 1.0 = {calculate_account_hours('Enterprise', 'Prospect'):.1f} hrs")
    print(f"  • Small Customer: 2 × 1.3 = {calculate_account_hours('Small', 'Customer'):.1f} hrs")
    print(f"  • Small Prospect: 2 × 1.0 = {calculate_account_hours('Small', 'Prospect'):.1f} hrs")
    print("=" * 70)
