#!/usr/bin/env python3
import argparse
import os
import re
import shutil

from source.py.utils import run

# Mapping of style names to weights
weight_map = {
    "Thin": "100",
    "ExtraLight": "200",
    "Light": "300",
    "Regular": "400",
    "Italic": "400",
    "SemiBold": "500",
    "Medium": "600",
    "Bold": "700",
    "ExtraBold": "800",
}


def format_filename(filename: str):
    match = re.match(r"MapleMono-(.*)\.(.*)$", filename)

    if not match:
        return None

    style = match.group(1)

    weight = weight_map[style.removesuffix("Italic") if style != "Italic" else "Italic"]
    suf = "normal" if "italic" in filename.lower() else "italic"

    new_filename = f"maple-mono-latin-{weight}-{suf}.{match.group(2)}"
    return new_filename


def rename_files(dir: str):
    for filename in os.listdir(dir):
        if not filename.endswith(".woff") and not filename.endswith(".woff2"):
            continue
        new_name = format_filename(filename)
        if new_name:
            os.rename(os.path.join(dir, filename), os.path.join(dir, new_name))
            print(f"Renamed: {filename} -> {new_name}")


def parse_tag(args):
    """
    Parse the tag from the command line arguments.
    Format: v7.0[-beta3]
    """
    tag = args.tag

    if not tag.startswith("v"):
        tag = f"v{tag}"

    if not re.match(r"^v\d+\.\d+$", tag):
        raise ValueError(f"Invalide tag: {tag}, format: v7.0")

    if args.beta:
        tag += "-" if args.beta.startswith("beta") else "-beta" + args.beta

    return tag

def update_build_script_version(tag):
    with open("build.py", "r", encoding="utf-8") as f:
        content = f.read()
        f.close()
    content = re.sub(r'FONT_VERSION = ".*"', f'FONT_VERSION = "{tag}"', content)
    with open("build.py", "w", encoding="utf-8") as f:
        f.write(content)
        f.close()


def git_commit(tag):
    run("git add woff2/var build.py")
    run(["git", "commit", "-m", f"Release {tag}"])
    run(f"git tag {tag}")
    print("Committed and tagged")

    run("git push origin")
    run(f"git push origin {tag}")
    print("Pushed to origin")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag",
        type=str,
        help="The tag to build the release for, format: 7.0 or v7.0",
    )
    parser.add_argument(
        "beta",
        nargs="?",
        type=str,
        help="Beta tag name, format: 3 or beta3",
    )
    args = parser.parse_args()
    tag = parse_tag(args)
    # prompt and wait for user input
    choose = input(f"Tag {tag}? (Y or n) ")
    if choose != "" and choose.lower() != "y":
        print("Aborted")
        return
    update_build_script_version(tag)

    target_dir = "fontsource"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    run("python build.py --ttf-only")
    run(f"ftcli converter ft2wf -f woff2 ./fonts/TTF -out {target_dir}")
    run(f"ftcli converter ft2wf -f woff ./fonts/TTF -out {target_dir}")
    run("ftcli converter ft2wf -f woff2 ./fonts/Variable -out woff2/var")
    rename_files(target_dir)

    git_commit(tag)


if __name__ == "__main__":
    main()
