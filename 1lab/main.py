from abc import ABC, abstractmethod
from enum import Enum

class Color(Enum):
    WHITE = "Белые"
    BLACK = "Черные"

class Move:
    def __init__(self, start_pos, end_pos, piece_moved, piece_captured=None, capture_pos=None, promoted=False):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        self.capture_pos = capture_pos if capture_pos else end_pos
        self.promoted = promoted

    def __str__(self):
        capture_str = f" (съедает {self.piece_captured.name})" if self.piece_captured else ""
        prom_str = " (Превращение!)" if self.promoted else ""
        return f"{self.piece_moved.name} с {self.start_pos} на {self.end_pos}{capture_str}{prom_str}"

class Piece(ABC):
    def __init__(self, color: Color):
        self.color = color
        self.name = self.__class__.__name__

    @abstractmethod
    def get_symbol(self):
        pass

    @abstractmethod
    def get_possible_moves(self, board, current_pos, history=None):
        pass

    def _is_valid_target(self, board, r, c):
        if not board.is_in_bounds(r, c):
            return False
        target = board.grid[r][c]
        return target is None or target.color != self.color

    def _get_sliding_moves(self, board, current_pos, directions):
        moves = []
        r, c = current_pos
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while board.is_in_bounds(nr, nc):
                target = board.grid[nr][nc]
                if target is None:
                    moves.append((nr, nc))
                elif target.color != self.color:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc
        return moves

class Pawn(Piece):
    def get_symbol(self): return '♙' if self.color == Color.WHITE else '♟'
    def get_possible_moves(self, board, current_pos, history=None):
        moves = []
        r, c = current_pos
        direction = -1 if self.color == Color.WHITE else 1
        start_row = 6 if self.color == Color.WHITE else 1

        if board.is_in_bounds(r + direction, c) and board.grid[r + direction][c] is None:
            moves.append((r + direction, c))
            if r == start_row and board.grid[r + 2 * direction][c] is None:
                moves.append((r + 2 * direction, c))

        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if board.is_in_bounds(nr, nc):
                target = board.grid[nr][nc]
                if target is not None and target.color != self.color:
                    moves.append((nr, nc))
                elif history:
                    last = history[-1]
                    if isinstance(last.piece_moved, Pawn) and abs(last.start_pos[0] - last.end_pos[0]) == 2:
                        if last.end_pos[0] == r and last.end_pos[1] == nc:
                            moves.append((nr, nc))
        return moves

class Knight(Piece):
    def get_symbol(self): return '♘' if self.color == Color.WHITE else '♞'
    def get_possible_moves(self, board, current_pos, history=None):
        r, c = current_pos
        jumps = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
        return [(r+dr, c+dc) for dr, dc in jumps if self._is_valid_target(board, r+dr, c+dc)]

class Bishop(Piece):
    def get_symbol(self): return '♗' if self.color == Color.WHITE else '♝'
    def get_possible_moves(self, board, current_pos, history=None):
        return self._get_sliding_moves(board, current_pos, [(-1,-1), (-1,1), (1,-1), (1,1)])

class Rook(Piece):
    def get_symbol(self): return '♖' if self.color == Color.WHITE else '♜'
    def get_possible_moves(self, board, current_pos, history=None):
        return self._get_sliding_moves(board, current_pos, [(-1,0), (1,0), (0,-1), (0,1)])

class Queen(Piece):
    def get_symbol(self): return '♕' if self.color == Color.WHITE else '♛'
    def get_possible_moves(self, board, current_pos, history=None):
        return self._get_sliding_moves(board, current_pos, [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)])

class King(Piece):
    def get_symbol(self): return '♔' if self.color == Color.WHITE else '♚'
    def get_possible_moves(self, board, current_pos, history=None):
        r, c = current_pos
        steps = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        return [(r+dr, c+dc) for dr, dc in steps if self._is_valid_target(board, r+dr, c+dc)]

class Checker(Piece):
    def get_symbol(self): return '⛀' if self.color == Color.WHITE else '⛂'
    def get_possible_moves(self, board, current_pos, history=None):
        moves = []
        r, c = current_pos
        direction = -1 if self.color == Color.WHITE else 1
        
        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if board.is_in_bounds(nr, nc) and board.grid[nr][nc] is None:
                moves.append((nr, nc))
                
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                nr, nc = r + dr * 2, c + dc * 2
                mid_r, mid_c = r + dr, c + dc
                if board.is_in_bounds(nr, nc) and board.grid[nr][nc] is None:
                    mid = board.grid[mid_r][mid_c]
                    if mid and mid.color != self.color:
                        moves.append((nr, nc))
        return moves

class CheckerKing(Piece):
    def get_symbol(self): return '♕' if self.color == Color.WHITE else '♛'
    def get_possible_moves(self, board, current_pos, history=None):
        moves = []
        r, c = current_pos
        for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            nr, nc = r + dr, c + dc
            jumped = False
            while board.is_in_bounds(nr, nc):
                target = board.grid[nr][nc]
                if target is None:
                    moves.append((nr, nc))
                    if jumped: break
                elif target.color != self.color and not jumped:
                    if board.is_in_bounds(nr + dr, nc + dc) and board.grid[nr + dr][nc + dc] is None:
                        moves.append((nr + dr, nc + dc))
                        jumped = True
                    else: break
                else: break
                nr += dr
                nc += dc
        return moves

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]

    def setup_chess(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        for c in range(8):
            self.grid[1][c] = Pawn(Color.BLACK)
            self.grid[6][c] = Pawn(Color.WHITE)
        placement = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for c in range(8):
            self.grid[0][c] = placement[c](Color.BLACK)
            self.grid[7][c] = placement[c](Color.WHITE)

    def setup_checkers(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 != 0: self.grid[r][c] = Checker(Color.BLACK)
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 != 0: self.grid[r][c] = Checker(Color.WHITE)

    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_threatened_pieces(self, color, history):
        enemy = Color.BLACK if color == Color.WHITE else Color.WHITE
        attacked_squares = set()
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color == enemy:
                    attacked_squares.update(p.get_possible_moves(self, (r, c), history))
        
        threatened = []
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color == color and (r, c) in attacked_squares:
                    threatened.append((r, c))
        return threatened

    def is_in_check(self, color, history):
        for r, c in self.get_threatened_pieces(color, history):
            if isinstance(self.grid[r][c], King):
                return True
        return False

    def print_board(self, threatened_positions=None):
        if threatened_positions is None: threatened_positions = []
        print("\n     a  b  c  d  e  f  g  h")
        print("   +------------------------+")
        for r in range(8):
            row_str = f" {8 - r} |"
            for c in range(8):
                piece = self.grid[r][c]
                if piece is None:
                    sym = " . "
                else:
                    sym = piece.get_symbol()
                    if (r, c) in threatened_positions:
                        sym = f"[{sym}]"
                    else:
                        sym = f" {sym} "
                row_str += sym
            print(row_str + f"| {8 - r}")
        print("   +------------------------+")
        print("     a  b  c  d  e  f  g  h\n")

    def execute_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.grid[sr][sc]
        captured_piece = self.grid[er][ec]
        capture_pos = (er, ec)
        promoted = False
        
        if isinstance(piece, Pawn) and sc != ec and captured_piece is None:
            capture_pos = (sr, ec)
            captured_piece = self.grid[sr][ec]
            self.grid[sr][ec] = None
            
        if piece.name in ["Checker", "CheckerKing"] and abs(sr - er) >= 2:
            dr = 1 if er > sr else -1
            dc = 1 if ec > sc else -1
            curr_r, curr_c = sr + dr, sc + dc
            while curr_r != er and curr_c != ec:
                if self.grid[curr_r][curr_c] is not None:
                    capture_pos = (curr_r, curr_c)
                    captured_piece = self.grid[curr_r][curr_c]
                    self.grid[curr_r][curr_c] = None
                    break
                curr_r += dr
                curr_c += dc

        if isinstance(piece, Pawn) and (er == 0 or er == 7): promoted = True
        if piece.name == "Checker" and (er == 0 or er == 7): promoted = True

        self.grid[er][ec] = piece
        self.grid[sr][sc] = None
        
        if promoted:
            self.grid[er][ec] = Queen(piece.color) if isinstance(piece, Pawn) else CheckerKing(piece.color)
            
        return Move(start, end, piece, captured_piece, capture_pos, promoted)

    def undo_move(self, move):
        self.grid[move.start_pos[0]][move.start_pos[1]] = move.piece_moved
        self.grid[move.end_pos[0]][move.end_pos[1]] = None
        if move.piece_captured:
            r, c = move.capture_pos
            self.grid[r][c] = move.piece_captured

class Game:
    def __init__(self):
        self.board = Board()
        self.history = []
        self.current_turn = Color.WHITE
        self.game_type = "chess"

    def parse_position(self, pos_str):
        if len(pos_str) != 2: return None
        ru_to_en = {'а':'a', 'с':'c', 'е':'e', 'х':'h', 'р':'p', 'о':'o', 'в':'b'}
        col_char = ru_to_en.get(pos_str.lower()[0], pos_str.lower()[0])
        row_char = pos_str[1]
        if col_char < 'a' or col_char > 'h' or not row_char.isdigit() or row_char < '1' or row_char > '8':
            return None
        return (8 - int(row_char), ord(col_char) - ord('a'))

    def play(self):
        print("=== ООП Игровой Движок ===")
        print("1 - Шахматы")
        print("2 - Шашки")
        
        try:
            choice = input("Выбери игру (1 или 2): ").strip()
        except EOFError:
            choice = '1'
            
        if choice == '2':
            self.game_type = "checkers"
            self.board.setup_checkers()
        else:
            self.board.setup_chess()

        print("\nУправление:")
        print("  'e2'    - показать куда может походить фигура (подсказка)")
        print("  'e2 e4' - сделать ход")
        print("  'undo'  - откатить последний ход")
        print("  'quit'  - выход\n")
        
        while True:
            threats = self.board.get_threatened_pieces(self.current_turn, self.history)
            self.board.print_board(threats)
            
            if self.game_type == "chess" and self.board.is_in_check(self.current_turn, self.history):
                print("!!! ⚠️ ВНИМАНИЕ: ТЕБЕ ШАХ !!!")
                
            print(f"Ход: {self.current_turn.value}")
            try:
                user_input = input("> ").strip().lower()
            except EOFError:
                break
                
            if not user_input:
                continue
                
            if user_input in ['quit', 'exit', 'выход']: break
                
            parts = user_input.split()
            
            if parts[0] == 'undo':
                count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                for _ in range(count):
                    if not self.history:
                        print("История пуста.")
                        break
                    last_move = self.history.pop()
                    self.board.undo_move(last_move)
                    self.current_turn = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
                continue
                
            if len(parts) == 1:
                pos = self.parse_position(parts[0])
                if pos:
                    p = self.board.grid[pos[0]][pos[1]]
                    if p and p.color == self.current_turn:
                        moves = p.get_possible_moves(self.board, pos, self.history)
                        coords = [f"{chr(c + ord('a'))}{8 - r}" for r, c in moves]
                        print(f"Доступные ходы: {', '.join(coords) if coords else 'нет'}")
                    else:
                        print("Выбери свою фигуру для подсказки.")
                continue

            if len(parts) == 2:
                start_pos, end_pos = self.parse_position(parts[0]), self.parse_position(parts[1])
                if not start_pos or not end_pos:
                    print("Ошибка ввода.")
                    continue
                piece = self.board.grid[start_pos[0]][start_pos[1]]
                if not piece or piece.color != self.current_turn:
                    print("Там нет твоей фигуры.")
                    continue
                possible_moves = piece.get_possible_moves(self.board, start_pos, self.history)
                if end_pos not in possible_moves:
                    print("Недопустимый ход.")
                    continue
                move_obj = self.board.execute_move(start_pos, end_pos)
                self.history.append(move_obj)
                self.current_turn = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
            else:
                print("Используй формат 'e2 e4' или 'undo'.")

if __name__ == "__main__":
    game = Game()
    game.play()
