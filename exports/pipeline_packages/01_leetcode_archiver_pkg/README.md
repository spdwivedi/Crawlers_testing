# Standalone Pipeline Package: `01_leetcode_archiver`

Self-contained containerized production pipeline exported by Antigravity Exporter.

## Local Execution
```bash
pip install -r requirements.txt
python pipeline_runner.py --help
python pipeline_runner.py --target "sample_target"
```

## Docker Execution
```bash
docker build -t 01_leetcode_archiver:latest .
docker run --rm 01_leetcode_archiver:latest --mock
```
