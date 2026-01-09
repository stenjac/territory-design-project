import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from capacity_calculator import (
    calculate_account_hours,
    AVAILABLE_SELLING_HOURS,
    MIN_UTILIZATION_PCT,
    MAX_UTILIZATION_PCT
)

"""
TERRITORY ANALYSIS DASHBOARD
Simple Streamlit dashboard for territory rebalancing analysis
"""

# Page configuration
st.set_page_config(
    page_title="Territory Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load all data files"""
    original_df = pd.read_csv('accounts.csv')
    rebalanced_df = pd.read_csv('accounts_rebalanced.csv')
    implementation_df = pd.read_csv('implementation_plan.csv')
    rep_summaries_df = pd.read_csv('rep_summaries.csv')

    return original_df, rebalanced_df, implementation_df, rep_summaries_df


def calculate_balance_score(cv):
    """Calculate balance score from CV"""
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


def analyze_territory_metrics(df, owner_column='current_owner'):
    """Calculate territory metrics"""
    reps = df[owner_column].unique()

    metrics = []
    for rep in reps:
        rep_accounts = df[df[owner_column] == rep]
        total_potential = rep_accounts['estimated_annual_value'].sum()

        # Calculate hours
        total_hours = sum(calculate_account_hours(row['account_size'], row['customer_status'])
                         for _, row in rep_accounts.iterrows())
        utilization_pct = (total_hours / AVAILABLE_SELLING_HOURS) * 100

        metrics.append({
            'Rep': rep,
            'Accounts': len(rep_accounts),
            'Total Potential': total_potential,
            'Hours Needed': total_hours,
            'Utilization %': utilization_pct
        })

    metrics_df = pd.DataFrame(metrics)

    # Calculate CV
    potentials = metrics_df['Total Potential']
    std_dev = potentials.std()
    mean_potential = potentials.mean()
    cv = (std_dev / mean_potential) * 100

    balance_score, balance_rating = calculate_balance_score(cv)

    return metrics_df, cv, balance_score, balance_rating


# Load data
original_df, rebalanced_df, implementation_df, rep_summaries_df = load_data()

# Calculate metrics
current_metrics, current_cv, current_score, current_rating = analyze_territory_metrics(original_df, 'current_owner')
proposed_metrics, proposed_cv, proposed_score, proposed_rating = analyze_territory_metrics(rebalanced_df, 'new_owner')

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Current State", "Proposed Changes", "Implementation"])

# Add summary in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Quick Summary")
st.sidebar.metric("Current Balance", f"{current_score:.0f}/100", delta=None)
st.sidebar.metric("Proposed Balance", f"{proposed_score:.0f}/100",
                  delta=f"+{proposed_score - current_score:.0f}", delta_color="normal")
st.sidebar.metric("Accounts to Move", len(implementation_df))

# ============================================================================
# PAGE 1: CURRENT STATE
# ============================================================================
if page == "Current State":
    st.title("📊 Territory Analysis Dashboard")
    st.markdown("### Current State Analysis")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Color code the balance score
        if current_score >= 70:
            st.markdown(f"<h1 style='color: green;'>{current_score:.0f}/100</h1>", unsafe_allow_html=True)
        elif current_score >= 50:
            st.markdown(f"<h1 style='color: orange;'>{current_score:.0f}/100</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: red;'>{current_score:.0f}/100</h1>", unsafe_allow_html=True)
        st.markdown(f"**Balance Score**")
        st.caption(current_rating)

    with col2:
        st.metric("Coefficient of Variation", f"{current_cv:.1f}%")
        st.caption("Target: <25% for good balance")

    with col3:
        reps_optimal = len(current_metrics[
            (current_metrics['Utilization %'] >= MIN_UTILIZATION_PCT * 100) &
            (current_metrics['Utilization %'] <= MAX_UTILIZATION_PCT * 100)
        ])
        st.metric("Reps in Optimal Range", f"{reps_optimal}/{len(current_metrics)}")
        st.caption("80-95% utilization")

    with col4:
        highest = current_metrics['Total Potential'].max()
        lowest = current_metrics['Total Potential'].min()
        ratio = highest / lowest
        st.metric("Imbalance Ratio", f"{ratio:.1f}x")
        st.caption(f"${highest/1e6:.2f}M / ${lowest/1e6:.2f}M")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Potential by Rep")

        # Create bar chart for potential
        fig_potential = px.bar(
            current_metrics.sort_values('Total Potential'),
            x='Total Potential',
            y='Rep',
            orientation='h',
            color='Total Potential',
            color_continuous_scale='RdYlGn',
            labels={'Total Potential': 'Total Potential ($)'}
        )
        fig_potential.update_layout(showlegend=False, height=400)
        fig_potential.update_xaxes(tickformat='$,.0f')
        st.plotly_chart(fig_potential, use_container_width=True)

    with col2:
        st.subheader("Current Utilization by Rep")

        # Create bar chart for utilization with color coding
        utilization_colors = current_metrics['Utilization %'].apply(
            lambda x: 'green' if MIN_UTILIZATION_PCT * 100 <= x <= MAX_UTILIZATION_PCT * 100
            else 'orange' if x < MIN_UTILIZATION_PCT * 100
            else 'red'
        )

        fig_util = go.Figure()
        fig_util.add_trace(go.Bar(
            x=current_metrics.sort_values('Utilization %')['Utilization %'],
            y=current_metrics.sort_values('Utilization %')['Rep'],
            orientation='h',
            marker_color=utilization_colors[current_metrics.sort_values('Utilization %').index],
            text=current_metrics.sort_values('Utilization %')['Utilization %'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))

        # Add target range shading
        fig_util.add_vrect(
            x0=MIN_UTILIZATION_PCT * 100, x1=MAX_UTILIZATION_PCT * 100,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
        )

        fig_util.update_layout(
            showlegend=False,
            height=400,
            xaxis_title="Utilization %",
            yaxis_title="Rep"
        )
        st.plotly_chart(fig_util, use_container_width=True)

    st.markdown("---")

    # Detailed metrics table
    st.subheader("Key Metrics by Rep")

    # Format the table
    display_df = current_metrics.copy()
    display_df['Total Potential'] = display_df['Total Potential'].apply(lambda x: f"${x:,.0f}")
    display_df['Hours Needed'] = display_df['Hours Needed'].apply(lambda x: f"{x:.1f}")
    display_df['Utilization %'] = display_df['Utilization %'].apply(lambda x: f"{x:.1f}%")

    # Add status column
    def get_status(util_str):
        util = float(util_str.rstrip('%'))
        if util < 70:
            return "⚠️ Underutilized"
        elif util < 80:
            return "📊 Light load"
        elif util <= 95:
            return "✅ Optimal"
        elif util <= 110:
            return "⚠️ Stretched"
        else:
            return "🔴 Overloaded"

    display_df['Status'] = display_df['Utilization %'].apply(get_status)

    st.dataframe(
        display_df.sort_values('Total Potential', ascending=False),
        use_container_width=True,
        hide_index=True
    )

# ============================================================================
# PAGE 2: PROPOSED CHANGES
# ============================================================================
elif page == "Proposed Changes":
    st.title("📊 Territory Analysis Dashboard")
    st.markdown("### Proposed Changes")

    # Before/After comparison
    st.subheader("Balance Score Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Before", f"{current_score:.0f}/100", help=current_rating)
        st.caption(f"CV: {current_cv:.1f}%")

    with col2:
        st.metric("After", f"{proposed_score:.0f}/100",
                  delta=f"+{proposed_score - current_score:.0f}",
                  help=proposed_rating)
        st.caption(f"CV: {proposed_cv:.1f}%")

    with col3:
        st.metric("Improvement", f"{proposed_score - current_score:.0f} points")
        st.caption(f"CV reduced by {current_cv - proposed_cv:.1f}%")

    st.markdown("---")

    # Side-by-side comparison charts
    st.subheader("Territory Distribution: Before vs After")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### BEFORE Rebalancing")

        fig_before = px.bar(
            current_metrics.sort_values('Total Potential'),
            x='Total Potential',
            y='Rep',
            orientation='h',
            color='Total Potential',
            color_continuous_scale='RdYlGn',
            title=f"Balance Score: {current_score:.0f}/100 | CV: {current_cv:.1f}%"
        )
        fig_before.update_layout(showlegend=False, height=400)
        fig_before.update_xaxes(tickformat='$,.0f')
        st.plotly_chart(fig_before, use_container_width=True)

    with col2:
        st.markdown("#### AFTER Rebalancing")

        fig_after = px.bar(
            proposed_metrics.sort_values('Total Potential'),
            x='Total Potential',
            y='Rep',
            orientation='h',
            color='Total Potential',
            color_continuous_scale='RdYlGn',
            title=f"Balance Score: {proposed_score:.0f}/100 | CV: {proposed_cv:.1f}%"
        )
        fig_after.update_layout(showlegend=False, height=400)
        fig_after.update_xaxes(tickformat='$,.0f')
        st.plotly_chart(fig_after, use_container_width=True)

    st.markdown("---")

    # Improvement summary
    st.subheader("📈 Key Improvements")

    # Calculate metrics
    current_highest = current_metrics['Total Potential'].max()
    current_lowest = current_metrics['Total Potential'].min()
    proposed_highest = proposed_metrics['Total Potential'].max()
    proposed_lowest = proposed_metrics['Total Potential'].min()

    current_ratio = current_highest / current_lowest
    proposed_ratio = proposed_highest / proposed_lowest

    current_reps_optimal = len(current_metrics[
        (current_metrics['Utilization %'] >= MIN_UTILIZATION_PCT * 100) &
        (current_metrics['Utilization %'] <= MAX_UTILIZATION_PCT * 100)
    ])
    proposed_reps_optimal = len(proposed_metrics[
        (proposed_metrics['Utilization %'] >= MIN_UTILIZATION_PCT * 100) &
        (proposed_metrics['Utilization %'] <= MAX_UTILIZATION_PCT * 100)
    ])

    col1, col2 = st.columns(2)

    with col1:
        st.success(f"✅ **Balance score improved by {proposed_score - current_score:.0f} points** ({current_score:.0f} → {proposed_score:.0f})")
        st.success(f"✅ **Imbalance ratio reduced from {current_ratio:.1f}x to {proposed_ratio:.1f}x**")
        st.success(f"✅ **CV improved from {current_cv:.1f}% to {proposed_cv:.1f}%** ({current_cv - proposed_cv:.1f} percentage point reduction)")

    with col2:
        st.info(f"📊 **{len(implementation_df)} accounts to be reassigned**")
        st.info(f"📊 **Reps in optimal range: {current_reps_optimal} → {proposed_reps_optimal}** ({proposed_reps_optimal - current_reps_optimal:+d})")

        # Calculate spread reduction
        current_spread_pct = ((current_highest - current_lowest) / current_metrics['Total Potential'].mean()) * 100
        proposed_spread_pct = ((proposed_highest - proposed_lowest) / proposed_metrics['Total Potential'].mean()) * 100
        st.info(f"📊 **Territory spread reduced from {current_spread_pct:.0f}% to {proposed_spread_pct:.0f}%** of average")

    st.markdown("---")

    # Rep-by-rep comparison
    st.subheader("Rep-by-Rep Changes")

    # Merge current and proposed for comparison
    comparison_df = current_metrics[['Rep', 'Total Potential', 'Utilization %']].copy()
    comparison_df.columns = ['Rep', 'Current Potential', 'Current Utilization']

    proposed_renamed = proposed_metrics[['Rep', 'Total Potential', 'Utilization %']].copy()
    proposed_renamed.columns = ['Rep', 'Proposed Potential', 'Proposed Utilization']

    comparison_full = comparison_df.merge(proposed_renamed, on='Rep')
    comparison_full['Potential Change'] = comparison_full['Proposed Potential'] - comparison_full['Current Potential']
    comparison_full['Potential Change %'] = (comparison_full['Potential Change'] / comparison_full['Current Potential'] * 100)
    comparison_full['Utilization Change'] = comparison_full['Proposed Utilization'] - comparison_full['Current Utilization']

    st.markdown("---")

    # BALANCE COMPARISON - Interactive Grouped Bar Chart
    st.subheader("📊 Balance Comparison: Before vs After")

    # Prepare data for grouped bar chart
    balance_data = []
    for _, row in comparison_full.iterrows():
        balance_data.append({
            'Rep': row['Rep'],
            'Scenario': 'Current',
            'Potential ($M)': row['Current Potential'] / 1e6
        })
        balance_data.append({
            'Rep': row['Rep'],
            'Scenario': 'Proposed',
            'Potential ($M)': row['Proposed Potential'] / 1e6
        })

    balance_df = pd.DataFrame(balance_data)

    fig_balance = px.bar(
        balance_df.sort_values('Potential ($M)'),
        x='Rep',
        y='Potential ($M)',
        color='Scenario',
        barmode='group',
        color_discrete_map={'Current': '#e74c3c', 'Proposed': '#27ae60'},
        title='Territory Potential: Current vs Proposed'
    )
    fig_balance.update_layout(height=400)
    fig_balance.update_yaxes(tickformat='$,.1f')
    st.plotly_chart(fig_balance, use_container_width=True)

    st.markdown("---")

    # UTILIZATION GAUGE CHARTS
    st.subheader("🎯 Utilization Targets by Rep (After Rebalancing)")
    st.caption("Target zone: 80-95% (green) | Below 80% or above 95% (red/orange)")

    # Create gauge charts in a grid
    cols = st.columns(4)
    for idx, (_, row) in enumerate(comparison_full.iterrows()):
        col = cols[idx % 4]

        with col:
            # Determine color based on utilization
            util = row['Proposed Utilization']
            if MIN_UTILIZATION_PCT * 100 <= util <= MAX_UTILIZATION_PCT * 100:
                color = 'green'
            elif util < 70 or util > 110:
                color = 'red'
            else:
                color = 'orange'

            # Create gauge chart
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=util,
                delta={'reference': row['Current Utilization'], 'suffix': '%'},
                title={'text': row['Rep'], 'font': {'size': 14}},
                gauge={
                    'axis': {'range': [0, 150], 'ticksuffix': '%'},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 70], 'color': '#ffcccc'},
                        {'range': [70, 80], 'color': '#fff3cd'},
                        {'range': [80, 95], 'color': '#d4edda'},
                        {'range': [95, 110], 'color': '#fff3cd'},
                        {'range': [110, 150], 'color': '#ffcccc'}
                    ],
                    'threshold': {
                        'line': {'color': 'black', 'width': 2},
                        'thickness': 0.75,
                        'value': util
                    }
                }
            ))
            fig_gauge.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # SUMMARY TABLE
    st.subheader("📋 Summary Table")

    # Format for display
    display_comparison = comparison_full.copy()
    display_comparison['Current $'] = display_comparison['Current Potential'].apply(lambda x: f"${x/1e6:.2f}M")
    display_comparison['Proposed $'] = display_comparison['Proposed Potential'].apply(lambda x: f"${x/1e6:.2f}M")
    display_comparison['Change %'] = display_comparison['Potential Change %'].apply(lambda x: f"{x:+.1f}%")
    display_comparison['New Utilization'] = display_comparison['Proposed Utilization'].apply(lambda x: f"{x:.1f}%")

    # Add status indicator
    def get_util_status(util):
        if MIN_UTILIZATION_PCT * 100 <= util <= MAX_UTILIZATION_PCT * 100:
            return "✅ Optimal"
        elif util < 70:
            return "⚠️ Under"
        elif util < 80:
            return "📊 Light"
        elif util <= 110:
            return "⚠️ Stretched"
        else:
            return "🔴 Over"

    display_comparison['Status'] = display_comparison['Proposed Utilization'].apply(get_util_status)

    summary_table = display_comparison[['Rep', 'Current $', 'Proposed $', 'Change %', 'New Utilization', 'Status']]
    summary_table.columns = ['Rep Name', 'Current $', 'Proposed $', 'Change', 'Utilization', 'Status']

    st.dataframe(
        summary_table.sort_values('Rep Name'),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # BIG IMPROVEMENT METRICS
    st.subheader("🎯 Key Improvement Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Balance Score",
            value=f"{proposed_score:.0f}/100",
            delta=f"{proposed_score - current_score:+.0f}",
            help="Overall territory balance quality"
        )
        st.caption(f"From {current_score:.0f} ({current_rating})")
        st.caption(f"To {proposed_score:.0f} ({proposed_rating})")

    with col2:
        st.metric(
            label="Coefficient of Variation",
            value=f"{proposed_cv:.1f}%",
            delta=f"{proposed_cv - current_cv:+.1f}%",
            delta_color="inverse",
            help="Lower is better - measures spread"
        )
        st.caption(f"Target: <25% for good balance")

    with col3:
        st.metric(
            label="Imbalance Ratio",
            value=f"{proposed_ratio:.1f}x",
            delta=f"{proposed_ratio - current_ratio:+.1f}x",
            delta_color="inverse",
            help="Ratio of highest to lowest territory"
        )
        st.caption(f"From {current_ratio:.1f}x to {proposed_ratio:.1f}x")

    with col4:
        st.metric(
            label="Accounts to Move",
            value=len(implementation_df),
            help="Number of prospect accounts to reassign"
        )
        st.caption("All prospects (0 customers)")

    st.markdown("---")

    # Visual improvement indicator
    st.subheader("📈 Overall Improvement")

    improvement_score = ((proposed_score - current_score) / 100) * 100
    cv_improvement = ((current_cv - proposed_cv) / current_cv) * 100

    col1, col2 = st.columns(2)

    with col1:
        fig_improvement = go.Figure()

        fig_improvement.add_trace(go.Bar(
            x=['Balance Score', 'CV Reduction', 'Ratio Reduction'],
            y=[improvement_score, cv_improvement, ((current_ratio - proposed_ratio) / current_ratio) * 100],
            marker_color=['#27ae60', '#3498db', '#9b59b6'],
            text=[f"+{improvement_score:.0f}%", f"-{cv_improvement:.0f}%", f"-{((current_ratio - proposed_ratio) / current_ratio) * 100:.0f}%"],
            textposition='outside'
        ))

        fig_improvement.update_layout(
            title="Improvement Percentages",
            yaxis_title="Improvement (%)",
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig_improvement, use_container_width=True)

    with col2:
        # Progress indicator
        progress_pct = min(100, (proposed_score / 70) * 100)  # 70 is "good" threshold

        st.markdown("### Progress to Target")
        st.progress(progress_pct / 100)

        if proposed_score >= 70:
            st.success(f"✅ **Good balance achieved!** ({proposed_score:.0f}/100)")
        elif proposed_score >= 50:
            st.warning(f"⚠️ **Moderate balance** ({proposed_score:.0f}/100) - Further optimization possible")
        else:
            st.error(f"❌ **Poor balance** ({proposed_score:.0f}/100) - Significant work needed")

        st.caption(f"Current: {current_score:.0f}/100 → Proposed: {proposed_score:.0f}/100")

# ============================================================================
# PAGE 3: IMPLEMENTATION
# ============================================================================
else:  # Implementation page
    st.title("📊 Territory Analysis Dashboard")
    st.markdown("### Implementation Plan")

    st.info(f"**Total accounts to be reassigned: {len(implementation_df)}** (All are prospects - no customer relationships disrupted)")

    # Export buttons in columns
    st.subheader("📥 Download Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**1️⃣ Implementation Plan**")
        st.caption("Detailed reassignment list with reasons")

        # Prepare implementation CSV
        impl_csv = implementation_df.to_csv(index=False)

        st.download_button(
            label="📥 Download Implementation Plan",
            data=impl_csv,
            file_name="territory_implementation_plan.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption(f"Contains {len(implementation_df)} reassignments")

    with col2:
        st.markdown("**2️⃣ Rep Summaries**")
        st.caption("Per-rep impact analysis")

        # Prepare rep summaries CSV
        summaries_csv = rep_summaries_df.to_csv(index=False)

        st.download_button(
            label="📥 Download Rep Summaries",
            data=summaries_csv,
            file_name="rep_impact_summaries.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption(f"Impact for all {len(rep_summaries_df)} reps")

    with col3:
        st.markdown("**3️⃣ Complete Territory Assignments**")
        st.caption("All accounts with new owners (CRM-ready)")

        # Prepare complete assignments CSV for CRM upload
        crm_export = rebalanced_df[['account_name', 'account_size', 'customer_status',
                                      'estimated_annual_value', 'current_owner', 'new_owner']].copy()
        crm_export.columns = ['Account Name', 'Account Size', 'Customer Status',
                               'Estimated Annual Value', 'Current Owner', 'New Owner']
        crm_csv = crm_export.to_csv(index=False)

        st.download_button(
            label="📥 Download Territory Assignments",
            data=crm_csv,
            file_name="complete_territory_assignments.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption(f"All {len(rebalanced_df)} accounts")

    st.markdown("---")

    # Summary metrics export
    st.subheader("📊 Export Summary Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Before/After Comparison**")

        # Create comparison metrics for export
        comparison_metrics = pd.DataFrame([
            {
                'Metric': 'Balance Score',
                'Before': f"{current_score:.0f}/100",
                'After': f"{proposed_score:.0f}/100",
                'Improvement': f"+{proposed_score - current_score:.0f}"
            },
            {
                'Metric': 'Coefficient of Variation',
                'Before': f"{current_cv:.1f}%",
                'After': f"{proposed_cv:.1f}%",
                'Improvement': f"{proposed_cv - current_cv:+.1f}%"
            },
            {
                'Metric': 'Imbalance Ratio',
                'Before': f"{current_highest / current_lowest:.1f}x",
                'After': f"{proposed_highest / proposed_lowest:.1f}x",
                'Improvement': f"{(proposed_highest / proposed_lowest) - (current_highest / current_lowest):+.1f}x"
            },
            {
                'Metric': 'Reps in Optimal Range',
                'Before': f"{current_reps_optimal}/{len(current_metrics)}",
                'After': f"{proposed_reps_optimal}/{len(proposed_metrics)}",
                'Improvement': f"+{proposed_reps_optimal - current_reps_optimal}"
            }
        ])

        comparison_csv = comparison_metrics.to_csv(index=False)

        st.download_button(
            label="📥 Download Comparison Metrics",
            data=comparison_csv,
            file_name="territory_comparison_metrics.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        st.markdown("**Executive Summary**")

        # Create executive summary text
        executive_summary = f"""TERRITORY REBALANCING - EXECUTIVE SUMMARY
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

CURRENT STATE
=============
Balance Score: {current_score:.0f}/100 ({current_rating})
Coefficient of Variation: {current_cv:.1f}%
Highest Territory: ${current_highest/1e6:.2f}M
Lowest Territory: ${current_lowest/1e6:.2f}M
Imbalance Ratio: {current_highest / current_lowest:.1f}x
Reps in Optimal Range: {current_reps_optimal}/{len(current_metrics)}

PROPOSED STATE
==============
Balance Score: {proposed_score:.0f}/100 ({proposed_rating})
Coefficient of Variation: {proposed_cv:.1f}%
Highest Territory: ${proposed_highest/1e6:.2f}M
Lowest Territory: ${proposed_lowest/1e6:.2f}M
Imbalance Ratio: {proposed_highest / proposed_lowest:.1f}x
Reps in Optimal Range: {proposed_reps_optimal}/{len(proposed_metrics)}

IMPROVEMENTS
============
Balance Score: +{proposed_score - current_score:.0f} points
CV Reduction: {current_cv - proposed_cv:.1f} percentage points
Ratio Improvement: {(current_highest / current_lowest) - (proposed_highest / proposed_lowest):.1f}x reduction

IMPLEMENTATION
==============
Total Accounts to Reassign: {len(implementation_df)}
Customers Moved: 0 (all relationships protected)
Prospects Redistributed: {len(implementation_df)}

RECOMMENDED TIMELINE
====================
Week 1: Announce changes to team
Weeks 2-4: Execute reassignments
Month 2: Review results and fine-tune

KEY BENEFITS
============
✓ Improved territory balance ({current_score:.0f} → {proposed_score:.0f})
✓ More equitable revenue distribution
✓ Better capacity utilization across team
✓ Protected all existing customer relationships
✓ Clear implementation plan with business reasons
"""

        st.download_button(
            label="📥 Download Executive Summary",
            data=executive_summary,
            file_name="executive_summary.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.markdown("---")

    # Show top reassignments
    st.subheader("Top Account Reassignments (by value)")

    # Display top 20
    display_impl = implementation_df.head(20).copy()
    st.dataframe(display_impl, use_container_width=True, hide_index=True)

    if len(implementation_df) > 20:
        st.caption(f"... and {len(implementation_df) - 20} more reassignments (download CSV for full list)")

    st.markdown("---")

    # Rep summaries
    st.subheader("Impact by Rep")

    st.dataframe(rep_summaries_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Implementation timeline
    st.subheader("🗓️ Suggested Implementation Timeline")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Week 1")
        st.markdown("**Announce Changes**")
        st.markdown("""
        - Share rebalancing rationale with team
        - Present before/after metrics
        - Address questions and concerns
        - Schedule 1-on-1s with affected reps
        """)

    with col2:
        st.markdown("### Weeks 2-4")
        st.markdown("**Execute Reassignments**")
        st.markdown("""
        - Update CRM system with new assignments
        - Introduce reps to new prospect accounts
        - Transfer account documentation
        - Schedule prospect introductions
        """)

    with col3:
        st.markdown("### Month 2")
        st.markdown("**Review Results**")
        st.markdown("""
        - Track utilization metrics
        - Measure balance improvements
        - Gather rep feedback
        - Fine-tune as needed
        """)

    st.markdown("---")

    # Important notes
    st.subheader("⚠️ Implementation Notes")

    st.warning("""
    **Important Considerations:**
    - ✅ All customer relationships are preserved (0 customers moved)
    - ✅ Only prospect accounts are being reassigned
    - ✅ Changes designed to achieve 80-95% optimal utilization
    - ✅ Target is to reduce CV below 25% for good balance
    - 📊 Current balance score: {:.0f}/100 → Proposed: {:.0f}/100 (+{:.0f} points)
    """.format(current_score, proposed_score, proposed_score - current_score))

    st.success("""
    **Next Steps:**
    1. Review the reassignment list above and rep summaries
    2. Verify no critical relationships are disrupted
    3. Communicate changes to affected sales reps
    4. Update CRM system with new account assignments
    5. Schedule transition meetings for reassigned prospects
    """)

# Footer
st.markdown("---")
st.caption("Territory Analysis Dashboard | Built with Streamlit")
