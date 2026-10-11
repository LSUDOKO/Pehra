# Pehra build helpers
LAYER := layers/core/python
PY := 3.12

.PHONY: layer test lint pages build deploy clean

## Build the shared Lambda layer (arm64 wheels + our packages + Cedar policies + web templates)
layer:
	rm -rf $(LAYER) && mkdir -p $(LAYER)
	uv pip install --quiet --target $(LAYER) --python-platform aarch64-manylinux2014 \
		--python-version $(PY) --only-binary=:all: -r layers/core/requirements.txt
	cp -r heatcore ihcommon agent $(LAYER)/
	cp -r cedar $(LAYER)/ihcommon/cedar
	cp -r web $(LAYER)/ihcommon/web
	find $(LAYER) -name "__pycache__" -type d -prune -exec rm -rf {} +
	du -sh $(LAYER)

test:
	uv run pytest

lint:
	uv run ruff check .

pages:
	uv run python scripts/build_pages.py

build: layer
	sam build

deploy: build
	sam deploy

clean:
	rm -rf $(LAYER) .aws-sam
