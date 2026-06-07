#!/usr/bin/env python3
import os
import argparse

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

def is_image(fname):
    return fname.lower().endswith(IMG_EXTS)

def effective_classes(split_path):
    """
    Return (set_of_effective_class_names, dict_details)
    Effective class names use 'crop___disease' when nested, or the folder name if images are directly inside.
    details maps effective_name -> info tuple for debugging.
    """
    eff = set()
    details = {}
    if not os.path.isdir(split_path):
        return eff, details

    for entry in sorted(os.listdir(split_path)):
        ent_path = os.path.join(split_path, entry)
        if not os.path.isdir(ent_path):
            continue

        # images directly in top-level folder -> treat folder name as class
        direct_imgs = [f for f in os.listdir(ent_path) if is_image(f)]
        if direct_imgs:
            eff.add(entry)
            details[entry] = ("direct", len(direct_imgs))
            continue

        # otherwise look for subfolders containing images -> treat as crop___disease
        found_sub = False
        for sub in sorted(os.listdir(ent_path)):
            sub_path = os.path.join(ent_path, sub)
            if not os.path.isdir(sub_path):
                continue
            imgs = [f for f in os.listdir(sub_path) if is_image(f)]
            if imgs:
                cname = f"{entry}___{sub}"
                eff.add(cname)
                details[cname] = ("nested", entry, sub, len(imgs))
                found_sub = True

        if not found_sub:
            details[entry] = ("empty_or_other", 0)

    return eff, details

def main():
    p = argparse.ArgumentParser(description="Find mismatching classes across train/valid/test split folders")
    p.add_argument("--split_dir", "-s", default="PlantDiseasesDataset_Split", help="Base split folder")
    args = p.parse_args()

    base = args.split_dir
    splits = {}
    details = {}

    for split in ("train", "valid", "test"):
        path = os.path.join(base, split)
        eff, det = effective_classes(path)
        splits[split] = eff
        details[split] = det
        print(f"{split}: path='{path}' exists={os.path.isdir(path)} effective_classes={len(eff)}")

    # Summary counts
    t, v, te = splits["train"], splits["valid"], splits["test"]
    print(f"\nCounts -> train: {len(t)}, valid: {len(v)}, test: {len(te)}")

    only_in_train = sorted(t - (v | te))
    only_in_valid = sorted(v - (t | te))
    only_in_test  = sorted(te - (t | v))
    in_all = sorted(t & v & te)

    print("\nClasses only in train (not in valid/test):")
    for c in only_in_train:
        print("  ", c)
    if not only_in_train:
        print("  (none)")

    print("\nClasses only in valid (not in train/test):")
    for c in only_in_valid:
        print("  ", c)
    if not only_in_valid:
        print("  (none)")

    print("\nClasses only in test (not in train/valid):")
    for c in only_in_test:
        print("  ", c)
    if not only_in_test:
        print("  (none)")

    print(f"\nClasses present in all splits: {len(in_all)} (sample)")
    print("  ", ", ".join(in_all[:20]) + ("" if len(in_all) <= 20 else f", ... (+{len(in_all)-20} more)"))

    # Show top-level folders that are plain crop folders in each split (possible nested layout)
    print("\nTop-level folders without '___' (possible nested crops):")
    for split in ("train","valid","test"):
        path = os.path.join(base, split)
        plain = []
        if os.path.isdir(path):
            for entry in sorted(os.listdir(path)):
                ent_path = os.path.join(path, entry)
                if not os.path.isdir(ent_path):
                    continue
                if "___" not in entry:
                    # check if it contains subdirs with images
                    has_sub = any(
                        os.path.isdir(os.path.join(ent_path, s)) and
                        any(is_image(f) for f in os.listdir(os.path.join(ent_path, s)))
                        for s in os.listdir(ent_path)
                    )
                    if has_sub:
                        plain.append(entry)
        print(f"  {split}: {len(plain)} -> {plain[:20]}")

    print("\nIf you see crop folders (e.g., 'Strawberry') listed above, the split wasn't flattened to 'crop___disease'.")
    print("Fix options: (1) rebuild the split to produce top-level 'crop___disease' folders, (2) copy/move the missing class folder(s) so train/valid/test have identical class folders, or (3) force generators to use a canonical `classes=` list.")

if __name__ == "__main__":
    main()