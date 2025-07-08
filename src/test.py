# Import your classes (assuming they're in the same file)
import numpy as np
import random
from model import Drosophila, FoodCup, Experiment

# Create weekly food schedule (every 7 days)
max_days = 300
exp_init_dates = list(range(0, max_days + 1, 7))  # [0, 7, 14, ..., 196]
exp_shelf_life = [14] * len(exp_init_dates)     # [14, 14, 14, ...]

# Initialize the experiment
experiment = Experiment(
    pop_size=300,  # Start with 10 adult flies
    food_init_dates=exp_init_dates,
    food_shelf_life=exp_shelf_life  # Each cup lasts 10 days
)

# Run the experiment for 20 days
for day in range(max_days):
    print(f"\n=== Day {day} ===")
    experiment.update_day()
    
    # Print detailed population stats
    #adults = [fly for fly in experiment.population if fly.stage == "adult"]
    #eggs_larvae = [fly for fly in experiment.population if fly.stage in ["egg", "larva"]]
    
    #print(f"Total population: {len(experiment.population)}")
    #print(f"Adults: {len(adults)} (Males: {sum(1 for f in adults if f.genotype['sex'] == 0)}, Females: {sum(1 for f in adults if f.genotype['sex'] == 1)})")
    #print(f"Eggs/Larvae: {len(eggs_larvae)}")
    #print(f"Active food cups: {len(experiment.active_food_cups)}")
    #print(f"Spent food cups: {len(experiment.spent_food_cups)}")

# Save and plot data
experiment.save_to_csv()
experiment.plot_population()