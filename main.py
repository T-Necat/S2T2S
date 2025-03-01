from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import os
from pydub import AudioSegment
import gc
import time
from datetime import datetime
import subprocess

start_time = time.time()

base_dir = "Your base voice path"
input_m4a_file = os.path.join(base_dir, "Voice file name")

base_filename = os.path.splitext(os.path.basename(input_m4a_file))[0]
output_wav_file = os.path.join(base_dir, f"{base_filename}.wav")

if not torch.cuda.is_available():
    print("WARNING: CUDA not found! Process will continue on CPU.")
    device = "cpu"
else:
    device = "cuda"
    torch.backends.cudnn.benchmark = True  
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"Total GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

try:
    audio = AudioSegment.from_file(input_m4a_file, format="m4a")
    audio.export(output_wav_file, format="wav")
    print(f"Converted file: {output_wav_file}")
except Exception as e:
    print("Error: FFmpeg might be missing or file is corrupted ->", e)
    exit()

whisper_model = "openai/whisper-large-v3-turbo"
print(f"Loading Whisper model: {whisper_model}")

whisper = pipeline(
    "automatic-speech-recognition", 
    model=whisper_model, 
    device=device,
    torch_dtype=torch.float16  
)

audio = AudioSegment.from_wav(output_wav_file)
segment_duration = 300 * 1000  
segments = [audio[i:i+segment_duration] for i in range(0, len(audio), segment_duration)]
print(f"Audio file split into {len(segments)} parts, transcription starting...")
full_transcription = ""

for idx, segment in enumerate(segments):
    print(f"Processing segment {idx+1}/{len(segments)}...")
    segment_path = os.path.join(base_dir, f"segment_{idx}.wav")
    segment.export(segment_path, format="wav")
    
    if device == "cuda":
        torch.cuda.empty_cache()
    
    try:
        transcription = whisper(
            segment_path, 
            return_timestamps=True,
            batch_size=16,    
            chunk_length_s=30 
        )["text"]
        full_transcription += transcription + " "
    except Exception as e:
        print(f"Segment {idx+1} transcription error: {e}")
        continue
    os.remove(segment_path)

transcription_output_file = os.path.join(base_dir, f"{base_filename}_transcript.txt")
with open(transcription_output_file, "w", encoding="utf-8") as f:
    f.write(full_transcription)
print(f"Transcription successfully saved: {transcription_output_file}")

del whisper
if device == "cuda":
    torch.cuda.empty_cache()
gc.collect()


chunk_size = 3000
input_chunks = [full_transcription[i:i+chunk_size] for i in range(0, len(full_transcription), chunk_size)]
print(f"Transcription split into {len(input_chunks)} parts, summarizing...")

summary_parts = []

for i, chunk in enumerate(input_chunks):
    print(f"Processing text chunk {i+1}/{len(input_chunks)}...")
    
    prompt = f"""Summarize the following lecture transcription. Please:
- Extract the main notes from the lecture,
- Emphasize important technical topics,
- Indicate relevant connections and relationships between concepts.

Text:
{chunk}

Summary:"""
    
    try:
        output = subprocess.check_output(
            ["ollama", "run", "deepseek-r1:32b"],
            input=prompt,
            encoding="utf-8"
        )
        print("Output from model:")
        print(output)
        summary_parts.append(output.strip())
    except subprocess.CalledProcessError as e:
        print("Command error:", e)
    except Exception as e:
        print("Error occurred:", e)


final_output = "\n\n".join(summary_parts)

timestamp = datetime.now().strftime("%H_%M_%d_%m_%Y")
result_dir = os.path.join(base_dir, "result_text")
os.makedirs(result_dir, exist_ok=True)

transcription_result_file = os.path.join(result_dir, f"transcription_{timestamp}.txt")
summary_result_file = os.path.join(result_dir, f"summary_{timestamp}.txt")

with open(transcription_result_file, "w", encoding="utf-8") as f:
    f.write(full_transcription)

with open(summary_result_file, "w", encoding="utf-8") as f:
    f.write(final_output)

print(f"\nTranscription result saved: {transcription_result_file}")
print(f"Summary result saved: {summary_result_file}")

end_time = time.time()
execution_time = end_time - start_time
print(f"\nTotal processing time: {execution_time:.2f} seconds")
print(f"\nGenerated Summary (first 500 characters):\n{final_output[:500]}...")
print(f"\nGenerated Transcription (first 500 characters):\n{full_transcription[:500]}...")