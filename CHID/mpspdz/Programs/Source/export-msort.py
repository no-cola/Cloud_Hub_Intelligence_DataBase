@export
def sort(x, key_indices):
    print_ln('x=%s', x.reveal())
    print_ln('key_indices=%s', key_indices)
    res = x.sort(key_indices=key_indices)
    print_ln('res=%s', x.reveal())

sort(sint.Matrix(500, 2), regint(0, size=1))
