"""Entry point for Transcriptor."""

import argparse
import logging

from transcriptor.app import App


def main():
    parser = argparse.ArgumentParser(description="Transcriptor — voice-to-text for Linux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=level,
    )

    app = App()
    app.run()


if __name__ == "__main__":
    main()
