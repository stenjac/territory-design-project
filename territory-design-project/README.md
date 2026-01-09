# Territory Design & Rebalancing System

A complete, production-ready territory optimization system that analyzes sales territories, identifies imbalances, and provides data-driven rebalancing recommendations with interactive visualizations.

![Territory Balance Comparison](https://img.shields.io/badge/Balance_Score-14→50-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 📊 Live Demo

Run the interactive dashboard:
```bash
streamlit run territory_dashboard.py
```

Then open http://localhost:8501 in your browser.

---

## 🎯 Problem Statement

Sales territories are often severely imbalanced, leading to:
- **Burnout** for overloaded reps (137% capacity utilization)
- **Underutilization** of underloaded reps (30% capacity)
- **Unfair compensation** (25x difference in territory potential)
- **Poor team morale** and high turnover

This system solves these issues through intelligent, constraint-based rebalancing.

---

## ✨ Key Features

### 🎨 Interactive Streamlit Dashboard
- **3-page web application** with real-time analysis
- **8 utilization gauges** showing capacity for each rep
- **Before/after comparison charts** with grouped bar visualizations
- **5 downloadable exports** (CSV, TXT) for implementation

### 🧮 Smart Rebalancing Algorithm
- **Protects customer relationships** (0 customers moved)
- **Balances revenue AND workload** simultaneously
- **Respects capacity constraints** (80-95% target utilization)
- **Provides clear business reasons** for each reassignment

### 📈 Realistic Capacity Modeling
- **208 available selling hours per quarter** (accounts for meetings, admin, PTO)
- **Different time requirements by account size** (Enterprise: 15 hrs, Small: 2 hrs)
- **Customer vs prospect multipliers** (1.3x for existing customers)
- **Configurable utilization targets**

### 📊 Comprehensive Analytics
- **Balance scoring system** based on Coefficient of Variation (CV)
- **Territory distribution metrics** (highest, lowest, ratio, CV)
- **Workload analysis** with capacity status per rep
- **Visual charts** (PNG exports for presentations)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/stenjac/territory-design-project.git
cd territory-design-project

# Install dependencies
pip install pandas matplotlib streamlit plotly
```

### Run the Dashboard

```bash
streamlit run territory_dashboard.py
```

The dashboard will open at http://localhost:8501

### Run Command-Line Tools

```bash
# Full territory analysis
python3 analyze_territories.py

# Capacity modeling
python3 capacity_calculator.py

# Run rebalancing algorithm
python3 rebalance_territories.py

# Compare before/after
python3 compare_territories.py

# Generate implementation plan
python3 generate_implementation_plan.py
```

---

## 📁 Project Structure

```
territory-design-project/
├── accounts.csv                        # Test data (200 accounts, 8 reps)
├── accounts_rebalanced.csv            # Optimized assignments
├── implementation_plan.csv            # Detailed reassignment list
├── rep_summaries.csv                  # Per-rep impact analysis
│
├── analyze_territories.py             # Comprehensive territory analysis
├── capacity_calculator.py             # Workload & capacity modeling
├── rebalance_territories.py           # Rebalancing algorithm
├── compare_territories.py             # Before/after comparison
├── generate_implementation_plan.py    # Implementation documentation
├── territory_dashboard.py             # Streamlit web dashboard
│
├── current_balance.png                # Revenue distribution chart
├── workload_utilization.png           # Capacity utilization chart
├── territory_comparison.png           # Side-by-side comparison
│
├── README.md                          # This file
├── QUICK_START.md                     # Quick reference guide
└── requirements.txt                   # Python dependencies
```

---

## 📊 Results

### Before Rebalancing (Poor Balance)
- **Balance Score**: 14/100 ❌
- **Coefficient of Variation**: 86.0%
- **Imbalance Ratio**: 25.0x
- **Reps in Optimal Range**: 0/8
- **Highest Territory**: $7.74M (Rep_1 at 137% capacity - burned out)
- **Lowest Territory**: $0.31M (Rep_8 at 30% capacity - underutilized)

### After Rebalancing (Moderate Balance)
- **Balance Score**: 50/100 ✅ (+37 points)
- **Coefficient of Variation**: 49.6% (-36.4 pp)
- **Imbalance Ratio**: 3.0x (-22x improvement)
- **Reps in Optimal Range**: 1/8 (+1)
- **Customers Moved**: 0 (all relationships protected)
- **Prospects Redistributed**: 40

---

## 🎓 Methodology

### Balance Scoring System

The system uses **Coefficient of Variation (CV)** to measure territory balance:

| CV Range | Score | Rating |
|----------|-------|--------|
| < 20% | 90-100 | Excellent Balance ⭐⭐⭐ |
| 20-30% | 70-89 | Good Balance ⭐⭐ |
| 30-50% | 50-69 | Moderate Imbalance ⭐ |
| > 50% | 0-49 | Poor Balance ❌ |

**CV = (Standard Deviation / Mean) × 100**

### Capacity Model (per quarter)

**Total Available Time:**
- 40 hrs/week × 13 weeks = 520 total hours

**Non-Selling Time Deductions (60%):**
- Meetings/Admin: 25% (130 hrs)
- Internal Work: 15% (78 hrs)
- PTO/Holidays: 10% (52 hrs)
- Deal Paperwork: 10% (52 hrs)

**Available Selling Time: 208 hours/quarter**

**Target Utilization: 80-95% (166-198 hours)**

### Time Per Account (quarterly)

| Account Size | Base Hours | Customer Multiplier |
|--------------|------------|---------------------|
| Enterprise | 15 hrs | 1.3x (19.5 hrs) |
| Large | 8 hrs | 1.3x (10.4 hrs) |
| Medium | 4 hrs | 1.3x (5.2 hrs) |
| Small | 2 hrs | 1.3x (2.6 hrs) |

**Prospect Multiplier: 1.0x** (standard prospecting effort)

### Rebalancing Algorithm

**Step 1: Lock Customers**
- All 160 customer accounts stay with current reps
- Protects established relationships

**Step 2: Sort Prospects**
- Sort 40 prospects by value (highest first)

**Step 3: Greedy Assignment**
- Assign highest-value prospects to lowest-potential reps
- Check capacity constraint (< 95% utilization)
- Repeat until balanced

**Step 4: Validate**
- Ensure no rep exceeds 95% capacity
- Calculate final balance score

---

## 📱 Dashboard Features

### Page 1: Current State
- **Balance Score Widget** with color coding (red/yellow/green)
- **Interactive Plotly charts** for potential and utilization
- **Metrics table** with status indicators (Optimal/Stretched/Overloaded)
- **Key insights**: CV, imbalance ratio, optimal range targets

### Page 2: Proposed Changes ⭐ NEW!
- **Grouped bar chart** comparing Current (red) vs Proposed (green)
- **8 utilization gauges** (one per rep) with target zones (80-95%)
- **Summary table** with before/after metrics and change percentages
- **Big improvement metrics** with deltas
- **Progress indicators** showing achievement vs 70/100 target
- **Improvement bar chart** (Balance Score, CV Reduction, Ratio Reduction)

### Page 3: Implementation ⭐ NEW!

**5 Download Options:**
1. **Implementation Plan (CSV)** - 40 reassignments with business reasons
2. **Rep Summaries (CSV)** - Per-rep impact analysis
3. **Complete Territory Assignments (CSV)** - CRM-ready export
4. **Comparison Metrics (CSV)** - Before/after summary
5. **Executive Summary (TXT)** - Ready-to-share report

**Additional Features:**
- Top 20 reassignments with reasons
- Rep-by-rep impact summaries
- Timeline suggestions (Weeks 1-4, Month 2)

---

## 🛠️ Advanced Usage

### Option 1: Customize Capacity Model

Edit `capacity_calculator.py`:

```python
# Adjust available hours
AVAILABLE_SELLING_HOURS = 180  # More conservative

# Change target utilization
MIN_UTILIZATION_PCT = 0.75  # 75%
MAX_UTILIZATION_PCT = 0.90  # 90%

# Modify account hours
BASE_HOURS = {
    'Enterprise': 20,  # More time for Enterprise
    'Large': 10,
    'Medium': 5,
    'Small': 2
}
```

### Option 2: Add Custom Constraints

Edit `rebalance_territories.py`:

```python
# Add geography constraint
if account['geography'] != rep_geography:
    continue  # Skip if different region

# Add industry expertise
if account['industry'] in rep_specializations:
    priority_bonus = 1.2  # Prefer matching expertise
```

### Option 3: Adjust Balance Scoring

Edit `analyze_territories.py`:

```python
def calculate_balance_score(cv):
    # More aggressive targets
    if cv < 15:  # Changed from 20
        return 100, "Excellent"
    # ... rest of function
```

---

## 📈 Performance Improvements

Current results achieve **50/100 balance score**. To improve further:

### Strategy 1: Allow Strategic Customer Moves
- Move low-risk customers (< 1 year tenure, < $100K value)
- Expected: **70-80/100 balance score**

### Strategy 2: Multi-Objective Optimization
- Use linear programming or genetic algorithms
- Optimize revenue + workload + account count simultaneously
- Expected: **60-75/100 balance score**

### Strategy 3: Geographic/Industry Clustering
- Add geography and industry fields
- Cluster accounts for travel efficiency and expertise match
- Expected: **Better win rates + efficiency**

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed strategies.

---

## 🧪 Testing with Your Data

### Step 1: Prepare Your Data

Create `accounts.csv` with these columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| account_name | string | Company name | "Acme Corp" |
| account_size | enum | Small/Medium/Large/Enterprise | "Enterprise" |
| current_owner | string | Current rep name | "Rep_1" |
| estimated_annual_value | float | Annual revenue potential | 450000 |
| customer_status | enum | Customer/Prospect | "Customer" |

### Step 2: Run Analysis

```bash
python3 analyze_territories.py
python3 rebalance_territories.py
python3 compare_territories.py
```

### Step 3: Review Results

```bash
streamlit run territory_dashboard.py
```

---

## 📚 Documentation

- **README.md** - This file (comprehensive documentation)
- **QUICK_START.md** - Quick reference guide for running tools
- **Code Comments** - Detailed docstrings in all Python files

---

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

1. **Add geographic clustering** for travel optimization
2. **Implement industry specialization** matching
3. **Create unit tests** for algorithms
4. **Add CI/CD pipeline** with GitHub Actions
5. **Build API endpoint** for integration with CRM systems
6. **Add machine learning** for predictive territory design

---

## 📄 License

MIT License - feel free to use this for commercial or personal projects.

---

## 🏆 Use Cases

This system is perfect for:

- **Sales Operations Teams** - Balance territories across sales reps
- **Revenue Operations** - Optimize account distribution
- **Territory Planning** - Design new territory structures
- **Sales Leadership** - Identify capacity issues and fix imbalances
- **Customer Success** - Balance CSM workloads
- **Account Management** - Distribute accounts fairly

---

## 💡 What This Demonstrates

This project showcases:

✅ **Data-driven decision making** with quantitative balance scoring
✅ **Constraint optimization** respecting business rules
✅ **Realistic modeling** of sales capacity and workload
✅ **Production-ready code** with comprehensive documentation
✅ **Interactive visualization** for stakeholder communication
✅ **Practical implementation** with detailed execution plans

Perfect for **Sales Operations**, **Revenue Operations**, or **Territory Planning** roles!

---

## 📞 Contact

Questions? Feedback? Suggestions?

- Open an issue on GitHub
- Submit a pull request
- Star this repo if you find it useful!

---

## 🙏 Acknowledgments

Built with:
- **Python** - Core language
- **Pandas** - Data manipulation
- **Matplotlib** - Static visualizations
- **Plotly** - Interactive charts
- **Streamlit** - Web dashboard framework

---

**⭐ Star this repo if you found it helpful!**

---

## Screenshots

### Dashboard - Current State
![Current State](docs/screenshots/current-state.png)

### Dashboard - Proposed Changes
![Proposed Changes](docs/screenshots/proposed-changes.png)

### Dashboard - Implementation Plan
![Implementation](docs/screenshots/implementation.png)

---

*Last Updated: January 2026*
