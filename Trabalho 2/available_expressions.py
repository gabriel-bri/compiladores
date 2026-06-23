import re
import sys
 
SEP = "-" * 30
  
def read_blocks(text: str):
  
    lines = text.split('\n')
    idx, n = 0, len(lines)
    order = []
    blocks = {}
 
    while idx < n:
        header = lines[idx].strip()
        idx += 1
        if header == '':
            continue
        parts = header.split()
        if len(parts) < 2:
            continue
        bid, m = int(parts[0]), int(parts[1])
 
        code = []
        for _ in range(m):
            code.append(lines[idx] if idx < n else '')
            idx += 1
 
        succ_line = lines[idx].strip() if idx < n else '0'
        idx += 1
        succ_nums = [int(x) for x in succ_line.split()] if succ_line else [0]
        succ = [] if succ_nums == [0] else succ_nums
 
        blocks[bid] = {'code': code, 'succ': succ}
        order.append(bid)
 
    return order, blocks
 
 
def build_preds(order, blocks):
    valid = set(order)
    preds = {bid: [] for bid in order}
    for bid in order:
        for s in blocks[bid]['succ']:
            if s in valid:
                preds[s].append(bid)
    return preds
 
 

 
_ID_OR_NUM = r'[A-Za-z_]\w*(?:\[[^\]]*\])?|\d+(?:\.\d+)?'
 
ASSIGN_RE = re.compile(
    r'^\s*([A-Za-z_]\w*(?:\[[^\]]*\])?)\s*=\s*(?!=)(.+?)\s*;?\s*$'
)
BINOP_RE = re.compile(
    r'^(' + _ID_OR_NUM + r')\s*(<<|>>|<=|>=|==|!=|&&|\|\||\*\*|[+\-*/%&|^<>])\s*('
    + _ID_OR_NUM + r')$'
)
UNARY_RE = re.compile(r'^(-|!|~)\s*(' + _ID_OR_NUM + r')$')
 
 
def base_var(token: str) -> str:

    m = re.match(r'^([A-Za-z_]\w*)', token)
    return m.group(1) if m else token
 
 
def is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False
 
 
def parse_statement(raw_line: str):
    line = raw_line.split('//')[0].strip()
    if not line:
        return None, None, None
 
    m = ASSIGN_RE.match(line)
    if not m:
        return None, None, None
 
    lhs_raw, rhs = m.group(1), m.group(2).strip()
    def_var = base_var(lhs_raw)
 
    b = BINOP_RE.match(rhs)
    if b:
        op1, operator, op2 = b.group(1), b.group(2), b.group(3)
        operands = set()
        if not is_number(op1):
            operands.add(base_var(op1))
        if not is_number(op2):
            operands.add(base_var(op2))
        expr_text = f"{op1} {operator} {op2}"
        return def_var, expr_text, operands
 
    u = UNARY_RE.match(rhs)
    if u:
        operator, operand = u.group(1), u.group(2)
        operands = set()
        if not is_number(operand):
            operands.add(base_var(operand))
        expr_text = f"{operator}{operand}"
        return def_var, expr_text, operands
 

    return def_var, None, None
 
 

def compute_available_expressions(order, blocks):

    universe_order = []
    universe_operands = {}
    for bid in order:
        for raw in blocks[bid]['code']:
            _, expr_text, operands = parse_statement(raw)
            if expr_text is not None and expr_text not in universe_operands:
                universe_order.append(expr_text)
                universe_operands[expr_text] = operands
 
    universe = set(universe_order)
 

    gen, kill = {}, {}
    for bid in order:
        gen_set, kill_set = set(), set()
        for raw in blocks[bid]['code']:
            def_var, expr_text, _ = parse_statement(raw)
            if def_var is None:
                continue
            for e in universe_order:
                if def_var in universe_operands[e] and e != expr_text:
                    kill_set.add(e)
                    gen_set.discard(e)
            if expr_text is not None:
                gen_set.add(expr_text)
                kill_set.discard(expr_text)
        gen[bid] = gen_set
        kill[bid] = kill_set
 
    preds = build_preds(order, blocks)
 
    IN = {bid: set() for bid in order}
    OUT = {bid: (set(universe) if preds[bid] else set()) for bid in order}
 
    changed = True
    while changed:
        changed = False
        for bid in order:
            if preds[bid]:
                in_set = None
                for p in preds[bid]:
                    in_set = set(OUT[p]) if in_set is None else (in_set & OUT[p])
            else:
                in_set = set()  # bloco de entrada: nada disponivel antes dele
 
            out_set = gen[bid] | (in_set - kill[bid])
 
            if in_set != IN[bid] or out_set != OUT[bid]:
                changed = True
            IN[bid] = in_set
            OUT[bid] = out_set
 
    return IN, OUT
 

def format_list(s):
    return str(sorted(s))
 
 
def main():
    text = sys.stdin.read()
    order, blocks = read_blocks(text)
    IN, OUT = compute_available_expressions(order, blocks)
 
    print("Resultado de Available Expressions:")
    for bid in order:
        print(f"IN[{bid}]  = {format_list(IN[bid])}")
        print(f"OUT[{bid}] = {format_list(OUT[bid])}")
        print(SEP)
 
 
if __name__ == "__main__":
    main()
