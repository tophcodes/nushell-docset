.PHONY: help build release clean test dev

help:
	@echo "Nushell Docset Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  help      - Show this help message"
	@echo "  build     - Build the docset only"
	@echo "  release   - Build production release with XML feed"
	@echo "  clean     - Remove build artifacts"
	@echo "  test      - Test build in ./test-output"
	@echo "  dev       - Enter development shell"

build:
	nix build

release:
	nix develop --command python build_release.py \
		--output releases \
		--base-url "https://github.com/YOUR_USERNAME/nushell-docset/releases/latest/download"

release-github:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable required. Usage: make release-github REPO=owner/repo"; \
		exit 1; \
	fi
	nix develop --command python build_release.py \
		--output releases \
		--github-release \
		--repo "$(REPO)"

clean:
	rm -rf result result-* releases/ test-output/ dist/ build/ *.egg-info

test:
	nix develop --command python generate_docset.py --output test-output

dev:
	nix develop
