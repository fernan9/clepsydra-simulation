import numpy as np

class FoodCup:
    def __init__(self, creation_day, food=30.0, fly_daily_rate = 0.05):
        self.creation_day = creation_day  # Day this cup was added
        self.food = food                  # Initial food (grams)
        self.spent = False
        self.fly_daily_rate = fly_daily_rate          # standard day consumption per fly
    
    def getCreationDay(self):
        return self.creation_day

    def deplete(self, immatures = 0):
        self.food -= self.fly_daily_rate * immatures
        self.food = max(0, self.food)
        if self.food == 0:
            self.spent = True


    
class Drosophila:
    def __init__(self, stage="egg", genotype=None, spermatheque=None, mating_threshold = 1.0, food_cup_ID = FoodCup.getCreationDay()):
        
        ''' Set initial values'''
        self.alive = True  # Track viability
        self.genotype = genotype or self._wildtype_genotype()
        mating_threshold = mating_threshold
        
        '''Define stages and age'''
        self.stage = stage  # "egg", "larva", "immature", "adult"
        if self.stage == "egg":
            self.age = 0    # Tracks time in current stage
        elif self.stage == "larva":
            self.age = 2
        elif self.stage == "immature":
            self.age = 10
        elif self.stage == "adult":
            self.age = 12
        else:
            raise ValueError("Stage provided is not valid.")

        self.food_cup_ID = food_cup_ID
        ''' Still missing how to handle food cups ID'''

## add IDs to flies to have an array to modify

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
            "receptivity-vigor": np.random()                # Receptivity-vigor locus: float between 1 and 0.  
        }

    def update(self):
        """Update age and transition stages at predefined thresholds."""
        self._transition_stage()
        self._transgenic_lethality()
        self._mortality_die()
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
        """Female mates with male if combined receptivity-vigor exceeds threshold."""
        new_receptivity = self.genotype["receptivity-vigor"] # multiply by a factor of age dependent fecundity
        new_vigor = male.genotype["receptivity-vigor"]

        if  (self.genotype["sex"] == 1 and  # Ensure female
            male.genotype["sex"] == 0 and  # Ensure male
            new_receptivity+new_vigor > self.mating_threshold):
            self.fecund = True
            self.spermatheque.append(male.genotype)            # append at tail, pop for oviposition
            self.spermatheque.pop()

    def oviposition(self):
        """Lay one egg using the last male's genotype (Mendelian inheritance with mutation)."""
        if not self.spermatheque or not self.fecund:
            return None
        
        # Get parental genotypes
        male_genotype = self.spermatheque[-1]  # Last mating partner
        female_genotype = self.genotype
        
        # Mendelian inheritance with possible mutation
        offspring_genotype = {
            "sex": np.random.choice([0, 1]),  # Random sex determination
            "transgenic-lethal": self._inherit_allele(female_genotype["transgenic-lethal"], 
                                                    male_genotype["transgenic-lethal"]),
            "receptivity-vigor": self._inherit_allele(female_genotype["receptivity-vigor"],
                                        male_genotype["receptivity-vigor"])
        }
        return offspring_genotype

    def _inherit_allele(self, mother_allele, father_allele, mutation_rate=0.001):
        """Randomly choose one parental allele with possible mutation."""
        allele = np.random.choice([mother_allele, father_allele])
        return allele # if np.random.random() > mutation_rate else 1 - allele

class PopulationTracker:
    def __init__(self):
        self.daily_data = {
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
    def __init__(
        self, 
        pop_size = 10, 
        release_dates = None, 
        release_sizes = None,
        food_init_dates = None,
        food_shelf_life = None
    ):
        self.day = 0
        self.population = []          # Global adult population
        self.morgue = []
        self.active_food_cups = []
        self.spent_food_cups = []
        self.food_schedule = []
        
        # initialize population
        for _ in range(pop_size):
            self.population.append(Drosophila(stage="adult"))  # always initialize with adults

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
            for start, _ , _ in self.food_schedule:
                if start == 0:
                    self.active_food_cups.append(FoodCup(creation_day=0))
    
    def update_day(self):
        
        # update flies in population
        for fly in self.population:
            "update emerged flies and egg, larvae in active cups"
            if fly.age > 10 or fly.ID in self.active_food_cups:
                fly.update()
        # mortality round
        self.mortality_round()
        # move dead flies to morgue
        self.morgue.extend([fly for fly in self.population if not fly.alive])
        # clear experimental population for alive flies only
        self.population = [fly for fly in self.population if fly.alive]

        # update cups
        for start, shelf_life  in self.food_schedule:
            "update cups, deplete if time is true"
            for cup in self.active_food_cups:
                cup.deplete()
                "retire cup if it has expired or spent"
                if self.day == cup.creation_day + shelf_life or cup.spent == True:
                    self.spent_food_cups.append() = self.active_food_cups.pop()
            "add a cup if on schedule"
            if start == self.day:
                self.active_food_cups.append(FoodCup(creation_day=self.day))


        #### on this stage the flies alive should remain and the rest should be on the morgue
        
        # release transgenic males
        # Check if a release is scheduled for the current day
        if hasattr(self, 'release_schedule') and self.day in self.release_schedule:
            for _ in range(self.release_schedule[self.day]):
                self.population.append(Drosophila(stage="adult", 
                                                  genotype={"sex":1, 
                                                            "transgenic-lethal": 1, 
                                                            "receptivity-vigor": np.random.random()}))

        # mate flies in population

        # female fly oviposition round
        # sample from the female pool with replacement
        # one round would be the number sample drawings equal to the complete female fertile population
        # this is the key parameter to estimate in the sum of squares adjustment to data
        # the number of rounds is important for simulation, but the actual reproductive output should be recorded daily
        # with the reproductive output and knowing the maternal lineage you can calculate the effective population size

        # complete day
        self.day += 1

    def mortality_round(self):
        for fly in self.flies:
            if fly.alive:
                # Check if the fly dies today based on age-independent probability
                if np.random.random() < self.p_daily:
                    fly.alive = False

    def add_transgenic_males(self, count):
        """Release transgenic males into the population."""
        for _ in range(count):
            self.adults.append(Adult(genotype="transgenic"))