#!/usr/bin/env python3
"""Hindley-Milner type inference — zero-dep."""

class Type:
    pass

class TVar(Type):
    _counter=0
    def __init__(self, name=None):
        if name is None: TVar._counter+=1; name=f"t{TVar._counter}"
        self.name=name
    def __repr__(self): return self.name

class TFun(Type):
    def __init__(self, arg, ret): self.arg=arg; self.ret=ret
    def __repr__(self): return f"({self.arg} -> {self.ret})"

class TInt(Type):
    def __repr__(self): return "Int"

class TBool(Type):
    def __repr__(self): return "Bool"

class Subst(dict):
    def apply(self, t):
        if isinstance(t,TVar): return self.apply(self[t.name]) if t.name in self else t
        if isinstance(t,TFun): return TFun(self.apply(t.arg),self.apply(t.ret))
        return t
    def compose(self, other):
        s=Subst({k:self.apply(v) for k,v in other.items()})
        s.update(self); return s

def unify(t1, t2):
    t1=resolve(t1); t2=resolve(t2)
    if isinstance(t1,TVar): return Subst({t1.name:t2})
    if isinstance(t2,TVar): return Subst({t2.name:t1})
    if isinstance(t1,TInt) and isinstance(t2,TInt): return Subst()
    if isinstance(t1,TBool) and isinstance(t2,TBool): return Subst()
    if isinstance(t1,TFun) and isinstance(t2,TFun):
        s1=unify(t1.arg,t2.arg); s2=unify(s1.apply(t1.ret),s1.apply(t2.ret))
        return s2.compose(s1)
    raise TypeError(f"Cannot unify {t1} with {t2}")

_subst=Subst()
def resolve(t):
    while isinstance(t,TVar) and t.name in _subst: t=_subst[t.name]
    return t

def infer(expr, env=None):
    global _subst; env=env or {}
    if isinstance(expr,int): return TInt()
    if isinstance(expr,bool): return TBool()
    if isinstance(expr,str):
        if expr in env: return env[expr]
        raise NameError(f"Unbound: {expr}")
    if isinstance(expr,tuple):
        if expr[0]=="lambda":
            _,param,body=expr; tv=TVar()
            new_env=dict(env); new_env[param]=tv
            ret=infer(body,new_env)
            return TFun(tv,ret)
        if expr[0]=="let":
            _,name,val,body=expr
            t=infer(val,env); new_env=dict(env); new_env[name]=t
            return infer(body,new_env)
        # Application
        fn,arg=expr
        tf=infer(fn,env); ta=infer(arg,env); tr=TVar()
        s=unify(tf,TFun(ta,tr)); _subst.compose(s)
        return s.apply(tr)

if __name__=="__main__":
    _subst=Subst()
    tests=[(42,"literal int"),(True,"literal bool"),
           (("lambda","x","x"),"identity"),
           (("lambda","x",("lambda","y","x")),"const"),
           (("let","id",("lambda","x","x"),("id",42)),"let + apply")]
    for expr,desc in tests:
        _subst=Subst(); TVar._counter=0
        try:
            t=infer(expr); print(f"  {desc}: {t}")
        except Exception as e: print(f"  {desc}: Error — {e}")
