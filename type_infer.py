#!/usr/bin/env python3
"""type_infer - Hindley-Milner type inference engine."""
import argparse

class Type: pass
class TVar(Type):
    _id=0
    def __init__(self,name=None):
        if name is None: TVar._id+=1;name=f"t{TVar._id}"
        self.name=name
    def __repr__(self): return self.name
class TCon(Type):
    def __init__(self,name): self.name=name
    def __repr__(self): return self.name
class TFun(Type):
    def __init__(self,arg,ret): self.arg,self.ret=arg,ret
    def __repr__(self): return f"({self.arg} -> {self.ret})"

INT=TCon("Int");BOOL=TCon("Bool");STRING=TCon("String")

class Expr: pass
class EVar(Expr):
    def __init__(s,n): s.name=n
class EInt(Expr):
    def __init__(s,v): s.value=v
class EBool(Expr):
    def __init__(s,v): s.value=v
class EApp(Expr):
    def __init__(s,f,a): s.fn,s.arg=f,a
class ELam(Expr):
    def __init__(s,p,b): s.param,s.body=p,b
class ELet(Expr):
    def __init__(s,n,v,b): s.name,s.val,s.body=n,v,b
class EIf(Expr):
    def __init__(s,c,t,e): s.cond,s.then,s.else_=c,t,e

class Substitution:
    def __init__(self): self.mapping={}
    def apply(self, t):
        if isinstance(t,TVar):
            if t.name in self.mapping: return self.apply(self.mapping[t.name])
            return t
        if isinstance(t,TCon): return t
        if isinstance(t,TFun): return TFun(self.apply(t.arg),self.apply(t.ret))
        return t
    def unify(self, t1, t2):
        t1,t2=self.apply(t1),self.apply(t2)
        if isinstance(t1,TVar): self.mapping[t1.name]=t2;return
        if isinstance(t2,TVar): self.mapping[t2.name]=t1;return
        if isinstance(t1,TCon) and isinstance(t2,TCon) and t1.name==t2.name: return
        if isinstance(t1,TFun) and isinstance(t2,TFun):
            self.unify(t1.arg,t2.arg);self.unify(t1.ret,t2.ret);return
        raise TypeError(f"Cannot unify {t1} with {t2}")

def infer(expr, env, sub):
    if isinstance(expr,EInt): return INT
    if isinstance(expr,EBool): return BOOL
    if isinstance(expr,EVar):
        if expr.name not in env: raise NameError(f"Unbound: {expr.name}")
        return env[expr.name]
    if isinstance(expr,ELam):
        tv=TVar(); new_env={**env,expr.param:tv}
        ret=infer(expr.body,new_env,sub)
        return TFun(sub.apply(tv),ret)
    if isinstance(expr,EApp):
        ft=infer(expr.fn,env,sub);at=infer(expr.arg,env,sub);rv=TVar()
        sub.unify(ft,TFun(at,rv))
        return sub.apply(rv)
    if isinstance(expr,ELet):
        vt=infer(expr.val,env,sub);new_env={**env,expr.name:vt}
        return infer(expr.body,new_env,sub)
    if isinstance(expr,EIf):
        ct=infer(expr.cond,env,sub);sub.unify(ct,BOOL)
        tt=infer(expr.then,env,sub);et=infer(expr.else_,env,sub)
        sub.unify(tt,et);return sub.apply(tt)
    raise TypeError(f"Unknown expr: {expr}")

def main():
    p=argparse.ArgumentParser(description="HM type inference");args=p.parse_args()
    env={"add":TFun(INT,TFun(INT,INT)),"eq":TFun(INT,TFun(INT,BOOL)),"not":TFun(BOOL,BOOL)}
    tests=[
        ("42",EInt(42)),
        ("true",EBool(True)),
        ("\\x.x",ELam("x",EVar("x"))),
        ("\\x.\\y.x",ELam("x",ELam("y",EVar("x")))),
        ("add 1",EApp(EVar("add"),EInt(1))),
        ("let id=\\x.x in id 42",ELet("id",ELam("x",EVar("x")),EApp(EVar("id"),EInt(42)))),
        ("if true then 1 else 2",EIf(EBool(True),EInt(1),EInt(2))),
    ]
    print("Hindley-Milner Type Inference:\n")
    for desc,expr in tests:
        sub=Substitution()
        try:
            t=infer(expr,env,sub);t=sub.apply(t)
            print(f"  {desc:30s} : {t}")
        except (TypeError,NameError) as e: print(f"  {desc:30s} : ERROR: {e}")

if __name__=="__main__":
    main()
