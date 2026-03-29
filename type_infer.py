#!/usr/bin/env python3
"""Hindley-Milner Type Inference - Infer types for a simple functional language."""
import sys

class TVar:
    _id = 0
    def __init__(self):
        self.id = TVar._id; TVar._id += 1; self.instance = None
    def __repr__(self): return f"t{self.id}" if not self.instance else repr(self.instance)

class TCon:
    def __init__(self, name, args=None):
        self.name = name; self.args = args or []
    def __repr__(self):
        if not self.args: return self.name
        if self.name == "->": return f"({self.args[0]} -> {self.args[1]})"
        return f"{self.name}[{', '.join(map(repr, self.args))}]"

Int = TCon("Int"); Bool = TCon("Bool"); Str = TCon("String")

def arrow(a, b): return TCon("->", [a, b])

def prune(t):
    if isinstance(t, TVar) and t.instance: t.instance = prune(t.instance); return t.instance
    return t

def occurs(v, t):
    t = prune(t)
    if t is v: return True
    if isinstance(t, TCon): return any(occurs(v, a) for a in t.args)
    return False

def unify(a, b):
    a, b = prune(a), prune(b)
    if isinstance(a, TVar):
        if a is not b:
            if occurs(a, b): raise TypeError(f"Recursive type: {a} in {b}")
            a.instance = b
    elif isinstance(b, TVar): unify(b, a)
    elif isinstance(a, TCon) and isinstance(b, TCon):
        if a.name != b.name or len(a.args) != len(b.args):
            raise TypeError(f"Cannot unify {a} with {b}")
        for x, y in zip(a.args, b.args): unify(x, y)

def infer(expr, env):
    if isinstance(expr, str):
        if expr.isdigit(): return Int
        if expr in ("true", "false"): return Bool
        if expr.startswith("\\"") and expr.endswith("\\""):  return Str
        if expr in env: return env[expr]
        raise NameError(f"Undefined: {expr}")
    if isinstance(expr, list):
        if expr[0] == "fn":
            param, body = expr[1], expr[2]
            tv = TVar(); new_env = {**env, param: tv}
            ret = infer(body, new_env)
            return arrow(tv, ret)
        if expr[0] == "let":
            name, val, body = expr[1], expr[2], expr[3]
            t = infer(val, env)
            return infer(body, {**env, name: t})
        if expr[0] == "if":
            cond, then, els = expr[1], expr[2], expr[3]
            unify(infer(cond, env), Bool)
            t = infer(then, env); unify(t, infer(els, env))
            return t
        func, arg = expr[0], expr[1]
        ft = infer(func, env); at = infer(arg, env)
        rt = TVar(); unify(ft, arrow(at, rt))
        return prune(rt)

def parse(s):
    tokens = s.replace("(", " ( ").replace(")", " ) ").split()
    pos = [0]
    def read():
        if tokens[pos[0]] == "(":
            pos[0] += 1; lst = []
            while tokens[pos[0]] != ")": lst.append(read())
            pos[0] += 1; return lst
        else:
            t = tokens[pos[0]]; pos[0] += 1; return t
    return read()

def main():
    builtins = {"+": arrow(Int, arrow(Int, Int)), "-": arrow(Int, arrow(Int, Int)),
                "*": arrow(Int, arrow(Int, Int)), "==": arrow(Int, arrow(Int, Bool)),
                "not": arrow(Bool, Bool)}
    if len(sys.argv) < 2:
        print("Usage: type_infer.py <expr>"); print("Example: type_infer.py "(fn x (+ x 1))""); sys.exit(1)
    expr = parse(sys.argv[1])
    TVar._id = 0
    try:
        t = infer(expr, builtins)
        print(f"Expression: {sys.argv[1]}"); print(f"Type: {prune(t)}")
    except (TypeError, NameError) as e:
        print(f"Type error: {e}")

if __name__ == "__main__":
    main()
