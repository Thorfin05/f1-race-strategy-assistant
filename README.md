# 🏎️ F1 Race Strategy Assistant

An AI-powered Formula 1 race strategy analysis assistant that explores historical race data, evaluates pit-stop decisions, compares driver performance, and studies lap-time degradation.

**Repository:** [Thorfin05/f1-race-strategy-assistant](https://github.com/Thorfin05/f1-race-strategy-assistant)

## 📌 Project Overview

Formula 1 race strategy involves analysing several factors, including lap times, pit-stop windows, driver pace, and tyre performance.

This project aims to build a race strategy assistant that uses historical Formula 1 data and analytical techniques to understand race events and support strategy-related decisions.

The current development focuses on building a reliable historical data analysis foundation before integrating advanced AI capabilities.

## 🎯 Current Features

- **Historical F1 Data Analysis:** Store and analyse historical race information using SQLite.
- **Pit-Stop Analysis:** Examine pit-stop laps and stop durations.
- **Driver Pace Comparison:** Compare average lap times before and after pit stops.
- **Undercut Analysis:** Explore pit timing and potential strategic advantages.
- **Pit Window Comparison:** Compare pit-stop timing across drivers.
- **Lap-Time Degradation Analysis:** Estimate lap-time trends across race stints.
- **Robust Regression:** Use a Theil-Sen estimator to reduce the influence of unusual lap-time observations.
- **Data Validation:** Identify missing laps, timing anomalies, and potentially pit-affected laps.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and analysis |
| SQLite | Historical race database |
| Pandas | Data manipulation and analysis |
| FastF1 | Formula 1 data access and caching |
| Matplotlib | Data visualization |
| Git & GitHub | Version control |

## 🏗️ Project Structure

```text
f1-race-strategy-assistant/
│
├── data/
│   ├── raw/                  # Raw historical F1 datasets
│   └── cache/                # Local data cache (not committed)
│
├── reports/                  # Generated analysis reports
│
├── src/
│   ├── load_database.py
│   ├── inspect_database.py
│   ├── first_analytics.py
│   ├── undercut_analysis.py
│   ├── pit_window_comparison.py
│   ├── pace_comparison.py
│   ├── strategy_report.py
│   ├── tyre_degradation.py
│   ├── tyre_degradation_clean.py
│   ├── tyre_degradation_robust.py
│   ├── tyre_degradation_v2.py
│   ├── plot_tyre_degradation.py
│   └── validate_lap_times.py
│
├── check_drivers.py
├── .gitignore
└── README.md
```

*The structure above documents the development scripts; individual scripts may evolve as the project develops.*

## 📊 Case Study: 2023 Italian Grand Prix

The project uses the 2023 Italian Grand Prix at Monza as an initial case study.

Selected pit-stop records:

| Driver | Pit Lap | Pit Stop Duration |
|---|---:|---:|
| Max Verstappen | 20 | 24.228 s |
| Sergio Pérez | 21 | 23.819 s |
| Carlos Sainz | 19 | 25.183 s |
| Charles Leclerc | 20 | 23.931 s |

### Driver Pace Comparison

The analysis compares average lap times before and after each driver's pit stop.

| Driver | Pre-Stop Average | Post-Stop Average | Difference |
|---|---:|---:|---:|
| Verstappen | 86.481 s | 86.124 s | -0.358 s |
| Pérez | 86.648 s | 85.776 s | -0.872 s |
| Sainz | 87.519 s | 85.832 s | -1.686 s |
| Leclerc | 87.623 s | 85.827 s | -1.796 s |

A negative difference indicates that the average lap time was lower after the pit stop.

### Robust Lap-Time Degradation

A Theil-Sen regression approach is used to estimate lap-time trends within race stints.

Example estimated slopes:

| Driver | Stint 1 | Stint 2 |
|---|---:|---:|
| Verstappen | +0.024 s/lap | +0.034 s/lap |
| Pérez | +0.021 s/lap | +0.011 s/lap |
| Sainz | +0.091 s/lap | +0.044 s/lap |
| Leclerc | +0.094 s/lap | +0.035 s/lap |

These values represent estimated lap-time trends, not direct measurements of physical tyre wear.

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Thorfin05/f1-race-strategy-assistant.git
cd f1-race-strategy-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

### 4. Install dependencies

Install the packages required by the project:

```bash
pip install pandas matplotlib fastf1
```

If you maintain a `requirements.txt`, you can install the complete environment using:

```bash
pip install -r requirements.txt
```

### 5. Prepare the database

Place the required historical F1 source datasets in the expected data directory and run:

```bash
python src/load_database.py
```

### 6. Run an analysis

For example:

```bash
python src/first_analytics.py
python src/pace_comparison.py
python src/undercut_analysis.py
python src/tyre_degradation_robust.py
```

Run scripts from the project root directory.

## 🧠 Planned AI Capabilities

The long-term objective is to develop the project into a natural-language race strategy assistant.

Planned enhancements include:

- Retrieval-Augmented Generation (RAG) over historical race information and relevant documents.
- Natural-language questions about historical races.
- AI agent tool-calling for structured race-data analysis.
- Step-by-step strategy explanations.
- More advanced pit-stop strategy recommendations.
- Interactive race analysis dashboard.

These capabilities are planned extensions and are not represented as completed features.

## ⚠️ Current Limitations

- The current analysis is primarily based on historical race data.
- Tyre compound and tyre-age information are not available in the current SQLite database.
- Lap-time trends are affected by traffic, fuel load, weather, and other race conditions.
- Pit-in and pit-out lap boundaries require careful validation.
- Lap-time degradation estimates should not be interpreted as direct physical tyre-wear measurements.
- Strategy recommendations require further development and validation.

## 🚀 Future Roadmap

- [ ] Improve historical data validation.
- [ ] Build more reliable tyre degradation models.
- [ ] Add additional race and season comparisons.
- [ ] Develop a RAG-based race knowledge system.
- [ ] Integrate AI agent tool-calling.
- [ ] Build a natural-language strategy assistant.
- [ ] Develop an interactive dashboard.
- [ ] Evaluate strategy recommendations against historical race outcomes.

## 👨‍💻 Author

**Nirmal Raj D**

B.Tech – Artificial Intelligence and Data Science

Jerusalem College of Engineering, Chennai

GitHub: [@Thorfin05](https://github.com/Thorfin05)

---

*This project is an ongoing learning and development initiative exploring Formula 1 analytics, data engineering, and applied AI.*