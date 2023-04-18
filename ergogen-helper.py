#!/usr/bin/env python3

import argparse
import os
import pcbnew
import shutil

from pathlib import Path


class ErgogenHelperException(Exception):
    pass


def get_traces(pcb):
    try:
        traces = pcb.GetTracks()
    except Exception as e:
        err = f'ERROR: Could not get traces: {e}'
        raise ErgogenHelperException(err) from e

    return traces


def copy_traces(src_pcb, dst_pcb):
    traces = get_traces(src_pcb)

    for trace in traces:
        try:
            dst_pcb.Add(trace)
        except Exception as e:
            err = f'Could not copy trace: {e}'
            raise ErgogenHelperException(err) from e


def save_pcb(pcb, should_backup, backup_name):
    pcb_path = pcb.GetFileName()
    pcb_path = Path(pcb_path)

    if should_backup is True and os.path.exists(pcb_path):
        backup_path = pcb_path.with_stem(f'{pcb_path.stem}_{backup_name}')
        try:
            shutil.copy(str(pcb_path), str(backup_path))
        except Exception as e:
            err = f'Could not backup pcb to {backup_path}: {e}'
            raise ErgogenHelperException(err) from e

    try:
        pcb.Save(pcb_path)
    except Exception as e:
        err = f'Could not save pcb to {pcb_path}: {e}'
        raise ErgogenHelperException(err) from e


def main():
    parser = argparse.ArgumentParser(
        description='Copies elements from one kicad file to another.'
    )
    parser.add_argument(
        'src_pcb_path',
        help='The source PCB file path.'
    )
    parser.add_argument(
        'dst_pcb_path',
        help='The destination PCB file path.'
    )
    parser.add_argument(
        '-n', '--backup-name',
        default="orig",
        help=(
            'String to append to the filename of the backup '
            '(default: %(default)s)'
        )
    )
    parser.add_argument(
        '-b', '--no-backup',
        default=False,
        action='store_true',
        help='Skip backup of PCB (default: %(default)s)'
    )

    args = parser.parse_args()

    try:
        src_pcb = pcbnew.LoadBoard(args.src_pcb_path)
        dst_pcb = pcbnew.LoadBoard(args.dst_pcb_path)

        copy_traces(src_pcb, dst_pcb)
        save_pcb(dst_pcb, not args.no_backup, args.backup_name)
    except ErgogenHelperException as e:
        print(f'ERROR: {e}')
        exit(-1)


if __name__ == '__main__':
    main()
