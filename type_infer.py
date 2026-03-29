#!/usr/bin/env python3
"""Hindley-Milner type inference (simplified). Zero dependencies."""
import sys

class Type:
    pass

class TVar(Type):
    _counter = 0
    def __init__(self, name=None):
        if name is None:
            TVar._counter += 1
            name = f"t{TVar._counter}"
        self.name = name; self.instance = None
    def __repr__(self): return self.instance.__repr__() if self.instance else self.name

class TCon(Type):
    def __init__(self, name, args=None):
        self.name = name; self.args = args or []
    def __repr__(self):
        if not self.args: return self.name
        if self.name == "->": return f"({self.args[0]} -> {self.args[1]})"
        return f"{self.name}[{', '.join(str(a) for a in self.args)}]"

Int = TCon("Int"); Bool = TCon("Bool"); String = TCon("String")
def Arrow(a, b): return TCon("->", [a, b])
def List(t): return TCon("List", [t])

def prune(t):
    if isinstance(t, TVar) and t.instance:
        t.instance = prune(t.instance)
        return t.instance
    return t

def occurs_in(v, t):
    t = prune(t)
    if t is v: return True
    if isinstance(t, TCon): return any(occurs_in(v, a) for a in t.args)
    return False

def unify(a, b):
    a, b = prune(a), prune(b)
    if isinstance(a, TVar):
        if a is not b:
            if occurs_in(a, b): raise TypeError(f"Recursive type: {a} in {b}")
            a.instance = b
    elif isinstance(b, TVar):
        unify(b, a)
    elif isinstance(a, TCon) and isinstance(b, TCon):
        if a.name != b.name or len(a.args) != len(b.args):
            raise TypeError(f"Type mismatch: {a} vs {b}")
        for aa, bb in zip(a.args, b.args):
            unify(aa, bb)

def infer(expr, env=None):
    env = env or {}
    if isinstance(expr, bool): return Bool
    if isinstance(expr, int): return Int
    if isinstance(expr, str):
        if expr in env: return env[expr]
        raise NameError(f"Undefined: {expr}")
    if isinstance(expr, tuple):
        if expr[0] == "lambda":
            _, param, body = expr
            tv = TVar()
            new_env = dict(env); new_env[param] = tv
            body_type = infer(body, new_env)
            return Arrow(tv, body_type)
        if expr[0] == "apply":
            _, fn, arg = expr
            fn_type = infer(fn, env)
            arg_type = infer(arg, env)
            result = TVar()
            unify(fn_type, Arrow(arg_type, result))
            return prune(result)
        if expr[0] == "let":
            _, name, val, body = expr
            val_type = infer(val, env)
            new_env = dict(env); new_env[name] = val_type
            return infer(body, new_env)
        if expr[0] == "if":
            _, cond, then, else_ = expr
            unify(infer(cond, env), Bool)
            then_t = infer(then, env)
            unify(then_t, infer(else_, env))
            return then_t

if __name__ == "__main__":
    env = {"add": Arrow(Int, Arrow(Int, Int)), "eq": Arrow(Int, Arrow(Int, Bool))}
    expr = ("apply", ("apply", "add", 1), 2)
    print(f"add 1 2 : {prune(infer(expr, env))}")
    id_fn = ("lambda", "x", "x")
    print(f"id : {prune(infer(id_fn, env))}")
