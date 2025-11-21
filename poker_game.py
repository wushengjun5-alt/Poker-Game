#!/usr/bin/env python3
"""
Texas Hold'em Poker Game
A complete console-based No-Limit Texas Hold'em poker game with 1 human player and 5 AI opponents.

Run with: python poker_game.py
"""

import random
from enum import IntEnum
from collections import Counter
from itertools import combinations
from typing import List, Tuple, Optional, Dict

# =============================================================================
# CONFIGURATION - Modify these values to customize the game
# =============================================================================
STARTING_CHIPS = 1000
SMALL_BLIND = 10
BIG_BLIND = 20
NUM_AI_PLAYERS = 5


# =============================================================================
# CARD AND DECK CLASSES
# =============================================================================
class Suit(IntEnum):
    """Card suits with integer values for comparison."""
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


class Rank(IntEnum):
    """Card ranks from 2 to Ace (14)."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card:
    """Represents a single playing card."""

    SUIT_SYMBOLS = {Suit.CLUBS: '♣', Suit.DIAMONDS: '♦', Suit.HEARTS: '♥', Suit.SPADES: '♠'}
    RANK_SYMBOLS = {
        Rank.TWO: '2', Rank.THREE: '3', Rank.FOUR: '4', Rank.FIVE: '5',
        Rank.SIX: '6', Rank.SEVEN: '7', Rank.EIGHT: '8', Rank.NINE: '9',
        Rank.TEN: '10', Rank.JACK: 'J', Rank.QUEEN: 'Q', Rank.KING: 'K', Rank.ACE: 'A'
    }

    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.RANK_SYMBOLS[self.rank]}{self.SUIT_SYMBOLS[self.suit]}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class Deck:
    """A standard 52-card deck that can be shuffled and dealt from."""

    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        """Reset the deck to a full 52 cards."""
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        """Deal cards from the top of the deck."""
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

    def deal_one(self) -> Card:
        """Deal a single card."""
        return self.deal(1)[0]


# =============================================================================
# HAND EVALUATION
# =============================================================================
class HandRank(IntEnum):
    """Poker hand rankings from lowest to highest."""
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class HandEvaluator:
    """Evaluates poker hands and determines the best 5-card hand from 7 cards."""

    HAND_NAMES = {
        HandRank.HIGH_CARD: "High Card",
        HandRank.ONE_PAIR: "One Pair",
        HandRank.TWO_PAIR: "Two Pair",
        HandRank.THREE_OF_A_KIND: "Three of a Kind",
        HandRank.STRAIGHT: "Straight",
        HandRank.FLUSH: "Flush",
        HandRank.FULL_HOUSE: "Full House",
        HandRank.FOUR_OF_A_KIND: "Four of a Kind",
        HandRank.STRAIGHT_FLUSH: "Straight Flush",
        HandRank.ROYAL_FLUSH: "Royal Flush"
    }

    @staticmethod
    def evaluate(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[int], List[Card]]:
        """
        Evaluate the best 5-card poker hand from hole cards and community cards.

        Returns:
            Tuple of (HandRank, tiebreaker_values, best_5_cards)
            tiebreaker_values is a list of integers used to break ties between same-ranked hands
        """
        all_cards = hole_cards + community_cards
        best_hand = None
        best_rank = None
        best_tiebreaker = None

        # Check all possible 5-card combinations
        for combo in combinations(all_cards, 5):
            cards = list(combo)
            rank, tiebreaker = HandEvaluator._evaluate_five(cards)

            if best_rank is None or rank > best_rank or (rank == best_rank and tiebreaker > best_tiebreaker):
                best_rank = rank
                best_tiebreaker = tiebreaker
                best_hand = cards

        return best_rank, best_tiebreaker, best_hand

    @staticmethod
    def _evaluate_five(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """Evaluate exactly 5 cards and return (rank, tiebreaker_values)."""
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        rank_counts = Counter(ranks)

        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._check_straight(ranks)

        # Check for straight flush / royal flush
        if is_flush and is_straight:
            if straight_high == Rank.ACE:
                return HandRank.ROYAL_FLUSH, [straight_high]
            return HandRank.STRAIGHT_FLUSH, [straight_high]

        # Four of a kind
        if 4 in rank_counts.values():
            quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandRank.FOUR_OF_A_KIND, [quad_rank, kicker]

        # Full house
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            return HandRank.FULL_HOUSE, [trips_rank, pair_rank]

        # Flush
        if is_flush:
            return HandRank.FLUSH, ranks

        # Straight
        if is_straight:
            return HandRank.STRAIGHT, [straight_high]

        # Three of a kind
        if 3 in rank_counts.values():
            trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return HandRank.THREE_OF_A_KIND, [trips_rank] + kickers

        # Two pair
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        if len(pairs) == 2:
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandRank.TWO_PAIR, pairs + [kicker]

        # One pair
        if len(pairs) == 1:
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return HandRank.ONE_PAIR, pairs + kickers

        # High card
        return HandRank.HIGH_CARD, ranks

    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        """Check if ranks form a straight. Returns (is_straight, high_card)."""
        unique_ranks = sorted(set(ranks), reverse=True)
        if len(unique_ranks) != 5:
            return False, 0

        # Normal straight check
        if unique_ranks[0] - unique_ranks[4] == 4:
            return True, unique_ranks[0]

        # Ace-low straight (A-2-3-4-5, wheel)
        if unique_ranks == [Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO]:
            return True, Rank.FIVE  # 5-high straight

        return False, 0

    @staticmethod
    def get_hand_name(rank: HandRank) -> str:
        """Get the human-readable name of a hand rank."""
        return HandEvaluator.HAND_NAMES[rank]


# =============================================================================
# PLAYER CLASSES
# =============================================================================
class Player:
    """Base class for a poker player."""

    def __init__(self, name: str, chips: int, is_human: bool = False):
        self.name = name
        self.chips = chips
        self.is_human = is_human
        self.hole_cards: List[Card] = []
        self.current_bet = 0
        self.is_folded = False
        self.is_all_in = False

    def reset_for_hand(self):
        """Reset player state for a new hand."""
        self.hole_cards = []
        self.current_bet = 0
        self.is_folded = False
        self.is_all_in = False

    def receive_cards(self, cards: List[Card]):
        """Receive hole cards."""
        self.hole_cards = cards

    def bet(self, amount: int) -> int:
        """
        Place a bet, handling all-in situations.
        Returns the actual amount bet.
        """
        actual_bet = min(amount, self.chips)
        self.chips -= actual_bet
        self.current_bet += actual_bet
        if self.chips == 0:
            self.is_all_in = True
        return actual_bet

    def fold(self):
        """Fold the hand."""
        self.is_folded = True

    def is_active(self) -> bool:
        """Check if player is still active in the hand (not folded and not all-in)."""
        return not self.is_folded and not self.is_all_in

    def is_in_hand(self) -> bool:
        """Check if player is still in the hand (not folded)."""
        return not self.is_folded

    def get_action(self, game_state: dict) -> Tuple[str, int]:
        """
        Determine the player's action. Override in subclasses.
        Returns: (action_type, amount) where action_type is 'fold', 'check', 'call', 'bet', 'raise'
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """Human player controlled via console input."""

    def __init__(self, name: str, chips: int):
        super().__init__(name, chips, is_human=True)

    def get_action(self, game_state: dict) -> Tuple[str, int]:
        """Get action from human player via console input."""
        current_bet = game_state['current_bet']
        to_call = current_bet - self.current_bet
        min_raise = game_state['min_raise']
        pot = game_state['pot']

        print(f"\n{'='*50}")
        print(f"Your turn, {self.name}!")
        print(f"Your cards: {self.hole_cards[0]} {self.hole_cards[1]}")
        if game_state['community_cards']:
            print(f"Community cards: {' '.join(str(c) for c in game_state['community_cards'])}")
        print(f"Pot: {pot} | Your chips: {self.chips} | Current bet to you: {to_call}")

        while True:
            # Build available actions
            actions = ['fold']
            if to_call == 0:
                actions.append('check')
                if self.chips > 0:
                    actions.append('bet')
            else:
                if to_call <= self.chips:
                    actions.append('call')
                if self.chips > to_call:
                    actions.append('raise')
                elif self.chips > 0 and self.chips <= to_call:
                    actions.append('all-in')

            print(f"Available actions: {', '.join(actions)}")
            action = input("Your action: ").strip().lower()

            if action == 'fold':
                return 'fold', 0

            elif action == 'check' and to_call == 0:
                return 'check', 0

            elif action == 'call' and to_call > 0:
                return 'call', min(to_call, self.chips)

            elif action == 'all-in' or (action == 'call' and self.chips <= to_call):
                return 'call', self.chips

            elif action == 'bet' and to_call == 0:
                while True:
                    try:
                        amount = int(input(f"Bet amount (min {min_raise}, max {self.chips}): "))
                        if amount < min_raise and amount != self.chips:
                            print(f"Minimum bet is {min_raise} (or all-in for {self.chips})")
                        elif amount > self.chips:
                            print(f"You only have {self.chips} chips")
                        elif amount <= 0:
                            print("Bet must be positive")
                        else:
                            return 'bet', amount
                    except ValueError:
                        print("Please enter a valid number")

            elif action == 'raise' and to_call > 0 and self.chips > to_call:
                while True:
                    try:
                        total = int(input(f"Raise to total (min {current_bet + min_raise}, max {self.current_bet + self.chips}): "))
                        raise_amount = total - self.current_bet
                        if total < current_bet + min_raise and raise_amount != self.chips:
                            print(f"Minimum raise is to {current_bet + min_raise}")
                        elif raise_amount > self.chips:
                            print(f"You can only raise to {self.current_bet + self.chips}")
                        elif raise_amount <= to_call:
                            print(f"Must raise more than the call amount of {to_call}")
                        else:
                            return 'raise', raise_amount
                    except ValueError:
                        print("Please enter a valid number")

            else:
                print("Invalid action. Please try again.")


class AIPlayer(Player):
    """AI-controlled player with simple decision logic."""

    def __init__(self, name: str, chips: int, aggression: float = 0.5):
        super().__init__(name, chips, is_human=False)
        self.aggression = aggression  # 0-1, higher = more aggressive

    def get_action(self, game_state: dict) -> Tuple[str, int]:
        """
        Determine AI action based on hand strength, position, and randomness.
        Uses a simple heuristic approach.
        """
        current_bet = game_state['current_bet']
        to_call = current_bet - self.current_bet
        min_raise = game_state['min_raise']
        pot = game_state['pot']
        community_cards = game_state['community_cards']
        position = game_state.get('position', 0)  # 0 = early, higher = later

        # Calculate hand strength (0-1)
        hand_strength = self._evaluate_hand_strength(community_cards)

        # Position bonus (later position = play more hands)
        position_bonus = position * 0.05

        # Add randomness
        randomness = random.uniform(-0.15, 0.15)

        # Final play score
        play_score = hand_strength + position_bonus + randomness + (self.aggression * 0.1)

        # Pot odds consideration
        if to_call > 0 and pot > 0:
            pot_odds = to_call / (pot + to_call)
            # If pot odds are good relative to hand strength, more likely to call
            if hand_strength > pot_odds:
                play_score += 0.1

        # Decision making
        if to_call == 0:  # Can check or bet
            if play_score > 0.7 and self.chips > min_raise:
                # Strong hand - bet
                bet_size = self._calculate_bet_size(pot, hand_strength)
                return 'bet', min(bet_size, self.chips)
            else:
                return 'check', 0

        else:  # Must call, raise, or fold
            if play_score < 0.3:
                # Weak hand - fold (but sometimes bluff)
                if random.random() < self.aggression * 0.15:
                    return 'call', min(to_call, self.chips)
                return 'fold', 0

            elif play_score < 0.6:
                # Medium hand - call
                if to_call <= self.chips:
                    return 'call', min(to_call, self.chips)
                elif to_call <= self.chips * 2:
                    return 'call', self.chips  # All-in
                return 'fold', 0

            else:
                # Strong hand - raise or call
                if random.random() < 0.6 and self.chips > to_call:
                    raise_amount = to_call + self._calculate_bet_size(pot, hand_strength)
                    return 'raise', min(raise_amount, self.chips)
                return 'call', min(to_call, self.chips)

    def _evaluate_hand_strength(self, community_cards: List[Card]) -> float:
        """
        Evaluate current hand strength on a scale of 0-1.
        Pre-flop uses hole card rankings, post-flop uses actual hand evaluation.
        """
        if not community_cards:
            # Pre-flop: evaluate hole cards
            return self._preflop_strength()

        # Post-flop: use actual hand evaluation
        rank, _, _ = HandEvaluator.evaluate(self.hole_cards, community_cards)

        # Convert hand rank to 0-1 scale
        base_strength = {
            HandRank.HIGH_CARD: 0.1,
            HandRank.ONE_PAIR: 0.3,
            HandRank.TWO_PAIR: 0.5,
            HandRank.THREE_OF_A_KIND: 0.6,
            HandRank.STRAIGHT: 0.7,
            HandRank.FLUSH: 0.75,
            HandRank.FULL_HOUSE: 0.85,
            HandRank.FOUR_OF_A_KIND: 0.95,
            HandRank.STRAIGHT_FLUSH: 0.98,
            HandRank.ROYAL_FLUSH: 1.0
        }
        return base_strength.get(rank, 0.1)

    def _preflop_strength(self) -> float:
        """Evaluate pre-flop hand strength based on hole cards."""
        c1, c2 = self.hole_cards
        r1, r2 = c1.rank, c2.rank
        high, low = max(r1, r2), min(r1, r2)
        is_suited = c1.suit == c2.suit
        is_pair = r1 == r2

        # Base score from high card
        score = (high - 2) / 12 * 0.4  # 0 to 0.4

        # Pair bonus
        if is_pair:
            score += 0.3 + (high - 2) / 12 * 0.2

        # Suited bonus
        if is_suited:
            score += 0.1

        # Connected cards bonus (straights)
        gap = high - low
        if gap <= 4 and not is_pair:
            score += (5 - gap) * 0.03

        # Premium hands boost
        if is_pair and high >= Rank.TEN:
            score += 0.15
        if high == Rank.ACE and low >= Rank.TEN:
            score += 0.1

        return min(score, 1.0)

    def _calculate_bet_size(self, pot: int, hand_strength: float) -> int:
        """Calculate an appropriate bet size based on pot and hand strength."""
        # Bet between 1/3 and full pot based on hand strength
        pot_fraction = 0.33 + hand_strength * 0.67
        bet_size = int(pot * pot_fraction)
        return max(bet_size, BIG_BLIND)


# =============================================================================
# POKER GAME CLASS
# =============================================================================
class PokerGame:
    """
    Main game controller for Texas Hold'em.
    Manages the game flow, betting rounds, pots, and winner determination.
    """

    def __init__(self):
        self.players: List[Player] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.side_pots: List[Tuple[int, List[Player]]] = []  # (amount, eligible_players)
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.dealer_index = 0
        self.hand_number = 0

    def setup_game(self):
        """Initialize the game with players."""
        print("\n" + "="*60)
        print("       TEXAS HOLD'EM POKER")
        print("="*60)

        name = input("\nEnter your name: ").strip() or "Player"
        self.players.append(HumanPlayer(name, STARTING_CHIPS))

        # AI personalities with varying aggression levels
        ai_names = ["Alice", "Bob", "Charlie", "Diana", "Eddie"]
        aggressions = [0.3, 0.5, 0.7, 0.4, 0.6]

        for i in range(NUM_AI_PLAYERS):
            self.players.append(AIPlayer(ai_names[i], STARTING_CHIPS, aggressions[i]))

        self.dealer_index = random.randint(0, len(self.players) - 1)
        print(f"\nGame started with {len(self.players)} players. Good luck!")

    def play(self):
        """Main game loop."""
        self.setup_game()

        while True:
            active_players = [p for p in self.players if p.chips > 0]

            if len(active_players) < 2:
                break

            if self.players[0].chips == 0:  # Human is out
                print("\nYou're out of chips! Game over.")
                break

            self.play_hand()

            # Remove broke players
            self.players = [p for p in self.players if p.chips > 0]

            if len(self.players) < 2:
                break

            if self.players[0].chips == 0:
                break

            # Ask to continue
            print("\n" + "-"*40)
            choice = input("Play another hand? (y/n): ").strip().lower()
            if choice != 'y' and choice != 'yes':
                break

        self.show_final_results()

    def play_hand(self):
        """Play a single hand of poker."""
        self.hand_number += 1
        self.reset_for_hand()

        print("\n" + "="*60)
        print(f"                    HAND #{self.hand_number}")
        print("="*60)

        # Show positions and chip counts
        self.show_positions()

        # Post blinds
        self.post_blinds()

        # Deal hole cards
        self.deal_hole_cards()

        # Pre-flop betting
        print("\n--- PRE-FLOP ---")
        if not self.betting_round(preflop=True):
            return self.end_hand()

        # Flop
        print("\n--- FLOP ---")
        self.deal_community_cards(3)
        self.show_community_cards()
        if not self.betting_round():
            return self.end_hand()

        # Turn
        print("\n--- TURN ---")
        self.deal_community_cards(1)
        self.show_community_cards()
        if not self.betting_round():
            return self.end_hand()

        # River
        print("\n--- RIVER ---")
        self.deal_community_cards(1)
        self.show_community_cards()
        if not self.betting_round():
            return self.end_hand()

        # Showdown
        self.showdown()

    def reset_for_hand(self):
        """Reset game state for a new hand."""
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.side_pots = []
        self.current_bet = 0
        self.min_raise = BIG_BLIND

        for player in self.players:
            player.reset_for_hand()

        # Rotate dealer
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

    def get_position_index(self, offset: int) -> int:
        """Get player index at offset from dealer."""
        return (self.dealer_index + offset) % len(self.players)

    def show_positions(self):
        """Display current positions and chip counts."""
        print("\nPositions and chip counts:")
        for i, player in enumerate(self.players):
            position = ""
            if i == self.dealer_index:
                position = "(Dealer)"
            elif i == self.get_position_index(1):
                position = "(Small Blind)"
            elif i == self.get_position_index(2):
                position = "(Big Blind)"

            marker = ">>> " if player.is_human else "    "
            print(f"{marker}{player.name}: {player.chips} chips {position}")

    def post_blinds(self):
        """Post small and big blinds."""
        sb_index = self.get_position_index(1)
        bb_index = self.get_position_index(2)

        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]

        sb_amount = sb_player.bet(SMALL_BLIND)
        bb_amount = bb_player.bet(BIG_BLIND)

        self.pot = sb_amount + bb_amount
        self.current_bet = BIG_BLIND

        print(f"\n{sb_player.name} posts small blind: {sb_amount}")
        print(f"{bb_player.name} posts big blind: {bb_amount}")

    def deal_hole_cards(self):
        """Deal 2 hole cards to each player."""
        for player in self.players:
            player.receive_cards(self.deck.deal(2))

        human = self.players[0]
        print(f"\nYour cards: {human.hole_cards[0]} {human.hole_cards[1]}")

    def deal_community_cards(self, count: int):
        """Deal community cards (burn one first)."""
        self.deck.deal_one()  # Burn card
        self.community_cards.extend(self.deck.deal(count))

    def show_community_cards(self):
        """Display current community cards."""
        cards_str = ' '.join(str(c) for c in self.community_cards)
        print(f"Community cards: {cards_str}")

    def betting_round(self, preflop: bool = False) -> bool:
        """
        Execute a betting round.
        Returns False if only one player remains (others folded), True otherwise.
        """
        # Reset current bets for new round (except pre-flop where blinds are already posted)
        if not preflop:
            for player in self.players:
                self.pot += player.current_bet  # Should already be in pot, but ensure
                player.current_bet = 0
            self.current_bet = 0
            self.min_raise = BIG_BLIND

        # Determine starting player
        if preflop:
            # Start after big blind
            start_index = self.get_position_index(3)
        else:
            # Start after dealer
            start_index = self.get_position_index(1)

        # Track who needs to act
        players_to_act = set(p for p in self.players if p.is_active())
        last_raiser = None

        current_index = start_index
        while players_to_act:
            player = self.players[current_index]

            # Skip folded or all-in players
            if not player.is_active():
                current_index = (current_index + 1) % len(self.players)
                continue

            if player not in players_to_act:
                current_index = (current_index + 1) % len(self.players)
                continue

            # Check if only one active player remains
            active_in_hand = [p for p in self.players if p.is_in_hand()]
            if len(active_in_hand) == 1:
                return False

            # Get player action
            game_state = {
                'current_bet': self.current_bet,
                'pot': self.pot,
                'min_raise': self.min_raise,
                'community_cards': self.community_cards,
                'position': (current_index - self.dealer_index) % len(self.players)
            }

            action, amount = player.get_action(game_state)
            self._process_action(player, action, amount)

            # Update who needs to act
            players_to_act.discard(player)

            if action in ('raise', 'bet'):
                # Everyone else needs to act again
                last_raiser = player
                players_to_act = set(p for p in self.players if p.is_active() and p != player)

            current_index = (current_index + 1) % len(self.players)

        # Collect bets into pot
        for player in self.players:
            self.pot += player.current_bet
            player.current_bet = 0

        return len([p for p in self.players if p.is_in_hand()]) > 1

    def _process_action(self, player: Player, action: str, amount: int):
        """Process a player's action."""
        if action == 'fold':
            player.fold()
            print(f"{player.name} folds")

        elif action == 'check':
            print(f"{player.name} checks")

        elif action == 'call':
            actual = player.bet(amount)
            all_in_str = " (ALL-IN)" if player.is_all_in else ""
            print(f"{player.name} calls {actual}{all_in_str}")

        elif action == 'bet':
            actual = player.bet(amount)
            self.current_bet = player.current_bet
            self.min_raise = amount
            all_in_str = " (ALL-IN)" if player.is_all_in else ""
            print(f"{player.name} bets {actual}{all_in_str}")

        elif action == 'raise':
            actual = player.bet(amount)
            raise_amount = player.current_bet - self.current_bet
            self.min_raise = max(self.min_raise, raise_amount)
            self.current_bet = player.current_bet
            all_in_str = " (ALL-IN)" if player.is_all_in else ""
            print(f"{player.name} raises to {player.current_bet}{all_in_str}")

    def end_hand(self):
        """End the hand early (everyone folded except one)."""
        winner = [p for p in self.players if p.is_in_hand()][0]
        winner.chips += self.pot
        print(f"\n{winner.name} wins {self.pot} chips (everyone else folded)")
        self.show_chip_counts()

    def showdown(self):
        """Determine winner(s) at showdown."""
        print("\n" + "="*50)
        print("              SHOWDOWN")
        print("="*50)

        remaining = [p for p in self.players if p.is_in_hand()]

        # Evaluate each player's hand
        hands = []
        for player in remaining:
            rank, tiebreaker, best_cards = HandEvaluator.evaluate(
                player.hole_cards, self.community_cards
            )
            hands.append((player, rank, tiebreaker, best_cards))

            # Show player's cards and hand
            cards_str = f"{player.hole_cards[0]} {player.hole_cards[1]}"
            best_str = ' '.join(str(c) for c in best_cards)
            hand_name = HandEvaluator.get_hand_name(rank)
            print(f"{player.name}: {cards_str} -> {hand_name} ({best_str})")

        # Sort by hand strength (rank first, then tiebreaker)
        hands.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Find winner(s) - may be ties
        winners = [hands[0]]
        for h in hands[1:]:
            if h[1] == winners[0][1] and h[2] == winners[0][2]:
                winners.append(h)
            else:
                break

        # Distribute pot
        pot_per_winner = self.pot // len(winners)
        remainder = self.pot % len(winners)

        print(f"\nPot: {self.pot}")
        if len(winners) == 1:
            winner = winners[0][0]
            winner.chips += self.pot
            print(f"{winner.name} wins {self.pot} chips with {HandEvaluator.get_hand_name(winners[0][1])}!")
        else:
            print("Split pot!")
            for i, (player, rank, _, _) in enumerate(winners):
                award = pot_per_winner + (1 if i < remainder else 0)
                player.chips += award
                print(f"{player.name} wins {award} chips with {HandEvaluator.get_hand_name(rank)}")

        self.show_chip_counts()

    def show_chip_counts(self):
        """Display current chip counts for all players."""
        print("\nChip counts:")
        for player in self.players:
            marker = ">>> " if player.is_human else "    "
            status = " (OUT)" if player.chips == 0 else ""
            print(f"{marker}{player.name}: {player.chips}{status}")

    def show_final_results(self):
        """Display final game results."""
        print("\n" + "="*60)
        print("                 GAME OVER")
        print("="*60)

        # Sort by chips
        all_players = sorted(self.players, key=lambda p: p.chips, reverse=True)

        print("\nFinal standings:")
        for i, player in enumerate(all_players, 1):
            marker = " (YOU)" if player.is_human else ""
            print(f"  {i}. {player.name}: {player.chips} chips{marker}")

        human = next((p for p in self.players if p.is_human), None)
        if human:
            profit = human.chips - STARTING_CHIPS
            if profit > 0:
                print(f"\nYou won {profit} chips! Great game!")
            elif profit < 0:
                print(f"\nYou lost {-profit} chips. Better luck next time!")
            else:
                print("\nYou broke even!")

        print("\nThanks for playing!")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    game = PokerGame()
    game.play()
