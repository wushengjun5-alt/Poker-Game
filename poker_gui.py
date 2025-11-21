#!/usr/bin/env python3
"""
Texas Hold'em Poker Game - Enhanced GUI Version
A complete Tkinter-based No-Limit Texas Hold'em poker game with:
- 1 human player + 5 AI opponents with distinct personalities
- Increasing blind levels
- Player statistics tracking
- Table chat/banter
- Visual feedback and animations

Run with: python poker_gui.py
"""

import random
import tkinter as tk
from tkinter import messagebox, ttk, Toplevel
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
# BLIND LEVEL CONFIGURATION
# Blinds increase every HANDS_PER_LEVEL hands by BLIND_MULTIPLIER
# =============================================================================
HANDS_PER_LEVEL = 10          # Increase blinds every N hands
BLIND_MULTIPLIER = 1.5        # Multiply blinds by this factor each level
MAX_BLIND_LEVEL = 10          # Cap on blind levels

# =============================================================================
# CHAT/ANIMATION SETTINGS
# =============================================================================
ENABLE_TABLE_CHAT = True      # Set False to disable AI chat messages
ENABLE_ANIMATIONS = True      # Set False to disable visual effects
AI_THINK_DELAY_MS = 800       # Milliseconds AI "thinks" before acting
POT_HIGHLIGHT_MS = 400        # Milliseconds pot stays highlighted


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
# PLAYER STATISTICS - Tracks performance across the session
# =============================================================================
class PlayerStats:
    """Tracks statistics for a player across the game session."""
    def __init__(self):
        self.hands_played = 0
        self.hands_won = 0
        self.biggest_pot_won = 0
        self.total_bet = 0
        self.total_won = 0

    def record_hand_played(self):
        self.hands_played += 1

    def record_bet(self, amount: int):
        self.total_bet += amount

    def record_win(self, amount: int):
        self.hands_won += 1
        self.total_won += amount
        if amount > self.biggest_pot_won:
            self.biggest_pot_won = amount

    @property
    def win_rate(self) -> float:
        return (self.hands_won / self.hands_played * 100) if self.hands_played > 0 else 0

    @property
    def net_profit(self) -> int:
        return self.total_won - self.total_bet


# =============================================================================
# AI PERSONALITY PROFILES
# Each AI has distinct traits that affect their play style and chat
# =============================================================================
class AIPersonality:
    """Defines an AI's personality traits and chat messages."""

    # Predefined personality profiles
    PROFILES = {
        "Loose Larry": {
            "aggression": 0.8,    # High aggression - bets/raises often
            "tightness": 0.2,     # Low tightness - plays many hands
            "bluff_rate": 0.4,    # Moderate bluffing
            "chat_style": "cocky",
            "chat_messages": {
                "raise": ["Let's make this interesting! 😎", "Who wants to play for real?", "Scared money don't make money!"],
                "big_raise": ["ALL GAS NO BRAKES! 🔥", "Come on, call me!", "Let's see what you've got!"],
                "win": ["Too easy! 💰", "That's how it's done!", "Pay up, friends!"],
                "lose": ["Lucky... this time.", "I'll get it back.", "Just warming up!"],
                "fold": ["Fine, take it... for now.", "I'll pick my spots.", "Not worth it."],
                "bluff_caught": ["You got me there!", "Well played... I guess.", "Ha! Had to try!"],
            }
        },
        "Tight Tina": {
            "aggression": 0.3,
            "tightness": 0.8,     # Very tight - only plays premium hands
            "bluff_rate": 0.1,    # Rarely bluffs
            "chat_style": "cautious",
            "chat_messages": {
                "raise": ["I have a good feeling about this one.", "This hand is worth it.", "Let's be smart here."],
                "big_raise": ["I don't do this often...", "Trust me on this one.", "Premium hand alert."],
                "win": ["Patience pays off.", "Quality over quantity.", "That's the right way to play."],
                "lose": ["That was unexpected.", "Back to waiting.", "Can't win them all."],
                "fold": ["Not worth the risk.", "I'll wait for better.", "Folding is winning sometimes."],
                "bluff_caught": ["...that rarely happens.", "Okay, I tried.", "Back to basics."],
            }
        },
        "Bluffing Bob": {
            "aggression": 0.6,
            "tightness": 0.4,
            "bluff_rate": 0.7,    # Bluffs very often
            "chat_style": "mysterious",
            "chat_messages": {
                "raise": ["Do you really want to find out? 🎭", "Maybe I have it, maybe I don't...", "Interesting spot..."],
                "big_raise": ["The question is... do you believe me?", "Big bet, big hand... or is it?", "🃏🃏🃏"],
                "win": ["Wouldn't you like to know!", "Was it real? Who knows!", "The mystery continues..."],
                "lose": ["Can't fool everyone.", "Worth the attempt!", "They'll never know for sure."],
                "fold": ["I'll keep you guessing.", "This time...", "Saving it for later."],
                "bluff_caught": ["You got lucky!", "Fine, you saw through me!", "The legend lives on!"],
            }
        },
        "Cautious Claire": {
            "aggression": 0.2,    # Very passive
            "tightness": 0.7,     # Quite tight
            "bluff_rate": 0.05,   # Almost never bluffs
            "chat_style": "nervous",
            "chat_messages": {
                "raise": ["Oh my, I hope this is right...", "Taking a chance here!", "This feels good... I think."],
                "big_raise": ["This is scary but here goes!", "Please don't have a monster...", "Big decision time!"],
                "win": ["Phew! That worked out!", "Oh thank goodness!", "My heart was racing!"],
                "lose": ["I knew I should have folded...", "That's okay, play safe.", "Deep breaths..."],
                "fold": ["Better safe than sorry!", "Too rich for my blood.", "I'll sit this one out."],
                "bluff_caught": ["I can't believe I did that!", "Never again!", "That was terrifying!"],
            }
        },
        "Random Rick": {
            "aggression": 0.5,
            "tightness": 0.5,
            "bluff_rate": 0.35,
            "chat_style": "chaotic",
            "chat_messages": {
                "raise": ["YOLO! 🎲", "Let's see what happens!", "Why not?!", "Feeling lucky!"],
                "big_raise": ["GO BIG OR GO HOME!", "Rolling the dice!", "CHAOS MODE ACTIVATED!"],
                "win": ["IT WORKED! 🎉", "Even I'm surprised!", "The RNG gods smile upon me!"],
                "lose": ["Worth it for the excitement!", "That's poker, baby!", "NEXT HAND!"],
                "fold": ["Eh, not feeling it.", "Maybe next time!", "The vibes are off."],
                "bluff_caught": ["SURPRISE! It was nothing!", "You never know with me!", "Chaos is fun!"],
            }
        }
    }

    def __init__(self, profile_name: str):
        profile = self.PROFILES.get(profile_name, self.PROFILES["Random Rick"])
        self.name = profile_name
        self.aggression = profile["aggression"]
        self.tightness = profile["tightness"]
        self.bluff_rate = profile["bluff_rate"]
        self.chat_style = profile["chat_style"]
        self.chat_messages = profile["chat_messages"]

    def get_chat(self, event: str) -> str:
        """Get a random chat message for an event."""
        messages = self.chat_messages.get(event, [])
        return random.choice(messages) if messages else ""


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
        self.stats = PlayerStats()  # Track player statistics

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
        self.stats.record_bet(actual)  # Track bet in stats
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
    """
    AI-controlled player with personality-driven decision logic.
    Personality affects aggression, tightness, bluff frequency, and chat.
    """
    def __init__(self, name: str, chips: int, personality: AIPersonality):
        super().__init__(name, chips, is_human=False)
        self.personality = personality
        self.last_action = ""
        self.was_bluffing = False

    def decide_action(self, game_state: dict) -> Tuple[str, int]:
        """
        Determine AI action based on personality traits and hand strength.

        The decision logic incorporates:
        - aggression: likelihood of betting/raising vs calling/checking
        - tightness: how strong a hand needs to be to play
        - bluff_rate: chance of betting with a weak hand
        """
        current_bet = game_state['current_bet']
        to_call = current_bet - self.current_bet
        min_raise = game_state['min_raise']
        pot = game_state['pot']
        community = game_state['community_cards']

        hand_strength = self._evaluate_strength(community)
        self.was_bluffing = False

        # Tightness affects the threshold for playing
        # Higher tightness = need stronger hand to continue
        play_threshold = 0.2 + (self.personality.tightness * 0.3)

        # Random factor for unpredictability
        randomness = random.uniform(-0.1, 0.1)
        adjusted_strength = hand_strength + randomness

        # Check for bluff opportunity
        is_bluffing = random.random() < self.personality.bluff_rate and hand_strength < 0.4
        if is_bluffing:
            adjusted_strength += 0.3  # Pretend we have a stronger hand
            self.was_bluffing = True

        if to_call == 0:  # Can check or bet
            # Aggression determines betting frequency
            bet_threshold = 0.5 - (self.personality.aggression * 0.2)

            if adjusted_strength > bet_threshold and self.chips > min_raise:
                # Bet sizing affected by aggression
                base_bet = pot * (0.3 + self.personality.aggression * 0.4)
                bet_size = max(int(base_bet), min_raise)
                self.last_action = "bet"
                return 'bet', min(bet_size, self.chips)

            self.last_action = "check"
            return 'check', 0

        else:  # Must call, raise, or fold
            # Tight players fold more often with marginal hands
            fold_threshold = play_threshold + (to_call / pot * 0.2 if pot > 0 else 0.1)

            if adjusted_strength < fold_threshold and not is_bluffing:
                self.last_action = "fold"
                return 'fold', 0

            # Decide between call and raise based on aggression
            raise_chance = self.personality.aggression * 0.6

            if adjusted_strength > 0.6 or (is_bluffing and random.random() < 0.5):
                if random.random() < raise_chance and self.chips > to_call:
                    raise_amt = to_call + max(int(pot * (0.3 + self.personality.aggression * 0.3)), min_raise)
                    self.last_action = "raise"
                    return 'raise', min(raise_amt, self.chips)

            self.last_action = "call"
            return 'call', min(to_call, self.chips)

    def get_chat_message(self, event: str) -> Optional[str]:
        """Get a chat message for the given event, if chat is enabled."""
        if not ENABLE_TABLE_CHAT:
            return None

        # Special handling for bluff scenarios
        if event == "win" and self.was_bluffing:
            if random.random() < 0.5:
                return self.personality.get_chat("bluff_caught")

        return self.personality.get_chat(event)

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
    Core poker game engine with blind level progression.
    Manages game state, betting, hand evaluation, and statistics.
    """

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
        self.dealer_index = 0
        self.current_player_index = 0
        self.hand_number = 0
        self.phase = self.PHASE_WAITING
        self.last_raiser_index = -1
        self.action_count = 0
        self.winners: List[Tuple[Player, int, str]] = []
        self.message = ""
        self.last_chat: Optional[Tuple[str, str]] = None  # (player_name, message)

        # Blind level tracking
        self.blind_level = 1
        self.small_blind = SMALL_BLIND
        self.big_blind = BIG_BLIND
        self.min_raise = BIG_BLIND

    def get_current_blinds(self) -> Tuple[int, int]:
        """Calculate current blind levels based on hands played."""
        # Blinds increase every HANDS_PER_LEVEL hands
        new_level = min((self.hand_number // HANDS_PER_LEVEL) + 1, MAX_BLIND_LEVEL)

        if new_level != self.blind_level:
            self.blind_level = new_level
            multiplier = BLIND_MULTIPLIER ** (new_level - 1)
            self.small_blind = int(SMALL_BLIND * multiplier)
            self.big_blind = int(BIG_BLIND * multiplier)

        return self.small_blind, self.big_blind

    def setup_players(self, human_name: str = "You"):
        """Initialize players with distinct AI personalities."""
        self.players = [Player(human_name, STARTING_CHIPS, is_human=True)]

        # Create AI players with different personalities
        personalities = [
            ("Loose Larry", AIPersonality("Loose Larry")),
            ("Tight Tina", AIPersonality("Tight Tina")),
            ("Bluffing Bob", AIPersonality("Bluffing Bob")),
            ("Cautious Claire", AIPersonality("Cautious Claire")),
            ("Random Rick", AIPersonality("Random Rick")),
        ]

        for i in range(NUM_AI_PLAYERS):
            name, personality = personalities[i]
            self.players.append(AIPlayer(name, STARTING_CHIPS, personality))

        self.dealer_index = random.randint(0, len(self.players) - 1)

    def start_new_hand(self):
        """Start a new hand with updated blinds."""
        self.players = [p for p in self.players if p.chips > 0]
        if len(self.players) < 2:
            self.phase = self.PHASE_HAND_OVER
            self.message = "Game Over - Not enough players!"
            return

        self.hand_number += 1

        # Update blind levels
        sb, bb = self.get_current_blinds()
        self.min_raise = bb

        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.winners = []
        self.last_chat = None
        self.message = f"Hand #{self.hand_number} | Blinds: {sb}/{bb}"

        # Record hand played for all players
        for p in self.players:
            p.reset_for_hand()
            p.stats.record_hand_played()

        self.dealer_index = self.dealer_index % len(self.players)

        # Post blinds
        sb_idx = (self.dealer_index + 1) % len(self.players)
        bb_idx = (self.dealer_index + 2) % len(self.players)

        sb_amt = self.players[sb_idx].bet(sb)
        bb_amt = self.players[bb_idx].bet(bb)
        self.pot = sb_amt + bb_amt
        self.current_bet = bb

        self.players[sb_idx].status = f"SB: {sb_amt}"
        self.players[bb_idx].status = f"BB: {bb_amt}"

        for p in self.players:
            p.receive_cards(self.deck.deal(2))

        self.phase = self.PHASE_PREFLOP
        self.current_player_index = (bb_idx + 1) % len(self.players)
        self.last_raiser_index = bb_idx
        self.action_count = 0
        self._advance_to_active_player()

    def get_current_player(self) -> Optional[Player]:
        if self.phase in [self.PHASE_WAITING, self.PHASE_SHOWDOWN, self.PHASE_HAND_OVER]:
            return None
        return self.players[self.current_player_index]

    def get_game_state(self) -> dict:
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
            'hand_number': self.hand_number,
            'blind_level': self.blind_level,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'last_chat': self.last_chat,
        }

    def set_chat(self, player_name: str, message: str):
        """Set the last chat message for display."""
        if message:
            self.last_chat = (player_name, message)

    def apply_action(self, action: str, amount: int = 0) -> Tuple[bool, Optional[str]]:
        """
        Apply an action. Returns (success, chat_event).
        chat_event indicates what type of chat message might be triggered.
        """
        player = self.get_current_player()
        if not player:
            return False, None

        to_call = self.current_bet - player.current_bet
        chat_event = None
        old_pot = self.pot

        if action == 'fold':
            player.fold()
            self.message = f"{player.name} folds"
            chat_event = "fold"

        elif action == 'check':
            if to_call > 0:
                return False, None
            player.status = "Check"
            self.message = f"{player.name} checks"

        elif action == 'call':
            actual = player.bet(to_call)
            self.pot += actual
            player.status = f"Call {actual}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} calls {actual}"

        elif action == 'bet':
            if to_call > 0 or amount < self.min_raise:
                return False, None
            actual = player.bet(amount)
            self.pot += actual
            self.current_bet = player.current_bet
            self.min_raise = amount
            self.last_raiser_index = self.current_player_index
            player.status = f"Bet {actual}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} bets {actual}"
            chat_event = "big_raise" if actual > old_pot else "raise"

        elif action == 'raise':
            if to_call == 0:
                return False, None
            actual = player.bet(amount)
            self.pot += actual
            raise_amount = player.current_bet - self.current_bet
            if raise_amount > 0:
                self.min_raise = max(self.min_raise, raise_amount)
            self.current_bet = player.current_bet
            self.last_raiser_index = self.current_player_index
            player.status = f"Raise to {player.current_bet}" + (" (All-in)" if player.is_all_in else "")
            self.message = f"{player.name} raises to {player.current_bet}"
            chat_event = "big_raise" if actual > old_pot else "raise"

        else:
            return False, None

        self.action_count += 1
        self._advance_game()
        return True, chat_event

    def _advance_to_active_player(self):
        for _ in range(len(self.players)):
            player = self.players[self.current_player_index]
            if player.is_active():
                return
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def _advance_game(self):
        active_in_hand = [p for p in self.players if p.is_in_hand()]
        if len(active_in_hand) == 1:
            winner = active_in_hand[0]
            winner.chips += self.pot
            winner.stats.record_win(self.pot)
            self.winners = [(winner, self.pot, "Last player standing")]
            self.message = f"{winner.name} wins {self.pot} (others folded)"
            self.phase = self.PHASE_HAND_OVER
            self.dealer_index = (self.dealer_index + 1) % len(self.players)
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self._advance_to_active_player()

        if self._is_betting_round_complete():
            self._end_betting_round()

    def _is_betting_round_complete(self) -> bool:
        active_players = [p for p in self.players if p.is_active()]
        if not active_players:
            return True
        for p in active_players:
            if p.current_bet < self.current_bet:
                return False
        if self.action_count < len([p for p in self.players if p.is_in_hand()]):
            return False
        if self.current_player_index == self.last_raiser_index:
            return True
        return self.action_count >= len([p for p in self.players if p.is_in_hand()])

    def _end_betting_round(self):
        for p in self.players:
            p.current_bet = 0
        self.current_bet = 0
        self.action_count = 0
        active_not_allin = [p for p in self.players if p.is_active()]

        if self.phase == self.PHASE_PREFLOP:
            self.phase = self.PHASE_FLOP
            self.deck.deal_one()
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

        self.current_player_index = (self.dealer_index + 1) % len(self.players)
        self.last_raiser_index = -1
        self._advance_to_active_player()

        if len(active_not_allin) <= 1:
            while len(self.community_cards) < 5:
                self.deck.deal_one()
                self.community_cards.extend(self.deck.deal(1))
            self._showdown()

    def _showdown(self):
        self.phase = self.PHASE_SHOWDOWN
        remaining = [p for p in self.players if p.is_in_hand()]

        hands = []
        for p in remaining:
            rank, tiebreaker, best_cards = HandEvaluator.evaluate(p.hole_cards, self.community_cards)
            hands.append((p, rank, tiebreaker, best_cards))

        hands.sort(key=lambda x: (x[1], x[2]), reverse=True)

        winners = [hands[0]]
        for h in hands[1:]:
            if h[1] == winners[0][1] and h[2] == winners[0][2]:
                winners.append(h)
            else:
                break

        pot_each = self.pot // len(winners)
        remainder = self.pot % len(winners)

        self.winners = []
        for i, (player, rank, _, _) in enumerate(winners):
            award = pot_each + (1 if i < remainder else 0)
            player.chips += award
            player.stats.record_win(award)
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
        players_with_chips = [p for p in self.players if p.chips > 0]
        human_has_chips = any(p.is_human and p.chips > 0 for p in self.players)
        return len(players_with_chips) < 2 or not human_has_chips


# =============================================================================
# TKINTER GUI WITH ENHANCED VISUALS
# =============================================================================
class PokerGUI:
    """
    Enhanced Tkinter GUI with animations, chat, and statistics display.
    """

    CARD_COLORS = {Suit.HEARTS: 'red', Suit.DIAMONDS: 'red', Suit.CLUBS: 'black', Suit.SPADES: 'black'}

    # Colors for visual feedback
    ACTIVE_PLAYER_BG = '#FFD700'       # Gold for current player
    ACTIVE_PLAYER_BORDER = '#FFA500'   # Orange border
    POT_HIGHLIGHT_BG = '#FFD700'       # Gold for pot highlight
    NORMAL_POT_BG = '#1a7c4c'          # Normal table green

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Texas Hold'em – 6 Player Table")
        self.root.geometry("950x800")
        self.root.configure(bg='#0a5c36')

        self.engine = PokerEngine()
        self.player_frames: List[dict] = []
        self.ai_delay = AI_THINK_DELAY_MS

        self._create_widgets()
        self._start_game()

    def _create_widgets(self):
        """Create all GUI widgets including chat area."""
        self.main_frame = tk.Frame(self.root, bg='#0a5c36')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top row: AI players 1-3
        self.top_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.top_frame.pack(fill=tk.X, pady=5)

        # Table area
        self.table_frame = tk.Frame(self.main_frame, bg='#1a7c4c', relief=tk.RIDGE, bd=3)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Blind level display
        self.blind_label = tk.Label(self.table_frame, text="Blinds: 10/20 (Level 1)",
                                     font=('Arial', 10), bg='#1a7c4c', fg='#aaffaa')
        self.blind_label.pack(pady=2)

        # Pot display
        self.pot_label = tk.Label(self.table_frame, text="Pot: 0", font=('Arial', 16, 'bold'),
                                   bg='#1a7c4c', fg='white')
        self.pot_label.pack(pady=5)

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

        # Chat area for table talk
        self.chat_frame = tk.Frame(self.table_frame, bg='#0d4d2a', relief=tk.SUNKEN, bd=2)
        self.chat_frame.pack(fill=tk.X, padx=20, pady=5)

        self.chat_label = tk.Label(self.chat_frame, text="🎰 Welcome to the table!",
                                    font=('Arial', 11, 'italic'), bg='#0d4d2a', fg='#88ddff',
                                    wraplength=600, justify=tk.LEFT)
        self.chat_label.pack(pady=5, padx=10)

        # Bottom row: AI players 4-5
        self.bottom_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.bottom_frame.pack(fill=tk.X, pady=5)

        # Human player
        self.human_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.human_frame.pack(fill=tk.X, pady=5)

        # Controls
        self.controls_frame = tk.Frame(self.main_frame, bg='#0a5c36')
        self.controls_frame.pack(fill=tk.X, pady=5)

        self.fold_btn = tk.Button(self.controls_frame, text="Fold", command=self._on_fold,
                                   font=('Arial', 12), width=8, bg='#cc4444')
        self.fold_btn.pack(side=tk.LEFT, padx=5)

        self.check_call_btn = tk.Button(self.controls_frame, text="Check", command=self._on_check_call,
                                         font=('Arial', 12), width=10, bg='#44aa44')
        self.check_call_btn.pack(side=tk.LEFT, padx=5)

        self.bet_raise_btn = tk.Button(self.controls_frame, text="Bet", command=self._on_bet_raise,
                                        font=('Arial', 12), width=10, bg='#4444cc')
        self.bet_raise_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(self.controls_frame, text="Amount:", bg='#0a5c36', fg='white',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=(20, 5))
        self.bet_entry = tk.Entry(self.controls_frame, font=('Arial', 12), width=8)
        self.bet_entry.pack(side=tk.LEFT, padx=5)
        self.bet_entry.insert(0, str(BIG_BLIND))

        self.allin_btn = tk.Button(self.controls_frame, text="All-In", command=self._on_allin,
                                    font=('Arial', 12), width=8, bg='#aa44aa')
        self.allin_btn.pack(side=tk.LEFT, padx=5)

        # Statistics button
        self.stats_btn = tk.Button(self.controls_frame, text="📊 Stats", command=self._show_statistics,
                                    font=('Arial', 11), width=8, bg='#666699')
        self.stats_btn.pack(side=tk.LEFT, padx=15)

        # Next hand button
        self.next_hand_btn = tk.Button(self.controls_frame, text="Next Hand", command=self._on_next_hand,
                                        font=('Arial', 12, 'bold'), width=12, bg='#ffaa00')
        self.next_hand_btn.pack(side=tk.RIGHT, padx=5)
        self.next_hand_btn.pack_forget()

        # Restart button (shown when game is over)
        self.restart_btn = tk.Button(self.controls_frame, text="🔄 Restart", command=self._on_restart,
                                      font=('Arial', 12, 'bold'), width=12, bg='#44aaaa')
        self.restart_btn.pack(side=tk.RIGHT, padx=5)
        self.restart_btn.pack_forget()

        self._disable_controls()

    def _create_player_display(self, parent: tk.Frame, player_idx: int) -> dict:
        """Create display widgets for a player with animation support."""
        frame = tk.Frame(parent, bg='#0f3d22', relief=tk.RAISED, bd=2)
        frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True)

        name_lbl = tk.Label(frame, text="", font=('Arial', 11, 'bold'), bg='#0f3d22', fg='white')
        name_lbl.pack(pady=2)

        cards_frame = tk.Frame(frame, bg='#0f3d22')
        cards_frame.pack(pady=2)

        card1_lbl = tk.Label(cards_frame, text="", width=4, height=2, font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, bg='white')
        card1_lbl.pack(side=tk.LEFT, padx=2)

        card2_lbl = tk.Label(cards_frame, text="", width=4, height=2, font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, bg='white')
        card2_lbl.pack(side=tk.LEFT, padx=2)

        chips_lbl = tk.Label(frame, text="Chips: 0", font=('Arial', 10), bg='#0f3d22', fg='#ffcc00')
        chips_lbl.pack(pady=2)

        status_lbl = tk.Label(frame, text="", font=('Arial', 9), bg='#0f3d22', fg='#88ff88')
        status_lbl.pack(pady=2)

        return {
            'frame': frame,
            'cards_frame': cards_frame,
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

        for i in range(1, 4):
            self.player_frames.append(self._create_player_display(self.top_frame, i))

        for i in range(4, 6):
            self.player_frames.append(self._create_player_display(self.bottom_frame, i))

        self.player_frames.insert(0, self._create_player_display(self.human_frame, 0))
        self.player_frames[0]['frame'].configure(bg='#1a4d2e', bd=3)

        self._start_new_hand()

    def _start_new_hand(self):
        """Start a new hand."""
        self.engine.start_new_hand()
        self.next_hand_btn.pack_forget()
        self._update_display()
        self._process_turn()

    def _highlight_pot(self):
        """Briefly highlight the pot when it increases (visual feedback)."""
        if not ENABLE_ANIMATIONS:
            return
        self.pot_label.config(bg=self.POT_HIGHLIGHT_BG)
        self.root.after(POT_HIGHLIGHT_MS, lambda: self.pot_label.config(bg=self.NORMAL_POT_BG))

    def _update_chat(self, player_name: str, message: str):
        """Update the chat display area."""
        if message and ENABLE_TABLE_CHAT:
            self.chat_label.config(text=f"💬 {player_name}: {message}")
            self.engine.set_chat(player_name, message)

    def _update_display(self):
        """Update all GUI elements."""
        state = self.engine.get_game_state()

        # Update blind level display
        self.blind_label.config(text=f"Blinds: {state['small_blind']}/{state['big_blind']} (Level {state['blind_level']})")

        # Update pot
        self.pot_label.config(text=f"Pot: {state['pot']}")
        self.message_label.config(text=state['message'])

        # Update community cards
        for i, lbl in enumerate(self.community_labels):
            if i < len(state['community_cards']):
                card = state['community_cards'][i]
                color = self.CARD_COLORS.get(card.suit, 'black')
                lbl.config(text=str(card), fg=color, bg='white')
            else:
                lbl.config(text="", bg='#2a8c5c')

        # Update bet entry with current big blind
        self.bet_entry.delete(0, tk.END)
        self.bet_entry.insert(0, str(state['big_blind']))

        # Update player displays
        for pf in self.player_frames:
            idx = pf['index']
            if idx < len(state['players']):
                player = state['players'][idx]
                self._update_player_display(pf, player, state)

        self._update_controls(state)

    def _update_player_display(self, pf: dict, player: Player, state: dict):
        """Update a single player's display with enhanced highlighting."""
        is_current = (state['current_player_index'] == pf['index'] and
                      state['phase'] not in [PokerEngine.PHASE_WAITING, PokerEngine.PHASE_SHOWDOWN,
                                             PokerEngine.PHASE_HAND_OVER])

        dealer_mark = " (D)" if pf['index'] == state['dealer_index'] else ""
        pf['name'].config(text=f"{player.name}{dealer_mark}")

        # Enhanced highlighting for current player
        if is_current and ENABLE_ANIMATIONS:
            pf['frame'].config(bg=self.ACTIVE_PLAYER_BG, bd=4, relief=tk.GROOVE)
            pf['name'].config(bg=self.ACTIVE_PLAYER_BG, fg='black')
            pf['chips'].config(bg=self.ACTIVE_PLAYER_BG, fg='#333333')
            pf['status'].config(bg=self.ACTIVE_PLAYER_BG, fg='#006600')
            pf['cards_frame'].config(bg=self.ACTIVE_PLAYER_BG)
        else:
            bg = '#1a4d2e' if player.is_human else '#0f3d22'
            pf['frame'].config(bg=bg, bd=2, relief=tk.RAISED)
            pf['name'].config(bg=bg, fg='white')
            pf['chips'].config(bg=bg, fg='#ffcc00')
            pf['status'].config(bg=bg, fg='#88ff88')
            pf['cards_frame'].config(bg=bg)

        pf['chips'].config(text=f"Chips: {player.chips}")

        status_text = player.status
        if player.current_bet > 0 and not player.is_folded:
            status_text = f"Bet: {player.current_bet}" + (f" ({player.status})" if player.status else "")
        pf['status'].config(text=status_text)

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

        if player.is_folded:
            pf['card1'].config(text="X", bg='#666666', fg='#333333')
            pf['card2'].config(text="X", bg='#666666', fg='#333333')
            pf['status'].config(fg='#ff6666')

    def _update_controls(self, state: dict):
        """Update control buttons."""
        current_player = self.engine.get_current_player()

        if state['phase'] == PokerEngine.PHASE_HAND_OVER:
            self._disable_controls()

            # Show winner chat
            if state['winners'] and ENABLE_TABLE_CHAT:
                winner = state['winners'][0][0]
                if isinstance(winner, AIPlayer):
                    chat = winner.get_chat_message("win")
                    if chat:
                        self._update_chat(winner.name, chat)

            if not self.engine.is_game_over():
                self.next_hand_btn.pack(side=tk.RIGHT, padx=5)
            else:
                self.message_label.config(text="Game Over! " + state['message'])
                self.restart_btn.pack(side=tk.RIGHT, padx=5)
            return

        if not current_player or not current_player.is_human:
            self._disable_controls()
            return

        self._enable_controls()
        to_call = state['current_bet'] - current_player.current_bet

        if to_call == 0:
            self.check_call_btn.config(text="Check")
            self.bet_raise_btn.config(text="Bet")
        else:
            self.check_call_btn.config(text=f"Call {to_call}")
            self.bet_raise_btn.config(text="Raise")

    def _enable_controls(self):
        self.fold_btn.config(state=tk.NORMAL)
        self.check_call_btn.config(state=tk.NORMAL)
        self.bet_raise_btn.config(state=tk.NORMAL)
        self.bet_entry.config(state=tk.NORMAL)
        self.allin_btn.config(state=tk.NORMAL)

    def _disable_controls(self):
        self.fold_btn.config(state=tk.DISABLED)
        self.check_call_btn.config(state=tk.DISABLED)
        self.bet_raise_btn.config(state=tk.DISABLED)
        self.bet_entry.config(state=tk.DISABLED)
        self.allin_btn.config(state=tk.DISABLED)

    def _process_turn(self):
        """Process turns with thinking animation for AI."""
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
        else:
            # AI turn with "thinking" display
            current_player.status = "Thinking... 🤔"
            self._update_display()
            self.root.after(self.ai_delay, self._process_ai_turn)

    def _process_ai_turn(self):
        """Process AI turn with chat messages."""
        current_player = self.engine.get_current_player()
        if not current_player or current_player.is_human:
            self._update_display()
            return

        game_state = self.engine.get_game_state()
        action, amount = current_player.decide_action(game_state)

        old_pot = self.engine.pot
        success, chat_event = self.engine.apply_action(action, amount)

        if success:
            # Highlight pot if it increased
            if self.engine.pot > old_pot:
                self._highlight_pot()

            # Get chat message for the action
            if chat_event and isinstance(current_player, AIPlayer):
                chat_msg = current_player.get_chat_message(chat_event)
                if chat_msg:
                    self._update_chat(current_player.name, chat_msg)

        self._update_display()
        self.root.after(300, self._process_turn)

    def _show_statistics(self):
        """Open a statistics window showing all player stats."""
        stats_window = Toplevel(self.root)
        stats_window.title("Player Statistics")
        stats_window.geometry("500x400")
        stats_window.configure(bg='#1a3d2e')

        tk.Label(stats_window, text="📊 Session Statistics", font=('Arial', 16, 'bold'),
                bg='#1a3d2e', fg='white').pack(pady=10)

        # Create stats table
        for player in self.engine.players:
            frame = tk.Frame(stats_window, bg='#0f2d1e', relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, padx=20, pady=5)

            marker = "👤 " if player.is_human else "🤖 "
            tk.Label(frame, text=f"{marker}{player.name}", font=('Arial', 12, 'bold'),
                    bg='#0f2d1e', fg='#ffcc00', width=20, anchor='w').grid(row=0, column=0, padx=5, pady=2)

            tk.Label(frame, text=f"Chips: {player.chips}", font=('Arial', 10),
                    bg='#0f2d1e', fg='white').grid(row=0, column=1, padx=5)

            stats = player.stats
            tk.Label(frame, text=f"Hands: {stats.hands_played}", font=('Arial', 10),
                    bg='#0f2d1e', fg='#88ff88').grid(row=1, column=0, padx=5)
            tk.Label(frame, text=f"Wins: {stats.hands_won} ({stats.win_rate:.1f}%)", font=('Arial', 10),
                    bg='#0f2d1e', fg='#88ff88').grid(row=1, column=1, padx=5)
            tk.Label(frame, text=f"Best pot: {stats.biggest_pot_won}", font=('Arial', 10),
                    bg='#0f2d1e', fg='#ffaa00').grid(row=2, column=0, padx=5)
            tk.Label(frame, text=f"Net: {stats.net_profit:+d}", font=('Arial', 10),
                    bg='#0f2d1e', fg='#00ff00' if stats.net_profit >= 0 else '#ff6666').grid(row=2, column=1, padx=5)

        # Game info
        state = self.engine.get_game_state()
        tk.Label(stats_window, text=f"\nHand #{state['hand_number']} | Blind Level {state['blind_level']} ({state['small_blind']}/{state['big_blind']})",
                font=('Arial', 11), bg='#1a3d2e', fg='#aaaaaa').pack(pady=10)

        tk.Button(stats_window, text="Close", command=stats_window.destroy,
                 font=('Arial', 11), bg='#666666').pack(pady=10)

    def _on_fold(self):
        if self.engine.apply_action('fold')[0]:
            self._update_display()
            self.root.after(300, self._process_turn)

    def _on_check_call(self):
        state = self.engine.get_game_state()
        player = self.engine.get_current_player()
        if not player:
            return

        to_call = state['current_bet'] - player.current_bet
        old_pot = self.engine.pot

        if to_call == 0:
            if self.engine.apply_action('check')[0]:
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            if self.engine.apply_action('call', to_call)[0]:
                if self.engine.pot > old_pot:
                    self._highlight_pot()
                self._update_display()
                self.root.after(300, self._process_turn)

    def _on_bet_raise(self):
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
        old_pot = self.engine.pot

        if to_call == 0:
            if amount < state['min_raise']:
                messagebox.showerror("Invalid Bet", f"Minimum bet is {state['min_raise']}.")
                return
            if self.engine.apply_action('bet', amount)[0]:
                self._highlight_pot()
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            total_bet = player.current_bet + amount
            if total_bet < state['current_bet'] + state['min_raise']:
                messagebox.showerror("Invalid Raise",
                                     f"Minimum raise is to {state['current_bet'] + state['min_raise']}.")
                return
            if self.engine.apply_action('raise', amount)[0]:
                self._highlight_pot()
                self._update_display()
                self.root.after(300, self._process_turn)

    def _on_allin(self):
        player = self.engine.get_current_player()
        if not player:
            return

        state = self.engine.get_game_state()
        to_call = state['current_bet'] - player.current_bet
        old_pot = self.engine.pot

        if to_call == 0:
            if self.engine.apply_action('bet', player.chips)[0]:
                self._highlight_pot()
                self._update_display()
                self.root.after(300, self._process_turn)
        else:
            if player.chips <= to_call:
                if self.engine.apply_action('call', player.chips)[0]:
                    self._highlight_pot()
                    self._update_display()
                    self.root.after(300, self._process_turn)
            else:
                if self.engine.apply_action('raise', player.chips)[0]:
                    self._highlight_pot()
                    self._update_display()
                    self.root.after(300, self._process_turn)

    def _on_next_hand(self):
        if self.engine.is_game_over():
            messagebox.showinfo("Game Over", "The game is over!")
            self._show_statistics()
        else:
            self._start_new_hand()

    def _on_restart(self):
        """Restart the game with fresh chips and stats."""
        # Clear existing player frames
        for pf in self.player_frames:
            pf['frame'].destroy()
        self.player_frames.clear()

        # Reset engine and create new players
        self.engine = PokerEngine()
        self.engine.setup_players("You")

        # Hide restart button
        self.restart_btn.pack_forget()

        # Recreate player displays
        for i in range(1, 4):
            self.player_frames.append(self._create_player_display(self.top_frame, i))
        for i in range(4, 6):
            self.player_frames.append(self._create_player_display(self.bottom_frame, i))
        self.player_frames.insert(0, self._create_player_display(self.human_frame, 0))
        self.player_frames[0]['frame'].configure(bg='#1a4d2e', bd=3)

        # Reset chat
        self.chat_label.config(text="🎰 Welcome back! New game started.")

        # Start new hand
        self._start_new_hand()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    root = tk.Tk()
    app = PokerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# =============================================================================
# DOCUMENTATION
# =============================================================================
"""
=== HOW TO RUN ===
    python poker_gui.py

=== BLIND LEVELS ===
    Blinds increase automatically every HANDS_PER_LEVEL hands (default: 10).
    Each level multiplies blinds by BLIND_MULTIPLIER (default: 1.5x).

    Example progression:
        Level 1: 10/20
        Level 2: 15/30
        Level 3: 22/45
        ...

    To adjust (lines 32-34):
        HANDS_PER_LEVEL = 10      # Change hands per level
        BLIND_MULTIPLIER = 1.5    # Change multiplier
        MAX_BLIND_LEVEL = 10      # Cap on levels

=== PLAYER STATISTICS ===
    Click "📊 Stats" button to view:
    - Hands played/won
    - Win rate percentage
    - Biggest pot won
    - Net profit/loss

    Statistics tracked in PlayerStats class (lines ~195-215).

=== AI PERSONALITIES ===
    5 distinct AI profiles defined in AIPersonality.PROFILES (lines ~230-310):

    - Loose Larry: High aggression (0.8), low tightness (0.2), moderate bluffs
    - Tight Tina: Low aggression (0.3), high tightness (0.8), rarely bluffs
    - Bluffing Bob: Moderate aggression (0.6), high bluff rate (0.7)
    - Cautious Claire: Very passive (0.2), tight (0.7), almost never bluffs
    - Random Rick: Balanced but unpredictable

    To modify personalities, edit the PROFILES dictionary.
    Parameters: aggression (0-1), tightness (0-1), bluff_rate (0-1)

=== TABLE CHAT ===
    AI players make comments during key events (raises, wins, folds).
    Each personality has unique chat messages.

    To disable: Set ENABLE_TABLE_CHAT = False (line 40)
    To add messages: Edit chat_messages dict in each profile

=== VISUAL EFFECTS ===
    - Active player highlighted in gold
    - Pot flashes when chips are added
    - "Thinking..." display before AI acts

    To disable: Set ENABLE_ANIMATIONS = False (line 41)
    To adjust AI delay: Change AI_THINK_DELAY_MS (line 42)
    To adjust pot highlight: Change POT_HIGHLIGHT_MS (line 43)

=== STARTING CHIPS & BLINDS ===
    Lines 25-28:
        STARTING_CHIPS = 1000
        SMALL_BLIND = 10
        BIG_BLIND = 20
        NUM_AI_PLAYERS = 5
"""
