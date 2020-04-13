FROM pandoc/core

ADD . /src

RUN apk --no-cache add python3 python3-dev zeromq-dev g++ && cd /src && pip3 install . && apk del g++ python3-dev zeromq-dev

ENTRYPOINT ["pandoc", "-t", "plain", "--filter", "pandoc-tangle"]
