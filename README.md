# What is this project?
This is a spinoff of a project included in UC Berkeley's CIS 61 class. The primary goals of the project are as follows:
* Plot out (or at least define) the "strategy space" of the game.
* Create a search algorithm that finds good strategies (or good sets of strategies, as I will discuss later).
* Somehow prove that the discovered strategy is the best possible strategy.
If any part of that interests you, please read below for more details on the environment and scope of the project!

# What is Hog?
Hog is a dice rolling "push your luck" type game where the goal is to get 100 points. Two players take turns back and forth until one player reaches this goal, at which point the game is finished. These are all of the rules of the game:
* At the start of every turn, check if the sum of both scores is a multiple of seven.
  * If yes, the active player will roll d4s (four sided-dice).
  * If no, the active player will roll d6s (six-sided-dice).
* The active player can now choose a number from 0 to 10.
  * If the active player chose 0, they get an amount of points equal to the largest digit in their opponent's score + 1. This is called Free Bacon. For example, choosing to take Free Bacon when your opponent has 72 points will yield you (7+1) = 8 points.
  * If the player did not choose 0, they roll that many dice. If any die lands on a 1, the active player gets a total of 1 point. If not, they get the sum of all dice rolled.
* At the end of every turn, check if your score is exactly half or double the opponent's score. If yes, players swap scores, and play continues from that point.

# How is there any strategy here?
While it may seem that this is a game of pure chance, there is actually a surprising (which is not to say large by any means) amount of both strategic and tactical depth. For example, let's say it's your turn, you have 31 points, and your opponent has 80. On most turns, it's probably best to roll some amount of dice, but you can see that taking Free Bacon here will create a swap that is worth 40 points for you, and -40 for the opponent, resulting in an 80 point swing in your favor! You can see further strategic depth in some of the strategies I've created in hog.py.

# What is a "strategy space"?
My current methodology for evaluating strategies revolves around conceptualizing an n-dimensional space, where n is the number of parameters I'm testing. The full volume of the space is what I call a strategy space, and I think it's extremely crucial to define your strategy space when you are running tests.

# How can we define a "good" strategy?
I think the abstract definition of the _best_ strategy in a strategy space is something along the lines of, 'a strategy that has a higher winrate than all other strategies in that strategy space.' We can narrow widen the scope of that definition to include _good_ strategies in a strategy space as, 'strategies that have a higher than 50% winrate in that strategy space.'
