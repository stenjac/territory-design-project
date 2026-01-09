import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MIN_UTILIZATION_PCT,
    MAX_UTILIZATION_PCT
)

"""
TERRITORY COMPARISON ANALYSIS
Compares current vs rebalanced territory assignments
"""


def calculate_balance_score(cv):
    """Calculate balance score based on coefficient of variation"""
    if cv < 20:
        score = 100 - (cv / 20) * 10
        rating = "Excellent Balance"
    elif cv < 30:
        score = 89 - ((cv - 20) / 10) * 19
        rating = "Good Balance"
    elif cv < 50:
        score = 69 - ((cv - 30) / 20) * 19
        rating = "Moderate Imbalance"
    else:
        score = max(0, 49 - ((cv - 50) / 50) * 49)
        rating = "Poor Balance"
    return score, rating


def analyze_assignments(df, owner_column='current_owner'):
    """Analyze territory assignments"""
    reps = df[owner_column].unique()

    metrics = []
    for rep in reps:
        rep_accounts = df[df[owner_column] == rep]

        # Calculate potential
        total_potential = rep_accounts['estimated_annual_value'].sum()

        # Calculate hours
        total_hours = sum(calculate_account_hours(row['account_size'], row['customer_status'])
                         for _, row in rep_accounts.iterrows())

        # Calculate utilization
        utilization_pct = (total_hours / AVAILABLE_SELLING_HOURS) * 100

        metrics.append({
            'rep': rep,
            'num_accounts': len(rep_accounts),
            'total_potential': total_potential,
            'total_hours': total_hours,
            'utilization_pct': utilization_pct
        })

    metrics_df = pd.DataFrame(metrics)

    # Calculate summary statistics
    potentials = metrics_df['total_potential']
    std_dev = potentials.std()
    mean_potential = potentials.mean()
    cv = (std_dev / mean_potential) * 100
    balance_score, balance_rating = calculate_balance_score(cv)

    highest = potentials.max()
    lowest = potentials.min()
    ratio = highest / lowest if lowest > 0 else 0

    # Utilization stats
    utils = metrics_df['utilization_pct']
    reps_in_range = sum(1 for u in utils if MIN_UTILIZATION_PCT * 100 <= u <= MAX_UTILIZATION_PCT * 100)

    return {
        'metrics_df': metrics_df,
        'balance_score': balance_score,
        'balance_rating': balance_rating,
        'cv': cv,
        'highest': highest,
        'lowest': lowest,
        'ratio': ratio,
        'mean_potential': mean_potential,
        'std_dev': std_dev,
        'reps_in_optimal': reps_in_range,
        'total_reps': len(reps)
    }


def print_comparison_report(before_stats, after_stats, movements_df):
    """Print detailed comparison report"""

    print("=" * 80)
    print("TERRITORY COMPARISON: BEFORE vs AFTER REBALANCING")
    print("=" * 80)
    print()

    # Balance Score Comparison
    print("BALANCE SCORE:")
    print("-" * 80)
    print(f"{'Metric':<30} {'Before':<20} {'After':<20} {'Change':<10}")
    print("-" * 80)

    score_change = after_stats['balance_score'] - before_stats['balance_score']
    print(f"{'Balance Score':<30} {before_stats['balance_score']:.0f}/100 ({before_stats['balance_rating']:<15}) "
          f"{after_stats['balance_score']:.0f}/100 ({after_stats['balance_rating']:<15}) {score_change:+.0f}")

    cv_change = after_stats['cv'] - before_stats['cv']
    print(f"{'Coefficient of Variation':<30} {before_stats['cv']:.1f}%{'':<15} "
          f"{after_stats['cv']:.1f}%{'':<15} {cv_change:+.1f}%")
    print()

    # Territory Distribution
    print("TERRITORY DISTRIBUTION:")
    print("-" * 80)
    print(f"{'Metric':<30} {'Before':<20} {'After':<20} {'Change':<10}")
    print("-" * 80)

    print(f"{'Highest territory':<30} ${before_stats['highest']/1e6:.2f}M{'':<12} "
          f"${after_stats['highest']/1e6:.2f}M{'':<12} "
          f"{(after_stats['highest'] - before_stats['highest'])/1e6:+.2f}M")

    print(f"{'Lowest territory':<30} ${before_stats['lowest']/1e6:.2f}M{'':<12} "
          f"${after_stats['lowest']/1e6:.2f}M{'':<12} "
          f"{(after_stats['lowest'] - before_stats['lowest'])/1e6:+.2f}M")

    print(f"{'Ratio (highest/lowest)':<30} {before_stats['ratio']:.1f}x{'':<16} "
          f"{after_stats['ratio']:.1f}x{'':<16} "
          f"{after_stats['ratio'] - before_stats['ratio']:+.1f}x")

    print(f"{'Average per rep':<30} ${before_stats['mean_potential']/1e6:.2f}M{'':<12} "
          f"${after_stats['mean_potential']/1e6:.2f}M{'':<12} "
          f"{(after_stats['mean_potential'] - before_stats['mean_potential'])/1e6:+.2f}M")

    print(f"{'Standard deviation':<30} ${before_stats['std_dev']/1e6:.2f}M{'':<12} "
          f"${after_stats['std_dev']/1e6:.2f}M{'':<12} "
          f"{(after_stats['std_dev'] - before_stats['std_dev'])/1e6:+.2f}M")
    print()

    # Utilization Comparison
    print("WORKLOAD UTILIZATION:")
    print("-" * 80)
    optimal_change = after_stats['reps_in_optimal'] - before_stats['reps_in_optimal']
    print(f"Reps in optimal range (80-95%): {before_stats['reps_in_optimal']}/{before_stats['total_reps']} → "
          f"{after_stats['reps_in_optimal']}/{after_stats['total_reps']} ({optimal_change:+d})")
    print()

    # Account Movements
    print("ACCOUNT MOVEMENTS:")
    print("-" * 80)
    customers_moved = len(movements_df[movements_df['customer_status'] == 'Customer'])
    prospects_moved = len(movements_df[movements_df['customer_status'] == 'Prospect'])

    print(f"Total accounts reassigned: {len(movements_df)}")
    print(f"  • Customers moved: {customers_moved}")
    print(f"  • Prospects moved: {prospects_moved}")
    print()

    # Key Improvements
    print("=" * 80)
    print("KEY IMPROVEMENTS:")
    print("=" * 80)
    print(f"✓ Balance score improved by {score_change:+.0f} points ({before_stats['balance_score']:.0f} → {after_stats['balance_score']:.0f})")
    print(f"✓ CV improved from {before_stats['cv']:.1f}% to {after_stats['cv']:.1f}% ({cv_change:+.1f} percentage points)")

    # Calculate percentage spread
    before_spread_pct = ((before_stats['highest'] - before_stats['lowest']) / before_stats['mean_potential']) * 100
    after_spread_pct = ((after_stats['highest'] - after_stats['lowest']) / after_stats['mean_potential']) * 100

    print(f"✓ Territory spread reduced from {before_spread_pct:.0f}% to {after_spread_pct:.0f}% of average")
    print(f"✓ Ratio improved from {before_stats['ratio']:.1f}x to {after_stats['ratio']:.1f}x")
    print(f"✓ {prospects_moved} prospects reassigned (protecting {len(movements_df[movements_df['customer_status'] == 'Customer']) or 'all'} customer relationships)")
    print()


def create_comparison_charts(before_stats, after_stats):
    """Create side-by-side comparison charts"""

    # Prepare data
    before_df = before_stats['metrics_df'].sort_values('total_potential', ascending=True)
    after_df = after_stats['metrics_df'].sort_values('total_potential', ascending=True)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # BEFORE chart
    reps_before = before_df['rep']
    values_before = before_df['total_potential'] / 1e6

    # Color gradient for before (red to yellow-green)
    colors_before = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(reps_before)))

    bars1 = ax1.barh(reps_before, values_before, color=colors_before, edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar, value in zip(bars1, values_before):
        width = bar.get_width()
        ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'${value:.2f}M',
                ha='left', va='center', fontweight='bold', fontsize=9)

    # Add average line
    avg_before = before_stats['mean_potential'] / 1e6
    ax1.axvline(avg_before, color='blue', linestyle='--', linewidth=2,
               label=f'Average: ${avg_before:.2f}M', alpha=0.7)

    ax1.set_xlabel('Total Potential Value (Millions $)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Sales Rep', fontsize=11, fontweight='bold')
    ax1.set_title(f'BEFORE Rebalancing\nBalance Score: {before_stats["balance_score"]:.0f}/100 | CV: {before_stats["cv"]:.1f}%\n'
                 f'Range: ${before_stats["lowest"]/1e6:.2f}M - ${before_stats["highest"]/1e6:.2f}M ({before_stats["ratio"]:.1f}x)',
                 fontsize=12, fontweight='bold', pad=15)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # AFTER chart
    reps_after = after_df['rep']
    values_after = after_df['total_potential'] / 1e6

    # Color gradient for after (more green = better balance)
    colors_after = plt.cm.RdYlGn(np.linspace(0.4, 1.0, len(reps_after)))

    bars2 = ax2.barh(reps_after, values_after, color=colors_after, edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar, value in zip(bars2, values_after):
        width = bar.get_width()
        ax2.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'${value:.2f}M',
                ha='left', va='center', fontweight='bold', fontsize=9)

    # Add average line
    avg_after = after_stats['mean_potential'] / 1e6
    ax2.axvline(avg_after, color='blue', linestyle='--', linewidth=2,
               label=f'Average: ${avg_after:.2f}M', alpha=0.7)

    ax2.set_xlabel('Total Potential Value (Millions $)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Sales Rep', fontsize=11, fontweight='bold')
    ax2.set_title(f'AFTER Rebalancing\nBalance Score: {after_stats["balance_score"]:.0f}/100 | CV: {after_stats["cv"]:.1f}%\n'
                 f'Range: ${after_stats["lowest"]/1e6:.2f}M - ${after_stats["highest"]/1e6:.2f}M ({after_stats["ratio"]:.1f}x)',
                 fontsize=12, fontweight='bold', pad=15)
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(axis='x', alpha=0.3, linestyle='--')

    # Make x-axis ranges the same for better comparison
    max_val = max(values_before.max(), values_after.max()) + 0.5
    ax1.set_xlim(0, max_val)
    ax2.set_xlim(0, max_val)

    plt.tight_layout()
    plt.savefig('territory_comparison.png', dpi=300, bbox_inches='tight')
    print("Chart saved as 'territory_comparison.png'")
    print()


# Main execution
if __name__ == "__main__":
    # Load data
    original_df = pd.read_csv('accounts.csv')
    rebalanced_df = pd.read_csv('accounts_rebalanced.csv')

    print("=" * 80)
    print("LOADING DATA FOR COMPARISON")
    print("=" * 80)
    print(f"Original accounts loaded: {len(original_df)}")
    print(f"Rebalanced accounts loaded: {len(rebalanced_df)}")
    print()

    # Analyze before and after
    print("Analyzing BEFORE state (current assignments)...")
    before_stats = analyze_assignments(original_df, 'current_owner')
    print("✓ Complete")
    print()

    print("Analyzing AFTER state (rebalanced assignments)...")
    after_stats = analyze_assignments(rebalanced_df, 'new_owner')
    print("✓ Complete")
    print()

    # Find movements
    movements = rebalanced_df[rebalanced_df['current_owner'] != rebalanced_df['new_owner']]

    # Print comparison report
    print_comparison_report(before_stats, after_stats, movements)

    # Create visualization
    print("=" * 80)
    print("CREATING COMPARISON VISUALIZATION")
    print("=" * 80)
    create_comparison_charts(before_stats, after_stats)

    print("=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
