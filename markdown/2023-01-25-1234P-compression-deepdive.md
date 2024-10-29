---
title: compression algorithms
short: a deep dive into compression algorithms and how to notice them in hex
date: 2023-01-25 2:42 PM
updated: 2024-09-09 4:01 PM
---

One of the things that my programmer friends often ask me about is how I can tell what kind of compression algorithm is used by a file.
This is an interesting question, and I hope that this post will help you understand how I notice compression algorithms in hex.

I will not be going over the fundamentals of compression algorithms or go into detail about how they work.

The forum posts[^eyes] and reference docs that have taught me how to do this are referenced where appropriate.

I will explain some of the structure of how the compression algorithms are set up because I believe that understanding _what_ these values mean,
it will help you understand _why_ they are there and how to notice them when the configuration values are anything but the defaults.

All magic values are written as byte sequences (i.e. big endian)

[^eyes]: [https://zenhax.com/viewtopic.php?t=27](https://web.archive.org/web/20230109220055/https://zenhax.com/viewtopic.php?t=27) (archived)

[TOC]

## The Basics

The first thing you need to know is that compression algorithms are not magic.
In many cases compression algorithms have a sanity check (a "magic" number) that is used to verify and set up the decompressor.
In other cases parts of the data can be seen in the compressed data.

## The Dreaded Lempel-Ziv Algorithm (Lz*)

The Lempel-Ziv algorithm is a compression algorithm that is used in many compression formats.
It comes in a lot of flavors and figuring out which one is used can be difficult.

To figure out if a file might be compressed with an Lz algorithm, you should look for the following:

- The first byte is almost always `0F`, `1F`, `F0`, or `FF`
- The following bytes are seemingly uncompressed data.
- The first byte repeats itself frequently in the data, especially at the start of the file.

This is because LZ algorithms use a dictionary to store data that has been seen before,
and the first byte (the "block") is used to determine the length of the data to be copied from the dictionary.

I strongly suggest using comscan[^comscan] with quickbms[^bms] to test what compression algorithm is used by a file when you encounter this and LZ4 (see below) does not work.

[^comscan]: [https://zenhax.com/viewtopic.php?t=23](https://web.archive.org/web/20221125023314/https://zenhax.com/viewtopic.php?t=23) (archived)

[^bms]: [https://aluigi.altervista.org/quickbms.htm](https://aluigi.altervista.org/quickbms.htm)

### LZ4

LZ4[^lz4] is a common compression algorithm used especially in video games during the 2010s.

LZ4's block has the following format:

```c
struct lz4_block {
    uint8_t encode_count : 4;
    uint8_t literal_count : 4;
}
```

The `encode_count` is the number of bytes to copy from the decompressed stream, and the `literal_count` is the number of bytes to copy from the compressed data.
There is also a special case where either byte is `0F`, which means that the next bytes are added to the count (until the byte is no longer `FF`).
The minimal number of literals read is 4.

[^lz4]: [https://github.com/lz4/lz4/](https://github.com/lz4/lz4/)


### LZMA, and LZMA2

LZMA[^7z] has no hard defined header[^lzma], though it will often start with `5D` or `2C` followed by a 32-bit integer that is the size of the inline dictionary data (usually zero.)

LZMA2 likewise has no header, though it will often start with `18` followed by compressed data. Note that this byte is optional.

I have not yet seen a raw LZMA stream in the wild beyond 7z files, likely due to it's large overhead.

[^7z]: [https://7-zip.org/sdk.html](https://7-zip.org/sdk.html)
[^lzma]: [https://github.com/jljusten/LZMA-SDK/blob/20d713a28e5aee284f5671c7cf41ffa52db0215e/DOC/lzma-specification.txt](https://github.com/jljusten/LZMA-SDK/blob/20d713a28e5aee284f5671c7cf41ffa52db0215e/DOC/lzma-specification.txt)


## DEFLATE, Zlib, and GZip

DEFLATE[^zlib] is a compression algorithm that is used in many files, and you will most likely have already seen it if you do any amount of file analysis.

ZLib uses a DEFLATE block with a header, and ADLER32 as it's checksum algorithm.

[^zlib]: [https://github.com/madler/zlib](https://github.com/madler/zlib)

### ZLib

ZLib[^rfc1950] preprends a 2 byte header to the compressed block (usually deflate). This usually is `78 9C` or `78 DA`

The first byte is the compression method, and the second byte has some flags. The compression method is usually `8`, which is DEFLATE.

```c
struct zlib_header {
    uint8_t compression_method : 4;
    uint8_t compression_info : 4;
    uint8_t checksum : 5;
    uint8_t dict : 1;
    uint8_t level : 2;
}
```

The `compression_info` is the log base 2 of the window size (the size of the dictionary used by the compressor), and the `checksum` a the checksum of the header.
The `dict` flag is set if a dictionary is used, and the `level` is the compression level used by the compressor.

Knowing this, zlib header will always start with `78` if the compression method is DEFLATE.

[^rfc1950]: [https://tools.ietf.org/html/rfc1950](https://tools.ietf.org/html/rfc1950)

### DEFLATE

A "raw" DEFLATE[^rfc1951] stream is not very common, but it is still used in some places (especially in files produced by C# projects).

It usually starts with `C#` or `E#` but it's a bit more complicated than that.

The DEFLATE block has the following format:

```c
struct deflate_block {
    uint8_t final : 1;
    uint8_t type : 2;
}
```

The `final` flag is set if this is the last block in the stream, and the `type` is the type of block.

[^rfc1951]: [https://tools.ietf.org/html/rfc1951](https://tools.ietf.org/html/rfc1951)

### GZip

GZip[^rfc1952] is a ZLib stream with a well formed header.

GZip will always start with a magic number (`1F 8B`) as well as a compression method (`8` for DEFLATE).

The header has the following format:

```c
struct gzip_header {
    uint16_t magic;
    uint8_t compression_method;
    uint8_t flags;
    uint32_t timestamp;
    uint8_t xtra_flags;
    uint8_t os;
}
```

[^rfc1952]: [https://tools.ietf.org/html/rfc1952](https://tools.ietf.org/html/rfc1952)

## ZStandard

ZStandard[^zstd] (zstd) is a relatively new compression algorithm that is starting to be used in many places due to it's ability to have very high compression ratios with specialized dictionaries.

Fortunately, ZStandard has a magic number that is used to identify the file, this usually is `## B5 2F FD` with the unknown byte being the specific version.

The ZStandard header has the following format[^zstddoc]:

```c
struct zstd_header {
    uint32_t magic;
    uint8_t content_size_flag : 2;
    uint8_t single_segment_flag : 1;
    uint8_t unused : 1;
    uint8_t reserved : 1;
    uint8_t checksum_flag : 1;
    uint8_t dict_id_flag : 2;
}
```

[^zstd]: [https://github.com/facebook/zstd](https://github.com/facebook/zstd)
[^zstddoc]: [https://github.com/facebook/zstd/blob/3732a08f5b82ed87a744e65daa2f11f77dabe954/doc/zstd_compression_format.md](https://github.com/facebook/zstd/blob/3732a08f5b82ed87a744e65daa2f11f77dabe954/doc/zstd_compression_format.md)

### ZDictionary

ZStandard might use a dictionary[^zdict] to compress the data, and the dictionary is stored either as a separate file, or in the same file as the compressed data. In some cases it might be in the executable itself (very rare!)
Documentation on ZDict is sparse, however we know that the magic value is `37 A4 30 EC`

The ZDict header has the following format:

```c
struct zdict_header {
    uint32_t magic;
    uint32_t dict_id;
}
```

[^zdict]: [https://github.com/facebook/zstd/blob/3732a08f5b82ed87a744e65daa2f11f77dabe954/doc/zstd_compression_format.md#dictionary-format](https://github.com/facebook/zstd/blob/3732a08f5b82ed87a744e65daa2f11f77dabe954/doc/zstd_compression_format.md#dictionary-format)

## Oodle

Oodle[^oodle] is a proprietary compression format used in many games, and has a hardware encoder in the PS5.

Oodle will always start with `#C` if it is made with version 4 or higher. Version 4 Oodle files have the following format:

```c
struct oodle_block_header {
    uint8_t magic : 4;
    uint8_t version : 2;
    bool copy : 1;
    bool reset : 1;
    uint8_t compression_type : 7;
    bool has_checksum : 1;
}
```

Compression type will be between 0 and 13 as of Oodle Version 9 (oo2core_9), and the checksum used is a modified Jenkins algorithm.
From this we can deduce that the second byte will be between `00` and `0D`, or `80` and `8D`

Note that Oodle will still load version 3 and older files, which will start with `#0`, `#1`, `#2`, or `#3` and will  usually look like LZW or LZB.

[^oodle]: [http://www.radgametools.com/oodle.htm](http://www.radgametools.com/oodle.htm)

## Tile Streaming (dstorage)

Tile Streaming uses a system to decompress multiple blocks simultaneously[^dstorage].
The format supports various compression formats, but at the moment only GDeflate[^gdeflate] (a variation of DEFLATE) is recognized.
The header is easily tested, the first byte will be the compression type (`04` for GDeflate) followed by that byte XORed with 0xFF (`FB` for GDeflate.) Followed by the number of "tiles".

Data compressed with GDeflate Tile Streaming will start with `04 FB`.

This ends up being:

```c
struct tile_stream_header {
    uint8_t compressor_id;
    uint8_t magic;
    uint16_t num_tiles;
    uint32_t tile_size_idx : 2; // this is always 1
    uint32_t last_tile_size: 18;
    uint32_t reserved : 12;
};
```

[^dstorage]: [https://github.com/microsoft/DirectStorage/tree/56489d25900d916a9cc450f5efe9e62b01789030/GDeflate/GDeflate](https://github.com/microsoft/DirectStorage/tree/56489d25900d916a9cc450f5efe9e62b01789030/GDeflate/GDeflate)
[^gdeflate]: [https://github.com/NVIDIA/libdeflate](https://github.com/NVIDIA/libdeflate)

## DENSITY

Density[^density] is a compression algorithm that claims[^density-benchmarks] 2x decompression speed compared to LZ4.

It has a very predictable header that is easy to spot.

```c
struct density_header {
    uint8_t version_major;
    uint8_t version_minor;
    uint8_t version_revision;
    uint8_t compression_type;
    uint32_t reserved;
}
```

Density has 18 releases, of which only 3 are not marked as pre released (0.14.0, 0.14.1, 0.14.2). It has 3 compression types (1, 2, 3.)

We can reduce this to a set byte sequences `00 0E 02 01 00 00 00 00` with 02 being the revision version, and 01 being the compression type.

[^density]: [https://github.com/g1mv/density](https://github.com/g1mv/density)
[^density-benchmarks]: [https://github.com/g1mv/density?tab=readme-ov-file#benchmarks](https://github.com/g1mv/density?tab=readme-ov-file#benchmarks)

## Zip Signature Speedrun

Compression archives almost always have a signature at the start of the file.
I'm adding them here for completeness.

- ZIP Magic: `50 4B` (PK)
- BZip2 Magic: `42 5A 68` (BZh)
- 7Zip Magic: `37 7A BC AF 27 1C` (7z)
- Rar Magic: `52 61 72 21 1A 07` (Rar!)
- WIM Magic: `4D 53 57 49 4D 00 00 00` (MSWIM)
- Xz Magic: `FD 37 7A 58 5A 00` (7zXZ)
- Tar Magic: `75 73 74 61 72` (ustar) - usually found at the end of filelist

## Changelog

- *Update: 2024-09-09 - Added DENSITY info.*
- *Update: 2024-08-19 - Added Tile Streaming info.*
- *Update: 2023-07-11 - zenhax is offline, replaced links with archive.org links.*
