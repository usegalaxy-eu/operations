# WIP: Migrating from NGINX to Traefik

## Middleware comparison


| NGINX                   | Traefik                       | Particularities           |
| ------------------------- | :------------------------------ | --------------------------- |
| gzip                    | compress                      |                           |
| client_body_buffer_size | Buffering/maxRequestBodyBytes |                           |
| proxy_http_version      | serversTransport/disableHTTP2 | not needed                |
| error_page              | Errors                        | must be served by service |
| proxy_pass              | Service                       |                           |
| upload_*                | N/A                           | NGINX Plugin              |
| add_header              | Headers (in general)          |                           |
| X-Accel-Redirect        | N/A                           |                           |
| proxy_cache             | HTTP Caching                  |                           |

## Services


| Location | proxy_pass    | headers |
| ---------- | --------------- | --------- |
| /        | http://galaxy |         |
|          |               |         |
