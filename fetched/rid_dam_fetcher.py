"""Backward compatibility shim for pipelines.rid_dam_fetcher."""

from pipelines.rid_dam_fetcher import *
from pipelines.rid_dam_fetcher import main

if __name__ == "__main__":
    main()
