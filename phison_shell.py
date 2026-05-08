import logging
import traceback
import argparse
import IPython
from phison_executor.phison_executor import PhisonExecutor


logger = logging.getLogger(__name__)

def parse_args():
    """PhisonExecutor argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('device', type=str, help='the path to the Phison NVMe device')

    return parser.parse_args()


def main(args):
    """PhisonExecutor entry point.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        pe = PhisonExecutor(args.device)
        IPython.embed(header="The Phison shell object can be accessed through 'pe'")
    except Exception:
        logging.critical(f"Error occured while creating PhisonExecutor: {traceback.format_exc()}")
        return 1

    return 0

if __name__ == "__main__":
    parsed_args = parse_args()
    main(parsed_args)
