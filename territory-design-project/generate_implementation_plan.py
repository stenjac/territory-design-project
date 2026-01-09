import pandas as pd
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MIN_UTILIZATION_PCT,
    MAX_UTILIZATION_PCT
)

"""
IMPLEMENTATION PLAN GENERATOR
Creates detailed reassignment lists and rep-by-rep summaries for territory changes
"""


def determine_reason(account, from_rep_metrics, to_rep_metrics):
    """
    Determine the reason for reassignment based on metrics.

    Parameters:
    -----------
    account : Series
        Account information
    from_rep_metrics : dict
        Metrics for the rep losing the account
    to_rep_metrics : dict
        Metrics for the rep gaining the account

    Returns:
    --------
    str : Reason for reassignment
    """
    from_util = from_rep_metrics.get('utilization_before', 0)
    to_util = to_rep_metrics.get('utilization_before', 0)

    # High-value prospect
    if account['estimated_annual_value'] >= 400000 and account['customer_status'] == 'Prospect':
        if to_util < 70:
            return f"High-value prospect to underutilized rep (was {to_util:.0f}% utilized)"
        else:
            return f"High-value prospect for balanced distribution"

    # Capacity balancing
    if from_util > 100:
        return f"Offload from over-capacity rep ({from_util:.0f}% → target 80-95%)"
    elif from_util > 95:
        return f"Prevent burnout (from {from_util:.0f}% utilization)"

    # Underutilization
    if to_util < 70:
        return f"Better utilize capacity (to rep at {to_util:.0f}%)"
    elif to_util < 80:
        return f"Fill capacity gap (to rep at {to_util:.0f}%)"

    # Revenue balancing
    from_potential = from_rep_metrics.get('potential_before', 0)
    to_potential = to_rep_metrics.get('potential_before', 0)

    if from_potential > to_potential * 2:
        return f"Balance territory potential (equalize revenue opportunity)"

    # Default
    return "Balance territories for fairness"


def generate_implementation_plan(original_df, rebalanced_df):
    """
    Generate detailed implementation plan with reassignment list and rep summaries.

    Parameters:
    -----------
    original_df : DataFrame
        Original accounts with current_owner
    rebalanced_df : DataFrame
        Rebalanced accounts with new_owner

    Returns:
    --------
    tuple : (reassignments_df, rep_summaries)
    """

    # Calculate before metrics for each rep
    before_metrics = {}
    for rep in original_df['current_owner'].unique():
        rep_accounts = original_df[original_df['current_owner'] == rep]
        total_potential = rep_accounts['estimated_annual_value'].sum()
        total_hours = sum(calculate_account_hours(row['account_size'], row['customer_status'])
                         for _, row in rep_accounts.iterrows())
        utilization = (total_hours / AVAILABLE_SELLING_HOURS) * 100

        before_metrics[rep] = {
            'potential_before': total_potential,
            'utilization_before': utilization,
            'accounts_before': len(rep_accounts)
        }

    # Calculate after metrics for each rep
    after_metrics = {}
    for rep in rebalanced_df['new_owner'].unique():
        rep_accounts = rebalanced_df[rebalanced_df['new_owner'] == rep]
        total_potential = rep_accounts['estimated_annual_value'].sum()
        total_hours = sum(calculate_account_hours(row['account_size'], row['customer_status'])
                         for _, row in rep_accounts.iterrows())
        utilization = (total_hours / AVAILABLE_SELLING_HOURS) * 100

        after_metrics[rep] = {
            'potential_after': total_potential,
            'utilization_after': utilization,
            'accounts_after': len(rep_accounts)
        }

    # Find all movements
    movements = rebalanced_df[rebalanced_df['current_owner'] != rebalanced_df['new_owner']].copy()

    # Create reassignment list
    reassignments = []
    for _, account in movements.iterrows():
        from_rep = account['current_owner']
        to_rep = account['new_owner']

        reason = determine_reason(
            account,
            before_metrics.get(from_rep, {}),
            before_metrics.get(to_rep, {})
        )

        reassignments.append({
            'account_name': account['account_name'],
            'from_rep': from_rep,
            'to_rep': to_rep,
            'account_size': account['account_size'],
            'customer_status': account['customer_status'],
            'account_value': account['estimated_annual_value'],
            'reason': reason
        })

    reassignments_df = pd.DataFrame(reassignments)

    # Sort by value (highest first) for better visibility
    reassignments_df = reassignments_df.sort_values('account_value', ascending=False)

    # Generate rep summaries
    all_reps = set(original_df['current_owner'].unique()) | set(rebalanced_df['new_owner'].unique())

    rep_summaries = []
    for rep in sorted(all_reps):
        # Accounts gained
        gained = reassignments_df[reassignments_df['to_rep'] == rep]

        # Accounts lost
        lost = reassignments_df[reassignments_df['from_rep'] == rep]

        # Calculate totals
        before_potential = before_metrics.get(rep, {}).get('potential_before', 0)
        after_potential = after_metrics.get(rep, {}).get('potential_after', 0)
        before_util = before_metrics.get(rep, {}).get('utilization_before', 0)
        after_util = after_metrics.get(rep, {}).get('utilization_after', 0)
        before_accounts = before_metrics.get(rep, {}).get('accounts_before', 0)
        after_accounts = after_metrics.get(rep, {}).get('accounts_after', 0)

        rep_summaries.append({
            'rep': rep,
            'accounts_gained': len(gained),
            'accounts_gained_names': ', '.join(gained['account_name'].tolist()) if len(gained) > 0 else 'None',
            'value_gained': gained['account_value'].sum(),
            'accounts_lost': len(lost),
            'accounts_lost_names': ', '.join(lost['account_name'].tolist()[:3]) if len(lost) > 0 else 'None',
            'accounts_lost_etc': f" + {len(lost) - 3} more" if len(lost) > 3 else "",
            'value_lost': lost['account_value'].sum(),
            'net_accounts': len(gained) - len(lost),
            'net_value': gained['account_value'].sum() - lost['account_value'].sum(),
            'before_potential': before_potential,
            'after_potential': after_potential,
            'before_utilization': before_util,
            'after_utilization': after_util,
            'before_accounts': before_accounts,
            'after_accounts': after_accounts
        })

    rep_summaries_df = pd.DataFrame(rep_summaries)

    return reassignments_df, rep_summaries_df


def print_implementation_plan(reassignments_df, rep_summaries_df):
    """Print detailed implementation plan"""

    print("=" * 100)
    print("TERRITORY IMPLEMENTATION PLAN")
    print("=" * 100)
    print()

    # Print reassignment list
    print("ACCOUNT REASSIGNMENTS")
    print("-" * 100)
    print(f"Total accounts to be reassigned: {len(reassignments_df)}")
    print()

    # Group by customer status
    customers_moved = reassignments_df[reassignments_df['customer_status'] == 'Customer']
    prospects_moved = reassignments_df[reassignments_df['customer_status'] == 'Prospect']

    print(f"Breakdown:")
    print(f"  • Customers: {len(customers_moved)} (${customers_moved['account_value'].sum():,.0f})")
    print(f"  • Prospects: {len(prospects_moved)} (${prospects_moved['account_value'].sum():,.0f})")
    print()

    # Show top 20 highest-value reassignments
    print("TOP 20 HIGHEST-VALUE REASSIGNMENTS:")
    print("-" * 100)
    print(f"{'Account':<30} {'From':<10} {'To':<10} {'Type':<12} {'Value':>12} {'Reason':<50}")
    print("-" * 100)

    for idx, row in reassignments_df.head(20).iterrows():
        account_display = row['account_name'][:28] + '..' if len(row['account_name']) > 30 else row['account_name']
        reason_display = row['reason'][:48] + '..' if len(row['reason']) > 50 else row['reason']

        print(f"{account_display:<30} {row['from_rep']:<10} {row['to_rep']:<10} "
              f"{row['customer_status']:<12} ${row['account_value']:>11,} {reason_display:<50}")

    if len(reassignments_df) > 20:
        print(f"\n... and {len(reassignments_df) - 20} more reassignments")
    print()

    # Print summary by rep
    print("=" * 100)
    print("SUMMARY BY REP")
    print("=" * 100)
    print()

    for _, rep_data in rep_summaries_df.iterrows():
        rep = rep_data['rep']

        print(f"{rep}:")
        print("-" * 100)

        # Accounts gained
        if rep_data['accounts_gained'] > 0:
            print(f"  Accounts gaining: {rep_data['accounts_gained']}")
            gained_list = rep_data['accounts_gained_names']
            if len(gained_list) > 80:
                gained_list = gained_list[:77] + "..."
            print(f"    • {gained_list}")
            print(f"    • Total value gaining: ${rep_data['value_gained']:,.0f}")
        else:
            print(f"  Accounts gaining: 0")

        print()

        # Accounts lost
        if rep_data['accounts_lost'] > 0:
            print(f"  Accounts losing: {rep_data['accounts_lost']}")
            lost_list = rep_data['accounts_lost_names'] + rep_data['accounts_lost_etc']
            if len(lost_list) > 80:
                lost_list = lost_list[:77] + "..."
            print(f"    • {lost_list}")
            print(f"    • Total value losing: ${rep_data['value_lost']:,.0f}")
        else:
            print(f"  Accounts losing: 0")

        print()

        # Net change
        net_symbol = "+" if rep_data['net_value'] >= 0 else ""
        print(f"  Net change: {net_symbol}{rep_data['net_accounts']} accounts, {net_symbol}${rep_data['net_value']:,.0f}")
        print()

        # Before/After summary
        potential_change = rep_data['after_potential'] - rep_data['before_potential']
        potential_symbol = "+" if potential_change >= 0 else ""

        print(f"  Territory potential:")
        print(f"    • Before: ${rep_data['before_potential']:,.0f} ({rep_data['before_accounts']} accounts)")
        print(f"    • After:  ${rep_data['after_potential']:,.0f} ({rep_data['after_accounts']} accounts)")
        print(f"    • Change: {potential_symbol}${potential_change:,.0f}")

        print()

        util_change = rep_data['after_utilization'] - rep_data['before_utilization']
        util_symbol = "+" if util_change >= 0 else ""

        # Determine status
        after_util = rep_data['after_utilization']
        if after_util < MIN_UTILIZATION_PCT * 100:
            status = "Under-utilized"
        elif after_util <= MAX_UTILIZATION_PCT * 100:
            status = "Optimal ✓"
        elif after_util <= 110:
            status = "Stretched"
        else:
            status = "Over-capacity"

        print(f"  Workload utilization:")
        print(f"    • Before: {rep_data['before_utilization']:.1f}%")
        print(f"    • After:  {rep_data['after_utilization']:.1f}% ({status})")
        print(f"    • Change: {util_symbol}{util_change:.1f} percentage points")

        print()
        print()

    print("=" * 100)
    print("IMPLEMENTATION NOTES")
    print("=" * 100)
    print()
    print("IMPORTANT:")
    print("  • All customer relationships are PRESERVED (customers stay with current reps)")
    print("  • Only prospect assignments are changed to balance territories")
    print("  • Changes are designed to achieve 80-95% optimal utilization range")
    print("  • Target is to get CV (Coefficient of Variation) under 25% for good balance")
    print()
    print("NEXT STEPS:")
    print("  1. Review reassignment list and rep summaries above")
    print("  2. Verify no critical customer relationships are disrupted")
    print("  3. Communicate changes to affected reps")
    print("  4. Update CRM system with new account assignments")
    print("  5. Schedule transition meetings for reassigned prospects")
    print()


# Main execution
if __name__ == "__main__":
    # Load data
    original_df = pd.read_csv('accounts.csv')
    rebalanced_df = pd.read_csv('accounts_rebalanced.csv')

    print("Generating implementation plan...")
    print()

    # Generate plan
    reassignments_df, rep_summaries_df = generate_implementation_plan(original_df, rebalanced_df)

    # Print detailed plan
    print_implementation_plan(reassignments_df, rep_summaries_df)

    # Export to CSV
    print("=" * 100)
    print("EXPORTING FILES")
    print("=" * 100)

    # Export reassignments
    reassignments_export = reassignments_df.copy()
    reassignments_export['account_value_formatted'] = reassignments_export['account_value'].apply(lambda x: f"${x:,.0f}")
    reassignments_export = reassignments_export[['account_name', 'from_rep', 'to_rep', 'account_size',
                                                   'customer_status', 'account_value_formatted', 'reason']]
    reassignments_export.columns = ['Account Name', 'From Rep', 'To Rep', 'Account Size',
                                      'Customer Status', 'Account Value', 'Reason']

    reassignments_export.to_csv('implementation_plan.csv', index=False)
    print(f"✓ Reassignment list saved to 'implementation_plan.csv' ({len(reassignments_df)} reassignments)")

    # Export rep summaries
    rep_summaries_export = rep_summaries_df.copy()
    rep_summaries_export['before_potential_fmt'] = rep_summaries_export['before_potential'].apply(lambda x: f"${x:,.0f}")
    rep_summaries_export['after_potential_fmt'] = rep_summaries_export['after_potential'].apply(lambda x: f"${x:,.0f}")
    rep_summaries_export['net_value_fmt'] = rep_summaries_export['net_value'].apply(lambda x: f"${x:+,.0f}")
    rep_summaries_export['before_util_fmt'] = rep_summaries_export['before_utilization'].apply(lambda x: f"{x:.1f}%")
    rep_summaries_export['after_util_fmt'] = rep_summaries_export['after_utilization'].apply(lambda x: f"{x:.1f}%")

    rep_summaries_export = rep_summaries_export[['rep', 'accounts_gained', 'value_gained', 'accounts_lost',
                                                   'value_lost', 'net_accounts', 'net_value_fmt',
                                                   'before_potential_fmt', 'after_potential_fmt',
                                                   'before_util_fmt', 'after_util_fmt']]

    rep_summaries_export.columns = ['Rep', 'Accounts Gained', 'Value Gained', 'Accounts Lost',
                                      'Value Lost', 'Net Accounts', 'Net Value Change',
                                      'Before Potential', 'After Potential', 'Before Utilization', 'After Utilization']

    rep_summaries_export.to_csv('rep_summaries.csv', index=False)
    print(f"✓ Rep summaries saved to 'rep_summaries.csv' ({len(rep_summaries_df)} reps)")
    print()

    print("=" * 100)
    print("IMPLEMENTATION PLAN COMPLETE")
    print("=" * 100)
    print()
    print("Files generated:")
    print("  • implementation_plan.csv - Detailed reassignment list")
    print("  • rep_summaries.csv - Summary by rep")
    print()
