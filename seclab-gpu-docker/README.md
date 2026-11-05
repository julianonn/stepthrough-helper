# seclab-gpu-docker



Installs and runs Qwen2.5-VL-7B-Instruct on UW `seclab-gpu1` (GPUs 0 and 1 of its 4× RTX 2080 Ti), so `pipeline/classify.py` can call it through an SSH tunnel. 

If you do not have a user account on this specific GPU, this subdirectory has no relevance to you. *TODO* eventually, a more generic module for any local GPU.

## Install once

1. Connnect to CS department VPN.
2. Add to `~/.ssh/config` on your laptop, then `ssh-copy-id sgpu` (VPN on):
   ```
   Host sgpu
     HostName <seclab-gpu1 full hostname>
     User <user>
   ```
3. Check there's ~20 GB free for the weights: `ssh sgpu "df -h ~ && quota -s"`. If not, change `~/.cache/huggingface` in `docker-compose.yml` to a folder on a drive that has room.
4. Copy this folder and start the model. The first start downloads ~16 GB of weights to `~/.cache/huggingface` on `seclab-gpu1`:
   ```
   scp -r seclab-gpu-docker sgpu:
   ssh sgpu "cd seclab-gpu-docker && docker compose up -d"
   ```
5. Ready when this lists the model: `ssh sgpu curl -s localhost:8000/v1/models`

The model keeps running, including after reboots, and holds GPUs 0 and 1. Stop it: `ssh sgpu "cd seclab-gpu-docker && docker compose down"`.

## Every run

1. Connnect to CS department VPN.
2. Run and leave this open: `ssh -N -L 8000:localhost:8000 sgpu`
3. In `stepthrough-helper/` on your laptop: `../.venv/bin/python pipeline/run.py`
