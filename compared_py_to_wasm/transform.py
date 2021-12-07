# transform.py

#

from .model import *

def transform(node):
    # Return the node back (unmodified) or a new node in its place
    return node

# Main function (for testing)
def main(filename):
    from .parse import parse_file
    model = parse_file(filename)
    model = transform(model)
    print(model)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -m wabbit.transform filename")
    main(sys.argv[1])
