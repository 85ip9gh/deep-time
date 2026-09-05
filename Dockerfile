# Built on the g7 node and imported straight into containerd, the same as the
# other apps-namespace tenants. There is no registry, so the Deployment pins
# image: deep-time:g7 with imagePullPolicy: IfNotPresent (see deploy/k8s).
FROM nginx:alpine

# The custom config listens on 8080 and keeps every writable path under /tmp so
# the container can run as a non-root uid with a read-only root filesystem.
COPY deploy/nginx.conf /etc/nginx/nginx.conf

# Only the static site ships. The build/ generator and its key never enter the
# image (see .dockerignore).
COPY public/ /usr/share/nginx/html/

EXPOSE 8080
