@export
def b2a(res, x):
    print_ln('x=%s', x.reveal())
    res[:] = sint(x[:])
    print_ln('res=%s', x.reveal())

b2a(sint.Array(size=10), sbitvec.get_type(16).Array(10))
