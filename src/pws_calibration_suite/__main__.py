from pws_calibration_suite.application.app import App
import logging
import sys


def configureLogger():
    logger = logging.getLogger("pws_calibration_suite")  # We get the root logger so that all loggers in pwspy will be handled.
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def main():
    directory = r'\\BackmanLabNAS\home\Year3\ITOPositionStability\AppTest'
    logger = configureLogger()
    logger.debug("Starting application.")
    app = App()
    app.exec()

    # logger.debug("Start ITO Analyzer")
    # loader = DateMeasurementLoader(directory, os.path.join(directory, '10_20_2020'))
    # anlzr = Analyzer(loader, useCached=True)
    # rvwr = Reviewer(loader)

    a = 1  # Debug Breakpoint


if __name__ == '__main__':
    main()
