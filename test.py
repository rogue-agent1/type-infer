from type_infer import infer, prune, Int, Bool, Arrow
env = {"add": Arrow(Int, Arrow(Int, Int))}
t = prune(infer(("apply", ("apply", "add", 1), 2), env))
assert t.name == "Int"
t2 = prune(infer(("lambda", "x", "x")))
assert "->" in str(t2)
t3 = prune(infer(True))
assert t3.name == "Bool"
print("Type inference tests passed")