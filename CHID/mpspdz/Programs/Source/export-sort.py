@export
def sort(x):
    print_ln('x=%s', x.reveal())
    res = x.sort()
    print_ln('res=%s', x.reveal())

sort(sint.Array(1000))
