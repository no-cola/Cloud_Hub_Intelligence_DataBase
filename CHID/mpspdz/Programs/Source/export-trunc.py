@export
def trunc_pr(x):
    print_ln('x=%s', x.reveal())
    res = x.round(32, 2)
    print_ln('res=%s', res.reveal())
    return res

trunc_pr(sint(0, size=1000))
