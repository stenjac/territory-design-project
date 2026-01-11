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
from geographic_clustering import (
    analyze_geographic_balance,
    calculate_territory_center,
    calculate_total_territory_travel
)

"""
TERRITORY ANALYSIS DASHBOARD - WITH GEOGRAPHIC METRICS
Enhanced dashboard with geographic clustering and travel analysis
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
    # Try to load geographic data first
    try:
        original_df = pd.read_csv('accounts_with_geography.csv')
        has_geography = True
    except:
        original_df = pd.read_csv('accounts.csv')
        has_geography = False

    # Try different rebalanced files
    try:
        rebalanced_df = pd.read_csv('accounts_rebalanced_regional.csv')
        rebalance_type = 'Regional'
    except:
        try:
            rebalanced_df = pd.read_csv('accounts_rebalanced.csv')
            rebalance_type = 'Revenue'
        except:
            rebalanced_df = original_df.copy()
            rebalanced_df['new_owner'] = rebalanced_df['current_owner']
            rebalance_type = 'None'

    try:
        implementation_df = pd.read_csv('implementation_plan.csv')
    except:
        implementation_df = pd.DataFrame()

    try:
        rep_summaries_df = pd.read_csv('rep_summaries.csv')
    except:
        rep_summaries_df = pd.DataFrame()

    return original_df, rebalanced_df, implementation_df, rep_summaries_df, has_geography, rebalance_type


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


def analyze_territory_metrics(df, owner_column='current_owner', include_geography=False):
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

        metric_dict = {
            'Rep': rep,
            'Accounts': len(rep_accounts),
            'Total Potential': total_potential,
            'Hours Needed': total_hours,
            'Utilization %': utilization_pct
        }

        # Add geographic metrics if available
        if include_geography and 'latitude' in df.columns:
            travel_metrics = calculate_total_territory_travel(rep_accounts)
            center_lat, center_lon = calculate_territory_center(rep_accounts)

            metric_dict.update({
                'Annual Travel (mi)': travel_metrics['total_annual_miles'],
                'Annual Travel (hrs)': travel_metrics['total_annual_hours'],
                'Avg Distance (mi)': travel_metrics['avg_distance_per_visit'],
                'Center Lat': center_lat,
                'Center Lon': center_lon
            })

            # Region concentration
            if 'region' in df.columns and len(rep_accounts) > 0:
                primary_region = rep_accounts['region'].mode()[0]
                region_pct = (rep_accounts['region'] == primary_region).sum() / len(rep_accounts) * 100
                metric_dict['Primary Region'] = primary_region
                metric_dict['Region Concentration %'] = region_pct

        metrics.append(metric_dict)

    metrics_df = pd.DataFrame(metrics)

    # Calculate CV
    potentials = metrics_df['Total Potential']
    std_dev = potentials.std()
    mean_potential = potentials.mean()
    cv = (std_dev / mean_potential) * 100

    balance_score, balance_rating = calculate_balance_score(cv)

    return metrics_df, cv, balance_score, balance_rating


# Load data
original_df, rebalanced_df, implementation_df, rep_summaries_df, has_geography, rebalance_type = load_data()

# Calculate metrics
current_metrics, current_cv, current_score, current_rating = analyze_territory_metrics(
    original_df, 'current_owner', include_geography=has_geography
)
proposed_metrics, proposed_cv, proposed_score, proposed_rating = analyze_territory_metrics(
    rebalanced_df, 'new_owner', include_geography=has_geography
)

# Sidebar navigation
st.sidebar.title("🗺️ Navigation")
page = st.sidebar.radio("Go to", ["Current State", "Proposed Changes", "Geographic Analysis", "Implementation"])

# Add summary in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.metric("Current Balance", f"{current_score:.0f}/100", f"{current_rating}")
st.sidebar.metric("Proposed Balance", f"{proposed_score:.0f}/100", f"{proposed_score - current_score:+.0f}")

if has_geography and 'Annual Travel (mi)' in current_metrics.columns:
    current_travel = current_metrics['Annual Travel (mi)'].sum()
    proposed_travel = proposed_metrics['Annual Travel (mi)'].sum()
    travel_savings = current_travel - proposed_travel
    travel_savings_pct = (travel_savings / current_travel * 100) if current_travel > 0 else 0

    st.sidebar.metric(
        "Travel Reduction",
        f"{travel_savings:,.0f} mi/yr",
        f"{travel_savings_pct:.1f}%",
        delta_color="normal"
    )
    st.sidebar.metric(
        "Cost Savings",
        f"${travel_savings * 0.67:,.0f}/yr",
        "IRS rate"
    )

st.sidebar.markdown(f"\n**Rebalance Type**: {rebalance_type}")
st.sidebar.markdown(f"**Total Accounts**: {len(original_df)}")
st.sidebar.markdown(f"**Total Reps**: {len(current_metrics)}")

# ============================================================================
# PAGE 1: CURRENT STATE
# ============================================================================

if page == "Current State":
    st.title("📊 Current Territory State")

    # Balance Score
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score_color = "🔴" if current_score < 50 else ("🟡" if current_score < 70 else "🟢")
        st.metric(
            "Balance Score",
            f"{current_score:.0f}/100 {score_color}",
            current_rating
        )

    with col2:
        st.metric(
            "Coefficient of Variation",
            f"{current_cv:.1f}%",
            "Target: <25%"
        )

    with col3:
        highest = current_metrics['Total Potential'].max()
        lowest = current_metrics['Total Potential'].min()
        ratio = highest / lowest
        st.metric(
            "Imbalance Ratio",
            f"{ratio:.1f}x",
            f"${highest/1e6:.1f}M / ${lowest/1e6:.1f}M"
        )

    with col4:
        optimal_count = ((current_metrics['Utilization %'] >= 80) &
                        (current_metrics['Utilization %'] <= 95)).sum()
        st.metric(
            "Reps in Optimal Range",
            f"{optimal_count}/{len(current_metrics)}",
            "80-95% utilization"
        )

    st.markdown("---")

    # Charts
    if has_geography and 'Annual Travel (mi)' in current_metrics.columns:
        # Two columns: Revenue + Geographic
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Current Potential by Rep")
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
            st.subheader("Annual Travel by Rep")
            fig_travel = px.bar(
                current_metrics.sort_values('Annual Travel (mi)'),
                x='Annual Travel (mi)',
                y='Rep',
                orientation='h',
                color='Annual Travel (mi)',
                color_continuous_scale='YlOrRd',
                labels={'Annual Travel (mi)': 'Annual Travel (miles)'}
            )
            fig_travel.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_travel, use_container_width=True)

    else:
        # Original two-column layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Current Potential by Rep")
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
            fig_util = px.bar(
                current_metrics.sort_values('Utilization %'),
                x='Utilization %',
                y='Rep',
                orientation='h',
                color='Utilization %',
                color_continuous_scale='RdYlGn_r',
                labels={'Utilization %': 'Capacity Utilization (%)'}
            )
            fig_util.add_vrect(x0=80, x1=95, fillcolor="green", opacity=0.1, line_width=0)
            fig_util.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_util, use_container_width=True)

    # Detailed metrics table
    st.subheader("Detailed Metrics by Rep")

    # Format the display dataframe
    display_df = current_metrics.copy()
    display_df['Total Potential'] = display_df['Total Potential'].apply(lambda x: f"${x/1e6:.2f}M")
    display_df['Hours Needed'] = display_df['Hours Needed'].apply(lambda x: f"{x:.0f}")
    display_df['Utilization %'] = display_df['Utilization %'].apply(lambda x: f"{x:.0f}%")

    if 'Annual Travel (mi)' in display_df.columns:
        display_df['Annual Travel (mi)'] = display_df['Annual Travel (mi)'].apply(lambda x: f"{x:,.0f}")
        display_df['Avg Distance (mi)'] = display_df['Avg Distance (mi)'].apply(lambda x: f"{x:.0f}")

    # Add status column
    def get_status(row):
        util = float(row['Utilization %'].strip('%'))
        if util < 70:
            return "⚪ Underutilized"
        elif util < 80:
            return "🔵 Light Load"
        elif util <= 95:
            return "🟢 Optimal"
        elif util <= 110:
            return "🟡 Stretched"
        else:
            return "🔴 Overloaded"

    display_df['Status'] = display_df.apply(get_status, axis=1)

    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 2: PROPOSED CHANGES
# ============================================================================

elif page == "Proposed Changes":
    st.title("🎯 Proposed Territory Changes")

    # Improvement metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        improvement = proposed_score - current_score
        score_color = "🟢" if improvement > 0 else "🔴"
        st.metric(
            "Balance Score",
            f"{proposed_score:.0f}/100 {score_color}",
            f"{improvement:+.0f} points"
        )

    with col2:
        cv_improvement = current_cv - proposed_cv
        st.metric(
            "CV Improvement",
            f"{proposed_cv:.1f}%",
            f"{cv_improvement:+.1f} pp"
        )

    with col3:
        current_ratio = current_metrics['Total Potential'].max() / current_metrics['Total Potential'].min()
        proposed_ratio = proposed_metrics['Total Potential'].max() / proposed_metrics['Total Potential'].min()
        st.metric(
            "Ratio Improvement",
            f"{proposed_ratio:.1f}x",
            f"{current_ratio - proposed_ratio:+.1f}x"
        )

    with col4:
        current_optimal = ((current_metrics['Utilization %'] >= 80) &
                          (current_metrics['Utilization %'] <= 95)).sum()
        proposed_optimal = ((proposed_metrics['Utilization %'] >= 80) &
                           (proposed_metrics['Utilization %'] <= 95)).sum()
        st.metric(
            "Optimal Reps",
            f"{proposed_optimal}/{len(proposed_metrics)}",
            f"{proposed_optimal - current_optimal:+d} reps"
        )

    st.markdown("---")

    # Geographic improvement (if available)
    if has_geography and 'Annual Travel (mi)' in current_metrics.columns:
        st.subheader("🗺️ Geographic Efficiency Gains")

        col1, col2, col3, col4 = st.columns(4)

        current_travel = current_metrics['Annual Travel (mi)'].sum()
        proposed_travel = proposed_metrics['Annual Travel (mi)'].sum()
        travel_savings = current_travel - proposed_travel
        travel_savings_pct = (travel_savings / current_travel * 100) if current_travel > 0 else 0

        with col1:
            st.metric(
                "Travel Reduction",
                f"{travel_savings:,.0f} mi/yr",
                f"{travel_savings_pct:.1f}%"
            )

        with col2:
            cost_savings = travel_savings * 0.67
            st.metric(
                "Cost Savings",
                f"${cost_savings:,.0f}/yr",
                "@ $0.67/mile"
            )

        with col3:
            hours_saved = travel_savings / 25  # 25 mph average
            days_saved = hours_saved / 8
            st.metric(
                "Time Savings",
                f"{days_saved:,.0f} days/yr",
                f"{hours_saved:,.0f} hrs"
            )

        with col4:
            current_avg_region = current_metrics['Region Concentration %'].mean() if 'Region Concentration %' in current_metrics.columns else 0
            proposed_avg_region = proposed_metrics['Region Concentration %'].mean() if 'Region Concentration %' in proposed_metrics.columns else 0
            st.metric(
                "Region Focus",
                f"{proposed_avg_region:.0f}%",
                f"{proposed_avg_region - current_avg_region:+.0f}%"
            )

        st.markdown("---")

    # Comparison charts
    st.subheader("Before vs After Comparison")

    # Prepare comparison data
    balance_df = pd.DataFrame({
        'Rep': list(current_metrics['Rep']) + list(proposed_metrics['Rep']),
        'Potential ($M)': list(current_metrics['Total Potential']/1e6) + list(proposed_metrics['Total Potential']/1e6),
        'Scenario': ['Current']*len(current_metrics) + ['Proposed']*len(proposed_metrics)
    })

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

    # Utilization gauges (8 reps)
    st.subheader("Utilization Changes by Rep")

    # Create 4x2 grid for 8 gauges
    for row_idx in range(2):
        cols = st.columns(4)
        for col_idx in range(4):
            rep_idx = row_idx * 4 + col_idx
            if rep_idx < len(current_metrics):
                with cols[col_idx]:
                    rep = current_metrics.iloc[rep_idx]['Rep']
                    current_util = current_metrics.iloc[rep_idx]['Utilization %']
                    proposed_row = proposed_metrics[proposed_metrics['Rep'] == rep]
                    proposed_util = proposed_row.iloc[0]['Utilization %'] if len(proposed_row) > 0 else current_util

                    # Color based on proposed utilization
                    if 80 <= proposed_util <= 95:
                        color = '#27ae60'  # Green
                    elif 70 <= proposed_util < 80 or 95 < proposed_util <= 110:
                        color = '#f39c12'  # Orange
                    else:
                        color = '#e74c3c'  # Red

                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=proposed_util,
                        delta={'reference': current_util, 'suffix': '%'},
                        title={'text': rep, 'font': {'size': 14}},
                        gauge={
                            'axis': {'range': [0, 150]},
                            'bar': {'color': color},
                            'steps': [
                                {'range': [0, 80], 'color': 'lightgray'},
                                {'range': [80, 95], 'color': '#d4edda'},
                                {'range': [95, 150], 'color': 'lightgray'}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 95
                            }
                        }
                    ))
                    fig_gauge.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_gauge, use_container_width=True)


# ============================================================================
# PAGE 3: GEOGRAPHIC ANALYSIS
# ============================================================================

elif page == "Geographic Analysis":
    st.title("🗺️ Geographic Territory Analysis")

    if not has_geography:
        st.warning("⚠️ Geographic data not available. Run `python3 add_geography.py` to add location data.")
        st.info("This page requires accounts with city, state, and lat/lon coordinates.")
        st.stop()

    # Summary metrics
    st.subheader("Geographic Efficiency Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        current_travel = current_metrics['Annual Travel (mi)'].sum()
        st.metric(
            "Current Annual Travel",
            f"{current_travel:,.0f} miles",
            f"${current_travel * 0.67:,.0f} cost"
        )

    with col2:
        proposed_travel = proposed_metrics['Annual Travel (mi)'].sum()
        travel_reduction = current_travel - proposed_travel
        st.metric(
            "Proposed Annual Travel",
            f"{proposed_travel:,.0f} miles",
            f"-{travel_reduction:,.0f} miles"
        )

    with col3:
        efficiency_gain = (travel_reduction / current_travel * 100) if current_travel > 0 else 0
        st.metric(
            "Efficiency Gain",
            f"{efficiency_gain:.1f}%",
            f"{travel_reduction / 8:,.0f} mi/rep"
        )

    st.markdown("---")

    # Regional distribution
    if 'region' in original_df.columns:
        st.subheader("Regional Distribution")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Current State**")
            region_counts = original_df['region'].value_counts()
            fig_region_current = px.pie(
                values=region_counts.values,
                names=region_counts.index,
                title="Accounts by Region"
            )
            st.plotly_chart(fig_region_current, use_container_width=True)

        with col2:
            st.markdown("**Rep Regional Focus**")
            if 'Primary Region' in current_metrics.columns:
                rep_region_df = current_metrics.groupby('Primary Region').size().reset_index(name='Reps')
                fig_rep_region = px.bar(
                    rep_region_df,
                    x='Primary Region',
                    y='Reps',
                    title="Reps per Region"
                )
                st.plotly_chart(fig_rep_region, use_container_width=True)

    st.markdown("---")

    # Territory compactness
    st.subheader("Territory Compactness")

    # Calculate average distance for each rep
    compact_data = []
    for idx, row in current_metrics.iterrows():
        compact_data.append({
            'Rep': row['Rep'],
            'Avg Distance (mi)': row['Avg Distance (mi)'],
            'Scenario': 'Current'
        })

    for idx, row in proposed_metrics.iterrows():
        compact_data.append({
            'Rep': row['Rep'],
            'Avg Distance (mi)': row['Avg Distance (mi)'],
            'Scenario': 'Proposed'
        })

    compact_df = pd.DataFrame(compact_data)

    fig_compact = px.bar(
        compact_df,
        x='Rep',
        y='Avg Distance (mi)',
        color='Scenario',
        barmode='group',
        color_discrete_map={'Current': '#e74c3c', 'Proposed': '#27ae60'},
        title='Average Distance to Territory Center'
    )
    st.plotly_chart(fig_compact, use_container_width=True)

    st.markdown("---")

    # Detailed geographic metrics
    st.subheader("Detailed Geographic Metrics")

    # Build comparison safely
    geo_data = {
        'Rep': current_metrics['Rep'].tolist(),
        'Current Travel (mi/yr)': current_metrics['Annual Travel (mi)'].apply(lambda x: f"{x:,.0f}").tolist()
    }

    # Add proposed travel safely
    proposed_travel_list = []
    savings_list = []
    for rep in current_metrics['Rep']:
        prop_row = proposed_metrics[proposed_metrics['Rep'] == rep]
        if len(prop_row) > 0:
            prop_travel = prop_row.iloc[0]['Annual Travel (mi)']
            curr_travel = current_metrics[current_metrics['Rep'] == rep].iloc[0]['Annual Travel (mi)']
            proposed_travel_list.append(f"{prop_travel:,.0f}")
            savings_list.append(f"{int(curr_travel - prop_travel):,}")
        else:
            proposed_travel_list.append("N/A")
            savings_list.append("N/A")

    geo_data['Proposed Travel (mi/yr)'] = proposed_travel_list
    geo_data['Savings (mi/yr)'] = savings_list

    # Add regions if available
    if 'Primary Region' in current_metrics.columns:
        geo_data['Current Region'] = current_metrics['Primary Region'].tolist()
    else:
        geo_data['Current Region'] = ['N/A'] * len(current_metrics)

    if 'Primary Region' in proposed_metrics.columns:
        proposed_regions = []
        for rep in current_metrics['Rep']:
            prop_row = proposed_metrics[proposed_metrics['Rep'] == rep]
            proposed_regions.append(prop_row.iloc[0]['Primary Region'] if len(prop_row) > 0 else 'N/A')
        geo_data['Proposed Region'] = proposed_regions
    else:
        geo_data['Proposed Region'] = ['N/A'] * len(current_metrics)

    if 'Region Concentration %' in proposed_metrics.columns:
        region_focus = []
        for rep in current_metrics['Rep']:
            prop_row = proposed_metrics[proposed_metrics['Rep'] == rep]
            region_focus.append(f"{prop_row.iloc[0]['Region Concentration %']:.0f}%" if len(prop_row) > 0 else 'N/A')
        geo_data['Region Focus'] = region_focus
    else:
        geo_data['Region Focus'] = ['N/A'] * len(current_metrics)

    geo_comparison = pd.DataFrame(geo_data)

    st.dataframe(geo_comparison, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 4: IMPLEMENTATION
# ============================================================================

elif page == "Implementation":
    st.title("📋 Implementation Plan")

    st.markdown("""
    This page provides downloadable files and actionable steps for implementing the territory changes.
    """)

    # Account changes summary
    if len(implementation_df) > 0:
        changes = len(implementation_df)
        # Check if 'reason' column exists
        if 'reason' in implementation_df.columns:
            customer_changes = implementation_df[implementation_df['reason'].str.contains('customer', case=False, na=False)]
            prospect_changes = implementation_df[~implementation_df['reason'].str.contains('customer', case=False, na=False)]
        else:
            customer_changes = pd.DataFrame()
            prospect_changes = implementation_df

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Changes", changes)

        with col2:
            st.metric("Customers Moved", len(customer_changes))

        with col3:
            st.metric("Prospects Moved", len(prospect_changes))

        with col4:
            # Check for value column (could be 'account_value' or 'estimated_annual_value')
            if 'account_value' in implementation_df.columns:
                total_value = implementation_df['account_value'].sum()
            elif 'estimated_annual_value' in implementation_df.columns:
                total_value = implementation_df['estimated_annual_value'].sum()
            else:
                total_value = 0
            st.metric("Total Value Moving", f"${total_value/1e6:.1f}M")

    st.markdown("---")

    # Download buttons
    st.subheader("📥 Download Implementation Files")

    col1, col2 = st.columns(2)

    with col1:
        # Implementation plan
        if len(implementation_df) > 0:
            impl_csv = implementation_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Implementation Plan (CSV)",
                data=impl_csv,
                file_name="territory_implementation_plan.csv",
                mime="text/csv"
            )

        # Rep summaries
        if len(rep_summaries_df) > 0:
            summaries_csv = rep_summaries_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Rep Summaries (CSV)",
                data=summaries_csv,
                file_name="rep_impact_summaries.csv",
                mime="text/csv"
            )

    with col2:
        # Complete assignments
        assignments_csv = rebalanced_df[['account_name', 'current_owner', 'new_owner', 'estimated_annual_value']].to_csv(index=False)
        st.download_button(
            label="📥 Download Complete Assignments (CSV)",
            data=assignments_csv,
            file_name="complete_territory_assignments.csv",
            mime="text/csv"
        )

        # Comparison metrics
        comparison_data = {
            'Metric': ['Balance Score', 'CV', 'Imbalance Ratio', 'Optimal Reps', 'Travel (mi/yr)', 'Travel Savings ($)'],
            'Current': [
                f"{current_score:.0f}/100",
                f"{current_cv:.1f}%",
                f"{current_metrics['Total Potential'].max() / current_metrics['Total Potential'].min():.1f}x",
                f"{((current_metrics['Utilization %'] >= 80) & (current_metrics['Utilization %'] <= 95)).sum()}/{len(current_metrics)}",
                f"{current_metrics['Annual Travel (mi)'].sum():,.0f}" if 'Annual Travel (mi)' in current_metrics.columns else 'N/A',
                'Baseline'
            ],
            'Proposed': [
                f"{proposed_score:.0f}/100",
                f"{proposed_cv:.1f}%",
                f"{proposed_metrics['Total Potential'].max() / proposed_metrics['Total Potential'].min():.1f}x",
                f"{((proposed_metrics['Utilization %'] >= 80) & (proposed_metrics['Utilization %'] <= 95)).sum()}/{len(proposed_metrics)}",
                f"{proposed_metrics['Annual Travel (mi)'].sum():,.0f}" if 'Annual Travel (mi)' in proposed_metrics.columns else 'N/A',
                f"${(current_metrics['Annual Travel (mi)'].sum() - proposed_metrics['Annual Travel (mi)'].sum()) * 0.67:,.0f}" if 'Annual Travel (mi)' in current_metrics.columns else 'N/A'
            ]
        }
        comparison_df = pd.DataFrame(comparison_data)
        comparison_csv = comparison_df.to_csv(index=False)

        st.download_button(
            label="📥 Download Comparison Metrics (CSV)",
            data=comparison_csv,
            file_name="territory_comparison_metrics.csv",
            mime="text/csv"
        )

    st.markdown("---")

    # Top changes preview
    if len(implementation_df) > 0:
        st.subheader("Top 20 Reassignments")
        st.dataframe(
            implementation_df.head(20),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # Implementation timeline
    st.subheader("🗓️ Suggested Implementation Timeline")

    st.markdown("""
    **Week 1: Announcement**
    - Share proposed changes with sales leadership
    - Communicate rationale and benefits
    - Address initial questions

    **Week 2-3: Transition Planning**
    - Reps review new account assignments
    - Plan customer handoff calls
    - Update CRM systems

    **Week 4: Execute**
    - Formal account transitions
    - Customer introduction emails/calls
    - Update all systems

    **Month 2: Monitor & Adjust**
    - Track early metrics
    - Address any issues
    - Gather rep feedback
    - Make minor adjustments if needed
    """)
