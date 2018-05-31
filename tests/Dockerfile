# For testing the static website content
#
# To build the image, run
# docker build -t angrychimp/code-license-org .
#
# To run a container, run
# docker run -d \
#   -v /repo-path/code-license/code-license-htdocs/:/var/www/html \
#   -v /repo-path/code-license/code-license/themes/:/var/www/themes \
#   -p 3001:80 angrychimp/code-license-org
#
# Then access the test site via a browser using http://127.0.0.1:3001
#

FROM debian:jessie

# Updating system
RUN apt-get update && apt-get upgrade -y

# Installation of nginx
RUN apt-get install nginx -y

# Add custom 404
RUN sed -i '/^\troot/a\\terror_page 404 = \/404.html;' /etc/nginx/sites-enabled/default
RUN sed -i '/^\tlocation/i\\tlocation \/themes\/ {\n\t\talias /var/www/themes/;\n\t}' /etc/nginx/sites-enabled/default

VOLUME /var/www/html
VOLUME /var/www/themes
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]