#!/usr/bin/env python3
"""
Texas Hold'em Poker Game - GUI Version
A complete Tkinter-based No-Limit Texas Hold'em poker game with 1 human player and 5 AI opponents.

Run with: python poker_gui.py

Structure:
- Game Engine (lines ~50-500): Card, Deck, HandEvaluator, Player, PokerEngine classes
- GUI Layer (lines ~500-900): PokerGUI class handles all Tkinter display and interaction
- Configuration (lines ~25-30): Adjust STARTING_CHIPS, SMALL_BLIND, BIG_BLIND, NUM_AI_PLAYERS
"""

import random
import tkinter as tk
from tkinter import messagebox, ttk
from enum import IntEnum
from collections import Counter
from itertools import combinations
from typing import List, Tuple, Optional, Callable

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
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


class Rank(IntEnum):
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


class Deck:
    """A standard 52-card deck."""
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

    def deal_one(self) -> Card:
        return self.deal(1)[0]


# =============================================================================
# HAND EVALUATION
# =============================================================================
class HandRank(IntEnum):
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
    """Evaluates poker hands and determines the best 5-card hand."""
    HAND_NAMES = {
        HandRank.HIGH_CARD: "High Card", HandRank.ONE_PAIR: "One Pair",
        HandRank.TWO_PAIR: "Two Pair", HandRank.THREE_OF_A_KIND: "Three of a Kind",
        HandRank.STRAIGHT: "Straight", HandRank.FLUSH: "Flush",
        HandRank.FULL_HOUSE: "Full House", HandRank.FOUR_OF_A_KIND: "Four of a Kind",
        HandRank.STRAIGHT_FLUSH: "Straight Flush", HandRank.ROYAL_FLUSH: "Royal Flush"
    }

    @staticmethod
    def evaluate(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[int], List[Card]]:
        """Evaluate best 5-card hand. Returns (rank, tiebreaker, best_cards)."""
        all_cards = hole_cards + community_cards
        best_hand, best_rank, best_tiebreaker = None, None, None

        for combo in combinations(all_cards, 5):
            cards = list(combo)
            rank, tiebreaker = HandEvaluator._evaluate_five(cards)
            if best_rank is None or rank > best_rank or (rank == best_rank and tiebreaker > best_tiebreaker):
                best_rank, best_tiebreaker, best_hand = rank, tiebreaker, cards

        return best_rank, best_tiebreaker, best_hand

    @staticmethod
    def _evaluate_five(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        rank_counts = Counter(ranks)

        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._check_straight(ranks)

        if is_flush and is_straight:
            return (HandRank.ROYAL_FLUSH if straight_high == Rank.ACE else HandRank.STRAIGHT_FLUSH), [straight_high]

        if 4 in rank_counts.values():
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandRank.FOUR_OF_A_KIND, [quad, kicker]

        if 3 in rank_counts.values() and 2 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return HandRank.FULL_HOUSE, [trips, pair]

        if is_flush:
            return HandRank.FLUSH, ranks
        if is_straight:
            return HandRank.STRAIGHT, [straight_high]

        if 3 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return HandRank.THREE_OF_A_KIND, [trips] + kickers

        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        if len(pairs) == 2:
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandRank.TWO_PAIR, pairs + [kicker]
        if len(pairs) == 1:
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return HandRank.ONE_PAIR, pairs + kickers

        return HandRank.HIGH_CARD, ranks

    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        unique = sorted(set(ranks), reverse=True)
        if len(unique) != 5:
            return False, 0
        if unique[0] - unique[4] == 4:
            return True, unique[0]
        if unique == [Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO]:
            return True, Rank.FIVE
        return False, 0

    @staticmethod
    def get_hand_name(rank: HandRank) -> str:
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
        self.status = ""

    def reset_for_hand(self):
        self.hole_cards = []
        self.current_bet = 0
        self.is_folded = False
        self.is_all_in = False
        self.status = ""

    def receive_cards(self, cards: List[Card]):
        self.hole_cards = cards

    def bet(self, amount: int) -> int:
        actual = min(amount, self.chips)
        self.chips -= actual
        self.current_bet += actual
        if self.chips == 0:
            self.is_all_in = True
            self.status = "All-in"
        return actual

    def fold(self):
        self.is_folded = True
        self.status = "Folded"

    def is_active(self) -> bool:
        return not self.is_folded and not self.is_all_in

    def is_in_hand(self) -> bool:
        return not self.is_folded


class AIPlayer(Player):
    """AI-controlled player with simple decision logic."""
    def __init__(self, name: str, chips: int, aggression: float = 0.5):
        super().__init__(name, chips, is_human=False)
        self.aggression = aggression

    def decide_action(self, game_state: dict) -> Tuple[str, int]:
        """Determine AI action based on hand strength and game state."""
        current_bet = game_state['current_bet']
        to_call = current_bet - self.current_bet
        min_raise = game_state['min_raise']
        pot = game_state['pot']
        community = game_state['community_cards']

        hand_strength = self._evaluate_strength(community)
        play_score = hand_strength + random.uniform(-0.15, 0.15) + self.aggression * 0.1

        if to_call == 0:
            if play_score > 0.7 and self.chips > min_raise:
                bet_size = max(int(pot * (0.33 + hand_strength * 0.67)), BIG_BLIND)
                return 'bet', min(bet_size, self.chips)
            return 'check', 0
        else:
            if play_score < 0.3:
                if random.random() < self.aggression * 0.15:
                    return 'call', min(to_call, self.chips)
                return 'fold', 0
            elif play_score < 0.6:
                return 'call', min(to_call, self.chips)
            else:
                if random.random() < 0.6 and self.chips > to_call:
                    raise_amt = to_call + max(int(pot * 0.5), min_raise)
                    return 'raise', min(raise_amt, self.chips)
                return 'call', min(to_call, self.chips)

    def _evaluate_strength(self, community: List[Card]) -> float:
        if not community:
            return self._preflop_strength()
        rank, _, _ = HandEvaluator.evaluate(self.hole_cards, community)
        strengths = {
            HandRank.HIGH_CARD: 0.1, HandRank.ONE_PAIR: 0.3, HandRank.TWO_PAIR: 0.5,
            HandRank.THREE_OF_A_KIND: 0.6, HandRank.STRAIGHT: 0.7, HandRank.FLUSH: 0.75,
            HandRank.FULL_HOUSE: 0.85, HandRank.FOUR_OF_A_KIND: 0.95,
            HandRank.STRAIGHT_FLUSH: 0.98, HandRank.ROYAL_FLUSH: 1.0
        }
        return strengths.get(rank, 0.1)

    def _preflop_strength(self) -> float:
        c1, c2 = self.hole_cards
        high, low = max(c1.rank, c2.rank), min(c1.rank, c2.rank)
        is_suited = c1.suit == c2.suit
        is_pair = c1.rank == c2.rank

        score = (high - 2) / 12 * 0.4
        if is_pair:
            score += 0.3 + (high - 2) / 12 * 0.2
        if is_suited:
            score += 0.1
        gap = high - low
        if gap <= 4 and not is_pair:
            score += (5 - gap) * 0.03
        if is_pair and high >= Rank.TEN:
            score += 0.15
        if high == Rank.ACE and low >= Rank.TEN:
            score += 0.1
        return min(score, 1.0)


# =============================================================================
# POKER ENGINE (Game Logic - UI Independent)
# =============================================================================
class PokerEngine:
    """
    Core poker game engine. Manages game state, betting, and hand evaluation.
    This class is UI-independent and can be used with any interface.
    """

    # Game phases
    PHASE_WAITING = "waiting"
    PHASE_PREFLOP = "preflop"
    PHASE_FLOP = "flop"
    PHASE_TURN = "turn"
    PHASE_RIVER = "river"
    PHASE_SHOWDOWN = "showdown"
    PHASE_HAND_OVER = "hand_over"

    def __init__(self):
        self.players: List[Player] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.dealer_index = 0
        self.current_player_index = 0
        self.hand_number = 0
        self.phase = self.PHASE_WAITING
        self.last_raiser_index = -1
        self.action_count = 0
        self.winners: List[Tuple[Player, int, str]] = []  # (player, chips_won, hand_name)
        self.message = ""

    def setup_players(self, human_name: str = "You"):
        """Initialize players for the game."""
        self.players = [Player(human_name, STARTING_CHIPS, is_human=True)]
        ai_names = ["Alice", "Bob", "Charlie", "Diana", "Eddie"]
        aggressions = [0.3, 0.5, 0.7, 0.4, 0.6]
        for i in range(NUM_AI_PLAYERS):
            self.players.append(AIPlayer(ai_names[i], STARTING_CHIPS, aggressions[i]))
        self.dealer_index = random.randint(0, len(self.players) - 1)

    def start_new_hand(self):
        """Start a new hand."""
        # Remove broke players
        self.players = [p for p in self.players if p.chips > 0]
        if len(self.players) < 2:
            self.phase = self.PHASE_HAND_OVER
            self.message = "Game Over - Not enough players!"
            return

        self.hand_number += 1
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.winners = []
        self.message = f"Hand #{self.hand_number}"

        for p in self.players:
            p.reset_for_hand()

        self.dealer_index = self.dealer_index % len(self.players)

        # Post blinds
        sb_idx = (self.dealer_index + 1) % len(self.players)
        bb_idx = (self.dealer_index + 2) % len(self.players)

        sb_amt = self.players[sb_idx].bet(SMALL_BLIND)
        bb_amt = self.players[bb_idx].bet(BIG_BLIND)
        self.pot = sb_amt + bb_amt
        self.current_bet = BIG_BLIND

        self.players[sb_idx].status = f"SB: {sb_amt}"
        self.players[bb_idx].status = f"BB: {bb_amt}"

        # Deal hole cards
        for p in self.players:
            p.receive_cards(self.deck.deal(2))

        # Start preflop
        self.phase = self.PHASE_PREFLOP
        self.current_player_index = (bb_idx + 1) % len(self.players)
        self.last_raiser_index = bb_idx
        self.action_count = 0

        # Skip to first active player
        self._advance_to_active_player()

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is."""
        if self.phase in [self.PHASE_WAITING, self.PHASE_SHOWDOWN, self.PHASE_HAND_OVER]:
            return None
        return self.players[self.current_player_index]

    def get_game_state(self) -> dict:
        """Return current game state for UI or AI decision making."""
        return {
            'pot': self.pot,
            'current_bet': self.current_bet,
            'min_raise': self.min_raise,
            'community_cards': self.community_cards,
            'phase': self.phase,
            'players': self.players,
            'current_player_index': self.current_player_index,
            'dealer_index': self.dealer_index,
            'message': self.message,
            'winners': self.winners,
            'hand_number': self.hand_number
        }

    def apply_action(self, action: str, amount: int = 0) -> bool:
        """
        Apply an action for the current player.
        Returns True if action was valid, False otherwise.
        """
        player = self.get_current_player()
        if not player:
            return False

        to_call = self.current_bet - player.current_bet

        if action == 'fold':
            player.fold()
            self.message = f"{player.name} folds"

        elif action == 'check':
            if to_call > 0:
                return False
            player.status = "Check"
            self.message = f"{player.name} checks"

        elif action == 'call':
            actual = player.bet(to_call)
            self.pot += actual
            player.status = f"Call {actual}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} calls {actual}"

        elif action == 'bet':
            if to_call > 0 or amount < self.min_raise:
                return False
            actual = player.bet(amount)
            self.pot += actual
            self.current_bet = player.current_bet
            self.min_raise = amount
            self.last_raiser_index = self.current_player_index
            player.status = f"Bet {actual}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} bets {actual}"

        elif action == 'raise':
            if to_call == 0:
                return False
            actual = player.bet(amount)
            self.pot += actual
            raise_amount = player.current_bet - self.current_bet
            if raise_amount > 0:
                self.min_raise = max(self.min_raise, raise_amount)
            self.current_bet = player.current_bet
            self.last_raiser_index = self.current_player_index
            player.status = f"Raise to {player.current_bet}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} raises to {player.current_bet}"

        else:
            return False

        self.action_count += 1
        self._advance_game()
        return True

    def _advance_to_active_player(self):
        """Move to the next active player."""
        for _ in range(len(self.players)):
            player = self.players[self.current_player_index]
            if player.is_active():
                return
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def _advance_game(self):
        """Advance the game state after an action."""
        # Check if hand is over (only one player left)
        active_in_hand = [p for p in self.players if p.is_in_hand()]
        if len(active_in_hand) == 1:
            winner = active_in_hand[0]
            winner.chips += self.pot
            self.winners = [(winner, self.pot, "Last player standing")]
            self.message = f"{winner.name} wins {self.pot} (others folded)"
            self.phase = self.PHASE_HAND_OVER
            self.dealer_index = (self.dealer_index + 1) % len(self.players)
            return

        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self._advance_to_active_player()

        # Check if betting round is complete
        if self._is_betting_round_complete():
            self._end_betting_round()

    def _is_betting_round_complete(self) -> bool:
        """Check if current betting round is complete."""
        active_players = [p for p in self.players if p.is_active()]

        if not active_players:
            return True

        # All active players must have matched the current bet
        for p in active_players:
            if p.current_bet < self.current_bet:
                return False

        # Everyone has had a chance to act since the last raise
        if self.action_count < len([p for p in self.players if p.is_in_hand()]):
            return False

        # The action has come back to the last raiser (or everyone checked)
        if self.current_player_index == self.last_raiser_index:
            return True

        # Edge case: if no raises happened this round and we're back to start
        return self.action_count >= len([p for p in self.players if p.is_in_hand()])

    def _end_betting_round(self):
        """End the current betting round and move to next phase."""
        # Collect bets
        for p in self.players:
            p.current_bet = 0

        self.current_bet = 0
        self.action_count = 0

        # Check if we can continue (need at least 2 players who can act, or go to showdown)
        active_not_allin = [p for p in self.players if p.is_active()]

        if self.phase == self.PHASE_PREFLOP:
            self.phase = self.PHASE_FLOP
            self.deck.deal_one()  # Burn
            self.community_cards.extend(self.deck.deal(3))
            self.message = "Flop dealt"

        elif self.phase == self.PHASE_FLOP:
            self.phase = self.PHASE_TURN
            self.deck.deal_one()
            self.community_cards.extend(self.deck.deal(1))
            self.message = "Turn dealt"

        elif self.phase == self.PHASE_TURN:
            self.phase = self.PHASE_RIVER
            self.deck.deal_one()
            self.community_cards.extend(self.deck.deal(1))
            self.message = "River dealt"

        elif self.phase == self.PHASE_RIVER:
            self._showdown()
            return

        # Set up for next betting round
        self.current_player_index = (self.dealer_index + 1) % len(self.players)
        self.last_raiser_index = -1
        self._advance_to_active_player()

        # If only one player can act, skip to showdown
        if len(active_not_allin) <= 1:
            # Deal remaining cards and go to showdown
            while len(self.community_cards) < 5:
                self.deck.deal_one()
                self.community_cards.extend(self.deck.deal(1))
            self._showdown()

    def _showdown(self):
        """Determine winner(s) at showdown."""
        self.phase = self.PHASE_SHOWDOWN
        remaining = [p for p in self.players if p.is_in_hand()]

        hands = []
        for p in remaining:
            rank, tiebreaker, best_cards = HandEvaluator.evaluate(p.hole_cards, self.community_cards)
            hands.append((p, rank, tiebreaker, best_cards))

        hands.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Find winners
        winners = [hands[0]]
        for h in hands[1:]:
            if h[1] == winners[0][1] and h[2] == winners[0][2]:
                winners.append(h)
            else:
                break

        # Distribute pot
        pot_each = self.pot // len(winners)
        remainder = self.pot % len(winners)

        self.winners = []
        for i, (player, rank, _, _) in enumerate(winners):
            award = pot_each + (1 if i < remainder else 0)
            player.chips += award
            hand_name = HandEvaluator.get_hand_name(rank)
            self.winners.append((player, award, hand_name))
            player.status = f"Winner! {hand_name}"

        if len(winners) == 1:
            self.message = f"{winners[0][0].name} wins {self.pot} with {HandEvaluator.get_hand_name(winners[0][1])}"
        else:
            self.message = f"Split pot! {len(winners)} winners"

        self.phase = self.PHASE_HAND_OVER
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

    def is_game_over(self) -> bool:
        """Check if game is over."""
        players_with_chips = [p for p in self.players if p.chips > 0]
        human_has_chips = any(p.is_human and p.chips > 0 for p in self.players)
        return len(players_with_chips) < 2 or not human_has_chips


# =============================================================================
# TKINTER GUI
# =============================================================================
class PokerGUI:
    """
    Tkinter-based GUI for the poker game.
    Handles all display and user interaction, communicating with PokerEngine.
    """

    # Card display colors
    CARD_COLORS = {Suit.HEARTS: 'red', Suit.DIAMONDS: 'red', Suit.CLUBS: 'black', Suit.SPADES: 'black'}

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Texas Hold'em – 6 Player Table")
        self.root.geometry("900x700")
        self.root.configure(bg='#0a5c36')

        self.engine = PokerEngine()
        self.player_frames: List[dict] = []
        self.ai_delay = 800  # milliseconds between AI actions

        self._create_widgets()
        self._start_game()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='#0a5c36')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top row: AI players 1-3
        self.top_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.top_frame.pack(fill=tk.X, pady=5)

        # Middle: Community cards and pot
        self.table_frame = tk.Frame(self.main_frame, bg='#1a7c4c', relief=tk.RIDGE, bd=3)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Pot display
        self.pot_label = tk.Label(self.table_frame, text="Pot: 0", font=('Arial', 16, 'bold'),
                                   bg='#1a7c4c', fg='white')
        self.pot_label.pack(pady=10)

        # Community cards
        self.community_frame = tk.Frame(self.table_frame, bg='#1a7c4c')
        self.community_frame.pack(pady=10)
        self.community_labels = []
        for i in range(5):
            lbl = tk.Label(self.community_frame, text="", width=5, height=2,
                          font=('Arial', 14, 'bold'), relief=tk.RAISED, bg='#2a8c5c')
            lbl.pack(side=tk.LEFT, padx=3)
            self.community_labels.append(lbl)

        # Message display
        self.message_label = tk.Label(self.table_frame, text="", font=('Arial', 12),
                                       bg='#1a7c4c', fg='yellow')
        self.message_label.pack(pady=5)

        # Bottom row: AI players 4-5 and human
        self.bottom_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.bottom_frame.pack(fill=tk.X, pady=5)

        # Human player section (larger)
        self.human_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.human_frame.pack(fill=tk.X, pady=5)

        # Control buttons
        self.controls_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.controls_frame.pack(fill=tk.X, pady=5)

        # Action buttons
        self.fold_btn = tk.Button(self.controls_frame, text="Fold", command=self._on_fold,
                                   font=('Arial', 12), width=8, bg='#cc4444')
        self.fold_btn.pack(side=tk.LEFT, padx=5)

        self.check_call_btn = tk.Button(self.controls_frame, text="Check", command=self._on_check_call,
                                         font=('Arial', 12), width=10, bg='#44aa44')
        self.check_call_btn.pack(side=tk.LEFT, padx=5)

        self.bet_raise_btn = tk.Button(self.controls_frame, text="Bet", command=self._on_bet_raise,
                                        font=('Arial', 12), width=10, bg='#4444cc')
        self.bet_raise_btn.pack(side=tk.LEFT, padx=5)

        # Bet amount entry
        tk.Label(self.controls_frame, text="Amount:", bg='#0a5c36', fg='white',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=(20, 5))
        self.bet_entry = tk.Entry(self.controls_frame, font=('Arial', 12), width=8)
        self.bet_entry.pack(side=tk.LEFT, padx=5)
        self.bet_entry.insert(0, str(BIG_BLIND))

        # All-in button
        self.allin_btn = tk.Button(self.controls_frame, text="All-In", command=self._on_allin,
                                    font=('Arial', 12), width=8, bg='#aa44aa')
        self.allin_btn.pack(side=tk.LEFT, padx=5)

        # Next hand button (initially hidden)
        self.next_hand_btn = tk.Button(self.controls_frame, text="Next Hand", command=self._on_next_hand,
                                        font=('Arial', 12, 'bold'), width=12, bg='#ffaa00')
        self.next_hand_btn.pack(side=tk.RIGHT, padx=5)
        self.next_hand_btn.pack_forget()

        self._disable_controls()

    def _create_player_display(self, parent: tk.Frame, player_idx: int, is_human: bool = False) -> dict:
        """Create display widgets for a player."""
        frame = tk.Frame(parent, bg='#0f3d22', relief=tk.RAISED, bd=2)
        frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True)

        # Name label
        name_lbl = tk.Label(frame, text="", font=('Arial', 11, 'bold'), bg='#0f3d22', fg='white')
        name_lbl.pack(pady=2)

        # Cards frame
        cards_frame = tk.Frame(frame, bg='#0f3d22')
        cards_frame.pack(pady=2)

        card1_lbl = tk.Label(cards_frame, text="", width=4, height=2, font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, bg='white')
        card1_lbl.pack(side=tk.LEFT, padx=2)

        card2_lbl = tk.Label(cards_frame, text="", width=4, height=2, font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, bg='white')
        card2_lbl.pack(side=tk.LEFT, padx=2)

        # Chips label
        chips_lbl = tk.Label(frame, text="Chips: 0", font=('Arial', 10), bg='#0f3d22', fg='#ffcc00')
        chips_lbl.pack(pady=2)

        # Status label
        status_lbl = tk.Label(frame, text="", font=('Arial', 9), bg='#0f3d22', fg='#88ff88')
        status_lbl.pack(pady=2)

        return {
            'frame': frame,
            'name': name_lbl,
            'card1': card1_lbl,
            'card2': card2_lbl,
            'chips': chips_lbl,
            'status': status_lbl,
            'index': player_idx
        }

    def _start_game(self):
        """Initialize and start the game."""
        self.engine.setup_players("You")

        # Create player displays
        # Top row: AI 1, 2, 3 (indices 1, 2, 3)
        for i in range(1, 4):
            self.player_frames.append(self._create_player_display(self.top_frame, i))

        # Bottom row: AI 4, 5 (indices 4, 5)
        for i in range(4, 6):
            self.player_frames.append(self._create_player_display(self.bottom_frame, i))

        # Human player (index 0) - in human_frame
        self.player_frames.insert(0, self._create_player_display(self.human_frame, 0, is_human=True))
        self.player_frames[0]['frame'].configure(bg='#1a4d2e', bd=3)

        self._start_new_hand()

    def _start_new_hand(self):
        """Start a new hand."""
        self.engine.start_new_hand()
        self.next_hand_btn.pack_forget()
        self._update_display()
        self._process_turn()

    def _update_display(self):
        """Update all GUI elements based on current game state."""
        state = self.engine.get_game_state()

        # Update pot
        self.pot_label.config(text=f"Pot: {state['pot']}")

        # Update message
        self.message_label.config(text=state['message'])

        # Update community cards
        for i, lbl in enumerate(self.community_labels):
            if i < len(state['community_cards']):
                card = state['community_cards'][i]
                color = self.CARD_COLORS.get(card.suit, 'black')
                lbl.config(text=str(card), fg=color, bg='white')
            else:
                lbl.config(text="", bg='#2a8c5c')

        # Update player displays
        for pf in self.player_frames:
            idx = pf['index']
            if idx < len(state['players']):
                player = state['players'][idx]
                self._update_player_display(pf, player, state)

        # Update controls based on whose turn it is
        self._update_controls(state)

    def _update_player_display(self, pf: dict, player: Player, state: dict):
        """Update a single player's display."""
        # Highlight current player
        is_current = (state['current_player_index'] == pf['index'] and
                      state['phase'] not in [PokerEngine.PHASE_WAITING, PokerEngine.PHASE_SHOWDOWN,
                                             PokerEngine.PHASE_HAND_OVER])

        # Dealer indicator
        dealer_mark = " (D)" if pf['index'] == state['dealer_index'] else ""
        pf['name'].config(text=f"{player.name}{dealer_mark}")

        if is_current:
            pf['frame'].config(bg='#3d6b3d')
            pf['name'].config(bg='#3d6b3d')
            pf['chips'].config(bg='#3d6b3d')
            pf['status'].config(bg='#3d6b3d')
        else:
            bg = '#1a4d2e' if player.is_human else '#0f3d22'
            pf['frame'].config(bg=bg)
            pf['name'].config(bg=bg)
            pf['chips'].config(bg=bg)
            pf['status'].config(bg=bg)

        # Chips
        pf['chips'].config(text=f"Chips: {player.chips}")

        # Status
        status_text = player.status
        if player.current_bet > 0 and not player.is_folded:
            status_text = f"Bet: {player.current_bet}" + (f" ({player.status})" if player.status else "")
        pf['status'].config(text=status_text)

        # Cards
        show_cards = (player.is_human or
                      state['phase'] in [PokerEngine.PHASE_SHOWDOWN, PokerEngine.PHASE_HAND_OVER] and player.is_in_hand())

        if player.hole_cards:
            if show_cards:
                c1, c2 = player.hole_cards
                pf['card1'].config(text=str(c1), fg=self.CARD_COLORS.get(c1.suit, 'black'), bg='white')
                pf['card2'].config(text=str(c2), fg=self.CARD_COLORS.get(c2.suit, 'black'), bg='white')
            else:
                pf['card1'].config(text="?", fg='blue', bg='#4444aa')
                pf['card2'].config(text="?", fg='blue', bg='#4444aa')
        else:
            pf['card1'].config(text="", bg='gray')
            pf['card2'].config(text="", bg='gray')

        # Dim folded players
        if player.is_folded:
            pf['card1'].config(text="X", bg='#666666', fg='#333333')
            pf['card2'].config(text="X", bg='#666666', fg='#333333')
            pf['status'].config(fg='#ff6666')

    def _update_controls(self, state: dict):
        """Update control buttons based on game state."""
        current_player = self.engine.get_current_player()

        if state['phase'] == PokerEngine.PHASE_HAND_OVER:
            self._disable_controls()
            if not self.engine.is_game_over():
                self.next_hand_btn.pack(side=tk.RIGHT, padx=5)
            else:
                self.message_label.config(text="Game Over! " + state['message'])
            return

        if not current_player or not current_player.is_human:
            self._disable_controls()
            return

        # Enable controls for human player
        self._enable_controls()

        to_call = state['current_bet'] - current_player.current_bet

        if to_call == 0:
            self.check_call_btn.config(text="Check")
            self.bet_raise_btn.config(text="Bet")
        else:
            self.check_call_btn.config(text=f"Call {to_call}")
            self.bet_raise_btn.config(text="Raise")

    def _enable_controls(self):
        """Enable action buttons."""
        self.fold_btn.config(state=tk.NORMAL)
        self.check_call_btn.config(state=tk.NORMAL)
        self.bet_raise_btn.config(state=tk.NORMAL)
        self.bet_entry.config(state=tk.NORMAL)
        self.allin_btn.config(state=tk.NORMAL)

    def _disable_controls(self):
        """Disable action buttons."""
        self.fold_btn.config(state=tk.DISABLED)
        self.check_call_btn.config(state=tk.DISABLED)
        self.bet_raise_btn.config(state=tk.DISABLED)
        self.bet_entry.config(state=tk.DISABLED)
        self.allin_btn.config(state=tk.DISABLED)

    def _process_turn(self):
        """Process the current turn (AI or wait for human)."""
        state = self.engine.get_game_state()

        if state['phase'] == PokerEngine.PHASE_HAND_OVER:
            self._update_display()
            return

        current_player = self.engine.get_current_player()
        if not current_player:
            self._update_display()
            return

        if current_player.is_human:
            self._update_display()
            # Wait for human input
        else:
            # AI turn
            current_player.status = "Thinking..."
            self._update_display()
            self.root.after(self.ai_delay, self._process_ai_turn)

    def _process_ai_turn(self):
        """Process an AI player's turn."""
        current_player = self.engine.get_current_player()
        if not current_player or current_player.is_human:
            self._update_display()
            return

        # Get AI decision
        game_state = self.engine.get_game_state()
        action, amount = current_player.decide_action(game_state)

        # Apply action
        self.engine.apply_action(action, amount)
        self._update_display()

        # Continue to next turn
        self.root.after(300, self._process_turn)

    def _on_fold(self):
        """Handle fold button."""
        if self.engine.apply_action('fold'):
            self._update_display()
            self.root.after(300, self._process_turn)

    def _on_check_call(self):
        """Handle check/call button."""
        state = self.engine.get_game_state()
        player = self.engine.get_current_player()
        if not player:
            return

        to_call = state['current_bet'] - player.current_bet

        if to_call == 0:
            if self.engine.apply_action('check'):
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            if self.engine.apply_action('call', to_call):
                self._update_display()
                self.root.after(300, self._process_turn)

    def _on_bet_raise(self):
        """Handle bet/raise button."""
        state = self.engine.get_game_state()
        player = self.engine.get_current_player()
        if not player:
            return

        try:
            amount = int(self.bet_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid Bet", "Bet amount must be positive.")
            return

        if amount > player.chips:
            messagebox.showerror("Invalid Bet", f"You only have {player.chips} chips.")
            return

        to_call = state['current_bet'] - player.current_bet

        if to_call == 0:
            # Betting
            if amount < state['min_raise']:
                messagebox.showerror("Invalid Bet", f"Minimum bet is {state['min_raise']}.")
                return
            if self.engine.apply_action('bet', amount):
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            # Raising
            total_bet = player.current_bet + amount
            if total_bet < state['current_bet'] + state['min_raise']:
                messagebox.showerror("Invalid Raise",
                                     f"Minimum raise is to {state['current_bet'] + state['min_raise']}.")
                return
            if self.engine.apply_action('raise', amount):
                self._update_display()
                self.root.after(300, self._process_turn)

    def _on_allin(self):
        """Handle all-in button."""
        player = self.engine.get_current_player()
        if not player:
            return

        state = self.engine.get_game_state()
        to_call = state['current_bet'] - player.current_bet

        if to_call == 0:
            if self.engine.apply_action('bet', player.chips):
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            if player.chips <= to_call:
                if self.engine.apply_action('call', player.chips):
                    self._update_display()
                    self.root.after(300, self._process_turn)
            else:
                if self.engine.apply_action('raise', player.chips):
                    self._update_display()
                    self.root.after(300, self._process_turn)

    def _on_next_hand(self):
        """Handle next hand button."""
        if self.engine.is_game_over():
            messagebox.showinfo("Game Over", "The game is over!")
            self.root.quit()
        else:
            self._start_new_hand()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Launch the poker GUI application."""
    root = tk.Tk()
    app = PokerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# =============================================================================
# DOCUMENTATION
# =============================================================================
"""
HOW TO RUN:
    python poker_gui.py

GUI STRUCTURE:
    - PokerEngine: Core game logic (lines ~270-480) - completely UI-independent
        - Manages players, deck, betting rounds, hand evaluation
        - Methods: setup_players(), start_new_hand(), apply_action(), get_game_state()

    - PokerGUI: Tkinter interface (lines ~490-830)
        - Creates visual table with player positions
        - Displays cards, chips, pot, and game messages
        - Handles button clicks and validates input
        - Uses root.after() to schedule AI turns without blocking

    Player layout:
        [AI 1]  [AI 2]  [AI 3]     <- Top row
        ┌─────────────────────┐
        │   Community Cards   │    <- Table center
        │       Pot: $$$      │
        └─────────────────────┘
        [AI 4]  [AI 5]             <- Bottom row
           [YOU]                   <- Human player
        [Fold][Check/Call][Bet/Raise][All-In]  <- Controls

CONFIGURATION (lines 25-28):
    STARTING_CHIPS = 1000   # Initial chips for each player
    SMALL_BLIND = 10        # Small blind amount
    BIG_BLIND = 20          # Big blind amount
    NUM_AI_PLAYERS = 5      # Number of AI opponents (1-5)

AI BEHAVIOR:
    - Each AI has different aggression levels (0.3 to 0.7)
    - Decisions based on hand strength, pot odds, and randomness
    - Modify AIPlayer.decide_action() for different strategies
"""
