#!/usr/bin/env python3
import json
import os
import glob
import base64
import re


def merge_json_files(file_list, output_file):
    merged = []
    for file_path in file_list:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged.extend(data)
                else:
                    merged.append(data)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"已更新 {output_file} ({len(merged)} 条)")


def get_json_files(folder_path):
    return sorted(glob.glob(os.path.join(folder_path, "*.json")))


def extract_host(url, header=""):
    if url and url.startswith("data:"):
        match = re.search(r"base64,([A-Za-z0-9+/=]+)", url)
        if match:
            try:
                decoded = base64.b64decode(match.group(1)).decode()
                if decoded.startswith("http"):
                    return decoded
            except Exception:
                pass
    if url and url.startswith("http") and not url.startswith("http@js"):
        return url
    if header:
        match = re.search(r"https?://[^\s\"'`]+", header)
        if match:
            return match.group(0)
    return ""


def extract_version(comment):
    if not comment:
        return ""
    match = re.search(r"(v[\d.]+\s*-\s*\d{4}\.\d{1,2}\.\d{1,2})", comment)
    return match.group(1) if match else comment.split("\n")[0].strip()


def generate_lb_file(dy_files, output_file, source_type):
    lb = []
    for file_path in dy_files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if source_type == "dy":
                name = item.get("sourceName", "")
                url = item.get("sourceUrl", "")
                comment = item.get("sourceComment", "")
                header = item.get("header", "")
            else:
                name = item.get("bookSourceName", "")
                url = item.get("bookSourceUrl", "")
                comment = item.get("bookSourceComment", "")
                header = ""
            rel_path = os.path.relpath(file_path, os.path.dirname(output_file)).replace("\\", "/")
            lb.append({
                "name": name,
                "host": extract_host(url, header),
                "time": extract_version(comment),
                "url": rel_path
            })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(lb, f, ensure_ascii=False, indent=2)
    print(f"已更新 {output_file} ({len(lb)} 条)")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # dy.json: fy.json + 订阅文件夹
    dy_files = [os.path.join(base_dir, "fy.json")] + get_json_files(os.path.join(base_dir, "订阅"))
    merge_json_files(dy_files, os.path.join(base_dir, "dy.json"))
    generate_lb_file(dy_files, os.path.join(base_dir, "dylb.json"), "dy")

    # sy.json: 书源文件夹
    sy_files = get_json_files(os.path.join(base_dir, "书源"))
    merge_json_files(sy_files, os.path.join(base_dir, "sy.json"))
    generate_lb_file(sy_files, os.path.join(base_dir, "sylb.json"), "sy")
