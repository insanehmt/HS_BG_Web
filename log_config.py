"""
設定 Hearthstone log.config，啟用必要的 log 輸出。
"""
import os

HS_PATH = r"D:\BZGame\Hearthstone"
LOG_CONFIG_PATH = os.path.join(HS_PATH, "log.config")

REQUIRED_CONFIG = """\
[Power]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=True

[Zone]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=True
"""


def setup_log_config():
    """確保 log.config 已正確設定。若已存在則合併必要區段。"""
    existing = {}

    if os.path.exists(LOG_CONFIG_PATH):
        current_section = None
        with open(LOG_CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    current_section = line
                    existing[current_section] = {}
                elif "=" in line and current_section:
                    key, _, val = line.partition("=")
                    existing[current_section][key.strip()] = val.strip()

    # 合併/覆寫必要的 Power 與 Zone 區段
    needed = {
        "[Power]": {
            "LogLevel": "1",
            "FilePrinting": "True",
            "ConsolePrinting": "False",
            "ScreenPrinting": "False",
            "Verbose": "True",
        },
        "[Zone]": {
            "LogLevel": "1",
            "FilePrinting": "True",
            "ConsolePrinting": "False",
            "ScreenPrinting": "False",
            "Verbose": "True",
        },
    }

    for section, values in needed.items():
        if section not in existing:
            existing[section] = {}
        existing[section].update(values)

    with open(LOG_CONFIG_PATH, "w", encoding="utf-8") as f:
        for section, values in existing.items():
            f.write(f"{section}\n")
            for k, v in values.items():
                f.write(f"{k}={v}\n")
            f.write("\n")

    print(f"[log_config] log.config 已設定：{LOG_CONFIG_PATH}")


if __name__ == "__main__":
    setup_log_config()
