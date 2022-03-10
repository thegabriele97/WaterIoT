.PHONY: genreq

genreq:
	@for a in $$(ls); do \
        if [ -d $$a ]; then \
            if [ -f $$a/Makefile ]; then\
                $(MAKE) -C $$a genreq; \
            fi \
        fi; \
    done;