#!/usr/bin/env python3
"""Upload a local file to Kie.ai temp hosting and print its public URL.

Usage: python3 upload.py <file>
Used once per run to host the style reference image, so later gen_image.py
calls can pass --style-url instead of re-uploading every time.
"""
import json
import sys

from dotenv import load_dotenv

import kie_common


def main():
    load_dotenv()
    if len(sys.argv) != 2:
        sys.exit("usage: upload.py <file>")
    url = kie_common.upload_file(sys.argv[1])
    print(json.dumps({"url": url}))


if __name__ == "__main__":
    main()
