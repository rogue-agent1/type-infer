#!/usr/bin/env python3
"""Hindley-Milner type inference from scratch."""
import sys
_n=0
def fresh():
    global _n; _n+=1; return f"t{_n}"
class TVar:
    def __init__(self,name): self.name=name
    def __repr__(self): return self.name
class TFunc:
    def __init__(self,a,b): self.arg=a; self.ret=b
    def __repr__(self): return f"({self.arg} -> {self.ret})"
class TConst:
    def __init__(self,name): self.name=name
    def __repr__(self): return self.name
def occurs(v,t):
    if isinstance(t,TVar): return t.name==v
    if isinstance(t,TFunc): return occurs(v,t.arg) or occurs(v,t.ret)
    return False
def apply_sub(s,t):
    if isinstance(t,TVar): return s.get(t.name,t)
    if isinstance(t,TFunc): return TFunc(apply_sub(s,t.arg),apply_sub(s,t.ret))
    return t
def unify(a,b,s=None):
    if s is None: s={}
    a=apply_sub(s,a); b=apply_sub(s,b)
    if isinstance(a,TVar):
        if a.name!=b.name if isinstance(b,TVar) else True:
            if occurs(a.name,b): raise TypeError(f"Infinite type {a} ~ {b}")
            s[a.name]=b
    elif isinstance(b,TVar): unify(b,a,s)
    elif isinstance(a,TFunc) and isinstance(b,TFunc):
        unify(a.arg,b.arg,s); unify(a.ret,b.ret,s)
    elif isinstance(a,TConst) and isinstance(b,TConst):
        if a.name!=b.name: raise TypeError(f"Cannot unify {a} and {b}")
    else: raise TypeError(f"Cannot unify {a} and {b}")
    return s
def infer(expr,env,s=None):
    if s is None: s={}
    if isinstance(expr,str):
        if expr.isdigit(): return TConst("Int"),s
        if expr in env: return apply_sub(s,env[expr]),s
        raise NameError(f"Undefined: {expr}")
    if isinstance(expr,tuple):
        if expr[0]=="lambda":
            tv=TVar(fresh()); new_env={**env,expr[1]:tv}
            bt,s=infer(expr[2],new_env,s)
            return TFunc(apply_sub(s,tv),bt),s
        if expr[0]=="let":
            vt,s=infer(expr[2],env,s)
            return infer(expr[3],{**env,expr[1]:vt},s)
        ft,s=infer(expr[0],env,s)
        at,s=infer(expr[1],env,s)
        rt=TVar(fresh())
        s=unify(ft,TFunc(at,rt),s)
        return apply_sub(s,rt),s
def main():
    global _n; _n=0
    env={"add":TFunc(TConst("Int"),TFunc(TConst("Int"),TConst("Int"))),
         "true":TConst("Bool"),"false":TConst("Bool"),
         "not":TFunc(TConst("Bool"),TConst("Bool"))}
    exprs=[
        ("42","42"),
        ("true","true"),
        (("lambda","x","x"),"λx.x"),
        (("lambda","x",("lambda","y","x")),"λx.λy.x"),
        ((("add","1"),"2"),"add 1 2"),
        (("not","true"),"not true"),
    ]
    for expr,desc in exprs:
        _n=0
        try:
            t,s=infer(expr,env)
            print(f"{desc} : {apply_sub(s,t)}")
        except Exception as e:
            print(f"{desc} : ERROR {e}")
if __name__=="__main__": main()
