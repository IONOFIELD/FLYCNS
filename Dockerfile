# The reference environment, frozen: Python 3.12, a C/C++ compiler for Brian2's code generation, and
# every package pinned in requirements.lock. CI builds this image and runs the regression test in it.
#
# Toy check, no account:   docker build -t flycns . && docker run --rm flycns
# Real data: mount the checkout so results, data and git history are your own:
#   docker run --rm -it -v "$PWD":/flycns flycns ./fly
#   docker run --rm -v "$PWD":/flycns flycns python benchmarks/gf_escape.py 40
FROM python:3.12-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ git less curl \
 && rm -rf /var/lib/apt/lists/* \
 && git config --system --add safe.directory '*'

WORKDIR /flycns
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "tests/regression.py"]
