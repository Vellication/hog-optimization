"""Strategy optimizer for Hog final_strategy.

This tool performs brute force parameter search to find optimal strategy parameters.
"""

from hog import play, simple_strategy, brain, take_turn
import csv
from itertools import product

def make_parameterized_strategy(risk_dividend, cons_d6, cons_d4, agg_d6, agg_d4):
    """Factory function that creates a strategy with the given parameters.
    
    risk_dividend: divides lead to determine risk adjustment
    cons_d6: conservative d6 roll amount (minimum rolls)
    cons_d4: conservative d4 roll amount (minimum rolls)
    agg_d6: aggressive d6 roll amount (maximum rolls)
    agg_d4: aggressive d4 roll amount (maximum rolls)
    """
    def strategy(score,opponent_score):
        # this strategy is the base case that I test against at the moment
        lead = score - opponent_score # mainly used for risk assessment
        risk = lead // risk_dividend # used to change die rolls and influence some other decisions
        d6_best = min(max(cons_d6, 6 - risk), agg_d6)
        d4_best = min(max(cons_d4, 4 - risk), agg_d4)
        dist_to_d4 = (score + opponent_score) % 7 # how many points I need to earn this turn to make my opponent roll d4s
        if dist_to_d4 != 0: # determines die type on this turn
            rolling_d6 = True
        else:
            rolling_d6 = False
        if rolling_d6:
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
        # Play as player 0
        score0, score1 = play(strategy, opponent_strategy)
        if score0 > score1:
            wins_as_0 += 1
        
        # Play as player 1
        score0, score1 = play(opponent_strategy, strategy)
        if score1 > score0:
            wins_as_1 += 1
    
    win_rate_0 = wins_as_0 / num_games
    win_rate_1 = wins_as_1 / num_games
    overall_win_rate = (win_rate_0 + win_rate_1) / 2
    
    return win_rate_0, win_rate_1, overall_win_rate

def brainless_strategy(score, opponent_score):
    dist_to_d4 = (score + opponent_score) % 7 # how many points I need to earn this turn to make my opponent roll d4s
    if dist_to_d4 != 0: # determines die type on this turn
        rolling_d6 = True
    else:
        rolling_d6 = False

    if rolling_d6:
        return 6
    else:
        return 4

def optimize_strategy(risk_dividend_range, cons_d6_range, cons_d4_range, agg_d6_range, agg_d4_range, num_games,
    step_sizes=(3, 2, 1, 2, 2), # step size for each parameter
    output_file='strategy_results.csv'
):
    """
    Brute force search for optimal strategy parameters.
    
    Parameters:
        risk_dividend_range: (min, max) for risk_dividend parameter
        cons_d6_range: (min, max) for conservative d6 rolls
        cons_d4_range: (min, max) for conservative d4 rolls
        agg_d6_range: (min, max) for aggressive d6 rolls
        agg_d4_range: (min, max) for aggressive d4 rolls
        step_sizes: tuple of step sizes for each parameter
        num_games: number of games to simulate per configuration
        output_file: CSV file to save results
    
    Returns:
        List of (parameters, win_rate) tuples sorted by win rate
    """
    # Generate parameter ranges with steps
    risk_dividends = range(risk_dividend_range[0], risk_dividend_range[1] + 1, step_sizes[0])
    cons_d6s = range(cons_d6_range[0], cons_d6_range[1] + 1, step_sizes[1])
    cons_d4s = range(cons_d4_range[0], cons_d4_range[1] + 1, step_sizes[2])
    agg_d6s = range(agg_d6_range[0], agg_d6_range[1] + 1, step_sizes[3])
    agg_d4s = range(agg_d4_range[0], agg_d4_range[1] + 1, step_sizes[4])
    
    # Create all combinations
    all_combinations = list(product(risk_dividends, cons_d6s, cons_d4s, agg_d6s, agg_d4s))
    total_combinations = len(all_combinations)
    
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"Running {num_games} games per combination against the baseline strategy...")
    print()
    
    results = []
    baseline_strategy = brainless_strategy
    
    # Test each combination
    for idx, (rd, c6, c4, a6, a4) in enumerate(all_combinations, 1):
        # Skip invalid combinations
        if c6 > a6 or c4 > a4:
            continue
            
        strategy = make_parameterized_strategy(rd, c6, c4, a6, a4)
        win_rate_0, win_rate_1, overall = test_strategy(strategy, baseline_strategy, num_games)
        
        results.append({
            'risk_dividend': rd,
            'cons_d6': c6,
            'cons_d4': c4,
            'agg_d6': a6,
            'agg_d4': a4,
            'win_rate_as_p0': win_rate_0,
            'win_rate_as_p1': win_rate_1,
            'overall_win_rate': overall
        })
        
        if idx % 10 == 0 or idx == total_combinations:
            print(f"Progress: {idx}/{total_combinations} ({100*idx/total_combinations:.1f}%)")
    
    # Sort by overall win rate
    results.sort(key=lambda x: x['overall_win_rate'], reverse=True)
    
    # Save to CSV
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['risk_dividend', 'cons_d6', 'cons_d4', 'agg_d6', 'agg_d4', 
                     'win_rate_as_p0', 'win_rate_as_p1', 'overall_win_rate']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults saved to {output_file}")
    print("\nTop 10 configurations:")
    print("-" * 90)
    print(f"{'Rank':<6}{'RiskDiv':<10}{'ConsD6':<10}{'ConsD4':<10}{'AggD6':<10}{'AggD4':<10}{'Win Rate':<12}")
    print("-" * 90)
    
    for i, result in enumerate(results[:10], 1):
        print(f"{i:<6}{result['risk_dividend']:<10}{result['cons_d6']:<10}{result['cons_d4']:<10}"
              f"{result['agg_d6']:<10}{result['agg_d4']:<10}{result['overall_win_rate']:.4f}")
    
    return results

def refine_search(best_params, num_games=2000, output_file='refined_results.csv',
                  risk_dividend_max=25, cons_d6_max=10, cons_d4_max=10, 
                  agg_d6_max=10, agg_d4_max=10):
    """
    Refine search around the best parameters found in coarse search.
    
    Parameters:
        best_params: dict with keys 'risk_dividend', 'cons_d6', 'cons_d4', 'agg_d6', 'agg_d4'
        num_games: number of games to test
        output_file: where to save refined results
        risk_dividend_max: max value for risk_dividend from coarse search
        cons_d6_max: max value for cons_d6 from coarse search
        cons_d4_max: max value for cons_d4 from coarse search
        agg_d6_max: max value for agg_d6 from coarse search
        agg_d4_max: max value for agg_d4 from coarse search
    """
    rd = best_params['risk_dividend']
    c6 = best_params['cons_d6']
    c4 = best_params['cons_d4']
    a6 = best_params['agg_d6']
    a4 = best_params['agg_d4']
    
    print(f"\nRefining search around: RD={rd}, C6={c6}, C4={c4}, A6={a6}, A4={a4}")
    
    # Test in a smaller range around the best params (±2 for each)
    return optimize_strategy(
        risk_dividend_range=(max(1, rd-2), min(risk_dividend_max, rd+2)),
        cons_d6_range=(max(0, c6-1), min(cons_d6_max, c6+1)),
        cons_d4_range=(max(0, c4-1), min(cons_d4_max, c4+1)),
        agg_d6_range=(max(0, a6-1), min(agg_d6_max, a6+1)),
        agg_d4_range=(max(0, a4-1), min(agg_d4_max, a4+1)),
        step_sizes=(1, 1, 1, 1, 1),  # Test every value in refined range
        num_games=num_games,
        output_file=output_file
    )

def test_against_previous_best(current_params, previous_params, num_games=1000):
    """Test the current best parameters against the previous best.
    
    Returns the win rate of current against previous.
    """
    current_strategy = make_parameterized_strategy(**current_params)
    previous_strategy = make_parameterized_strategy(**previous_params)
    
    _, _, win_rate = test_strategy(current_strategy, previous_strategy, num_games)
    
    print(f"\nCurrent params vs Previous params:")
    print(f"Current: {current_params}")
    print(f"Previous: {previous_params}")
    print(f"Win rate: {win_rate:.4f}")
    
    return win_rate

if __name__ == "__main__":
    # Define search ranges
    RISK_DIVIDEND_RANGE = (1, 50)
    CONS_D6_RANGE = (0, 10)
    CONS_D4_RANGE = (0, 10)
    AGG_D6_RANGE = (0, 10)
    AGG_D4_RANGE = (0, 10)
    
    # Run coarse grid search
    print("=" * 80)
    print("PHASE 1: Coarse Grid Search")
    print("=" * 80)
    results = optimize_strategy(
        risk_dividend_range=RISK_DIVIDEND_RANGE,
        cons_d6_range=CONS_D6_RANGE,
        cons_d4_range=CONS_D4_RANGE,
        agg_d6_range=AGG_D6_RANGE,
        agg_d4_range=AGG_D4_RANGE,
        num_games=500,
        output_file='strategy_results_coarse.csv'
    )
    
    # Get best from coarse search
    best_coarse = results[0]
    print(f"\nBest from coarse search:")
    print(f"Parameters: RD={best_coarse['risk_dividend']}, C6={best_coarse['cons_d6']}, "
          f"C4={best_coarse['cons_d4']}, A6={best_coarse['agg_d6']}, A4={best_coarse['agg_d4']}")
    print(f"Win rate: {best_coarse['overall_win_rate']:.4f}")
    
    # Refine search around best
    print("\n" + "=" * 80)
    print("PHASE 2: Refined Search")
    print("=" * 80)
    refined_results = refine_search(
        best_coarse, 
        num_games=1000, 
        output_file='strategy_results_refined.csv',
        risk_dividend_max=RISK_DIVIDEND_RANGE[1],
        cons_d6_max=CONS_D6_RANGE[1],
        cons_d4_max=CONS_D4_RANGE[1],
        agg_d6_max=AGG_D6_RANGE[1],
        agg_d4_max=AGG_D4_RANGE[1]
    )
    
    best_refined = refined_results[0]
    print(f"\nBest from refined search:")
    print(f"Parameters: RD={best_refined['risk_dividend']}, C6={best_refined['cons_d6']}, "
          f"C4={best_refined['cons_d4']}, A6={best_refined['agg_d6']}, A4={best_refined['agg_d4']}")
    print(f"Win rate: {best_refined['overall_win_rate']:.4f}")
    
    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)