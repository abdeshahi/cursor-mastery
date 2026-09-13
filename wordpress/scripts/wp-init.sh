#!/bin/sh
set -eu

cd /var/www/html

MYCNF="/tmp/wp-client.cnf"
cat > "${MYCNF}" <<EOF
[client]
host=127.0.0.1
user=${WORDPRESS_DB_USER}
password=${WORDPRESS_DB_PASSWORD}
skip-ssl
EOF
chmod 600 "${MYCNF}"

echo "Waiting for WordPress files..."
until [ -f wp-config.php ] || [ -f wp-config-docker.php ]; do
  sleep 2
done

echo "Waiting for database..."
TRIES=0
until mariadb --defaults-extra-file="${MYCNF}" -e "SELECT 1" >/dev/null 2>&1; do
  TRIES=$((TRIES + 1))
  if [ "${TRIES}" -ge 40 ]; then
    echo "Database not reachable after 40 attempts."
    exit 1
  fi
  sleep 3
done

if ! wp core is-installed --allow-root 2>/dev/null; then
  echo "Installing WordPress (fa_IR)..."
  wp core install \
    --url="http://${DOMAIN}" \
    --title="${WORDPRESS_SITE_TITLE}" \
    --admin_user="${WORDPRESS_ADMIN_USER}" \
    --admin_password="${WORDPRESS_ADMIN_PASSWORD}" \
    --admin_email="${WORDPRESS_ADMIN_EMAIL}" \
    --skip-email \
    --allow-root

  wp language core install fa_IR --activate --allow-root
  wp rewrite structure '/%postname%/' --allow-root
  wp rewrite flush --allow-root
else
  echo "WordPress already installed."
  wp language core install fa_IR --activate --allow-root 2>/dev/null || true
fi

if ! wp plugin is-installed woocommerce --allow-root 2>/dev/null; then
  echo "Installing WooCommerce..."
  wp plugin install woocommerce --version=9.6.2 --activate --allow-root
  wp language plugin install woocommerce fa_IR --activate --allow-root 2>/dev/null || true
else
  wp plugin activate woocommerce --allow-root 2>/dev/null || true
fi

wp option update timezone_string 'Asia/Tehran' --allow-root
wp option update WPLANG 'fa_IR' --allow-root

echo "WordPress + WooCommerce initialization complete."
