import pandas as pd
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MIN_TARGET_HOURS,
    MAX_TARGET_HOURS,
    MIN_UTILIZATION_PCT,
    MAX_UTILIZATION_PCT
)

"""
SIMPLE REBALANCING ALGORITHM

RULES:
1. Keep existing customers with their current rep (Don't disrupt relationships)
2. Redistribute prospects to balance potential and workload

ALGORITHM:
1. Lock all Customer accounts to current owners
2. Get list of all Prospect accounts
3. Sort reps by current total potential (lowest first)
4. Sort prospects by value (highest first)
5. Assign highest-value prospects to lowest-potential reps
6. Repeat until balanced or capacity reached

CONSTRAINTS:
- Don't exceed 95% capacity for any rep (MAX_TARGET_HOURS)
- Try to get all reps between 80-95% utilization
- Try to get potential within 25% of each other
"""


def calculate_rep_metrics(accounts_df, rep_name, new_owner_col='new_owner'):
    """
    Calculate current metrics for a rep based on their assigned accounts.

    Parameters:
    -----------
    accounts_df : DataFrame
        Full accounts dataframe with assignments
    rep_name : str
        Name of the rep
    new_owner_col : str
        Column name for new assignments (default: 'new_owner')

    Returns:
    --------
    dict : Metrics including total potential, hours needed, utilization
    """
    rep_accounts = accounts_df[accounts_df[new_owner_col] == rep_name]

    total_potential = rep_accounts['estimated_annual_value'].sum()

    total_hours = 0
    for _, account in rep_accounts.iterrows():
        hours = calculate_account_hours(account['account_size'], account['customer_status'])
        total_hours += hours

    utilization_pct = (total_hours / AVAILABLE_SELLING_HOURS) * 100
    num_accounts = len(rep_accounts)

    return {
        'rep': rep_name,
        'total_potential': total_potential,
        'total_hours': total_hours,
        'utilization_pct': utilization_pct,
        'num_accounts': num_accounts,
        'available_hours': AVAILABLE_SELLING_HOURS - total_hours
    }


def simple_rebalance(accounts_df):
    """
    Rebalance territories by keeping customers locked and redistributing prospects.

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts dataframe with columns: account_name, account_size, current_owner,
        estimated_annual_value, customer_status

    Returns:
    --------
    DataFrame : Updated accounts dataframe with 'new_owner' column
    """
    # Create a copy to work with
    df = accounts_df.copy()

    # Initialize new_owner with current_owner
    df['new_owner'] = df['current_owner']

    # Get list of unique reps
    reps = df['current_owner'].unique().tolist()

    print("=" * 70)
    print("TERRITORY REBALANCING - SIMPLE ALGORITHM")
    print("=" * 70)
    print()

    # Step 1: Lock all Customer accounts
    customers = df[df['customer_status'] == 'Customer'].copy()
    prospects = df[df['customer_status'] == 'Prospect'].copy()

    print(f"Step 1: Locking Customer accounts to current reps")
    print(f"  • Total Customers: {len(customers)}")
    print(f"  • Total Prospects: {len(prospects)}")
    print()

    # Step 2: Calculate current potential per rep (locked customers only)
    print("Step 2: Calculating baseline (customers only)...")
    print("-" * 70)

    rep_metrics = {}
    for rep in reps:
        # Temporarily set prospects to unassigned to calculate baseline
        df.loc[df['customer_status'] == 'Prospect', 'new_owner'] = None
        metrics = calculate_rep_metrics(df, rep)
        rep_metrics[rep] = metrics
        print(f"{rep}: ${metrics['total_potential']:,.0f} potential, "
              f"{metrics['total_hours']:.1f} hrs, {metrics['utilization_pct']:.1f}% utilization")
    print()

    # Step 3: Sort prospects by value (highest first)
    prospects_sorted = prospects.sort_values('estimated_annual_value', ascending=False).copy()
    print(f"Step 3: Sorting {len(prospects_sorted)} prospects by value (highest first)...")
    print(f"  • Highest value prospect: ${prospects_sorted.iloc[0]['estimated_annual_value']:,.0f}")
    print(f"  • Lowest value prospect: ${prospects_sorted.iloc[-1]['estimated_annual_value']:,.0f}")
    print()

    # Step 4: Assign prospects to balance potential and capacity
    print("Step 4: Assigning prospects to reps...")
    print("-" * 70)

    assignments_made = 0
    skipped_capacity = 0

    for idx, prospect in prospects_sorted.iterrows():
        prospect_value = prospect['estimated_annual_value']
        prospect_hours = calculate_account_hours(prospect['account_size'], prospect['customer_status'])

        # Sort reps by current total potential (lowest first)
        # This ensures we assign high-value prospects to low-potential reps
        reps_by_potential = sorted(reps, key=lambda r: rep_metrics[r]['total_potential'])

        # Find best rep: lowest potential who has capacity
        assigned = False
        for rep in reps_by_potential:
            current_hours = rep_metrics[rep]['total_hours']
            new_hours = current_hours + prospect_hours
            new_utilization = (new_hours / AVAILABLE_SELLING_HOURS) * 100

            # Check capacity constraint (don't exceed 95%)
            if new_utilization <= MAX_UTILIZATION_PCT * 100:
                # Assign prospect to this rep
                df.loc[idx, 'new_owner'] = rep

                # Update rep metrics
                rep_metrics[rep]['total_potential'] += prospect_value
                rep_metrics[rep]['total_hours'] = new_hours
                rep_metrics[rep]['utilization_pct'] = new_utilization
                rep_metrics[rep]['num_accounts'] += 1
                rep_metrics[rep]['available_hours'] = AVAILABLE_SELLING_HOURS - new_hours

                assignments_made += 1
                assigned = True
                break

        if not assigned:
            # All reps are at capacity, keep with current owner
            skipped_capacity += 1

    print(f"Assignments completed:")
    print(f"  • Prospects reassigned: {assignments_made}")
    print(f"  • Prospects kept (capacity limit): {skipped_capacity}")
    print()

    return df, rep_metrics


def print_rebalancing_results(original_df, rebalanced_df, rep_metrics):
    """
    Print detailed results comparing before and after rebalancing.

    Parameters:
    -----------
    original_df : DataFrame
        Original accounts dataframe
    rebalanced_df : DataFrame
        Rebalanced accounts dataframe with new_owner column
    rep_metrics : dict
        Dictionary of rep metrics after rebalancing
    """
    print("=" * 70)
    print("REBALANCING RESULTS")
    print("=" * 70)
    print()

    # Calculate original metrics for comparison
    print("BEFORE vs AFTER COMPARISON:")
    print("-" * 70)

    reps = sorted(rep_metrics.keys())

    original_metrics = []
    new_metrics = []

    for rep in reps:
        # Original
        orig_accounts = original_df[original_df['current_owner'] == rep]
        orig_potential = orig_accounts['estimated_annual_value'].sum()
        orig_hours = sum(calculate_account_hours(row['account_size'], row['customer_status'])
                        for _, row in orig_accounts.iterrows())
        orig_util = (orig_hours / AVAILABLE_SELLING_HOURS) * 100

        original_metrics.append({
            'rep': rep,
            'potential': orig_potential,
            'hours': orig_hours,
            'utilization': orig_util,
            'accounts': len(orig_accounts)
        })

        # New
        new_metrics.append(rep_metrics[rep])

    # Print comparison table
    print(f"{'Rep':<10} {'Before':>15} {'After':>15} {'Change':>15} {'Status':<12}")
    print("-" * 70)

    for orig, new in zip(original_metrics, new_metrics):
        rep = orig['rep']
        potential_change = new['total_potential'] - orig['potential']
        change_pct = (potential_change / orig['potential'] * 100) if orig['potential'] > 0 else 0

        # Determine status
        if abs(change_pct) < 5:
            status = "Minimal change"
        elif change_pct > 0:
            status = "↑ Increased"
        else:
            status = "↓ Decreased"

        print(f"{rep:<10} ${orig['potential']/1e6:>6.2f}M → ${new['total_potential']/1e6:>6.2f}M "
              f"{change_pct:>+6.1f}% {status:<12}")

    print()

    # Calculate balance improvements
    orig_potentials = [m['potential'] for m in original_metrics]
    new_potentials = [m['total_potential'] for m in new_metrics]

    orig_std = pd.Series(orig_potentials).std()
    new_std = pd.Series(new_potentials).std()

    orig_mean = pd.Series(orig_potentials).mean()
    new_mean = pd.Series(new_potentials).mean()

    orig_cv = (orig_std / orig_mean) * 100
    new_cv = (new_std / new_mean) * 100

    print("BALANCE IMPROVEMENTS:")
    print("-" * 70)
    print(f"Coefficient of Variation (CV):")
    print(f"  • Before: {orig_cv:.1f}%")
    print(f"  • After:  {new_cv:.1f}%")
    print(f"  • Improvement: {orig_cv - new_cv:+.1f} percentage points")
    print()

    # Utilization improvements
    orig_utils = [m['utilization'] for m in original_metrics]
    new_utils = [m['utilization_pct'] for m in new_metrics]

    orig_in_range = sum(1 for u in orig_utils if MIN_UTILIZATION_PCT * 100 <= u <= MAX_UTILIZATION_PCT * 100)
    new_in_range = sum(1 for u in new_utils if MIN_UTILIZATION_PCT * 100 <= u <= MAX_UTILIZATION_PCT * 100)

    print(f"Reps in Optimal Utilization Range (80-95%):")
    print(f"  • Before: {orig_in_range}/{len(reps)}")
    print(f"  • After:  {new_in_range}/{len(reps)}")
    print(f"  • Improvement: {new_in_range - orig_in_range:+d} reps")
    print()

    # Account movements
    movements = rebalanced_df[rebalanced_df['current_owner'] != rebalanced_df['new_owner']]
    print(f"ACCOUNT MOVEMENTS:")
    print(f"  • Total accounts moved: {len(movements)}")
    print(f"  • Customers moved: {len(movements[movements['customer_status'] == 'Customer'])}")
    print(f"  • Prospects moved: {len(movements[movements['customer_status'] == 'Prospect'])}")
    print()

    # Show detailed movements if any
    if len(movements) > 0:
        print("DETAILED ACCOUNT MOVEMENTS:")
        print("-" * 70)
        movements_by_rep = movements.groupby(['current_owner', 'new_owner']).agg({
            'account_name': 'count',
            'estimated_annual_value': 'sum'
        }).reset_index()
        movements_by_rep.columns = ['From', 'To', 'Count', 'Total Value']

        for _, row in movements_by_rep.iterrows():
            print(f"{row['From']} → {row['To']}: {row['Count']} accounts, ${row['Total Value']:,.0f}")
        print()

    return {
        'orig_cv': orig_cv,
        'new_cv': new_cv,
        'cv_improvement': orig_cv - new_cv,
        'orig_in_range': orig_in_range,
        'new_in_range': new_in_range,
        'accounts_moved': len(movements)
    }


# Main execution
if __name__ == "__main__":
    # Load accounts
    df = pd.read_csv('accounts.csv')

    print("STARTING TERRITORY REBALANCING")
    print("=" * 70)
    print()
    print("Initial State:")
    print(f"  • Total accounts: {len(df)}")
    print(f"  • Total potential: ${df['estimated_annual_value'].sum():,.0f}")
    print(f"  • Customers: {len(df[df['customer_status'] == 'Customer'])}")
    print(f"  • Prospects: {len(df[df['customer_status'] == 'Prospect'])}")
    print(f"  • Number of reps: {df['current_owner'].nunique()}")
    print()

    # Run rebalancing
    rebalanced_df, rep_metrics = simple_rebalance(df)

    # Print results
    improvements = print_rebalancing_results(df, rebalanced_df, rep_metrics)

    # Save rebalanced assignments
    output_file = 'accounts_rebalanced.csv'
    rebalanced_df.to_csv(output_file, index=False)
    print(f"Rebalanced assignments saved to '{output_file}'")
    print()

    # Final summary
    print("=" * 70)
    print("REBALANCING SUMMARY")
    print("=" * 70)
    print(f"✓ CV improved from {improvements['orig_cv']:.1f}% to {improvements['new_cv']:.1f}%")
    print(f"✓ {improvements['new_in_range']}/{len(rep_metrics)} reps now in optimal utilization range")
    print(f"✓ {improvements['accounts_moved']} prospects redistributed (0 customers moved)")
    print()

    if improvements['new_cv'] < 25:
        print("🎯 Target achieved: CV < 25% (Good balance)")
    elif improvements['new_cv'] < 30:
        print("✓ Near target: CV < 30% (Approaching good balance)")
    else:
        print("⚠ Further optimization may be needed to reach CV < 25%")
    print()
