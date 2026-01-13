#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ----------------------------
# Config / Tokens
# ----------------------------
NEWLINE_TOKEN = "으이?"

# Named registers (preferred, human-readable)
NAMED_REGS = [
    "멘똔",
    "배털",
    "정빵",
    "애플리프트",
    "깨무이",
    "혁두",
    "턱살개구리",
    "잉진이",
    "민짜이",
]

REG_BASE = ["멘", "빵", "깨", "털", "두", "덜", "애"]  # order defines register ordering
REGTOK_GLUE = "가"

TOK_SET = "하요하요"
TOK_RESET = "바요바요"

TOK_ADD = "누이 좋고"
TOK_SUB = "매부 좋고"
TOK_MUL = "아주 좋고"

TOK_IF = "건방진"
TOK_WHILE = "좋다좋다"
TOK_END = "쉐끼마"
TOK_ELSE = "정신이 나갔어 정신이"

CMP_GT = "응나멘똔"
CMP_LT = "응너도혁"

TOK_PRINT_START = "와타시는"
TOK_PRINT_NUM_END = "이라는 것이야"
TOK_PRINT_CHAR_END = "한다는 것이야"

# Output-only shortcuts (inside 와타시는 ... 종료토큰)
TOK_OUT_SPACE = "~"      # prints a single space
TOK_OUT_NEWLINE = "ㅢ?!"  # prints a newline

# Laugh-number tokens
NEG_LAUGH = "뭐꼬"
T_I = "훠"
T_X = "훳"
T_C = "허"
T_M = "헛"
T_FIVE_PREFIX = "훠러"
T_GROUP_ZERO = "찢"


# ----------------------------
# Helpers: comment stripping
# ----------------------------
def clean_line(raw: str) -> str:
    """
    Comment rule:
      - Anything after '#' is ignored.
      - Leading/trailing whitespace trimmed.
    """
    return raw.split("#", 1)[0].strip()


# ----------------------------
# Helpers: register parsing
# ----------------------------
def build_register_set() -> Tuple[Dict[str, int], Dict[int, str]]:
    """
    Registers:
      - 9 named registers (NAMED_REGS)
      - 49 patterned registers: A가B가 where A,B in REG_BASE (7x7 total)

    Total: 58 registers.
    """
    reg_to_idx: Dict[str, int] = {}
    idx_to_reg: Dict[int, str] = {}

    # 1) Named registers first (stable ordering)
    idx = 0
    for name in NAMED_REGS:
        if name in reg_to_idx:
            continue
        reg_to_idx[name] = idx
        idx_to_reg[idx] = name
        idx += 1

    if idx != 9:
        raise RuntimeError(f"NAMED_REGS must contain 9 unique registers, got {idx}")

    # 2) Patterned registers (existing 49)
    for a in REG_BASE:
        for b in REG_BASE:
            token = f"{a}{REGTOK_GLUE}{b}{REGTOK_GLUE}"
            reg_to_idx[token] = idx
            idx_to_reg[idx] = token
            idx += 1

    return reg_to_idx, idx_to_reg


REG_TO_IDX, IDX_TO_REG = build_register_set()


def is_register_token(line: str) -> bool:
    return line.strip() in REG_TO_IDX


# ----------------------------
# Helpers: number parsing
# ----------------------------
def parse_arabic_int(s: str) -> Optional[int]:
    s = s.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_laugh_number(s: str) -> Optional[int]:
    """
    Laugh-number format (stack / prefix-eval)

    Tokens:
      - 훠   : push 1
      - 훳   : top *= 10
      - 허   : top *= 100
      - 헛   : top *= 1000
      - 훠러 : top += 5
      - 뭐꼬 : negative prefix (negate final sum)

    Evaluation:
      - Read left -> right and execute on an integer stack.
      - Final value = sum(stack). Apply negation if prefixed with 뭐꼬.

    Notes:
      - 찢 is not used in this system; if present, parsing fails.
      - Operators (훳/허/헛/훠러) require a non-empty stack.
    """
    raw = s.strip()
    if not raw:
        return None

    neg = False
    if raw.startswith(NEG_LAUGH):
        neg = True
        raw = raw[len(NEG_LAUGH):].strip()
        if not raw:
            return None

    # Reject legacy token explicitly (찢)
    if T_GROUP_ZERO in raw:
        return None

    stack: List[int] = []

    i = 0
    while i < len(raw):
        # 훠러 (top += 5)
        if raw.startswith(T_FIVE_PREFIX, i):
            if not stack:
                return None
            stack[-1] += 5
            i += len(T_FIVE_PREFIX)
            continue

        ch = raw[i]

        # 훠 (push 1)
        if ch == T_I:
            stack.append(1)
            i += 1
            continue

        # Multiply operators: 훳 / 허 / 헛
        if ch in (T_X, T_C, T_M):
            if not stack:
                return None
            if ch == T_X:
                stack[-1] *= 10
            elif ch == T_C:
                stack[-1] *= 100
            else:  # T_M
                stack[-1] *= 1000
            i += 1
            continue

        # Unknown token
        return None

    if not stack:
        return None

    value = sum(stack)
    return -value if neg else value


def parse_number_or_none(s: str) -> Optional[int]:
    v = parse_arabic_int(s)
    if v is not None:
        return v
    return parse_laugh_number(s)


# ----------------------------
# Program indexing (blocks)
# ----------------------------
@dataclass
class IfMeta:
    else_ip: Optional[int]
    end_ip: int


@dataclass
class WhileMeta:
    start_ip: int
    end_ip: int


@dataclass
class ProgramIndex:
    if_map: Dict[int, IfMeta]
    while_map: Dict[int, WhileMeta]


def index_blocks(lines: List[str]) -> ProgramIndex:
    """
    Build jump tables for if/else/end and while/end.
    Comments are ignored.
    """
    if_map: Dict[int, IfMeta] = {}
    while_map: Dict[int, WhileMeta] = {}

    stack: List[Tuple[str, int, Optional[int]]] = []  # (kind, start_ip, else_ip_if_any)

    for ip, raw in enumerate(lines):
        line = clean_line(raw)
        if not line:
            continue

        if line.startswith(TOK_IF):
            stack.append(("if", ip, None))
        elif line == TOK_ELSE:
            if not stack or stack[-1][0] != "if":
                raise SyntaxError(f"ELSE without IF at line {ip+1}")
            kind, start_ip, _ = stack.pop()
            stack.append((kind, start_ip, ip))
        elif line.startswith(TOK_WHILE):
            stack.append(("while", ip, None))
        elif line == TOK_END:
            if not stack:
                raise SyntaxError(f"END without block at line {ip+1}")
            kind, start_ip, else_ip = stack.pop()
            if kind == "if":
                if_map[start_ip] = IfMeta(else_ip=else_ip, end_ip=ip)
            elif kind == "while":
                while_map[start_ip] = WhileMeta(start_ip=start_ip, end_ip=ip)
            else:
                raise SyntaxError(f"Unknown block kind at line {ip+1}")

    if stack:
        kind, start_ip, _ = stack[-1]
        raise SyntaxError(f"Unclosed block '{kind}' starting at line {start_ip+1}")

    return ProgramIndex(if_map=if_map, while_map=while_map)


# ----------------------------
# Condition parsing/evaluation
# ----------------------------
def parse_condition(line: str) -> Tuple[int, str]:
    parts = line.strip().split()
    if len(parts) < 2:
        raise SyntaxError(f"Missing number in condition: '{line}'")

    n_str = parts[1]
    n = parse_number_or_none(n_str)
    if n is None:
        raise SyntaxError(f"Invalid number in condition: '{n_str}'")

    op = "=="
    if len(parts) >= 3:
        if parts[2] == CMP_GT:
            op = ">"
        elif parts[2] == CMP_LT:
            op = "<"
        else:
            raise SyntaxError(f"Unknown comparator '{parts[2]}' in: '{line}'")
    return n, op


def eval_condition(cur: int, n: int, op: str) -> bool:
    if op == "==":
        return cur == n
    if op == ">":
        return cur > n
    if op == "<":
        return cur < n
    raise RuntimeError(f"Unknown op: {op}")


# ----------------------------
# Interpreter
# ----------------------------
class Interpreter:
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.index = index_blocks(lines)

        self.regs: List[int] = [0] * len(REG_TO_IDX)
        self.cur_idx: int = REG_TO_IDX["멘똔"]

        self.output_chunks: List[str] = []

    def cur_value(self) -> int:
        return self.regs[self.cur_idx]

    def set_cur_value(self, v: int) -> None:
        self.regs[self.cur_idx] = v

    def run(self) -> str:
        ip = 0
        while ip < len(self.lines):
            raw = self.lines[ip]
            line = clean_line(raw)

            if not line:
                ip += 1
                continue

            if is_register_token(line):
                self.cur_idx = REG_TO_IDX[line]
                ip += 1
                continue

            if line == TOK_PRINT_START:
                ip = self._exec_output_block(ip)
                continue

            if line.startswith(TOK_IF):
                n, op = parse_condition(line)
                meta = self.index.if_map.get(ip)
                if meta is None:
                    raise RuntimeError(f"Missing IF meta at line {ip+1}")

                cond = eval_condition(self.cur_value(), n, op)
                if cond:
                    ip += 1
                else:
                    if meta.else_ip is not None:
                        ip = meta.else_ip + 1
                    else:
                        ip = meta.end_ip + 1
                continue

            if line == TOK_ELSE:
                owner_if = None
                for _if_ip, meta in self.index.if_map.items():
                    if meta.else_ip == ip:
                        owner_if = meta
                        break
                if owner_if is None:
                    raise RuntimeError(f"ELSE meta not found at line {ip+1}")
                ip = owner_if.end_ip + 1
                continue

            if line.startswith(TOK_WHILE):
                n, op = parse_condition(line)
                meta = self.index.while_map.get(ip)
                if meta is None:
                    raise RuntimeError(f"Missing WHILE meta at line {ip+1}")

                cond = eval_condition(self.cur_value(), n, op)
                if cond:
                    ip += 1
                else:
                    ip = meta.end_ip + 1
                continue

            if line == TOK_END:
                owner_while_start = None
                for wstart, wmeta in self.index.while_map.items():
                    if wmeta.end_ip == ip:
                        owner_while_start = wstart
                        break
                if owner_while_start is not None:
                    ip = owner_while_start
                else:
                    ip += 1
                continue

            if line.startswith(TOK_SET):
                rest = line[len(TOK_SET):].strip()
                if rest == "":
                    self.set_cur_value(0)
                else:
                    v = parse_number_or_none(rest)
                    if v is None:
                        raise SyntaxError(f"Invalid number for SET at line {ip+1}: '{rest}'")
                    self.set_cur_value(v)
                ip += 1
                continue

            if line == TOK_RESET:
                self.set_cur_value(0)
                ip += 1
                continue

            if line.startswith(TOK_ADD):
                rest = line[len(TOK_ADD):].strip()
                delta = 1
                if rest:
                    v = parse_number_or_none(rest)
                    if v is None:
                        raise SyntaxError(f"Invalid number for ADD at line {ip+1}: '{rest}'")
                    delta = v
                self.set_cur_value(self.cur_value() + delta)
                ip += 1
                continue

            if line.startswith(TOK_SUB):
                rest = line[len(TOK_SUB):].strip()
                delta = 1
                if rest:
                    v = parse_number_or_none(rest)
                    if v is None:
                        raise SyntaxError(f"Invalid number for SUB at line {ip+1}: '{rest}'")
                    delta = v
                self.set_cur_value(self.cur_value() - delta)
                ip += 1
                continue

            if line.startswith(TOK_MUL):
                rest = line[len(TOK_MUL):].strip()
                if not rest:
                    raise SyntaxError(f"MUL missing operand at line {ip+1}")

                # 레지스터 또는 숫자(아랍숫자/웃음숫자) 둘 다 허용
                if rest in REG_TO_IDX:
                    rhs = self.regs[REG_TO_IDX[rest]]
                else:
                    v = parse_number_or_none(rest)
                    if v is None:
                        raise SyntaxError(
                            f"MUL operand must be a register token or number at line {ip+1}: '{rest}'"
                        )
                    rhs = v

                self.set_cur_value(self.cur_value() * rhs)
                ip += 1
                continue

            raise SyntaxError(f"Unknown statement at line {ip+1}: '{line}'")

        return "".join(self.output_chunks)

    def _exec_output_block(self, start_ip: int) -> int:
        ip = start_ip + 1
        if ip >= len(self.lines):
            raise SyntaxError(f"Unterminated output block starting at line {start_ip+1}")

        content: List[str] = []
        terminator: Optional[str] = None

        while ip < len(self.lines):
            line = clean_line(self.lines[ip])
            if line == "":
                ip += 1
                continue
            if line == TOK_PRINT_NUM_END or line == TOK_PRINT_CHAR_END:
                terminator = line
                break
            content.append(line)
            ip += 1

        if terminator is None:
            raise SyntaxError(f"Unterminated output block starting at line {start_ip+1}")

        if terminator == TOK_PRINT_NUM_END:
            for item in content:
                if item == TOK_OUT_SPACE:
                    self.output_chunks.append(" ")
                    continue
                if item == TOK_OUT_NEWLINE:
                    self.output_chunks.append("\n")
                    continue

                if item in REG_TO_IDX:
                    v = self.regs[REG_TO_IDX[item]]
                else:
                    v = parse_number_or_none(item)
                    if v is None:
                        raise SyntaxError(
                            f"Invalid number/register in numeric output near line {ip+1}: '{item}'"
                        )
                self.output_chunks.append(str(v))
        else:
            for item in content:
                if item == TOK_OUT_SPACE:
                    self.output_chunks.append(" ")
                    continue
                if item == TOK_OUT_NEWLINE:
                    self.output_chunks.append("\n")
                    continue

                v = parse_number_or_none(item)
                if v is None:
                    raise SyntaxError(
                        f"Invalid number in ASCII output (register not allowed) near line {ip+1}: '{item}'"
                    )
                self.output_chunks.append(chr(v % 256))

        return ip + 1


# ----------------------------
# I/O
# ----------------------------
def preprocess(src: str) -> str:
    return src.replace(NEWLINE_TOKEN, "\n")


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("Usage: python mentonlang_v4.py <program.txt>", file=sys.stderr)
        return 2

    path = argv[1]
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    src = preprocess(src)
    lines = src.splitlines()

    interp = Interpreter(lines)
    out = interp.run()
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
