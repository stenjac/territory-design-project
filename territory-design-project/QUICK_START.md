# 🚀 Quick Start Guide

## Run the Interactive Dashboard

```bash
streamlit run territory_dashboard.py
```

Or if `streamlit` is not in your PATH:

```bash
python3 -m streamlit run territory_dashboard.py
```

The dashboard will open in your browser at http://localhost:8501

## Dashboard Features

### Page 1: Current State
- **Balance Score** (14/100) with color coding
- **Interactive bar charts** for potential and utilization
- **Metrics table** with status indicators
- Key insights: CV, imbalance ratio, optimal range

### Page 2: Proposed Changes ⭐ NEW FEATURES!
- **Grouped bar chart** comparing before/after
- **8 utilization gauges** (one per rep) with target zones
- **Summary table** with all key metrics
- **Big improvement metrics** with deltas
- **Progress indicators** showing achievement vs target

### Page 3: Implementation ⭐ NEW EXPORTS!
- **5 Download Options**:
  1. Implementation Plan (CSV) - 40 reassignments with reasons
  2. Rep Summaries (CSV) - Per-rep impact analysis
  3. Territory Assignments (CSV) - Complete CRM-ready export
  4. Comparison Metrics (CSV) - Before/after summary
  5. Executive Summary (TXT) - Ready-to-share report
- **Top 20 reassignments** with business reasons
- **Rep impact summaries**
- **Timeline suggestions** (Weeks 1-4, Month 2)

## New Visualizations

### 1. Balance Comparison Chart
Side-by-side grouped bars showing Current (red) vs Proposed (green) for each rep

### 2. Utilization Gauges (8 total)
- Color-coded gauges for each rep
- Green zone (80-95%) = optimal
- Shows delta from current utilization
- Easy to spot over/under-utilized reps

### 3. Summary Table
| Rep Name | Current $ | Proposed $ | Change | Utilization | Status |
|----------|-----------|------------|--------|-------------|--------|
| Rep_1    | $7.74M    | $6.19M     | -20.0% | 115.0%      | ⚠️ Stretched |
| Rep_8    | $0.31M    | $2.06M     | +565%  | 55.5%       | ⚠️ Under |

### 4. Big Improvement Metrics
- **Balance Score**: 14 → 50 (+37)
- **CV**: 86.0% → 49.6% (-36.4%)
- **Imbalance Ratio**: 25.0x → 3.0x (-22x)
- **Accounts to Move**: 40 prospects

### 5. Improvement Bar Chart
Visual representation of:
- Balance score improvement: +37%
- CV reduction: -42%
- Ratio reduction: -88%

### 6. Progress Indicator
Progress bar showing how close to "good balance" (70/100 target)

## Command Line Tools

If you prefer command-line analysis:

```bash
# Full analysis
python3 analyze_territories.py

# Capacity modeling
python3 capacity_calculator.py

# Run rebalancing
python3 rebalance_territories.py

# Compare before/after
python3 compare_territories.py

# Generate implementation plan
python3 generate_implementation_plan.py
```

## Key Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Balance Score | 14/100 | 50/100 | **+37 points** |
| CV | 86.0% | 49.6% | **-36.4 pp** |
| Imbalance Ratio | 25.0x | 3.0x | **-22x** |
| Reps in Optimal Range | 0/8 | 1/8 | **+1** |

## Files Generated

- `accounts_rebalanced.csv` - New assignments
- `implementation_plan.csv` - 40 reassignments with reasons
- `rep_summaries.csv` - Per-rep impact
- `current_balance.png` - Revenue visualization
- `workload_utilization.png` - Capacity chart
- `territory_comparison.png` - Side-by-side comparison

## Tips

1. **Explore interactively**: Hover over charts for details
2. **Download data**: Use CSV download for implementation
3. **Share with stakeholders**: Screenshots or share the URL
4. **Customize**: Edit `territory_dashboard.py` for your needs

## Troubleshooting

**Port already in use?**
```bash
streamlit run territory_dashboard.py --server.port 8502
```

**Missing dependencies?**
```bash
pip3 install streamlit plotly pandas matplotlib
```

**Can't find streamlit command?**
```bash
python3 -m streamlit run territory_dashboard.py
```

## Next Steps

1. Review the Current State page for baseline
2. Check Proposed Changes for improvements
3. Download implementation plan from page 3
4. Share dashboard with team for review
5. Execute reassignments per timeline

---

**Questions?** See README.md for full documentation.
