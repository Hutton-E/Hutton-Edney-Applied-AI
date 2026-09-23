import random
import math
from entities import Gatherer
from config import *

class GeneticAlgorithm:
    def __init__(self):
        self.generation = 1
        self.fitness_history = []
        self.trait_history = []  # Track trait averages over generations
    
    def create_initial_population(self):
        population = []
        for _ in range(INITIAL_POPULATION):
            gatherer = Gatherer()
            population.append(gatherer)
        return population
    
    def evaluate_fitness(self, population):
        fitness_scores = []
        for gatherer in population:
            fitness = gatherer.calculate_fitness()
            fitness_scores.append((gatherer, fitness))
        
        # Sort by fitness (highest first)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        return fitness_scores
    
    def select_survivors(self, fitness_scores):
        # STUDENT ASSIGNMENT 3: Implement a better selection mechanism
        # Current version just takes top 50% - very simple!
        #
        # Available information:
        # - fitness_scores: list of (gatherer, fitness) tuples, sorted by fitness (best first)
        # - SURVIVAL_RATE: currently 0.05 (top 5% survive)
        # - len(fitness_scores): total population size
        #
        # Alternative selection strategies to consider:
        # 1. Tournament selection: pick random groups, take best from each
        # 2. Roulette wheel: probability proportional to fitness
        # 3. Rank-based: select based on rank, not raw fitness values
        # 4. Elite + random: guarantee best survive, then random selection
        # 5. Fitness-proportionate with scaling (linear/exponential)
        # 6. Hybrid approaches: combine multiple strategies
        #
        # Strategy hints:
        # - Pure elitism (current) can cause premature convergence
        # - Pure randomness loses good solutions
        # - Tournament selection often works well (simple + effective)
        # - Consider selection pressure: too high = less diversity, too low = slow evolution
        #
        # Remember: Selection determines which traits get passed to next generation!
        
        ELITE = 0.10
        SURVIVAL_FRACT = 0.50
        total = len(fitness_scores)
        num_survs = max(2, int(total * SURVIVAL_FRACT))
        num_elite = max(1, int(total * ELITE))

        ranked = [gatherer for gatherer, fitness in fitness_scores]  # best first
        elites = ranked[:num_elite]
        remain = ranked[num_elite:] # everyone below the elites
        num_rand = max(0, min(len(remain), num_survs - num_elite))

        # first non-elite gets the largest weight, last gets 1
        weights = [len(remain) - i for i in range(len(remain))]

        # draw one, remove it, repeat
        randoms = []
        for _ in range(num_rand):
            idx = random.choices(range(len(remain)), weights=weights, k=1)[0]
            randoms.append(remain.pop(idx))
            weights.pop(idx)
    
    def crossover(self, parent1, parent2):
        child_genes = {}
        for gene_name in parent1.genes:
            # 50% chance to inherit from each parent
            if random.random() < 0.5:
                child_genes[gene_name] = parent1.genes[gene_name]
            else:
                child_genes[gene_name] = parent2.genes[gene_name]
        
        child = Gatherer(genes=child_genes)
        return child
    
    def mutate(self, gatherer):
        # STUDENT ASSIGNMENT 2: Implement a better mutation strategy
        # Current version just randomly flips genes - very crude!
        #
        # Available information:
        # - gatherer.genes: dict with 'speed', 'caution', 'search_pattern', 'efficiency', 'cooperation'
        # - GENE_RANGES: dict with (min, max) values for each gene
        # - MUTATION_RATE: probability of mutation (currently 0.1 = 10%)
        # - MUTATION_STRENGTH: how much to change (currently 0.2 = ±20%)
        #
        # Strategy hints:
        # 1. Current approach: percentage-based change (good for most genes)
        # 2. Alternative: Gaussian/normal distribution around current value
        # 3. Alternative: Fixed step size (add/subtract small amount)
        # 4. Consider adaptive mutation (larger changes early, smaller later)
        # 5. Maybe different strategies for different gene types?
        # 6. Should all genes mutate equally? Maybe cooperation needs special handling?
        #
        # Remember: Mutation provides diversity but shouldn't destroy good solutions!
        
        scale = max(0.3, math.exp(-self.generation / 50))
        boost = 1.0
        history = self.fitness_history
        if len(history) > 5:
            recent = [h['avg_fitness'] for h in history[-6:]]
            if max(recent[1:]) <= recent[0] * 1.01:
                boost = 2.0
        rate = min(0.5, MUTATION_RATE * boost)
        for gene in gatherer.genes:
            if random.random() < rate:
                min_val, max_val = GENE_RANGES[gene]
                sig = (max_val- min_val) * 0.1 * scale * boost
                new_val = gatherer.genes[gene] + random.gauss(0, sig)
                gatherer.genes[gene] = max(min_val, min(max_val, new_val))
    
    def create_next_generation(self, population):
        # Evaluate fitness
        fitness_scores = self.evaluate_fitness(population)
        
        # Record statistics
        if fitness_scores:
            best_fitness = fitness_scores[0][1]
            avg_fitness = sum(fitness for _, fitness in fitness_scores) / len(fitness_scores)
            self.fitness_history.append({
                'generation': self.generation,
                'best_fitness': best_fitness,
                'avg_fitness': avg_fitness
            })
            
            # Record trait averages
            all_gatherers = [gatherer for gatherer, _ in fitness_scores]
            trait_averages = {
                'generation': self.generation,
                'avg_speed': sum(g.genes['speed'] for g in all_gatherers) / len(all_gatherers),
                'avg_caution': sum(g.genes['caution'] for g in all_gatherers) / len(all_gatherers),
                'avg_search_pattern': sum(g.genes['search_pattern'] for g in all_gatherers) / len(all_gatherers),
                'avg_efficiency': sum(g.genes['efficiency'] for g in all_gatherers) / len(all_gatherers),
                'avg_cooperation': sum(g.genes['cooperation'] for g in all_gatherers) / len(all_gatherers)
            }
            self.trait_history.append(trait_averages)
        
        # Select survivors
        survivors = self.select_survivors(fitness_scores)
        
        # Create new population
        new_population = []
        
        # Add survivors (reset their state)
        for survivor in survivors:
            new_gatherer = Gatherer(genes=survivor.genes)
            new_population.append(new_gatherer)
        
        # Create offspring to fill remaining slots
        offspring_count = INITIAL_POPULATION - len(survivors)
        for _ in range(offspring_count):
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)
            child = self.crossover(parent1, parent2)
            self.mutate(child)
            new_population.append(child)
        
        self.generation += 1
        return new_population
    
    def get_population_stats(self, population):
        if not population:
            return {
                'alive_count': 0,
                'total_count': 0,
                'avg_fitness': 0,
                'best_fitness': 0,
                'avg_speed': 0,
                'avg_caution': 0,
                'avg_cooperation': 0
            }
        
        alive_gatherers = [g for g in population if g.alive]
        alive_count = len(alive_gatherers)
        total_count = len(population)
        
        if alive_gatherers:
            fitness_scores = [g.calculate_fitness() for g in alive_gatherers]
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            best_fitness = max(fitness_scores)
            avg_speed = sum(g.genes['speed'] for g in alive_gatherers) / len(alive_gatherers)
            avg_caution = sum(g.genes['caution'] for g in alive_gatherers) / len(alive_gatherers)
            avg_cooperation = sum(g.genes['cooperation'] for g in alive_gatherers) / len(alive_gatherers)
        else:
            # Check all gatherers if none alive
            fitness_scores = [g.calculate_fitness() for g in population]
            avg_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
            best_fitness = max(fitness_scores) if fitness_scores else 0
            avg_speed = sum(g.genes['speed'] for g in population) / len(population)
            avg_caution = sum(g.genes['caution'] for g in population) / len(population)
            avg_cooperation = sum(g.genes['cooperation'] for g in population) / len(population)
        
        return {
            'alive_count': alive_count,
            'total_count': total_count,
            'avg_fitness': avg_fitness,
            'best_fitness': best_fitness,
            'avg_speed': avg_speed,
            'avg_caution': avg_caution,
            'avg_cooperation': avg_cooperation
        }
    
    def reset(self):
        self.generation = 1
        self.fitness_history = []
        self.trait_history = []