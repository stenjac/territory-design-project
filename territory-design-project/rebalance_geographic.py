"""
Geographic Territory Rebalancing

This script rebalances territories using geographic clustering as the primary
constraint, following mid-market best practices:

1. Define geographic regions (Northeast, South, Midwest, West, Mountain)
2. Assign reps to regions to balance workload
3. Within regions, minimize travel distance
4. Protect strategic customer relationships
5. Balance revenue and capacity

Algorithm: Region-based clustering with capacity balancing
"""

import pandas as pd
import numpy as np
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MAX_UTILIZATION_PCT
)
from geographic_clustering import (
    calculate_territory_center,
    haversine_distance,
    analyze_geographic_balance,
    calculate_total_territory_travel,
    print_geographic_summary
)


def calculate_rep_metrics_geo(accounts_df, rep_name, new_owner_col='new_owner'):
    """
    Calculate metrics for a rep including geographic data.

    Returns:
    --------
    dict : Comprehensive rep metrics
    """
    rep_accounts = accounts_df[accounts_df[new_owner_col] == rep_name]

    total_potential = rep_accounts['estimated_annual_value'].sum()

    # Calculate hours
    total_hours = 0
    for _, account in rep_accounts.iterrows():
        hours = calculate_account_hours(account['account_size'], account['customer_status'])
        total_hours += hours

    utilization_pct = (total_hours / AVAILABLE_SELLING_HOURS) * 100
    num_accounts = len(rep_accounts)

    # Geographic metrics
    center_lat, center_lon = calculate_territory_center(rep_accounts)
    travel_metrics = calculate_total_territory_travel(rep_accounts)

    # Region distribution
    if len(rep_accounts) > 0:
        primary_region = rep_accounts['region'].mode()[0]
        region_concentration = (rep_accounts['region'] == primary_region).sum() / len(rep_accounts)
    else:
        primary_region = None
        region_concentration = 0

    return {
        'rep': rep_name,
        'total_potential': total_potential,
        'total_hours': total_hours,
        'utilization_pct': utilization_pct,
        'num_accounts': num_accounts,
        'available_hours': AVAILABLE_SELLING_HOURS - total_hours,
        'center_lat': center_lat,
        'center_lon': center_lon,
        'annual_travel_miles': travel_metrics['total_annual_miles'],
        'annual_travel_hours': travel_metrics['total_annual_hours'],
        'primary_region': primary_region,
        'region_concentration': region_concentration
    }


def geographic_rebalance(accounts_df, target_reps_per_region=None):
    """
    Rebalance territories using geographic clustering.

    Strategy:
    1. Lock all Customer accounts (protect relationships)
    2. Group Prospect accounts by region
    3. Assign reps to regions to balance total workload
    4. Within each region, assign accounts to minimize travel

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with geography and account info
    target_reps_per_region : dict (optional)
        Desired rep count per region. If None, distributes evenly.

    Returns:
    --------
    DataFrame : Accounts with new territory assignments
    """

    print("\n" + "="*80)
    print("GEOGRAPHIC TERRITORY REBALANCING")
    print("="*80)

    # Create working copy
    df = accounts_df.copy()
    df['new_owner'] = df['current_owner']

    # Get all reps
    all_reps = sorted(df['current_owner'].unique())
    num_reps = len(all_reps)

    print(f"\nReps: {num_reps}")
    print(f"Total Accounts: {len(df)}")

    # Separate customers and prospects
    customers = df[df['customer_status'] == 'Customer'].copy()
    prospects = df[df['customer_status'] == 'Prospect'].copy()

    print(f"Customers (locked): {len(customers)}")
    print(f"Prospects (rebalanceable): {len(prospects)}")

    # STEP 1: Lock customers to current owners
    print("\nSTEP 1: Locking customer accounts to current owners...")
    # Customers already have new_owner = current_owner

    # STEP 2: Analyze regions
    print("\nSTEP 2: Analyzing regional distribution...")
    regions = prospects['region'].unique()
    print(f"Regions: {list(regions)}")

    # Calculate total potential by region
    region_stats = prospects.groupby('region').agg({
        'estimated_annual_value': 'sum',
        'account_name': 'count'
    }).rename(columns={'estimated_annual_value': 'total_value', 'account_name': 'count'})

    print("\nProspects by Region:")
    print(region_stats)

    # STEP 3: Assign reps to regions
    print("\nSTEP 3: Assigning reps to regions...")

    # Calculate how many reps per region based on workload
    if target_reps_per_region is None:
        # Auto-calculate based on value
        total_prospect_value = prospects['estimated_annual_value'].sum()
        target_value_per_rep = total_prospect_value / num_reps

        target_reps_per_region = {}
        for region in regions:
            region_value = region_stats.loc[region, 'total_value']
            num_reps_needed = max(1, round(region_value / target_value_per_rep))
            target_reps_per_region[region] = num_reps_needed

    print("\nTarget reps per region:")
    for region, count in target_reps_per_region.items():
        print(f"  {region}: {count} reps")

    # Assign reps to regions based on current workload
    # Prefer to keep reps in their primary region when possible
    current_metrics = {}
    for rep in all_reps:
        current_metrics[rep] = calculate_rep_metrics_geo(df, rep, 'current_owner')

    rep_to_region = {}
    assigned_reps_by_region = {region: [] for region in regions}

    # First pass: assign reps to their current primary region
    for rep in all_reps:
        primary_region = current_metrics[rep]['primary_region']
        if primary_region and primary_region in regions:
            if len(assigned_reps_by_region[primary_region]) < target_reps_per_region.get(primary_region, 1):
                rep_to_region[rep] = primary_region
                assigned_reps_by_region[primary_region].append(rep)

    # Second pass: assign remaining reps to regions that need more
    unassigned_reps = [rep for rep in all_reps if rep not in rep_to_region]
    for region in regions:
        needed = target_reps_per_region.get(region, 1) - len(assigned_reps_by_region[region])
        for _ in range(needed):
            if unassigned_reps:
                rep = unassigned_reps.pop(0)
                rep_to_region[rep] = region
                assigned_reps_by_region[region].append(rep)

    # Assign any leftover reps to largest regions
    while unassigned_reps:
        # Find region with most value per rep
        best_region = max(regions, key=lambda r: region_stats.loc[r, 'total_value'] / max(1, len(assigned_reps_by_region[r])))
        rep = unassigned_reps.pop(0)
        rep_to_region[rep] = best_region
        assigned_reps_by_region[best_region].append(rep)

    print("\nRep assignments to regions:")
    for region in regions:
        reps_in_region = assigned_reps_by_region[region]
        print(f"  {region}: {reps_in_region}")

    # STEP 4: Within each region, assign prospects to reps
    print("\nSTEP 4: Assigning prospects within regions...")

    for region in regions:
        region_prospects = prospects[prospects['region'] == region].copy()
        region_reps = assigned_reps_by_region[region]

        if len(region_reps) == 0:
            print(f"  Warning: No reps assigned to {region}, skipping...")
            continue

        print(f"\n  {region}: {len(region_prospects)} prospects → {len(region_reps)} reps")

        # Sort prospects by value (highest first)
        region_prospects = region_prospects.sort_values('estimated_annual_value', ascending=False)

        # Assign to reps in round-robin fashion, checking capacity
        for idx, (_, prospect) in enumerate(region_prospects.iterrows()):
            # Find rep with lowest current load
            rep_loads = []
            for rep in region_reps:
                metrics = calculate_rep_metrics_geo(df, rep, 'new_owner')
                rep_loads.append({
                    'rep': rep,
                    'utilization': metrics['utilization_pct'],
                    'potential': metrics['total_potential']
                })

            # Sort by utilization (assign to least utilized)
            rep_loads.sort(key=lambda x: x['utilization'])

            # Try to assign to least loaded rep who has capacity
            assigned = False
            for rep_info in rep_loads:
                if rep_info['utilization'] < (MAX_UTILIZATION_PCT * 100):
                    # Assign this prospect
                    df.loc[prospect.name, 'new_owner'] = rep_info['rep']
                    assigned = True
                    break

            if not assigned:
                # All reps at capacity, assign to least loaded anyway
                df.loc[prospect.name, 'new_owner'] = rep_loads[0]['rep']

    # STEP 5: Calculate results
    print("\n" + "="*80)
    print("REBALANCING COMPLETE")
    print("="*80)

    # Count changes
    changes = (df['new_owner'] != df['current_owner']).sum()
    customer_changes = ((df['customer_status'] == 'Customer') & (df['new_owner'] != df['current_owner'])).sum()
    prospect_changes = ((df['customer_status'] == 'Prospect') & (df['new_owner'] != df['current_owner'])).sum()

    print(f"\nAccounts reassigned: {changes}")
    print(f"  Customers moved: {customer_changes}")
    print(f"  Prospects moved: {prospect_changes}")

    # Geographic improvement
    print("\n" + "="*80)
    print("GEOGRAPHIC IMPROVEMENT")
    print("="*80)

    before_geo = analyze_geographic_balance(df, 'current_owner')
    after_geo = analyze_geographic_balance(df, 'new_owner')

    print("\nBEFORE:")
    print(f"  Total team travel: {before_geo['total_annual_travel_miles'].sum():,.0f} miles/year")
    print(f"  Average territory radius: {before_geo['max_radius_miles'].mean():.0f} miles")
    print(f"  Most spread out: {before_geo['max_radius_miles'].max():.0f} miles")

    print("\nAFTER:")
    print(f"  Total team travel: {after_geo['total_annual_travel_miles'].sum():,.0f} miles/year")
    print(f"  Average territory radius: {after_geo['max_radius_miles'].mean():.0f} miles")
    print(f"  Most spread out: {after_geo['max_radius_miles'].max():.0f} miles")

    travel_reduction = before_geo['total_annual_travel_miles'].sum() - after_geo['total_annual_travel_miles'].sum()
    travel_reduction_pct = (travel_reduction / before_geo['total_annual_travel_miles'].sum()) * 100

    print(f"\n✓ Travel reduction: {travel_reduction:,.0f} miles/year ({travel_reduction_pct:.1f}%)")

    # Cost savings (assume $0.67/mile IRS rate)
    cost_savings = travel_reduction * 0.67
    print(f"✓ Estimated cost savings: ${cost_savings:,.0f}/year")

    # Save results
    df.to_csv('accounts_rebalanced_geographic.csv', index=False)
    print("\n✓ Results saved to: accounts_rebalanced_geographic.csv")

    return df


if __name__ == "__main__":
    # Load accounts with geography
    print("Loading accounts with geographic data...")
    df = pd.read_csv('accounts_with_geography.csv')

    # Run geographic rebalancing
    result_df = geographic_rebalance(df)

    # Show detailed geographic analysis
    print("\n" + "="*80)
    print("DETAILED TERRITORY ANALYSIS (AFTER REBALANCING)")
    print("="*80)

    geo_metrics = analyze_geographic_balance(result_df, 'new_owner')
    print_geographic_summary(geo_metrics)
