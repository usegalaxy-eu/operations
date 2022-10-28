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
| X-Accel-Redirect        | Froward-Request-Headers, CORS |                           |
| proxy_cache             | HTTP Caching                  |                           |


| General Headers | Image URL Headers |   |
| ----------------- | ------------------- | --- |
|                 |                   |   |
|                 |                   |   |

## Services


| Location                                                 | service                  | headers                                                              |
| ---------------------------------------------------------- | -------------------------- | ---------------------------------------------------------------------- |
| /                                                        | http://galaxy            | General                                                              |
| /api/libraries/datasets/download/                        | 302 https://usegalaxy.eu | General + Rate limit                                                 |
| ^/api/dataset_collections/([^/]+)/download/?$            | http://galaxy            | General + proxy_buffering off                                        |
| /_x_accel_redirect                                       | alias /                  | CORS Headers                                                         |
| /_upload                                                 |                          |                                                                      |
| /.well-known/<br />(not needed anymore - Traefik's acme) | http://127.0.0.1:8118    | X-Real-IP, X-Forwarded-For, X-Forwarded-Proto, Host, Request-Headers |
