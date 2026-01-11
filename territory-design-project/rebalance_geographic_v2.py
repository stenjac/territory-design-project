"""
Geographic Territory Rebalancing V2 - Aggressive Geographic Clustering

This version creates STRICTLY REGIONAL territories to dramatically reduce travel.

Strategy:
1. Assign each rep to ONE PRIMARY REGION only
2. All accounts in that region go to assigned reps
3. Balance workload within regional constraints
4. Customers stay with current rep (exception to regional rule)

This mirrors real mid-market practice where reps cover specific states/regions.
"""

import pandas as pd
import numpy as np
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MAX_UTILIZATION_PCT
)
from geographic_clustering import (
    analyze_geographic_balance,
    print_geographic_summary
)


def strict_regional_rebalance(accounts_df):
    """
    Create strictly regional territories.

    Each rep covers ONE region. No cross-region assignments (except locked customers).
    """

    print("\n" + "="*80)
    print("STRICT REGIONAL TERRITORY REBALANCING")
    print("="*80)
    print("Strategy: Assign each rep to ONE region for geographic efficiency")
    print("="*80)

    # Create working copy
    df = accounts_df.copy()
    df['new_owner'] = df['current_owner']

    # Get all reps
    all_reps = sorted(df['current_owner'].unique())
    num_reps = len(all_reps)

    # Separate customers and prospects
    customers = df[df['customer_status'] == 'Customer']
    prospects = df[df['customer_status'] == 'Prospect']

    print(f"\nTotal Accounts: {len(df)}")
    print(f"  Customers (keep with current rep): {len(customers)}")
    print(f"  Prospects (reassignable): {len(prospects)}")
    print(f"  Sales Reps: {num_reps}")

    # STEP 1: Analyze ALL accounts by region (customers + prospects)
    print("\n" + "="*80)
    print("STEP 1: Analyzing Regional Distribution")
    print("="*80)

    region_summary = df.groupby('region').agg({
        'account_name': 'count',
        'estimated_annual_value': 'sum'
    }).rename(columns={'account_name': 'accounts', 'estimated_annual_value': 'total_value'})

    region_summary = region_summary.sort_values('total_value', ascending=False)

    print("\nAll Accounts by Region:")
    print(region_summary)

    # Calculate hours needed per region
    region_hours = {}
    for region in region_summary.index:
        region_accounts = df[df['region'] == region]
        total_hours = 0
        for _, account in region_accounts.iterrows():
            hours = calculate_account_hours(account['account_size'], account['customer_status'])
            total_hours += hours
        region_hours[region] = total_hours
        region_summary.loc[region, 'hours_needed'] = total_hours

    print("\nWorkload by Region:")
    for region in region_summary.index:
        accounts = region_summary.loc[region, 'accounts']
        value = region_summary.loc[region, 'total_value']
        hours = region_summary.loc[region, 'hours_needed']
        reps_needed = hours / AVAILABLE_SELLING_HOURS
        print(f"  {region:12} | {int(accounts):3} accts | ${value/1e6:5.2f}M | {int(hours):4} hrs | {reps_needed:.1f} reps needed")

    # STEP 2: Assign reps to regions based on workload
    print("\n" + "="*80)
    print("STEP 2: Assigning Reps to Regions")
    print("="*80)

    # Calculate how many reps each region needs
    total_hours_needed = sum(region_hours.values())
    reps_per_region = {}

    for region in region_summary.index:
        # Proportional to workload
        region_pct = region_hours[region] / total_hours_needed
        num_reps_for_region = max(1, round(num_reps * region_pct))
        reps_per_region[region] = num_reps_for_region

    # Adjust if total doesn't match (rounding errors)
    while sum(reps_per_region.values()) > num_reps:
        # Remove from region with most reps
        max_region = max(reps_per_region, key=reps_per_region.get)
        if reps_per_region[max_region] > 1:
            reps_per_region[max_region] -= 1

    while sum(reps_per_region.values()) < num_reps:
        # Add to region with most workload per rep
        max_region = max(region_summary.index,
                        key=lambda r: region_hours[r] / reps_per_region[r])
        reps_per_region[max_region] += 1

    print("\nReps Assigned per Region:")
    for region in region_summary.index:
        num_reps_assigned = reps_per_region[region]
        hours_per_rep = region_hours[region] / num_reps_assigned
        utilization = (hours_per_rep / AVAILABLE_SELLING_HOURS) * 100
        print(f"  {region:12} | {num_reps_assigned} reps | {hours_per_rep:.0f} hrs/rep | {utilization:.0f}% utilization")

    # STEP 3: Assign specific reps to regions
    print("\n" + "="*80)
    print("STEP 3: Assigning Specific Reps")
    print("="*80)

    # For each rep, find their current primary region
    rep_current_regions = {}
    for rep in all_reps:
        rep_accounts = df[df['current_owner'] == rep]
        if len(rep_accounts) > 0:
            primary_region = rep_accounts['region'].mode()[0]
            rep_current_regions[rep] = primary_region

    # Assign reps to regions (prefer their current region)
    region_to_reps = {region: [] for region in region_summary.index}
    assigned_reps = set()

    # First pass: assign reps to their current primary region if space available
    for rep in all_reps:
        current_region = rep_current_regions.get(rep)
        if current_region and len(region_to_reps[current_region]) < reps_per_region[current_region]:
            region_to_reps[current_region].append(rep)
            assigned_reps.add(rep)

    # Second pass: assign remaining reps to regions that need more
    unassigned = [rep for rep in all_reps if rep not in assigned_reps]
    for region in region_summary.index:
        needed = reps_per_region[region] - len(region_to_reps[region])
        for _ in range(needed):
            if unassigned:
                rep = unassigned.pop(0)
                region_to_reps[region].append(rep)
                assigned_reps.add(rep)

    print("\nFinal Rep Assignments:")
    for region in region_summary.index:
        reps_in_region = region_to_reps[region]
        print(f"  {region:12} → {reps_in_region}")

    # STEP 4: Reassign ALL accounts (except customers) to regional reps
    print("\n" + "="*80)
    print("STEP 4: Reassigning Accounts to Regional Reps")
    print("="*80)

    reassignments = 0
    customer_stays = 0
    prospect_moves = 0

    for region in region_summary.index:
        reps_in_region = region_to_reps[region]
        if not reps_in_region:
            continue

        # Get all accounts in this region
        region_accounts = df[df['region'] == region].copy()

        # Separate customers and prospects
        region_customers = region_accounts[region_accounts['customer_status'] == 'Customer']
        region_prospects = region_accounts[region_accounts['customer_status'] == 'Prospect']

        print(f"\n  {region}: {len(region_accounts)} accounts ({len(region_customers)} customers, {len(region_prospects)} prospects)")
        print(f"    Assigned to: {reps_in_region}")

        # Keep customers with current rep IF that rep is in this region
        for idx, customer in region_customers.iterrows():
            if customer['current_owner'] in reps_in_region:
                # Rep is in region, keep assignment
                customer_stays += 1
            else:
                # Rep is NOT in region, need to reassign to a regional rep
                # Assign to least loaded rep in region
                rep_loads = []
                for rep in reps_in_region:
                    rep_accounts = df[df['new_owner'] == rep]
                    total_hours = sum([calculate_account_hours(acc['account_size'], acc['customer_status'])
                                     for _, acc in rep_accounts.iterrows()])
                    utilization = (total_hours / AVAILABLE_SELLING_HOURS) * 100
                    rep_loads.append({'rep': rep, 'utilization': utilization})

                rep_loads.sort(key=lambda x: x['utilization'])
                df.loc[idx, 'new_owner'] = rep_loads[0]['rep']
                reassignments += 1
                print(f"      → Reassigned customer '{customer['account_name']}' from {customer['current_owner']} to {rep_loads[0]['rep']}")

        # Distribute prospects among regional reps
        region_prospects = region_prospects.sort_values('estimated_annual_value', ascending=False)

        for idx, prospect in region_prospects.iterrows():
            # Assign to least loaded rep in region
            rep_loads = []
            for rep in reps_in_region:
                rep_accounts = df[df['new_owner'] == rep]
                total_hours = sum([calculate_account_hours(acc['account_size'], acc['customer_status'])
                                 for _, acc in rep_accounts.iterrows()])
                utilization = (total_hours / AVAILABLE_SELLING_HOURS) * 100
                rep_loads.append({'rep': rep, 'utilization': utilization})

            rep_loads.sort(key=lambda x: x['utilization'])
            best_rep = rep_loads[0]['rep']

            if prospect['current_owner'] != best_rep:
                df.loc[idx, 'new_owner'] = best_rep
                prospect_moves += 1
                reassignments += 1

    # RESULTS
    print("\n" + "="*80)
    print("REBALANCING COMPLETE")
    print("="*80)

    print(f"\nTotal reassignments: {reassignments}")
    print(f"  Customers moved: {reassignments - prospect_moves}")
    print(f"  Customers stayed: {customer_stays}")
    print(f"  Prospects moved: {prospect_moves}")

    # Geographic improvement
    print("\n" + "="*80)
    print("GEOGRAPHIC IMPROVEMENT")
    print("="*80)

    before_geo = analyze_geographic_balance(df, 'current_owner')
    after_geo = analyze_geographic_balance(df, 'new_owner')

    print("\nBEFORE (Cross-Regional Territories):")
    print(f"  Total team travel: {before_geo['total_annual_travel_miles'].sum():,.0f} miles/year")
    print(f"  Average territory radius: {before_geo['max_radius_miles'].mean():.0f} miles")
    print(f"  Average region concentration: {before_geo['region_concentration_pct'].mean():.1f}%")

    print("\nAFTER (Regional Territories):")
    print(f"  Total team travel: {after_geo['total_annual_travel_miles'].sum():,.0f} miles/year")
    print(f"  Average territory radius: {after_geo['max_radius_miles'].mean():.0f} miles")
    print(f"  Average region concentration: {after_geo['region_concentration_pct'].mean():.1f}%")

    travel_reduction = before_geo['total_annual_travel_miles'].sum() - after_geo['total_annual_travel_miles'].sum()
    travel_reduction_pct = (travel_reduction / before_geo['total_annual_travel_miles'].sum()) * 100

    print(f"\n✓ Travel reduction: {travel_reduction:,.0f} miles/year ({travel_reduction_pct:.1f}%)")

    # Cost savings
    cost_savings = travel_reduction * 0.67  # IRS mileage rate
    print(f"✓ Estimated cost savings: ${cost_savings:,.0f}/year")

    # Time savings
    hours_saved = before_geo['total_annual_travel_hours'].sum() - after_geo['total_annual_travel_hours'].sum()
    print(f"✓ Time savings: {hours_saved:,.0f} hours/year ({hours_saved/num_reps:.0f} hrs/rep)")

    # Additional selling time
    selling_days_gained = hours_saved / 8
    print(f"✓ Additional selling time: {selling_days_gained:,.0f} days/year ({selling_days_gained/num_reps:.0f} days/rep)")

    # Save results
    df.to_csv('accounts_rebalanced_regional.csv', index=False)
    after_geo.to_csv('geographic_metrics_regional.csv', index=False)

    print("\n✓ Results saved to:")
    print("  - accounts_rebalanced_regional.csv")
    print("  - geographic_metrics_regional.csv")

    return df


if __name__ == "__main__":
    # Load accounts with geography
    print("Loading accounts with geographic data...")
    df = pd.read_csv('accounts_with_geography.csv')

    # Run strict regional rebalancing
    result_df = strict_regional_rebalance(df)

    # Show detailed analysis
    print("\n" + "="*80)
    print("DETAILED TERRITORY ANALYSIS (REGIONAL MODEL)")
    print("="*80)

    geo_metrics = analyze_geographic_balance(result_df, 'new_owner')
    print_geographic_summary(geo_metrics)
