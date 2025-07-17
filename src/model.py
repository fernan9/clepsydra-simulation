import numpy as np
import random
import csv
import matplotlib.pyplot as plt

class FoodCup:
    def __init__(self, creation_day, food=30.0, fly_daily_rate = 0.00001):
        self.creation_day = creation_day  # Day this cup was added
        self.food = food                  # Initial food (grams)
        self.spent = False
        self.fly_daily_rate = fly_daily_rate          # standard day consumption per fly
        self.flies_ID = []

    def deplete(self):
        self.food -= self.fly_daily_rate * len(self.flies_ID)
        self.food = max(0, self.food)
        if self.food == 0:
            self.spent = True

    def hold(self, new_fly_ID):
        self.flies_ID.append(new_fly_ID)

    
class Drosophila:
    # ID zero is only for founding population
    _next_id = 1

    def __init__(self, 
                 bday, 
                 age=0, 
                 genotype=None, 
                 motherID = 0,
                 fatherID = 0,
                 spermatheque=None, 
                 mating_threshold = 1.0):
        # class variable that increments with each fly

        ''' Set initial values'''
        self.alive = True  # Track viability
        self.genotype = genotype or self._wildtype_genotype()
        self.mating_threshold = mating_threshold
        self.bday = bday
        self.dday = None
        self.mated = False
        self.age = age
        ''' ID handling '''
        self.id = Drosophila._next_id
        Drosophila._next_id += 1
        self.fatherID = fatherID
        self.motherID = motherID
        
        '''Define stages and age'''
        if self.age == 0:    # Tracks time in current stage
            self.stage = "egg"
        elif self.age == 2:
            self.stage = "larva"
        elif self.age == 10:
            self.stage = "immature"
        elif self.age == 12:
            self.stage = "adult"
        else:
            raise ValueError("Stage provided is not valid.")

        #female spescific attributes
        if self.genotype["sex"] == 1:   # sex locus = 1: female
            self.spermatheque = []
            self.fecund = False
        else:                           # sex locus = 0: male
            self.spermatheque = None
            self.fecund = None


    def _wildtype_genotype(self):
        # will be good to adjust later for a bitmask: Pack into a single integer (e.g., 0b101 = sex=1, lethal=0, vigor=1).
        return {
            "sex": np.random.choice([0, 1]),                # SEX locus: 0 for male. 1 for female.
            "transgenic-lethal": 0 ,  # Sterility locus: 0 for wildtype. 1 for transgenic.
            "receptivity-vigor": np.random.random()                # Receptivity-vigor locus: float between 1 and 0.  
        }
    
    def transgenic_male(self):
        # will be good to adjust later for a bitmask: Pack into a single integer (e.g., 0b101 = sex=1, lethal=0, vigor=1).
        return {
            "sex": 0,                # SEX locus: 0 for male. 1 for female.
            "transgenic-lethal": 1 ,  # Sterility locus: 0 for wildtype. 1 for transgenic.
            "receptivity-vigor": np.random.random()                # Receptivity-vigor locus: float between 1 and 0.  
        }

    def update(self):
        """Update age and transition stages at predefined thresholds."""
        self._transition_stage()
        self._transgenic_lethality()
        self.age += 1

    def _transgenic_lethality(self):
        """Kill transgenic-lethal embryos."""
        if (self.stage == "egg" and 
            self.genotype["transgenic-lethal"] == 1 and 
            np.random.random() < 0.97):  # 97% penetrance
            self.alive = False
        
    def cull (self):
        self.alive = True

    def _transition_stage(self):
        if self.stage == "egg" and self.age >= 1:  # Eggs hatch after 5 timesteps
            self.stage = "larva"
        elif self.stage == "larva" and self.age >= 10:  # Larvae mature after 10 timesteps
            self.stage = "immature"
        elif self.stage == "immature" and self.age >= 12:  # Larvae mature after 10 timesteps
            self.stage = "adult"
            self.fertile = True

    def cross(self, male):
        ''' Female exclusive trait'''
        # Female mates with male if combined receptivity-vigor exceeds threshold
        new_receptivity = self.genotype["receptivity-vigor"] # multiply by a factor of age dependent fecundity
        new_vigor = male.genotype["receptivity-vigor"]

        if  (self.genotype["sex"] == 1 and  # Ensure female
            male.genotype["sex"] == 0 and  # Ensure male
            new_receptivity+new_vigor > self.mating_threshold):
            self.fecund = True
            self.spermatheque.append(male.genotype)            # append at tail, pop for oviposition
            self.spermatheque.pop()

    def oviposition(self):
        ''' Female exclusive trait'''
        # Lay one egg using the last male's genotype (Mendelian inheritance with mutation)
        if not self.spermatheque or not self.fecund:
            return None
        
        # Get parental genotypes
        male_genotype = self.spermatheque[-1]  # Last mating partner
        female_genotype = self.genotype
        
        # Mendelian inheritance with possible mutation
        offspring_genotype = {
            "sex": np.random.choice([0, 1]),  # Random sex determination
            "transgenic-lethal": male_genotype["transgenic-lethal"],
            "receptivity-vigor": self._inherit_allele(female_genotype["receptivity-vigor"],
                                        male_genotype["receptivity-vigor"])
        }
        return offspring_genotype

    def _inherit_allele(self, mother_allele, father_allele, mutation_rate=0.001):
        """Randomly choose one parental allele with possible mutation."""
        allele = np.random.choice([mother_allele, father_allele])
        return allele # if np.random.random() > mutation_rate else 1 - allele

class PopulationMaintenance:
    def __init__(self):
        self.report_data = {
            'date': [],
            'N': [],
            'genotype_freqs': [],  # Dict: {genotype_hash: count}
            'mating_events': [],
            'age_dist': []  # Binned ages
        }
    
    def record(self, experiment_population, date):
        adults = [f for f in experiment_population if f.stage == 'adult']
        self.daily_data['date'].append(date)
        self.daily_data['N'].append(len(adults))
        
        # Genotype frequency (using hash for dictionary keys)
        freqs = {}
        for ind in adults:
            ghash = hash(frozenset(ind.genotype.items()))
            freqs[ghash] = freqs.get(ghash, 0) + 1
        self.daily_data['genotype_freqs'].append(freqs)
        
        # Mating stats
        mated = sum(1 for f in adults if f.sex==1 and f.mates)   # sex is not handled properly
        self.daily_data['mating_events'].append(mated)
        
        # Age distribution (10-day bins)
        self.daily_data['age_dist'].append(
            np.histogram([f.age for f in adults], bins=range(0,100,10))[0])

class Experiment:
    def __init__(self,
                p_daily = 0.1,
                pop_size = 30, 
                clutch_size = 5,
                consumption_rate = 0.00001,
                release_dates = None, 
                release_sizes = None,
                food_init_dates = None,
                food_shelf_life = None):
        # begin setup
        self.day = 0
        self.p_daily = p_daily
        self.clutch_size = clutch_size
        self.consumption_rate = consumption_rate
        # global populations, alive and dead
        self.population = []
        self.morgue = []
        # handling of food
        self.food_schedule = []     # a list of dates for cups to arrive
        # lists of foodcups
        self.active_food_cups = []
        self.spent_food_cups = [] 
        # data logging
        self.daily_data = []  # Store daily logs: [day, total, males, females]
        
        # initialize population
        for _ in range(pop_size):
            self.population.append(Drosophila(bday = self.day, age = 12))  # always initialize with adults

        if release_dates is not None:
            # check for inconsistencies
            if release_sizes is None:
                raise ValueError("Both release_dates and release_sizes must be provided if one is given.")
            
            if len(release_dates) != len(release_sizes):
                raise ValueError("release_dates and release_sizes must be of the same length.")
                
            # Store release schedule (day: size)
            self.release_schedule = dict(zip(release_dates, release_sizes))

        # Initialize food schedule
        if food_init_dates is not None:
            if food_shelf_life is None:
                raise ValueError("food_init_dates, and food_shelf_life must all be provided.")
            if len(food_init_dates) != len(food_shelf_life):
                raise ValueError("Food scheduling vectors must have the same length.")
            
            # Store food events as tuples: (start_day, end_day, size)
            self.food_schedule = list(zip(food_init_dates, food_shelf_life))
            
            # Add initial food cups (if any start on day 0)
            #for start, _  in self.food_schedule:
            #    if start == 0:
            #        self.active_food_cups.append(FoodCup(creation_day=0))
    
    def update_day(self):
        ''' update flies'''
        # update flies in population
        for fly in self.population:
            # update emerged flies and egg, larvae in active cups
            #if fly.age > 10 or fly.id in self.active_food_cups:
            fly.update()
        # mortality round
        self.mortality_round()
        ''' update cups'''
        for start, shelf_life  in self.food_schedule:
            # update cups, deplete if time is true
            if len(self.active_food_cups) > 0:
                for cup in self.active_food_cups:
                    cup.deplete()
                    # retire cup if it has expired or spent
                    if self.day == cup.creation_day + shelf_life or cup.spent == True:
                        spent_cup = self.active_food_cups.pop()
                        self.spent_food_cups.append(spent_cup)
                        # cull flies on spent cup
                        for fly_id in spent_cup.flies_ID:
                            for fly in self.population:
                                if (fly.id == fly_id and fly.age < 10):
                                    fly.alive = False  # Mark for removal
                                    break  # Exit inner loop once found
                    
            # add a cup if on schedule
            if start == self.day:
                self.active_food_cups.append(FoodCup(creation_day=self.day, fly_daily_rate = self.consumption_rate))
        
        '''move dead flies to morgue'''
        daily_mortality = [fly for fly in self.population if not fly.alive]
        daily_adult_mortality = [fly for fly in self.population if not fly.alive and fly.age > 9]
        daily_mortality_census = len(daily_adult_mortality)
        self.morgue.extend(daily_adult_mortality)

        # clear experimental population for alive flies only
        self.population = [fly for fly in self.population if fly.alive]

        #### on this stage the flies alive should remain and the rest should be on the morgue
        
        ''' release transgenic males'''
        # Check if a release is scheduled for the current day
        if hasattr(self, 'release_schedule') and self.day in self.release_schedule:
            for _ in range(self.release_schedule[self.day]):
                self.population.append(Drosophila(bday = self.day,
                                                  stage="adult", 
                                                  genotype={"sex":1, 
                                                            "transgenic-lethal": 1, 
                                                            "receptivity-vigor": np.random.random()}))

        ''' cross cycle'''
        # mate flies in population
        # separate males from females that are adults
        self.temp_males = [fly for fly in self.population 
                          if (fly.genotype["sex"] == 0
                          and fly.stage == "adult")]
        
        self.temp_females = [fly for fly in self.population
                            if (fly.genotype["sex"] == 1 
                            and fly.stage == "adult")]
        
        # round across all females
        for fem in self.temp_females:
            if not self.temp_males:
                break
            if fem.fecund: # potential multiple mating section
                break
            male = self.temp_males[0]
            fem.cross(male)
            random.shuffle(self.temp_males)
        # optional counts in the future
        # In __init__:
        # self.mating_count = 0
        # In cross():
        # self.mating_count += 1
        ''' oviposition cycle'''
        random.shuffle(self.temp_females)
        if len(self.active_food_cups) > 0:
            for fem in self.temp_females:
                # random chance above 0.5 
                for _ in range(self.clutch_size):
                    if np.random.random() > 0.5:
                        embryo_genotype = fem.oviposition()
                        new_fly = Drosophila(bday = self.day, genotype=embryo_genotype)
                        self.population.append(new_fly)
                        random.shuffle(self.active_food_cups)
                        self.active_food_cups[0].hold(new_fly.id)

        ''' documentation cycle'''
        #print(f"pop size: {len(self.population)}")
        #print(f"morgue size: {len(self.morgue)}")
        #print(f"End of day: {self.day}")

        '''complete day'''
        self.log_data(daily_mortality_census)  # Record data before incrementing day
        self.day += 1

    def mortality_round(self):
        for fly in self.population:
            if fly.alive:
                # Check if the fly dies today based on age-independent probability
                if np.random.random() < self.p_daily:
                    fly.alive = False

    def add_transgenic_males(self, count):
        """Release transgenic males into the population. PENDING"""
        transgenic_male_genotype = {
            "sex": 0,                # SEX locus: 0 for male. 1 for female.
            "transgenic-lethal": 1 ,  # Sterility locus: 0 for wildtype. 1 for transgenic.
            "receptivity-vigor": np.random.random()                # Receptivity-vigor locus: float between 1 and 0.  
        }
        for _ in range(count):
            self.population.append(Drosophila(bday = self.day, 
                                              stage="adult", 
                                              genotype=transgenic_male_genotype))
    
    def log_data(self, mortality_counts):
        """Record daily population stats (total, males, females)."""
        adults = [fly for fly in self.population if fly.stage == "adult"]
        males = sum(1 for fly in adults if fly.genotype["sex"] == 0)
        females = sum(1 for fly in adults if fly.genotype["sex"] == 1)
        self.daily_data.append([self.day, len(adults), males, females, mortality_counts])
    
    def save_to_csv(self, filename="population_data.csv"):
        """Save daily logs to a CSV file."""
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Day", "Total", "Males", "Females"])
            writer.writerows(self.daily_data)
        print(f"Data saved to {filename}")

    def plot_population(self):
        """Plot population trends over time."""
        days = [row[0] for row in self.daily_data]
        total = [row[1] for row in self.daily_data]
        males = [row[2] for row in self.daily_data]
        females = [row[3] for row in self.daily_data]
        total_deaths = [row[4] for row in self.daily_data]

        plt.figure(figsize=(10, 6))
        plt.plot(days, total, label="Total", linestyle="-", color="black")
        plt.plot(days, males, label="Males", linestyle="--", color="blue")
        plt.plot(days, females, label="Females", linestyle="--", color="red")
        plt.plot(days, total_deaths, label="Adult mortality", linestyle="dotted", color="gray")
        plt.xlabel("Day")
        plt.ylabel("Population")
        plt.title("Drosophila Population Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()

    def mortality_census_fit_data(self):
        # extract the vector of adult mortality
        mortality_census = [row[4] for row in self.daily_data]
        # aggregate weekly deaths
        weekly_mortality_census = []
        for i in range(0, len(mortality_census), 7):
            group = mortality_census[i:i+7]          # Extract group of 7 elements
            weekly_mortality_census.append(sum(group)) # Sum the group
        # extract the final adult population
        final_adult_census = [row[1] for row in self.daily_data][-1]
        # add final population to last mortality count
        weekly_mortality_census[-1] += final_adult_census

        return weekly_mortality_census
