"""
Some example classes for people who want to create a homemade bot.

With these classes, bot makers will not have to implement the UCI or XBoard interfaces themselves.
"""

from __future__ import annotations
import chess
from chess.engine import PlayResult, Limit
import chess.engine
import random
from lib.engine_wrapper import MinimalEngine, MOVE
from typing import Any, Optional, Union
import logging
from lib.config import Configuration
import sys
from stockfish import Stockfish
from lib.conversation import Conversation, ChatLine
import lichess_bot

stockfishPath = "engines\\stockfish.exe"
stockfish = Stockfish(path=stockfishPath)

def create_file(file_name, text):
    try:
        with open(file_name, 'w') as file:
            file.write(text)
        print(f"File '{file_name}' created successfully with the given text.")
    except Exception as e:
        print(f"Error occurred while creating the file: {e}")

# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)


class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""

    pass


# Bot names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    """Get a random move."""

    def search(self, board: chess.Board, *args: Any) -> PlayResult:
        """Choose a random move."""
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    """Get the first move when sorted by san representation."""

    def search(self, board: chess.Board, *args: Any) -> PlayResult:
        """Choose the first move alphabetically."""
        moves = list(board.legal_moves)
        print(board)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Get the first move when sorted by uci representation."""

    def search(self, board: chess.Board, *args: Any) -> PlayResult:
        """Choose the first move alphabetically in uci representation."""
        moves = list(board.legal_moves)
        moves.sort(key=str)
        print(PlayResult(moves[0], None))
        print("----")
        print(moves[0])
        return PlayResult(moves[0], None)


class ComboEngine(ExampleEngine):
    """
    Get a move using multiple different methods.

    This engine demonstrates how one can use `time_limit`, `draw_offered`, and `root_moves`.
    """

    def search(self, board: chess.Board, time_limit: Limit, ponder: bool, draw_offered: bool, root_moves: MOVE) -> PlayResult:
        """
        Choose a move using multiple different methods.

        :param board: The current position.
        :param time_limit: Conditions for how long the engine can search (e.g. we have 10 seconds and search up to depth 10).
        :param ponder: Whether the engine can ponder after playing a move.
        :param draw_offered: Whether the bot was offered a draw.
        :param root_moves: If it is a list, the engine should only play a move that is in `root_moves`.
        :return: The move to play.
        """
        if isinstance(time_limit.time, int):
            my_time = time_limit.time
            my_inc = 0
        elif board.turn == chess.WHITE:
            my_time = time_limit.white_clock if isinstance(time_limit.white_clock, int) else 0
            my_inc = time_limit.white_inc if isinstance(time_limit.white_inc, int) else 0
        else:
            my_time = time_limit.black_clock if isinstance(time_limit.black_clock, int) else 0
            my_inc = time_limit.black_inc if isinstance(time_limit.black_inc, int) else 0

        possible_moves = root_moves if isinstance(root_moves, list) else list(board.legal_moves)

        if my_time / 60 + my_inc > 10:
            # Choose a random move.
            move = random.choice(possible_moves)
        else:
            # Choose the first move alphabetically in uci representation.
            possible_moves.sort(key=str)
            move = possible_moves[0]
        return PlayResult(move, None, draw_offered=draw_offered)

class TestFish(ExampleEngine):
    def __init__ (self, *args, cwd):
        self.stockfish = chess.engine.SimpleEngine.popen_uci(stockfishPath)
        super().__init__(*args)
    def evaluate (self, board, timeLimit = 0.1):
        result = self.stockfish.analyse(board, chess.engine.Limit(time = timeLimit - 0.01))
        print(result["score"].relative)
        return result["score"].relative
    
    def search(self, board: chess.Board, timeLeft, *args) -> PlayResult:
        move_type = random.choice(["Best", "Best", "Best", "Random", "Worst","Capture"]) #, "Capture", "Check"
        create_file("move_type.txt", move_type)
        if move_type == "Best":
            print("Best")
##            stockfish.set_depth(15) #dont use pls
            stockfish.set_fen_position(board.fen())
##            movelsit = stockfish.get_top_moves(1)
##            print(movelsit)
            bmove = stockfish.get_best_move()
            print("BMOVE: "+bmove)
##            topmoves = stockfish.get_top_moves()
##            print(topmoves)
##            print(topmoves[0])
            return PlayResult(bmove, None)
        elif move_type == "Random":
            print("Random")
            return PlayResult(random.choice(list(board.legal_moves)), None)
        elif move_type == "Capture":
            captures = []
            legalMoves = tuple(board.legal_moves)
            for move in legalMoves:
                if board.is_capture(move):
                    captures.append(move)
            if captures:
                return PlayResult(random.choice(list(captures)), None)
            stockfish.set_fen_position(board.fen())
            bmove = stockfish.get_best_move()
            print("BMOVE: "+bmove)
            return PlayResult(bmove, None)
        elif move_type == "Worst":
            legalMoves = tuple(board.legal_moves)
            searchTime = 0.1
            if type(timeLeft) != chess.engine.Limit:
                timeLeft /= 1000  # Convert to seconds
                if len(legalMoves) * searchTime > timeLeft / 10:
                    searchTime = (timeLeft / 10) / len(legalMoves)
            worstEvaluation = None
            worstMoves = []
            for move in legalMoves:
                move.isCapture = board.is_capture(move)
                board.push(move)
                move.isCheck = board.is_check()
                evaluation = self.evaluate(board, searchTime)
                if worstEvaluation is None or worstEvaluation < evaluation:
                    worstEvaluation = evaluation
                    worstMoves = [move]
                elif worstEvaluation == evaluation:
                    worstMoves.append(move)
                board.pop()
            worstCaptures = []
            worstChecks = []
            worstOther = []
            for move in worstMoves:
                if move.isCapture:
                    worstCaptures.append(move)
                elif move.isCheck:
                    worstChecks.append(move)
                else:
                    worstOther.append(move)
            if len(worstOther) != 0:
                return PlayResult(random.choice(worstOther), None)
            elif len(worstChecks) != 0:
                return PlayResult(random.choice(worstChecks), None)
            else:
                return PlayResult(random.choice(worstCaptures), None)
class WorstFish(ExampleEngine):

    def __init__ (self, *args, cwd):
        self.stockfish = chess.engine.SimpleEngine.popen_uci(stockfishPath)
        super().__init__(*args)

    def evaluate (self, board, timeLimit = 0.1):
        result = self.stockfish.analyse(board, chess.engine.Limit(time = timeLimit - 0.01))
        print(result["score"].relative)
        return result["score"].relative

    def search (self, board: chess.Board, timeLeft, *args):
        legalMoves = tuple(board.legal_moves)
        searchTime = 0.1
        if type(timeLeft) != chess.engine.Limit:
            timeLeft /= 1000  # Convert to seconds
            if len(legalMoves) * searchTime > timeLeft / 10:
                searchTime = (timeLeft / 10) / len(legalMoves)
        worstEvaluation = None
        worstMoves = []
        for move in legalMoves:
            move.isCapture = board.is_capture(move)
            board.push(move)
            move.isCheck = board.is_check()
            evaluation = self.evaluate(board, searchTime)
            if worstEvaluation is None or worstEvaluation < evaluation:
                worstEvaluation = evaluation
                worstMoves = [move]
            elif worstEvaluation == evaluation:
                worstMoves.append(move)
            board.pop()
        worstCaptures = []
        worstChecks = []
        worstOther = []
        for move in worstMoves:
            if move.isCapture:
                worstCaptures.append(move)
            elif move.isCheck:
                worstChecks.append(move)
            else:
                worstOther.append(move)
        if len(worstOther) != 0:
            return PlayResult(random.choice(worstOther), None)
        elif len(worstChecks) != 0:
            return PlayResult(random.choice(worstChecks), None)
        else:
            return PlayResult(random.choice(worstCaptures), None)
    def quit(self):
        self.stockfish.close()
