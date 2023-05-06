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


def check_traces_equal(trace_1, trace_2):
    if (trace_1.GetStart() == trace_2.GetStart() and
       trace_1.GetEnd() == trace_2.GetEnd()):
        return True
    else:
        return False


def pcb_has_trace(pcb, lookup_trace):
    traces = pcb.GetTracks()

    for pcb_trace in traces:
        if check_traces_equal(lookup_trace, pcb_trace) is True:
            return True

    return False


def get_trace_descr(trace):
    start_x = trace.GetStart()[0] / 1000000
    start_y = trace.GetStart()[1] / 1000000
    end_x = trace.GetEnd()[0] / 1000000
    end_y = trace.GetEnd()[1] / 1000000
    length = trace.GetLength() / 1000000

    return f'({start_x}, {start_y}) -> ({end_x}, {end_y}) ({length}mm)'


def copy_traces(src_pcb, dst_pcb):
    traces = get_traces(src_pcb)

    skipped = 0
    for trace in traces:
        try:
            if pcb_has_trace(dst_pcb, trace) is True:
                print(
                    f'WARN: Skipping trace {get_trace_descr(trace)}: '
                    f'Already present in pcb.'
                )
                skipped += 1
                continue
            dst_pcb.Add(trace)
        except Exception as e:
            err = f'Could not copy trace: {e}'
            raise ErgogenHelperException(err) from e

    copied = len(traces) - skipped
    print(f'Copied {copied} / {len(traces)} traces.')


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


def cmd_copy_traces(args):
    try:
        src_pcb = pcbnew.LoadBoard(args.src_pcb_path)
        dst_pcb = pcbnew.LoadBoard(args.dst_pcb_path)

        copy_traces(src_pcb, dst_pcb)
        save_pcb(dst_pcb, not args.no_backup, args.backup_name)
    except ErgogenHelperException as e:
        print(f'ERROR: {e}')
        exit(-1)


def cmd_update_pcb(args):
    try:
        pcb = pcbnew.LoadBoard(args.pcb_path)
        save_pcb(pcb, not args.no_backup, args.backup_name)
    except ErgogenHelperException as e:
        print(f'ERROR: {e}')
        exit(-1)


def main():
    parser = argparse.ArgumentParser(
        description='Utility to make ergogen keyboard development easier.'
    )
    subparsers = parser.add_subparsers(title='command', dest='cmd')

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

    # Command: copy-traces
    copy_traces_parser = subparsers.add_parser(
        'copy-traces',
        help='Copy traces from source PCB to destination PCB'
    )
    copy_traces_parser.add_argument(
        'src_pcb_path',
        help='The source PCB file path.'
    )
    copy_traces_parser.add_argument(
        'dst_pcb_path',
        help='The destination PCB file path.'
    )
    copy_traces_parser.set_defaults(func=cmd_copy_traces)

    # Subcommand: update-pcb
    update_pcb = subparsers.add_parser(
        'update-pcb',
        help=(
            'Update KiCad pcb from v5 to v7 by opening it and saving it again.'
        )
    )
    update_pcb.add_argument(
        'pcb_path',
        help='The KiCad PCB file path.'
    )
    update_pcb.set_defaults(func=cmd_update_pcb)

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        return

    # Call the appropriate subcommand function based on the selected subcommand
    args.func(args)


if __name__ == '__main__':
    main()
