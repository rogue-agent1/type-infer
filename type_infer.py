#!/usr/bin/env python3
"""type_infer - Hindley-Milner type inference."""
import sys, argparse

class Type: pass
class TVar(Type):
    _counter = 0
    def __init__(self, name=None):
        if name is None: TVar._counter += 1; name = f"t{TVar._counter}"
        self.name = name
    def __repr__(self): return self.name
class TCon(Type):
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name
class TFun(Type):
    def __init__(self, arg, ret): self.arg = arg; self.ret = ret
    def __repr__(self): return f"({self.arg} -> {self.ret})"

INT = TCon("Int"); BOOL = TCon("Bool"); STR = TCon("String")

class Expr: pass
class EVar(Expr):
    def __init__(self, name): self.name = name
class EInt(Expr):
    def __init__(self, val): self.val = val
class EBool(Expr):
    def __init__(self, val): self.val = val
class ELam(Expr):
    def __init__(self, param, body): self.param = param; self.body = body
class EApp(Expr):
    def __init__(self, func, arg): self.func = func; self.arg = arg
class ELet(Expr):
    def __init__(self, name, val, body): self.name = name; self.val = val; self.body = body
class EIf(Expr):
    def __init__(self, cond, then, else_): self.cond = cond; self.then = then; self.else_ = else_

class Scheme:
    def __init__(self, vars_, type_): self.vars = vars_; self.type = type_

def free_vars(t):
    if isinstance(t, TVar): return {t.name}
    if isinstance(t, TCon): return set()
    if isinstance(t, TFun): return free_vars(t.arg) | free_vars(t.ret)
    return set()

def apply_subst(subst, t):
    if isinstance(t, TVar): return subst.get(t.name, t)
    if isinstance(t, TCon): return t
    if isinstance(t, TFun): return TFun(apply_subst(subst, t.arg), apply_subst(subst, t.ret))
    return t

def compose(s1, s2):
    result = {k: apply_subst(s1, v) for k, v in s2.items()}
    result.update(s1)
    return result

def unify(t1, t2):
    if isinstance(t1, TVar):
        if t1.name in free_vars(t2) and t1 != t2: raise TypeError(f"Infinite type: {t1} ~ {t2}")
        return {t1.name: t2}
    if isinstance(t2, TVar): return unify(t2, t1)
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name == t2.name: return {}
        raise TypeError(f"Type mismatch: {t1} vs {t2}")
    if isinstance(t1, TFun) and isinstance(t2, TFun):
        s1 = unify(t1.arg, t2.arg)
        s2 = unify(apply_subst(s1, t1.ret), apply_subst(s1, t2.ret))
        return compose(s2, s1)
    raise TypeError(f"Cannot unify {t1} and {t2}")

def instantiate(scheme):
    mapping = {v: TVar() for v in scheme.vars}
    def go(t):
        if isinstance(t, TVar): return mapping.get(t.name, t)
        if isinstance(t, TCon): return t
        if isinstance(t, TFun): return TFun(go(t.arg), go(t.ret))
        return t
    return go(scheme.type)

def generalize(env, t):
    env_fv = set()
    for s in env.values():
        env_fv |= free_vars(s.type) - set(s.vars)
    return Scheme(list(free_vars(t) - env_fv), t)

def infer(env, expr):
    if isinstance(expr, EInt): return {}, INT
    if isinstance(expr, EBool): return {}, BOOL
    if isinstance(expr, EVar):
        if expr.name not in env: raise TypeError(f"Unbound: {expr.name}")
        return {}, instantiate(env[expr.name])
    if isinstance(expr, ELam):
        tv = TVar()
        new_env = dict(env); new_env[expr.param] = Scheme([], tv)
        s, t = infer(new_env, expr.body)
        return s, TFun(apply_subst(s, tv), t)
    if isinstance(expr, EApp):
        s1, t1 = infer(env, expr.func)
        env2 = {k: Scheme(v.vars, apply_subst(s1, v.type)) for k, v in env.items()}
        s2, t2 = infer(env2, expr.arg)
        tv = TVar()
        s3 = unify(apply_subst(s2, t1), TFun(t2, tv))
        return compose(s3, compose(s2, s1)), apply_subst(s3, tv)
    if isinstance(expr, ELet):
        s1, t1 = infer(env, expr.val)
        env2 = {k: Scheme(v.vars, apply_subst(s1, v.type)) for k, v in env.items()}
        scheme = generalize(env2, t1)
        env2[expr.name] = scheme
        s2, t2 = infer(env2, expr.body)
        return compose(s2, s1), t2
    if isinstance(expr, EIf):
        s1, t1 = infer(env, expr.cond)
        s2 = unify(t1, BOOL)
        s = compose(s2, s1)
        env2 = {k: Scheme(v.vars, apply_subst(s, v.type)) for k, v in env.items()}
        s3, t2 = infer(env2, expr.then)
        s4, t3 = infer(env2, expr.else_)
        s5 = unify(t2, t3)
        return compose(s5, compose(s4, compose(s3, s))), apply_subst(s5, t2)
    raise TypeError(f"Unknown expr: {expr}")

def main():
    p = argparse.ArgumentParser(description="Hindley-Milner type inference")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    if args.demo:
        tests = [
            ("42", EInt(42)),
            ("\\x.x", ELam("x", EVar("x"))),
            ("\\f.\\x. f x", ELam("f", ELam("x", EApp(EVar("f"), EVar("x"))))),
            ("let id = \\x.x in id 42", ELet("id", ELam("x", EVar("x")), EApp(EVar("id"), EInt(42)))),
            ("let id = \\x.x in id id", ELet("id", ELam("x", EVar("x")), EApp(EVar("id"), EVar("id")))),
        ]
        for name, expr in tests:
            try:
                s, t = infer({}, expr)
                print(f"{name:35s} : {apply_subst(s, t)}")
            except TypeError as e:
                print(f"{name:35s} : ERROR: {e}")
    else: p.print_help()

if __name__ == "__main__":
    main()
