#!/usr/bin/env python3

import argparse
import copy
import os
import shutil
import sys
import time
import traceback

from bs4 import BeautifulSoup
from http.server import test, SimpleHTTPRequestHandler

def ensure_parent(p):
    parent = os.path.dirname(p)
    if not os.path.exists(parent):
        os.mkdir(parent)

def is_webgen_attr(tag):
    return any(k.startswith("wg-") for k in tag.attrs.keys())

def genhtml(inpath, outpath, templates, inroot):
    print(f"= Processing {inpath}")
    with open(inpath) as fp:
        soup = BeautifulSoup(fp, "html.parser")
    for webgen in soup.find_all("webgen"):
        template_name = webgen.get("template")
        if template_name is None:
            rel = os.path.relpath(inpath, inroot)
            raise RuntimeError("{rel}: Unable to determine which template to use, please specify via `template` attribute")
        if template_name not in templates:
            rel = os.path.relpath(inpath, inroot)
            raise RuntimeError("{rel}: Unable to find template '{template_name}'!")
        args = webgen.attrs

        template_soup = copy.copy(templates[template_name])
        for wg_text in template_soup.find_all("wg-text"):
            name = wg_text.get("name")
            if name in args:
                wg_text.string += args[name]
                wg_text.unwrap()
            else:
                wg_text.decompose()

        for dynamic_elem in template_soup.find_all(is_webgen_attr):
            for key in [k for k in dynamic_elem.attrs.keys() if k.startswith("wg-")]:
                arg_name = dynamic_elem[key]
                del dynamic_elem[key]
                if arg_name in args:
                    attr_name = key[3:]
                    dynamic_elem[key[3:]] = args[arg_name]

        webgen.replace_with(template_soup)

    ensure_parent(outpath)
    with open(outpath, "w") as fp:
        fp.write(soup.prettify())
    print(f"    * Wrote {outpath}")

def load_template(template_path):
    with open(template_path) as fp:
        return BeautifulSoup(fp, "html.parser").contents[0]

def copyfile(src, dst, **kwargs):
    ensure_parent(dst)
    print(f"* Copying {src} -> {dst}")
    shutil.copyfile(src, dst, **kwargs)

def process_file(filepath, dest_filepath, templates, in_dir):
    if not os.path.exists(filepath):
        return
    if not filepath.endswith("html"):
        copyfile(filepath, dest_filepath)
    else:
        genhtml(filepath, dest_filepath, templates, in_dir)

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", default="site", help="Specify the directory containing the input files to be copied/processed into --out-dir")
    parser.add_argument("--out-dir", default="sitegen", help="Specify the output directory. All files from --in-dir will be copied/processed into this directory")
    parser.add_argument("--listen", default=False, action="store_true", help="If specified, stay alive & process files as they change")
    parser.add_argument("--clean", default=False, action="store_true", help="If specified, cleans the out directory before starting")
    parser.add_argument("--port", default=8000, type=int, help="Specify the port to listen to when --listen is specified")

    parsed_args = parser.parse_args()
    in_dir = os.path.abspath(parsed_args.in_dir)
    out_dir = os.path.abspath(parsed_args.out_dir)

    if parsed_args.clean:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir, ignore_errors=True)

    webgen_dir = os.path.join(in_dir, "webgen")
    templates = {
        os.path.splitext(template)[0]: load_template(os.path.join(webgen_dir, template))
        for template in os.listdir(webgen_dir)
    }

    for root, dirs, files in os.walk(in_dir):
        if root == in_dir:
            if "webgen" in dirs:
                dirs.remove("webgen")
        for file in files:
            filepath = os.path.join(root, file)
            rel_filepath = os.path.relpath(filepath, in_dir)
            dest_filepath = os.path.join(out_dir, rel_filepath)
            process_file(filepath, dest_filepath, templates, in_dir)

    if parsed_args.listen:
        from watchdog import events as wd_events
        from watchdog.observers.fsevents import FSEventsObserver as Observer

        class WebGenEventHandler(wd_events.FileSystemEventHandler):
            def __init__(self, in_dir, out_dir, templates):
                self.in_dir = in_dir
                self.webgen_dir = os.path.join(in_dir, "webgen")
                self.out_dir = out_dir
                self.templates = templates

            def dispatch(self, event):
                if event.is_directory:
                    return

                if os.path.commonpath([self.webgen_dir, event.src_path]) == self.webgen_dir:
                    return

                if isinstance(event, wd_events.FileSystemMovedEvent):
                    if os.path.commonpath([self.webgen_dir, event.dest_path]) == self.webgen_dir:
                        return

                try:
                    super().dispatch(event)
                except Exception:
                    traceback.print_exc()

            def on_created(self, event):
                #print(f"[Created] {event.src_path}")
                self.on_created_path(event.src_path)

            def on_deleted(self, event):
                #print(f"[Deleted] {event.src_path}")
                self.on_deleted_path(event.src_path)

            def on_modified(self, event):
                #print(f"[Modified] {event.src_path}")
                self.on_modified_path(event.src_path)

            def on_moved(self, event):
                #print(f"[Moved] {event.src_path} -> {event.dest_path}")
                self.on_deleted_path(event.src_path)
                self.on_created_path(event.dest_path)

            def on_created_path(self, path):
                self.on_modified_path(path)

            def on_deleted_path(self, path):
                rel = os.path.relpath(path, self.in_dir)
                out_path = os.path.join(self.out_dir, rel)
                if not os.path.exists(out_path):
                    return
                print(f"* Removing {out_path}")
                if os.path.isdir(out_path):
                    os.rmdir(out_path)
                else:
                    os.remove(out_path)

            def on_modified_path(self, path):
                if os.path.isdir(path):
                    return
                rel = os.path.relpath(path, self.in_dir)
                process_file(path, os.path.join(self.out_dir, rel), self.templates, self.in_dir)

        event_handler = WebGenEventHandler(in_dir, out_dir, templates)

        observer = Observer()
        observer.schedule(event_handler, in_dir, recursive=True)
        observer.start()
        try:
            os.chdir(out_dir)
            test(SimpleHTTPRequestHandler, port=parsed_args.port)
        finally:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    main(sys.argv[1:])
