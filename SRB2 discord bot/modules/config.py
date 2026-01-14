
import sys
import json
from pathlib import Path

class BotConfig():
    token: str = None
    srb2_path: Path = None
    channel_ids: list = None
    log_channel_ids: list = None

    def __init__(self, config_path: Path):
        if not config_path.exists():
            print("Generating config file.")
            config_path.touch()
            with open(config_path, "w", encoding="utf-8") as cfg:
                cfg.write(json.dumps({
                    "token": "1234567890",
                    "srb2_path": "~/.srb2",
                    "channel_ids": ["1234567890"],
                    "log_channel_ids": ["1234567890"]
                }, sort_keys=True, indent=4))
            sys.exit()

        with open(config_path) as cfg:
            cfg_read = cfg.read()

        config: dict = json.loads(cfg_read)
        self.token = config["token"]
        self.srb2_path = Path(config["srb2_path"]).expanduser()
        self.channel_ids = config["channel_ids"]
        self.log_channel_ids = config["log_channel_ids"]
