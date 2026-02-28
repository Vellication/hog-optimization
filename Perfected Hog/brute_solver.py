"""Exact Dynamic Programming solver for optimal Hog strategy.

Computes the mathematically optimal decision at every game state
using exact probability distributions — no simulation needed.
Solves the full 100x100 state space in under a second.
"""

import csv


def _precompute_dice_distributions():
    """Precompute exact outcome distributions for all (dice_type, num_rolls) combos.

    For k dice with d sides, the distribution accounts for Pig Out (any 1 → score 1)
    and enumerates all non-Pig-Out sums via DP convolution over faces {2..d}.

    Returns dict: (num_sides, num_rolls) -> {outcome: probability}
    """
    distributions = {}
    for num_sides in (4, 6):
        for num_rolls in range(1, 11):
            d, k = num_sides, num_rolls
            total = d ** k
            outcomes = {}

            # Probability of rolling a 1 for k dice with n sides
            no_pig_count = (d - 1) ** k
            pig_prob = (total - no_pig_count) / total
            if pig_prob > 0:
                outcomes[1] = pig_prob

            # Calculate distribution of total values for k dice with n sides
            ways = {0: 1}
            for dice in range(k):
                new_ways = {}
                for prev_sum, count in ways.items():
                    for face in range(2, d + 1):
                        s = prev_sum + face
                        new_ways[s] = new_ways.get(s, 0) + count
                ways = new_ways

            for outcome, count in ways.items():
                outcomes[outcome] = count / total

            distributions[(num_sides, num_rolls)] = outcomes
    return distributions


def solve():
    """Solve for the optimal strategy at every game state via backward induction.

    States are processed in decreasing order of (s + o). Since scoring always
    increases the total and Swine Swap preserves it, all future states are
    guaranteed to be solved before they're needed.

    Returns:
        win_prob:    100x100 list, win_prob[s][o] = P(current mover wins)
        best_action: 100x100 list, best_action[s][o] = optimal num_rolls (0-10)
    """
    dice_dist = _precompute_dice_distributions()

    win_prob = [[0.0] * 100 for _ in range(100)]
    best_action = [[0] * 100 for _ in range(100)]

    for total in range(1998, -1, -1):
        for s in range(max(0, total - 99), min(100, total + 1)):
            o = total - s
            if o < 0 or o >= 1000:
                continue

            num_sides = 4 if (s + o) % 7 == 0 else 6
            best_wr = -1.0
            best_roll = 0

            for num_rolls in range(11):
                if num_rolls == 0:
                    # Free Bacon (deterministic)
                    bacon_points = max(o % 10, o // 10) + 1
                    bacon_score, bacon_opp = s + bacon_points, o
                    if bacon_score == 2 * bacon_opp or bacon_opp == 2 * bacon_score:
                        bacon_score, bacon_opp = bacon_opp, bacon_score
                    if bacon_score >= 100:
                        winrate = 1.0
                    elif bacon_opp >= 100:
                        winrate = 0.0
                    else:
                        winrate = 1.0 - win_prob[bacon_opp][bacon_score]
                else:
                    # Roll dice: weighted sum over exact outcome distribution
                    winrate = 0.0
                    for points, prob in dice_dist[(num_sides, num_rolls)].items():
                        roll_score, roll_opp = s + points, o
                        if roll_score == 2 * roll_opp or roll_opp == 2 * roll_score:
                            roll_score, roll_opp = roll_opp, roll_score
                        if roll_score >= 100:
                            winrate += prob
                        elif roll_opp >= 100:
                            pass  # contributes 0
                        else:
                            winrate += prob * (1.0 - win_prob[roll_opp][roll_score])

                if winrate > best_wr:
                    best_wr = winrate
                    best_roll = num_rolls

            win_prob[s][o] = best_wr
            best_action[s][o] = best_roll

    return win_prob, best_action


def make_optimal_strategy(best_action):
    """Create a strategy function from the solved action table."""
    def strategy(score, opponent_score):
        return best_action[score][opponent_score]
    return strategy


def save_csv(win_prob, best_action, filename='optimal_hog_strategy.csv'):
    """Save every state to CSV: score, opponent_score, best_roll, win_prob."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['score', 'opponent_score', 'best_roll', 'win_prob'])
        for s in range(100):
            for o in range(100):
                writer.writerow([s, o, best_action[s][o], f'{win_prob[s][o]:.6f}'])
    print(f"Saved to {filename}")


def load_csv(filename='optimal_hog_strategy.csv'):
    """Load solved tables from CSV and return (win_prob, best_action)."""
    win_prob = [[0.0] * 100 for _ in range(100)]
    best_action = [[0] * 100 for _ in range(100)]
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s, o = int(row['score']), int(row['opponent_score'])
            best_action[s][o] = int(row['best_roll'])
            win_prob[s][o] = float(row['win_prob'])
    return win_prob, best_action


def print_summary(win_prob, best_action):
    """Print key states from the solution."""
    print(f"\nFirst-mover win probability: {win_prob[0][0]:.6f}")
    print(f"\n{'State (s, opp)':<20} {'Roll':<10} {'Win Prob':<10}")
    print("-" * 40)
    for s, o in [(0,0),(10,10),(25,25),(50,50),(75,75),
                 (90,90),(20,40),(40,60),(60,80),(80,95)]:
        print(f"({s:2d}, {o:2d}){' '*12} {best_action[s][o]:<10} {win_prob[s][o]:.6f}")


if __name__ == "__main__":
    print("Solving Hog (exact DP)...")
    win_prob, best_action = solve()
    print_summary(win_prob, best_action)
    save_csv(win_prob, best_action)
    print("\n")