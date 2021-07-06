ARG base_image=python:3.9-alpine@sha256:709505ac2ed5824430abb76db8cd24c45415aa1f267e133546977e0b18241d3e
FROM ${base_image} as base-image

WORKDIR /opt/resource

COPY requirements.txt /opt/resource

RUN pip install -r requirements.txt

COPY src/ /opt/resource/


