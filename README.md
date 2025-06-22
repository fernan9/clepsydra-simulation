# Drosophila Population Dynamics Simulator

An agent-based model simulating transgenic male releases in cage systems with:
- Age-structured populations
- Food-limited dynamics
- Genetic tracking

## Installation
```bash
pip install -r requirements.txt
```
## Project Structure
```bash
clepsydra-simulation/
├── src/                      # Main simulation code
│   ├── model.py              # Core classes (FoodCup, Larva, Adult, Experiment)
│   ├── run_simulation.py     # Example simulation script
│   └── analysis.py           # Data analysis/visualization (optional)
├── data/                     # Input/Output data
│   ├── census_data.csv       # Empirical census data (for calibration)
│   └── poolseq/              # Pool-seq allele frequencies (time points)
├── config/                   # Parameter files
│   └── params.yaml           # Simulation parameters (mortality, food, etc.)
├── results/                  # Outputs
│   ├── plots/                # Population trajectory plots
│   └── Ne_estimates.csv      # Effective population size calculations
└── README.md                 # This file
```
## Development Log
- **2025-06-22**: Implemented core `Drosophila` class with genotype tracking
- **2025-06-21**: Added FoodCup dynamics with larval development
