import sys

import klupu.db

def _main():
    klupu.db.init(sys.argv[1])

if __name__ == "__main__":
    _main()
