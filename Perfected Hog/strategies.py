def always_roll(n):
    """
    Return a strategy that always rolls N dice.
    """
    def strategy(score, opponent_score):
        return n
    return strategy


def consistent_strategy(score, opponent_score):
        """
        This strategy uses statistics and combinatorial game theory (where applicable in a 
        game about rolling dice) to outperform all previous strategies.
        6 and 4 are the best roll numbers for d6s and d4s, so those are my baselines.
        Free Bacon is stronger than it initially seems. It can cause swaps, force opponents to 
        roll d4s, and is generally stronger than rolling d4s.
        I'll also adjust my risk factor based on the lead. I only need to win by one, but I also need to win.
        """
        bacon_points = take_turn(0, opponent_score) # shorthand for points earning by taking Free Bacon
        bacon_score = score + bacon_points # used for a variety of choices
        lead = score - opponent_score # mainly used for risk assessment
        risk = lead // 15 # basically, how many points I need to be ahead/behind to increment the die count.
        score_sum = score + opponent_score # used to check what kind of die is being rolled
        d6_best = min(max(3, 6 - risk), 7)
        d4_best = min(max(0, 4 - risk), 2)
        if score_sum % 7 != 0: # determines die type on this turn
            rolling_d6 = True
        else:
            rolling_d6 = False
        
        if bacon_score == 2 * opponent_score: # Strategic hint: swapping when you have the lead is bad =D
            if rolling_d6:
                return d6_best
            else:
                return d4_best
        elif bacon_points >= 8:
            return 0
        elif lead < -4 and bacon_score * 2 == opponent_score: # Swap only if it's better than rolling dice
            return 0
        elif (bacon_score + opponent_score) % 7 == 0: # Make my opponent roll d4s if I can't swap
            return 0
        
        # Default return when none of the conditions above are met
        if rolling_d6:
            return d6_best
        else:
            return d4_best

### THE BRAIN ###

# It's alive! This is the metastrategy that decides which strategy I'll use based on the game state.

def brain(score, opponent_score):
    # Start by stating all known information about the game state

    # average points for 1-10 d6 rolls
    avg_d6 = [3.5, 5.861, 7.365, 8.233, 8.635, 
    8.702, 8.535, 8.209, 7.783, 7.298]

    # average points for 1-10 d4 rolls
    avg_d4 = [2.5, 3.8125, 4.375, 4.480, 4.322, 
    4.025, 3.669, 3.302, 2.952, 2.633]

    bacon_points = take_turn(0, opponent_score) # points earned by taking Free Bacon
    bacon_score = score + bacon_points # used for a variety of choices
    lead = score - opponent_score # mainly used for risk assessment
    risk_dividend = 15 # How far a lead needs to be to increment risk. This value is arbitrary and will be parameterized at some point when I know how to (probably some nonlinear formula with both scores).
    risk = lead // risk_dividend # used to change die rolls and influence some other decisions
    score_sum = score + opponent_score # do I need to explain this one?
    dist_to_d4 = score_sum % 7 # how many points I need to earn this turn to make my opponent roll d4s
    if dist_to_d4 != 0: # determines die type on this turn
        rolling_d6 = True
    else:
        rolling_d6 = False

    # Strategies 

    def simple_strategy(score,opponent_score):
        # this strategy is the base case that I test against at the moment
        d6_best = min(max(3, 6 - risk), 7)
        d4_best = min(max(0, 4 - risk), 2)
        if rolling_d6:
            return d6_best
        else:
            return d4_best

    return simple_strategy(score, opponent_score)

    # Strategies to add: flowchart type strategy, wait to swap strategy, make my opponent roll d4s, maybe add the brute_table.

# Vanilla Strategies

def bacon_strategy(score, opponent_score):
    """This strategy rolls 0 dice if that gives at least BACON_MARGIN points,
    and rolls BASELINE_NUM_ROLLS otherwise.

    >>> bacon_strategy(0, 0)
    5
    >>> bacon_strategy(70, 50)
    5
    >>> bacon_strategy(50, 70)
    0
    """
    opp_score_digits = []
    opp_score_digits.append(opponent_score % 10) # ones digit
    opp_score_digits.append(opponent_score // 10) # tens digit
    if max(opp_score_digits) + 1 >= BACON_MARGIN:
        return 0
    else:
        return BASELINE_NUM_ROLLS

def swap_strategy(score, opponent_score):
    """This strategy rolls 0 dice when it would result in a beneficial swap and
    rolls BASELINE_NUM_ROLLS if it would result in a harmful swap. It also rolls
    0 dice if that gives at least BACON_MARGIN points and rolls
    BASELINE_NUM_ROLLS otherwise.

    >>> swap_strategy(23, 60) # 23 + (1 + max(6, 0)) = 30: Beneficial swap
    0
    >>> swap_strategy(27, 18) # 27 + (1 + max(1, 8)) = 36: Harmful swap
    5
    >>> swap_strategy(50, 80) # (1 + max(8, 0)) = 9: Lots of free bacon
    0
    >>> swap_strategy(12, 12) # Baseline
    5
    """
    bacon_score = score + take_turn(0, opponent_score)
    if bacon_score == 2 * opponent_score:
        return BASELINE_NUM_ROLLS
    elif opponent_score == 2 * bacon_score:
        return 0
    elif take_turn(0, opponent_score) >= BACON_MARGIN:
        return 0

    return BASELINE_NUM_ROLLS
def final_strategy(score, opponent_score):
    """This strategy uses statistics and combinatorial game theory (where applicable in a 
    game about rolling dice) to outperform all previous strategies.
    6 and 4 are the best roll numbers for d6s and d4s, so those are my baselines.
    The Free Bacon is stronger than it initially seems. It can cause swaps, force opponents to 
    roll d4s, and is generally stronger than rolling d4s.
    I'll also adjust my risk factor based on the lead. I only need to win by one, but I also need to win.
    """
    bacon_points = take_turn(0, opponent_score) # shorthand for points earning by taking Free Bacon
    bacon_score = score + bacon_points # used for a variety of choices
    lead = score - opponent_score # mainly used for risk assessment
    risk = lead // 9 # an arbitrary threshold of risk. If you're reading this, I haven't yet tested other values.
    score_sum = score + opponent_score # used to check what kind of die is being rolled
    d6_best = min(max(4, 6 - risk), 8)
    d4_best = min(max(3, 4 - risk), 6)

    
    if score_sum % 7 != 0: # determines die type on this turn
        rolling_d6 = True
    else:
        rolling_d6 = False
    
    if bacon_score == 2 * opponent_score: # Strategic hint: swapping when you have the lead is bad =D
        if rolling_d6:
            return d6_best
        else:
            return d4_best
    elif bacon_points >= 8:
        return 0
    elif lead < -4 and bacon_score * 2 == opponent_score: # Swap only if it's better than rolling dice
        return 0
    elif (bacon_score + opponent_score) % 7 == 0: # Make my opponent roll d4s if I can't swap
        return 0
    
    # Default return when none of the conditions above are met
    if rolling_d6:
        return d6_best
    else:
        return d4_best