FROM nginx:alpine

# Copy the HTML file as a template
COPY index.html /usr/share/nginx/html/index.html.template

# Default backend URL (can be overridden at runtime)
ENV BACKEND_URL="http://localhost:8080"

# Expose port 80
EXPOSE 80

# Use envsubst to replace only $BACKEND_URL (ignoring JS template literals like ${username})
# Then start nginx
CMD envsubst '$BACKEND_URL' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'
