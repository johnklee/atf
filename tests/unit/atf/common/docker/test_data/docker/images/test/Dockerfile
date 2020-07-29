#
# Testing image
#
FROM johnklee/centos7_flask:latest
ENV PATH=/opt/rh/rh-python36/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV X_SCLS=rh-python36
WORKDIR /app
USER root
EXPOSE 5000
COPY ./index.py ./
CMD ["python3", "index.py"]
