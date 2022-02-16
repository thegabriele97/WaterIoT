.PHONY: genreq

genreq:
	@for a in $$(ls); do \
        if [ -d $$a ]; then \
            $(MAKE) -C $$a genreq; \
        fi; \
    done;