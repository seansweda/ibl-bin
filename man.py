#!/usr/bin/env python

import os
import re
from io import open

def help( filename ):
    comment = re.compile( "^# " )
    end = re.compile ( "^$" )

    try:
        with open( filename, 'r' ) as fp:
            for line in fp.readlines():
                c = comment.match(line)
                e = end.match(line)

                if e:
                    break

                if c:
                    print(line, end="")

    except PermissionError:
        print("Permission denied")
        sys.exit(1)
    except OSError as err:
        print(str(err))
        sys.exit(1)

