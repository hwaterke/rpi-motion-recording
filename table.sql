CREATE TABLE `motion` (
  `name` varchar(32) NOT NULL,
  `event` varchar(32) NOT NULL,
  `value` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `created_at_utc` datetime NOT NULL,
  `updated_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
