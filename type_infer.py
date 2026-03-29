#!/usr/bin/env python3
"""type_infer - Hindley-Milner type inference engine."""
import sys

class Type:
    pass

class TVar(Type):
    _counter = 0
    def __init__(self, name=None):
        if name is None:
            TVar._counter += 1
            name = f"t{TVar._counter}"
        self.name = name
    def __repr__(self): return self.name
    def __eq__(self, other): return isinstance(other, TVar) and self.name == other.name
    def __hash__(self): return hash(self.name)

class TCon(Type):
    def __init__(self, name):
        self.name = name
    def __repr__(self): return self.name
    def __eq__(self, other): return isinstance(other, TCon) and self.name == other.name
    def __hash__(self): return hash(self.name)

class TFun(Type):
    def __init__(self, arg, ret):
        self.arg = arg
        self.ret = ret
    def __repr__(self): return f"({self.arg} -> {self.ret})"
    def __eq__(self, other): return isinstance(other, TFun) and self.arg == other.arg and self.ret == other.ret
    def __hash__(self): return hash((type(self), self.arg, self.ret))

INT = TCon("Int")
BOOL = TCon("Bool")
STR = TCon("String")

class Subst:
    def __init__(self, mapping=None):
        self.mapping = mapping or {}
    
    def apply(self, t):
        if isinstance(t, TVar):
            if t.name in self.mapping:
                return self.apply(self.mapping[t.name])
            return t
        if isinstance(t, TCon):
            return t
        if isinstance(t, TFun):
            return TFun(self.apply(t.arg), self.apply(t.ret))
        return t
    
    def compose(self, other):
        new = {k: self.apply(v) for k, v in other.mapping.items()}
        new.update(self.mapping)
        return Subst(new)

def occurs(name, t):
    if isinstance(t, TVar): return t.name == name
    if isinstance(t, TFun): return occurs(name, t.arg) or occurs(name, t.ret)
    return False

def unify(t1, t2):
    if isinstance(t1, TVar):
        if t1 == t2: return Subst()
        if occurs(t1.name, t2): raise TypeError(f"Infinite type: {t1} in {t2}")
        return Subst({t1.name: t2})
    if isinstance(t2, TVar):
        return unify(t2, t1)
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name == t2.name: return Subst()
        raise TypeError(f"Type mismatch: {t1} vs {t2}")
    if isinstance(t1, TFun) and isinstance(t2, TFun):
        s1 = unify(t1.arg, t2.arg)
        s2 = unify(s1.apply(t1.ret), s1.apply(t2.ret))
        return s2.compose(s1)
    raise TypeError(f"Cannot unify {t1} and {t2}")

def infer(expr, env=None, subst=None):
    env = env or {}
    subst = subst or Subst()
    
    if isinstance(expr, bool):
        return BOOL, subst
    if isinstance(expr, int):
        return INT, subst
    if isinstance(expr, str) and not isinstance(expr, tuple):
        if expr in env:
            return env[expr], subst
        raise NameError(f"Unbound: {expr}")
    if isinstance(expr, tuple):
        if expr[0] == "lam":
            _, param, body = expr
            tv = TVar()
            new_env = {**env, param: tv}
            ret_type, s = infer(body, new_env, subst)
            return TFun(s.apply(tv), ret_type), s
        if expr[0] == "app":
            _, fn, arg = expr
            fn_type, s1 = infer(fn, env, subst)
            arg_type, s2 = infer(arg, env, s1)
            ret = TVar()
            s3 = unify(s2.apply(fn_type), TFun(arg_type, ret))
            return s3.apply(ret), s3.compose(s2)
        if expr[0] == "let":
            _, name, val, body = expr
            val_type, s1 = infer(val, env, subst)
            new_env = {**env, name: s1.apply(val_type)}
            return infer(body, new_env, s1)
        if expr[0] == "if":
            _, cond, then, els = expr
            ct, s1 = infer(cond, env, subst)
            s2 = unify(s1.apply(ct), BOOL)
            s = s2.compose(s1)
            tt, s3 = infer(then, env, s)
            et, s4 = infer(els, env, s3)
            s5 = unify(s4.apply(tt), et)
            return s5.apply(et), s5.compose(s4)
    raise TypeError(f"Cannot infer type of {expr}")

def test():
    # Literals
    assert infer(42)[0] == INT
    assert infer(True)[0] == BOOL
    
    # Variable
    assert infer("x", {"x": INT})[0] == INT
    
    # Lambda
    t, _ = infer(("lam", "x", "x"))
    assert isinstance(t, TFun) and t.arg == t.ret  # id: a -> a
    
    # Application
    env = {"inc": TFun(INT, INT)}
    t, _ = infer(("app", "inc", 5), env)
    assert t == INT
    
    # Let
    t, _ = infer(("let", "id", ("lam", "x", "x"), ("app", "id", 42)))
    assert t == INT
    
    # If
    t, _ = infer(("if", True, 1, 2))
    assert t == INT
    
    # Type error
    try:
        unify(INT, BOOL)
        assert False
    except TypeError:
        pass
    
    # Occurs check
    try:
        tv = TVar("a")
        unify(tv, TFun(tv, INT))
        assert False
    except TypeError:
        pass
    
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: type_infer.py test")
