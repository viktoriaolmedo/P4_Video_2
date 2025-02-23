from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from typing import List, Optional
import numpy as np
from typing import Union
import pywt
import subprocess
import os
import cv2
from tempfile import NamedTemporaryFile
import shutil
import tempfile
import uuid
import shutil
import zipfile
from fastapi.responses import FileResponse
import secrets


# Path Inés
#OUTPUT_DIR = "/Users/isall/Downloads/ffmpeg_outputs_ex_2"
#if not os.path.exists(OUTPUT_DIR):
    #os.makedirs(OUTPUT_DIR)
    
# Path Viktoria
OUTPUT_DIR = "/Users/viktoriaolmedo/Desktop/P4_Vid3o/media"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    
# Path Maria
#OUTPUT_DIR = "/Users/mariasanninomezquita/Downloads/ffmpeg_outputs"
#if not os.path.exists(OUTPUT_DIR):
#    os.makedirs(OUTPUT_DIR)


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}


def apply_drm(dash_output_dir: str, hls_output_dir: str, encryption_key: str):
    # encrypt MPEG-DASH
    dash_files = [f for f in os.listdir(dash_output_dir) if f.endswith('.m4s') or f.endswith('.mpd')]
    for file in dash_files:
        input_file = os.path.join(dash_output_dir, file)
        subprocess.run(
            ["mp4encrypt", "--key", f"1:{encryption_key}", input_file],
            check=True
        )

    # encrypt HLS 
    hls_files = [f for f in os.listdir(hls_output_dir) if f.endswith('.ts') or f.endswith('.m3u8')]
    for file in hls_files:
        input_file = os.path.join(hls_output_dir, file)
        subprocess.run(
            ["mp4encrypt", "--key", f"1:{encryption_key}", input_file],
            check=True
        )
        


@app.post("/cut_and_package_video")
async def cut_and_package_video(file: UploadFile = File(...)):
    try:
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "input.mp4")
        cut_video_path = os.path.join(temp_dir, "cut_video.mp4")
        hls_output_dir = os.path.join(temp_dir, "hls_output")
        dash_output_dir = os.path.join(temp_dir, "dash_output")
        zip_output_path = os.path.join(OUTPUT_DIR, "packaged_video.zip")

        os.makedirs(hls_output_dir, exist_ok=True)
        os.makedirs(dash_output_dir, exist_ok=True)

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # trim video to 1 min
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-t", "60", "-c", "copy", cut_video_path],
            check=True
        )

        #HLS 
        subprocess.run(
            [
                "ffmpeg",
                "-i", cut_video_path,
                "-c:v", "libx264",
                "-b:v", "2000k",
                "-c:a", "aac",
                "-b:a", "128k",
                "-hls_time", "10",
                "-hls_playlist_type", "vod",
                "-f", "hls",
                os.path.join(hls_output_dir, "output.m3u8"),
            ],
            check=True
        )

        #MPEG-DASH
        subprocess.run(
            [
                "ffmpeg",
                "-i", cut_video_path,
                "-c:v", "libvpx-vp9",
                "-b:v", "2000k",
                "-c:a", "aac",
                "-b:a", "128k",
                "-f", "dash",
                os.path.join(dash_output_dir, "output.mpd"),
            ],
            check=True
        )

        # DRM 
        encryption_key = 'e7d4dbec4bcb4b345f8ccaf9ef430f74'  # DRM encryption key
        try:
            apply_drm(dash_output_dir, hls_output_dir, encryption_key)
        except Exception as drm_error:
            print(f"DRM application failed: {drm_error}")

        # zip files
        with zipfile.ZipFile(zip_output_path, "w") as zipf:
            for folder, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(folder, file)
                    zipf.write(file_path, os.path.relpath(file_path, temp_dir))

        return FileResponse(zip_output_path, media_type="application/zip", filename="packaged_video.zip")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing video: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



