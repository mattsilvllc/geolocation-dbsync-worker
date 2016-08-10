CREATE TABLE IF NOT EXISTS `geo_ip_blocks` (
  `ip_from` int unsigned NOT NULL,
  `ip_to` int unsigned NOT NULL,
  `network` varchar(32) NOT NULL,
  `geoname_id` int unsigned NOT NULL,
  `registered_country_geoname_id` int unsigned NOT NULL,
  `represented_country_geoname_id` int unsigned NOT NULL,
  `is_anonymous_proxy` tinyint(1) NOT NULL,
  `is_satellite_provider` tinyint(1) NOT NULL,
  `postal_code` varchar(32) NOT NULL,
  `latitude` float(8,4) NOT NULL,
  `longitude` float(8,4) NOT NULL,
  `accuracy_radius` smallint unsigned NOT NULL
);
