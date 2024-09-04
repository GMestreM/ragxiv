"""Configuration for the different steps of RAG flow"""

import yaml

# arXiv categories relevant for this project.
# Quantitative finance categories are listed in https://arxiv.org/archive/q-fin
ARXIV_FIELDS = [
    "q-fin.CP",  # Computational Finance
    "q-fin.EC",  # Economics
    "q-fin.GN",  # General Finance
    "q-fin.MF",  # Mathematical Finance
    "q-fin.PM",  # Portfolio Management
    "q-fin.PR",  # Pricing of Securities
    "q-fin.RM",  # Risk Management
    "q-fin.ST",  # Statistical Finance
    "q-fin.TR",  # Trading and Market Microstructure
]


def get_config() -> dict | None:
    config_paths = ["config.yaml", "./config.yaml", "../config.yaml"]

    for path in config_paths:
        config = load_config(path=path)
        if config:
            return config
    return None


def load_config(path: str) -> dict | None:
    try:
        with open(path, "r") as file:
            config = yaml.safe_load(file)
            return config
    except Exception as e:
        print(e)
        return None
