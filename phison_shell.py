import logging
import argparse
import IPython
from phison_executor.phison_executor import PhisonExecutor


logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('device', type=str, help='the path to the Phison NVMe device')

    return parser.parse_args()


def main(args):
    logging.basicConfig(level=logging.INFO)

    #try:
    pe = PhisonExecutor(args.device)
    IPython.embed(header="The Phison shell object can be accessed through 'pe'")
    #except Exception as e:
    #   logging.critical(f"Error occured while creating PhisonExecutor: {str(e)}")
    #    return 1


if __name__ == "__main__":
    args = parse_args()
    main(args)
