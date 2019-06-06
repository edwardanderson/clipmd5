# Extract a clip with FFmpeg and determine if it maintains frameMD5 fixity with its source

# Use:
#    $ clipmd5 /path/to/source.mkv --start 00:01:15 --end 00:03:00 --output clip.mkv
#    $ clipmd5 source.mkv --start 00:05:00 --end 25 --output clip.mkv --ffmpeg -an


import sys
import argparse
import subprocess
from tqdm import tqdm
from colorama import init, Style, Back


def framemd5(cmd, progress_bar=True):
    ''' Generate a manifest of MD5 checksums: a list per stream '''

    # Append framemd5 arguments to given command
    cmd.extend(['-loglevel', 'quiet', '-hide_banner', '-f', 'framemd5', '-'])

    # Excute process
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)

    md5s = {}

    # Parse standard out
    for i in tqdm(p.stdout, desc='FrameMD5', leave=False, disable=not progress_bar):
        line = i.strip('\r\n')
        data = [i for i in line.split(' ') if i]
        if data[0].startswith('#'):
            continue

        stream_id = data[0]
        md5 = data[-1]
        if stream_id in md5s:
            md5s[stream_id].append(md5)
        else:
            md5s[stream_id] = [md5]

    return md5s


def segment(cmd, progress_bar=True):
    ''' Trim a new file from the given source '''

    # Define progress bar
    pbar = tqdm(desc='Segment', unit='f', leave=False, disable=not progress_bar)

    # Execute process
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)

    # Parse FFmpeg stderr for progress and update progress bar
    frames_seen = 0
    while True:
        line = p.stderr.readline().rstrip('\r\n')
        status = p.poll()
        if line == '' and status is not None:
            # Finished
            break

        # Update progress
        if line.startswith('frame'):
            ffmpeg_stderr = line.replace('=', ' ').replace('  ', ' ')
            frame = int(ffmpeg_stderr.split()[1])
            diff = frame - frames_seen
            pbar.update(int(diff))
            frames_seen = frame

    pbar.close()

    if status == 0:
        return True


def compare_checksum_manifests(src, dst):
    ''' Check each stream's checksums '''

    checks = []

    for stream in dst:
        src_str = ','.join(src[stream])

        hashes = dst[stream]
        dst_str = ','.join(hashes)
        checks.append(dst_str in src_str)

    return all(checks)


def error_message(message):
    ''' Print and close '''

    sys.stderr.write(message + Style.RESET_ALL + '\n')
    sys.stderr.flush()
    sys.exit(1)


def create_clip(cmd):
    ''' Trim a clip from source given timecodes (hh:mm:ss) and compare its framemd5 with source '''

    # Generate framemd5s for source
    src_md5 = framemd5(cmd[:-1])

    # Create segment
    segment(cmd)

    # Remove in/out args from given command
    for i in ['-ss', '-to', '-t']:
        if i in cmd:
            pos = cmd.index(i)
            cmd.pop(pos+1)
            cmd.pop(pos)

    # Replace given input path with recent output
    pos = cmd.index('-i') + 1
    cmd[pos] = cmd[-1]

    # Generate framemd5s for destination
    dst_md5 = framemd5(cmd[:-1])

    # Compare md5 manifests
    result = compare_checksum_manifests(src_md5, dst_md5)
    return result


def clipmd5(in_file, start, out_file, end=None, ffmpeg=None):
    ''' Wrapper '''

    cmd = construct_command(in_file, start, out_file, end, ffmpeg)
    status = create_clip(cmd)
    return status


def construct_command(in_file, start, out_file, end=None, ffmpeg=None):
    ''' Assemble an FFmpeg command as a list of parameters '''

    cmd = ['ffmpeg', '-i', in_file, '-ss', start]

    # Pass end str as [--to] or int as [-t]
    if end:
        try:
            int(end)
            out = '-t'
        except ValueError:
            out = '-to'

        cmd.extend([out, end])

    # Append any FFmpeg parameters; put output path at the end
    if ffmpeg:
        cmd.extend(ffmpeg + [out_file])
    else:
        cmd.append(outfile)

    return cmd


def main():
    ''' Create a new clip, and confirm that its framemd5 manifest matches the source '''

    # Colorama
    init()

    parser = argparse.ArgumentParser(description='Extract a clip with framemd5 fixity')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'), help='Input file')
    parser.add_argument('--start', type=str, required=True, help='Extract from [hh:mm:ss]')
    parser.add_argument('--end', help='Extract until position given as [hh:mm:ss] or [s]')
    parser.add_argument('--output', type=str, required=True, help='Create clip with filename')

    # Permit any FFmpeg arguments
    parser.add_argument('--ffmpeg',
                        nargs=argparse.REMAINDER,
                        default=['-map', '0',     # All streams
                                 '-c', 'copy',    # Stream copy, no transcode
                                 '-n'],           # Do not overwrite output
                        help='Any additional FFmpeg parameters')

    args = parser.parse_args()

    status = clipmd5(args.file.name, args.start, args.output, args.end, args.ffmpeg)

    if not status:
        error_message(Back.RED + '{}\tNO fixity'.format(args.output))
    else:
        print('{}\tFixity OK'.format(args.output))


if __name__ == '__main__':
    main()
