import numpy as np

class FoodCup:
    def __init__(self, creation_day, food=30):
        self.creation_day = creation_day  # Day this cup was added
        self.food = food                  # Initial food (grams)
        self.eggs = []                    # List of (lay_day, genotype)
        self.larvae = []                  # List of Larva objects
    
    def add_eggs(self, day, genotype, count):
        """Log eggs laid on a specific day (only first 4 days matter)."""
        if day <= self.creation_day + 4:  # Critical 4-day window
            self.eggs.extend([(day, genotype)] * count)
    
    def update(self, current_day):
        """Update food, hatch eggs, and cull larvae."""
        # 1. Food depletion by larvae
        self.food -= 0.5 * len(self.larvae)
        self.food = max(0, self.food)
        
        # 2. Hatch eggs into larvae (10-day development)
        new_larvae = [
            Larva(genotype, lay_day) 
            for (lay_day, genotype) in self.eggs 
            if current_day - lay_day == 10
        ]
        self.larvae.extend(new_larvae)
        
        # there was a step for culling larvae from day 4 onwards but it was removed
        # this is because the larvae must continue eating from the cup and exhaust the food
        # food cunsumption should be adjusted, perhaps just for dry mass balance
        # meaning, get the dry mass of food cup 30g, then use the dry mass per fly, adjust
        
        # 3. Metamorphose larvae into adults
        new_adults = [
            Adult(larva.genotype) 
            for larva in self.larvae if larva.age >= 3
        ]
        self.larvae = [larva for larva in self.larvae if larva.age < 3]
        
        return new_adults
    
class Drosophila:
    def __init__(self, stage="egg", genotype=None, spermatheque=None, mating_threshold = 1):
        self.stage = stage                                     # "egg", "larva", "immature", "adult"
        self.genotype = genotype or self._random_genotype()
        mating_threshold = mating_threshold
        self.age = 0  # Tracks time in current stage
        self.alive = True  # Track viability

        #female spescific attributes
        if self.genotype["sex"] == 1:   # sex locus = 1: female
            self.spermatheque = []
            self.fecund = False
        else:                           # sex locus = 0: male
            self.spermatheque = None
            self.fecund = None


    def _random_genotype(self):
        # will be good to adjust later for a bitmask: Pack into a single integer (e.g., 0b101 = sex=1, lethal=0, vigor=1).
        return {
            "sex": np.random.choice([0, 1]),                # SEX locus: 0 for male. 1 for female.
            "transgenic-lethal": np.random.choice([0, 1]),  # Sterility locus: 0 for wildtype. 1 for transgenic.
            "receptivity-vigor": np.random()                # Receptivity-vigor locus: float between 1 and 0.  
        }

    def update(self):
        """Update age and transition stages at predefined thresholds."""
        self._transition_stage()
        self._check_viability()
        self.age += 1
    
    def _check_viability(self):
        """Kill transgenic-lethal embryos."""
        if (self.stage == "egg" and 
            self.genotype["transgenic-lethal"] == 1 and 
            np.random.random() < 0.97):  # 97% penetrance
            self.alive = False

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
        new_receptivity = self.genotype^["receptivity-vigor"] # multiply by a factor of age dependent fecundity
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
        self.fecund = False  # Reset until next mating
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
    
    def record(self, population, date):
        adults = [f for f in population if f.stage == 'adult']
        self.daily_data['date'].append(date)
        self.daily_data['N'].append(len(adults))
        
        # Genotype frequency (using hash for dictionary keys)
        freqs = {}
        for ind in adults:
            ghash = hash(frozenset(ind.genotype.items()))
            freqs[ghash] = freqs.get(ghash, 0) + 1
        self.daily_data['genotype_freqs'].append(freqs)
        
        # Mating stats
        mated = sum(1 for f in adults if f.sex==1 and f.mates)
        self.daily_data['mating_events'].append(mated)
        
        # Age distribution (10-day bins)
        self.daily_data['age_dist'].append(
            np.histogram([f.age for f in adults], bins=range(0,100,10))[0])

class ClepsydraExperiment:
    def __init__(self):
        self.day = 0
        self.cups = [FoodCup(0)]  # Start with 1 cup, on day 0
        self.adults = []          # Global adult population
    
    def update_day(self):
        self.day += 1
        
        # 1. Update all cups, get new adults
        new_adults = []
        for cup in self.cups:
            new_adults.extend(cup.update(self.day))
        self.adults.extend(new_adults)
        
        # 2. Replace oldest cup every 14 days
        if self.day % 14 == 0:
            self.cups.pop(0)
            self.cups.append(FoodCup(self.day))
        
        # 3. Adults lay eggs in newest cup (first 4 days only)
        if self.cups[-1].creation_day + 4 >= self.day:
            for adult in self.adults:
                if adult.sex == "female" and adult.mature:
                    self.cups[-1].add_eggs(
                        day=self.day,
                        genotype=adult.genotype,
                        count=np.random.poisson(20)  # Clutch size
                    )
        
        # 4. Apply adult mortality (genotype-specific)
        self.adults = [
            adult for adult in self.adults 
            if random.random() > (0.1 if adult.genotype == "transgenic" else 0.02)]
    
    def add_transgenic_males(self, count):
        """Release transgenic males into the population."""
        for _ in range(count):
            self.adults.append(Adult(genotype="transgenic"))