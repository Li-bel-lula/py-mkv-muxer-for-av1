# py-mkv-muxer-for-av1
A Python script for replacing the video stream of non-AV1 (or non-HEVC) mkv video(s) with AV1 video stream in another file

Codec priority: AV1 > HEVC

AV1 mkv file + another non-AV1 mkv file = AV1 + Audios/Subs/Attachments... from the other
  
HEVC mkv file + another non-AV1/HEVC mkv file = HEVC + Audios/Subs/Attachments... from the other
  
Double click to run the script 
Python and MKVToolNix should be installed and added to PATH
Both files should be Matroska (.mkv) and in the same directory 
Output(s) are in the subdirectory .\output\
Using SxxExx as identifier in order to facilitate batching. (Such as S01E01, S01E02, etc. Make sure that the markers are in the file names)
