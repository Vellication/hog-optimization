"""Strategy optimizer for Hog final_strategy.

This tool performs brute force parameter search to find optimal strategy parameters.
All optimizer functions are generic and driven by PARAM_DEFS — to change the
strategy, just update PARAM_DEFS, PARAM_CONSTRAINTS, and make_parameterized_strategy.
"""

from hog import play, brain, take_turn
import csv
from itertools import product

# Testing rigor
coarse_games = 500
fine_games = 2000

# Strategy Parameters
""" 
Each parameter here adds a dimension to the strategy space, start small if you're trying to understand how the optimizer works.
You'll need to redefine both PARAM_DEFS and PARAM_CONSTRAINTS from scratch if you're changing the strategy.
To add/remove strategy parameters, edit this list to match the parameterized values in make_parameterize_strategy.
"""

# Each entry: (name, (min, max), coarse_step)
PARAM_DEFS = [
    ('risk_dividend', (1, 50), 3),
    ('cons_d6',       (0, 10), 2),
    ('cons_d4',       (0, 10), 1),
    ('agg_d6',        (0, 10), 2),
    ('agg_d4',        (0, 10), 2),
]

# Declarative ordering constraints: each (lo, hi) pair requires params[lo] <= params[hi].
PARAM_CONSTRAINTS = [
    ('cons_d6', 'agg_d6'),
    ('cons_d4', 'agg_d4'),
]

def make_parameterized_strategy(*args):
    """Factory function that creates a strategy with the given parameters.
    
    Arguments are positional, matching the order in PARAM_DEFS.
    Access parameters via the `p` dict so the body adapts to PARAM_DEFS changes.
    """
    assert len(args) == len(PARAM_DEFS), \
        f"Expected {len(PARAM_DEFS)} args ({[d[0] for d in PARAM_DEFS]}), got {len(args)}"
    p = {name: val for (name, _, _), val in zip(PARAM_DEFS, args)}

    def strategy(score, opponent_score):
        lead = score - opponent_score
        risk = lead // p['risk_dividend']
        d6_best = min(max(p['cons_d6'], 6 - risk), p['agg_d6'])
        d4_best = min(max(p['cons_d4'], 4 - risk), p['agg_d4'])
        dist_to_d4 = (score + opponent_score) % 7
        if dist_to_d4 != 0:
            return d6_best
        else:
            return d4_best
    return strategy

def test_strategy(strategy, opponent_strategy, num_games=500):
    """Test a strategy against an opponent and return win rate.
    
    Returns: (win_rate_as_player_0, win_rate_as_player_1, overall_win_rate)
    """
    wins_as_0 = 0
    wins_as_1 = 0
    
    for _ in range(num_games):
        score0, score1 = play(strategy, opponent_strategy)
        if score0 > score1:
            wins_as_0 += 1
        score0, score1 = play(opponent_strategy, strategy)
        if score1 > score0:
            wins_as_1 += 1
    
    win_rate_0 = wins_as_0 / num_games
    win_rate_1 = wins_as_1 / num_games
    overall_win_rate = (win_rate_0 + win_rate_1) / 2
    
    return win_rate_0, win_rate_1, overall_win_rate

def brainless_strategy(score, opponent_score):
    dist_to_d4 = (score + opponent_score) % 7
    if dist_to_d4 != 0:
        return 6
    else:
        return 4

def default_validate(args):
    """Validation driven by PARAM_CONSTRAINTS: each (lo, hi) pair must satisfy lo <= hi."""
    p = {name: val for (name, _, _), val in zip(PARAM_DEFS, args)}
    return all(p[lo] <= p[hi] for lo, hi in PARAM_CONSTRAINTS)

def optimize_strategy(param_defs, num_games, validate=None, output_file='strategy_results.csv'):
    """
    Brute force search for optimal strategy parameters.
    
    Parameters:
        param_defs: list of (name, (min, max), step) tuples
        num_games:  number of games to simulate per configuration
        validate:   optional function(args_tuple) -> bool; False skips the combo
        output_file: CSV file to save results
    
    Returns:
        List of result dicts sorted by win rate (descending).
    """
    param_names = [p[0] for p in param_defs]
    ranges = [range(p[1][0], p[1][1] + 1, p[2]) for p in param_defs]
    all_combinations = list(product(*ranges))
    total_combinations = len(all_combinations)
    
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"Running {num_games} games per combination against the baseline strategy...")
    print()
    
    results = []
    baseline_strategy = brainless_strategy
    
    for idx, combo in enumerate(all_combinations, 1):
        if validate and not validate(combo):
            continue
            
        strategy = make_parameterized_strategy(*combo)
        win_rate_0, win_rate_1, overall = test_strategy(strategy, baseline_strategy, num_games)
        
        result = {name: val for name, val in zip(param_names, combo)}
        result['win_rate_as_p0'] = win_rate_0
        result['win_rate_as_p1'] = win_rate_1
        result['overall_win_rate'] = overall
        results.append(result)
        
        if idx % 10 == 0 or idx == total_combinations:
            print(f"Progress: {idx}/{total_combinations} ({100*idx/total_combinations:.1f}%)")
    
    results.sort(key=lambda x: x['overall_win_rate'], reverse=True)
    
    # Save to CSV
    fieldnames = param_names + ['win_rate_as_p0', 'win_rate_as_p1', 'overall_win_rate']
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Print top results
    col_width = max(len(n) for n in param_names) + 2
    header = f"{'Rank':<6}" + "".join(f"{n:<{col_width}}" for n in param_names) + f"{'Win Rate':<12}"
    print(f"\nResults saved to {output_file}")
    print("\nTop 10 configurations:")
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    
    for i, result in enumerate(results[:10], 1):
        line = f"{i:<6}" + "".join(f"{result[n]:<{col_width}}" for n in param_names)
        line += f"{result['overall_win_rate']:.4f}"
        print(line)
    
    return results

def refine_search(best_result, param_defs, num_games=2000, validate=None,
                  output_file='refined_results.csv'):
    """
    Refine search around the best parameters found in coarse search.
    
    Parameters:
        best_result: dict returned by optimize_strategy (one entry from the results list)
        param_defs:  the same PARAM_DEFS used for the coarse search
        num_games:   number of games to test
        validate:    optional validation function
        output_file: where to save refined results
    """
    param_names = [p[0] for p in param_defs]
    best_vals = [best_result[n] for n in param_names]
    
    print(f"\nRefining search around: {', '.join(f'{n}={v}' for n, v in zip(param_names, best_vals))}")
    
    refined_defs = [
        (name, (max(lo, val - 2), min(hi, val + 2)), 1)
        for (name, (lo, hi), _), val in zip(param_defs, best_vals)
    ]
    
    return optimize_strategy(refined_defs, num_games, validate=validate, output_file=output_file)

def test_against_previous_best(current_params, previous_params, param_defs=PARAM_DEFS,
                               num_games=1000):
    """
    Test the current best parameters against the previous best.
    
    Returns the win rate of current against previous.
    """
    param_names = [p[0] for p in param_defs]
    current_strategy = make_parameterized_strategy(*(current_params[n] for n in param_names))
    previous_strategy = make_parameterized_strategy(*(previous_params[n] for n in param_names))
    
    _, _, win_rate = test_strategy(current_strategy, previous_strategy, num_games)
    
    print(f"\nCurrent params vs Previous params:")
    print(f"Current: {current_params}")
    print(f"Previous: {previous_params}")
    print(f"Win rate: {win_rate:.4f}")
    
    return win_rate

if __name__ == "__main__":
    param_names = [p[0] for p in PARAM_DEFS]

    # Phase 1: Coarse grid search
    print("=" * 80)
    print("PHASE 1: Coarse Grid Search")
    print("=" * 80)
    results = optimize_strategy(
        PARAM_DEFS,
        num_games=coarse_games,
        validate=default_validate,
        output_file='strategy_results_coarse.csv'
    )
    
    best_coarse = results[0]
    print(f"\nBest from coarse search:")
    print(f"Parameters: {', '.join(f'{n}={best_coarse[n]}' for n in param_names)}")
    print(f"Win rate: {best_coarse['overall_win_rate']:.4f}")
    
    # Phase 2: Refined search around best
    print("\n" + "=" * 80)
    print("PHASE 2: Refined Search")
    print("=" * 80)
    refined_results = refine_search(
        best_coarse,
        PARAM_DEFS,
        num_games=fine_games,
        validate=default_validate,
        output_file='strategy_results_refined.csv'
    )
    
    best_refined = refined_results[0]
    print(f"\nBest from refined search:")
    print(f"Parameters: {', '.join(f'{n}={best_refined[n]}' for n in param_names)}")
    print(f"Win rate: {best_refined['overall_win_rate']:.4f}")
    
    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)