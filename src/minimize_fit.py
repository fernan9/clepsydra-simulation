import numpy as np
from model import Drosophila, FoodCup, Experiment
from scipy.optimize import minimize
from pathlib import Path
import pandas as pd
import os

# Set working directory to your project root
os.chdir("C:/Users/fr_pe/OneDrive/Documents/05-PROYECTOS/03-EvolutionaryResponse/clepsydra-simulation")

# Now you can import your model
from model import Drosophila, FoodCup, Experiment

# Load your data
csv_path = os.path.join("data", "Experimental evolution-DSPR-census.csv")
df = pd.read_csv(csv_path)

# Pivot to get 22 weeks x 8 populations
pivoted = df.pivot(index='week', columns='cage', values='census')
# Convert to 8 lists (each with 22 weeks)
population_lists = [pivoted[i].tolist() for i in pivoted.columns]
# print(f"Population 1 (Weeks 1-3): {population_lists[0][:3]}")
data_Census = population_lists[0]

def objective(params, experimental_data):

    """Calculate error between model and experimental mortality data."""
    p_daily, pop_size, clutch_size, consumption_rate = params
    
    # Create experiment with current parameters
    experiment = Experiment(
        p_daily=float(p_daily),
        pop_size=int(pop_size),
        clutch_size=int(clutch_size),
        consumption_rate=float(consumption_rate),
        food_init_dates=list(range(0, 154, 7)),  # 22 weeks (154 days)
        food_shelf_life=[14]*22  # 2-week shelf life
    )
    
    # Run simulation for 22 weeks (154 days)
    for _ in range(154):
        experiment.update_day()
    
    model_output = experiment.mortality_census_fit_data()

    # Compare model output to experimental data
    # Calculate MSE (ensure same lengths)
    min_length = min(len(model_output), len(experimental_data))
    mse = np.mean((np.array(model_output[:min_length]) - np.array(experimental_data[:min_length])) ** 2)
    return mse

initial_guess = [0.1, 300, 5, 0.00001]  # Initial p_daily, fly_daily_rate
result = minimize(
    fun=objective,
    x0=initial_guess,
    args=(data_Census),
    bounds=[(0.01, 0.5), 
            (50, 300),
            (1, 5),
            (0.000001, 0.0001)],  # Parameter constraints
    method="L-BFGS-B",  # Handles bounds
    options={'maxiter': 100, 'disp': True}
)
print("Optimized parameters:", result.x)