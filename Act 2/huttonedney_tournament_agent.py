#!/usr/bin/env python
"""
Tournament Agent: S(herlock)anta Holmes
Student: Hutton Edney
Generated: 2026-10-04 21:25:44

Evolution Details:
- Generations: 100
- Final Fitness: 154.5
- Trained against: Adaptive, Hard Majority, Random (0.9), Random (0.3), Pavlov...

Strategy: Santa starts cautiously, watches what you do, forgives almost everything, and only gives coal when the evidence of naughtiness becomes strong.
"""

from agents import Agent, INVEST, UNDERCUT
import random


class HuttonEdneyAgent(Agent):
    """
    S(herlock)anta Holmes

    Santa starts cautiously, watches what you do, forgives almost everything, and only gives coal when the evidence of naughtiness becomes strong.

    Evolved Genes: [0.02449889017642974, 0.018033966708632505, 0.14866494128511734, 1.0, 0.38492083610472205, 0.4696607392073748]
    """

    def __init__(self):
        # These genes were evolved through 100 generations
        self.genes = [0.02449889017642974, 0.018033966708632505, 0.14866494128511734, 1.0, 0.38492083610472205, 0.4696607392073748]

        # Required for tournament compatibility
        self.student_name = "Hutton Edney"

        super().__init__(
            name="S(herlock)anta Holmes",
            description="Santa starts cautiously, watches what you do, forgives almost everything, and only gives coal when the evidence of naughtiness becomes strong."
        )

    def choose_action(self) -> bool:

        opening_niceness = self.genes[0] # how nice Santa is at the beginning
        present_reward = self.genes[1] # how likely Santa is to reward nice behavior
        coal_retaliation = self.genes[2] # how likely Santa is to give coal for naughty behavior
        forgiveness = self.genes[3] # how willing Santa is to forgive naughtiness
        memory_length_gene = self.genes[4] # how much opponent history Santa remembers
        naughty_threshold_gene = self.genes[5] # how suspicious Sants is before deciding someone is naughty

        if self.round_num < 3:
            return random.random() < opening_niceness

        memory_length = max(
            1,
            int(memory_length_gene * 10) + 1
        )

        recent_history = self.history[-memory_length:]
        recent_niceness = sum(recent_history) / len(recent_history)

        long_length = max(10, memory_length * 2)

        if len(self.history) < long_length:
            long_history = self.history
        else:
            long_history = self.history[-long_length:]

        long_term_niceness = sum(long_history) / len(long_history)

        niceness_score = (
            recent_niceness * 0.7
            + long_term_niceness * 0.3
        )

        naughty_threshold = (
            0.30 + naughty_threshold_gene * 0.50
        )

        behavior_change = abs(
            recent_niceness - long_term_niceness
        )

        isolated_naughtiness = False

        if self.history[-1] == UNDERCUT:
            if (
                long_term_niceness >= naughty_threshold
                and recent_niceness >= 0.50
            ):
                isolated_naughtiness = True

        repeated_naughtiness = False

        if len(recent_history) >= 3:
            if recent_niceness < 0.34:
                repeated_naughtiness = True

        if behavior_change > 0.30:

            if self.history[-1] == UNDERCUT:

                if random.random() < coal_retaliation:
                    return UNDERCUT

                if random.random() < forgiveness:
                    return INVEST

                return UNDERCUT

            if random.random() < present_reward:
                return INVEST

            return UNDERCUT

        if isolated_naughtiness:

            if random.random() < forgiveness:
                return INVEST

            if random.random() < coal_retaliation:
                return UNDERCUT

            return INVEST

        if repeated_naughtiness:

            if random.random() < coal_retaliation:
                return UNDERCUT

            if random.random() < forgiveness:
                return INVEST

            return UNDERCUT

        if niceness_score >= naughty_threshold:

            if random.random() < present_reward:
                return INVEST

            return UNDERCUT

        if random.random() < coal_retaliation:
            return UNDERCUT

        if random.random() < forgiveness:
            return INVEST

        return UNDERCUT



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return HuttonEdneyAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f"✅ Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
