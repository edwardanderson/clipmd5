# clipmd5

*DISCLAIMER: this is work in progress; it might not work expectedly*

This is a prototype utility for extracting time-region segments from video files with FFmpeg and ensuring `framemd5` fixity.

It's essentially a wrapper peforming four actions:

1. Fetch framemd5 manifest for source
  `ffmepg -i [input] -loglevel quiet -hide_banner -f framemd5`

2. Stream copy from source to destination according to in/out times
  `ffmpeg -i [input] -ss [t-in] -to [t-out] -map 0 -c copy -n`

3. Fetch framemd5 manifest for destination

4. Compare checksums of all streams, determining that all of destination is contained in source.
  > Note that streams are exepected in the same positions in both source and destination (currently)


## Use

```bash
python clipmd5.py input.mkv --start 00:25:15 --end 00:30:45 --output clip.mkv
```

`--start` and `--end` are required parameters; `--start` is always passed to FFmepg as an _output parameter_. See [-ss position (input/output)](https://ffmpeg.org/ffmpeg.html).

Segmentation time points are expected as `hh:mm:ss`; the end-point is handled by FFmpeg with `-to`, but an integer can be passed to `--end` instead, forcing `-t` behaviour (see FFmpeg documentation).

Additional FFmpeg paramenters can be set by using `--ffmpeg` at the end of the command, eg:

```bash
# Extract 60s of content without audio starting from the 30s point
python clipmd5.py i.mkv --start 00:00:30 --end 60 --output o.mkv --ffmpeg -an
```

## Module

The utility can be imported into other Python projects. The `clipmd5()` function returns `True` if a fixty-ensured subclip was created successfully. 

```python
import clipmd5

input = '/path/to/i.mkv'
in_ = '00:00:30'
out = '00:00:45'
additional_args = ['-an']


fixity = clipmd5.clipmd5(input, in_, 'output.mkv', out, ffmpeg=additional_args)
```


## Install

While still a prototype, simply clone this repository and install the requirements.

```bash
pip install tqdm colorama
```

## Future

I really only have a single use case for this utility at the moment: ensuring that all streams are copied integrally when extracting a clip. Please do contribute your own use cases or suggestions for behaviour or improvement.
