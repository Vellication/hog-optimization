"""The Game of Hog."""

from dice import four_sided, six_sided, make_test_dice
from ucb import main, trace, log_current_line, interact
from itertools import product

GOAL_SCORE = 100 # The goal of Hog is to score 100 points.

######################
# Phase 1: Simulator #
######################

# Taking turns

def roll_dice(num_rolls, dice=six_sided):
    """Roll DICE for NUM_ROLLS times.  Return either the sum of the outcomes,
    or 1 if a 1 is rolled (Pig out). This calls DICE exactly NUM_ROLLS times.

    num_rolls:  The number of dice rolls that will be made; at least 1.
    dice:       A zero-argument function that returns an integer outcome.
    """
    # These assert statements ensure that num_rolls is a positive integer.
    assert type(num_rolls) == int, 'num_rolls must be an integer.'
    assert num_rolls > 0, 'Must roll at least once.'
    
    dice_list = []
    points = 0
    for i in range(num_rolls):
        current_die = dice()
        dice_list.append(current_die)
    if 1 in dice_list:
        points = 1 # Pig out
    else:
        points = sum(dice_list)
    return points

def take_turn(num_rolls, opponent_score, dice=six_sided):
    """Simulate a turn rolling NUM_ROLLS dice, which may be 0 (Free bacon).

    num_rolls:       The number of dice rolls that will be made.
    opponent_score:  The total score of the opponent.
    dice:            A function of no args that returns an integer outcome.
    """
    assert type(num_rolls) == int, 'num_rolls must be an integer.'
    assert num_rolls >= 0, 'Cannot roll a negative number of dice.'
    assert num_rolls <= 10, 'Cannot roll more than 10 dice.'
    assert opponent_score < 100, 'The game should be over.'
    
    if num_rolls == 0:
        opp_score_digits = []
        opp_score_digits.append(opponent_score % 10) # ones digit
        opp_score_digits.append(opponent_score // 10) # tens digit
        return max(opp_score_digits) + 1
    else:
        return roll_dice(num_rolls, dice)

# Playing a game

def select_dice(score, opponent_score):
    """Select six-sided dice unless the sum of SCORE and OPPONENT_SCORE is a
    multiple of 7, in which case select four-sided dice (Hog wild).

    >>> select_dice(4, 24) == four_sided
    True
    >>> select_dice(16, 64) == six_sided
    True
    >>> select_dice(0, 0) == four_sided
    True
    """
    if (score + opponent_score) % 7 == 0:
        return four_sided
    else:
        return six_sided

def other(who):
    """Return the other player, for a player WHO numbered 0 or 1.

    >>> other(0)
    1
    >>> other(1)
    0
    """
    return 1 - who

def play(strategy0, strategy1, goal=GOAL_SCORE):
    """Simulate a game and return the final scores of both players, with
    Player 0's score first, and Player 1's score second.

    A strategy is a function that takes two total scores as arguments
    (the current player's score, and the opponent's score), and returns a
    number of dice that the current player will roll this turn.

    strategy0:  The strategy function for Player 0, who plays first.
    strategy1:  The strategy function for Player 1, who plays second.
    """
    who = 0
    score0, score1 = 0, 0  # Always track Player 0 and Player 1 separately
    
    while score0 < goal and score1 < goal:
        if who == 0:
            score0 += take_turn(strategy0(score0, score1), score1, select_dice(score0, score1))
        else:
            score1 += take_turn(strategy1(score1, score0), score0, select_dice(score0, score1))
        
        if score0 == 2 * score1 or score1 == 2 * score0:
            score0, score1 = score1, score0
        who = other(who)
    
    return score0, score1  # You may wish to change this line.

#######################
# Phase 2: Strategies #
#######################

# Basic Strategy

BASELINE_NUM_ROLLS = 5
BACON_MARGIN = 8

# I've replaced the baseline with a slightly better strategy. I have a seperate 

def simple_strategy(score,opponent_score):
        # this strategy is the base case that I test against at the moment. I used a coarse > fine search to optimize the RD and die_best values
        lead = score - opponent_score # mainly used for risk assessment
        risk_dividend = 18 # How far a lead needs to be to increment risk. This value was determined by parameterized testing, but I think it could still be improved (probably shouldn't be linear)
        risk = lead // risk_dividend # used to change die rolls and influence some other decisions
        d6_best = min(max(3, 6 - risk), 9)
        d4_best = min(max(0, 4 - risk), 0) # I tested this many times to confirm, if you're just rolling dice, bacon is better than d4s on average, based on testing
        dist_to_d4 = score + opponent_score % 7 # how many points I need to earn this turn to make my opponent roll d4s
        if dist_to_d4 != 0: # determines die type on this turn
            rolling_d6 = True
        else:
            rolling_d6 = False
        if rolling_d6:
            return d6_best
        else:
            return d4_best

# Experiments

def make_averaged(fn, num_samples=2000):
    """Return a function that returns the average_value of FN when called.

    To implement this function, you will have to use *args syntax, a new Python
    feature introduced in this project.  See the project description.

    >>> dice = make_test_dice(3, 1, 5, 6)
    >>> averaged_dice = make_averaged(dice, 1000)
    >>> averaged_dice()
    3.75
    >>> make_averaged(roll_dice, 1000)(2, dice)
    6.0

    In this last example, two different turn scenarios are averaged.
    - In the first, the player rolls a 3 then a 1, receiving a score of 1.
    - In the other, the player rolls a 5 and 6, scoring 11.
    Thus, the average value is 6.0.
    """
    def strategy(*args):
        fn_sum = 0
        for i in range(num_samples):
            fn_sum += fn(*args)
        fn_average = fn_sum / num_samples
        return fn_average
    return strategy

def max_scoring_num_rolls(dice=six_sided):
    """Return the number of dice (1 to 10) that gives the highest average turn
    score by calling roll_dice with the provided DICE.  Print all averages as in
    the doctest below.  Assume that dice always returns positive outcomes.

    >>> dice = make_test_dice(3)
    >>> max_scoring_num_rolls(dice)
    1 dice scores 3.0 on average
    2 dice scores 6.0 on average
    3 dice scores 9.0 on average
    4 dice scores 12.0 on average
    5 dice scores 15.0 on average
    6 dice scores 18.0 on average
    7 dice scores 21.0 on average
    8 dice scores 24.0 on average
    9 dice scores 27.0 on average
    10 dice scores 30.0 on average
    10
    """
    best_score = 1
    for i in range(10):
        averaged_result = make_averaged(roll_dice,2000)
        actual_value = averaged_result(i+1, dice)
        print(i+1, "dice scores", actual_value, "on average")
        if actual_value >= best_score:
            best_score = actual_value
            best_dice = i+1
    return best_dice

def winner(strategy0, strategy1):
    """Return 0 if strategy0 wins against strategy1, and 1 otherwise."""
    score0, score1 = play(strategy0, strategy1)
    if score0 > score1:
        return 0
    else:
        return 1

def average_win_rate(strategy, baseline=simple_strategy):
    """Return the average win rate (0 to 1) of STRATEGY against BASELINE."""
    win_rate_as_player_0 = 1 - make_averaged(winner)(strategy, baseline)
    win_rate_as_player_1 = make_averaged(winner)(baseline, strategy)
    return (win_rate_as_player_0 + win_rate_as_player_1) / 2 # Average results

# I wrote this to confirm the statistical data from max_scoring_num_rolls

def find_average_points(dice=six_sided): 
    """
    A better version of make_averaged() that doesn't use random simulation.
    Funny story: This function was originally about 10 times as long, and I may or may not have tried to convert every number from 1 to 6^10 to base 6 and then make a tuple from their digits...
    """
    if dice == six_sided:
        type = 7
    else:
        type = 5

    for i in range(10):
        all_combos = list(product(range(1, type), repeat=i+1))
        all_rolls = []
        for permutation in all_combos:
            all_rolls.append(roll_dice(len(permutation), make_test_dice(*permutation)))
        print(sum(all_rolls)/len(all_rolls))

    return

# Test Strategy
# I change this function to test a variety of things. It has no consistent goal, and is just for speeding up some space searching.

def test(score,opponent_score):
        # this strategy is the base case that I test against at the moment
        lead = score - opponent_score # mainly used for risk assessment
        risk_dividend = 7 # How far a lead needs to be to increment risk. This value is arbitrary and will be parameterized at some point when I know how to (probably some nonlinear formula with both scores).
        risk = lead // risk_dividend # used to change die rolls and influence some other decisions
        d6_best = min(max(4, 6 - risk), 6)
        d4_best = min(max(4, 4 - risk), 4)
        dist_to_d4 = score + opponent_score % 7 # how many points I need to earn this turn to make my opponent roll d4s
        if dist_to_d4 != 0: # determines die type on this turn
            rolling_d6 = True
        else:
            rolling_d6 = False
        if rolling_d6:
            return d6_best
        else:
            return d4_best

def run_experiments():
    """Run a series of strategy experiments and report results."""
    if False: # Change to False when done finding max_scoring_num_rolls
        six_sided_max = max_scoring_num_rolls(six_sided)
        print('Max scoring num rolls for six-sided dice:', six_sided_max)
        four_sided_max = max_scoring_num_rolls(four_sided)
        print('Max scoring num rolls for four-sided dice:', four_sided_max)

    if False: # Change to True to test always_roll(8)
        print('always_roll(8) win rate:', average_win_rate(always_roll(8)))

    if False: # Change to True to test bacon_strategy
        print('bacon_strategy win rate:', average_win_rate(bacon_strategy))

    if False: # Change to True to test swap_strategy
        print('swap_strategy win rate:', average_win_rate(swap_strategy))

    if False: # Change to True to test final_strategy
        print('final_strategy win rate:', average_win_rate(final_strategy))

    if False: # finds the mathematic average score for each number of dice rolls. Like the first experiment, but better (and slower).
        six_sided_average = find_average_points(six_sided)
        four_sided_average = find_average_points(four_sided)
        print('Max scoring num rolls for six-sided dice:', six_sided_average)
        print('Max scoring num rolls for four-sided dice:', four_sided_average)

    if False: #tests brain()
        print('brain win rate:', average_win_rate(brain))

    if True: #use for double checking coarse search results
        print('test win rate:', average_win_rate(test))


    "*** You may add additional experiments as you wish ***"
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

    '''
        This is the strategy I wrote by hand and then used a coarse -> smooth search to optimize various parameters in the strategy.
    def consistent_strategy(score, opponent_score):
        """
        This strategy uses statistics and combinatorial game theory (where applicable in a 
        game about rolling dice) to outperform all previous strategies.
        6 and 4 are the best roll numbers for d6s and d4s, so those are my baselines.
        The Free Bacon is stronger than it initially seems. It can cause swaps, force opponents to 
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
    '''

    '''
        this one is REALLY bad in the base case (~35% wr)
    def hate_roll_strategy(score, opponent_score):
        bacon_points, bacon_score, lead, risk, score_sum, dist_to_d4, rolling_d6 = brain(score, opponent_score)
        best_roll = 0
        check_dist = 3.5
        if rolling_d6:
            for i in range(len(avg_d6)):
                if abs(dist_to_d4 - avg_d6[i]) < check_dist:
                    check_dist = avg_d6[i]
                    best_roll = i + 1
        else:
            for i in range(len(avg_d4)):
                if abs(dist_to_d4 - avg_d4[i]) < check_dist:
                    check_dist = avg_d4[i]
                    best_roll = i + 1
        return best_roll
    '''

    '''
    def wait_to_swap_strategy(score, opponent_score):
        """
        The goal with this strategy is simple: slow roll until your opponent is at about 60 and swap them
        """

        # I have literally no clue how to make this happen

        

        if lead < -25 and bacon_score * 2 == opponent_score: # Always check for a big swap first
            return 0

    '''


##########################
# Command Line Interface #
##########################

# Note: Functions in this section do not need to be changed.  They use features
#       of Python not yet covered in the course.

def get_int(prompt, min):
    """Return an integer greater than or equal to MIN, given by the user."""
    choice = input(prompt)
    while not choice.isnumeric() or int(choice) < min:
        print('Please enter an integer greater than or equal to', min)
        choice = input(prompt)
    return int(choice)

def interactive_dice():
    """A dice where the outcomes are provided by the user."""
    return get_int('Result of dice roll: ', 1)

def make_interactive_strategy(player):
    """Return a strategy for which the user provides the number of rolls."""
    prompt = 'Number of rolls for Player {0}: '.format(player)
    def interactive_strategy(score, opp_score):
        if player == 1:
            score, opp_score = opp_score, score
        print(score, 'vs.', opp_score)
        choice = get_int(prompt, 0)
        return choice
    return interactive_strategy

def roll_dice_interactive():
    """Interactively call roll_dice."""
    num_rolls = get_int('Number of rolls: ', 1)
    turn_total = roll_dice(num_rolls, interactive_dice)
    print('Turn total:', turn_total)

def take_turn_interactive():
    """Interactively call take_turn."""
    num_rolls = get_int('Number of rolls: ', 0)
    opp_score = get_int('Opponent score: ', 0)
    turn_total = take_turn(num_rolls, opp_score, interactive_dice)
    print('Turn total:', turn_total)

def play_interactive():
    """Interactively call play."""
    strategy0 = make_interactive_strategy(0)
    strategy1 = make_interactive_strategy(1)
    score0, score1 = play(strategy0, strategy1)
    print('Final scores:', score0, 'to', score1)

@main
def run(*args):
    """Read in the command-line argument and calls corresponding functions.

    This function uses Python syntax/techniques not yet covered in this course.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Play Hog")
    parser.add_argument('--interactive', '-i', type=str,
                        help='Run interactive tests for the specified question')
    parser.add_argument('--run_experiments', '-r', action='store_true',
                        help='Runs strategy experiments')
    args = parser.parse_args()

    if args.interactive:
        test = args.interactive + '_interactive'
        if test not in globals():
            print('To use the -i option, please choose one of these:')
            print('\troll_dice', '\ttake_turn', '\tplay', sep='\n')
            exit(1)
        try:
            globals()[test]()
        except (KeyboardInterrupt, EOFError):
            print('\nQuitting interactive test')
            exit(0)
    elif args.run_experiments:
        run_experiments()
