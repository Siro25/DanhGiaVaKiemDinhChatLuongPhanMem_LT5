# Generated manually to create parking_parkinglot table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0003_alter_parkinglot_options_alter_parkingrecord_options'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS `parking_parkinglot` (
                `id` bigint NOT NULL AUTO_INCREMENT,
                `name` varchar(100) NOT NULL,
                `description` longtext NOT NULL,
                `capacity` int unsigned NOT NULL,
                `available_slots` int unsigned NOT NULL,
                `location` varchar(200) NOT NULL,
                `status` varchar(20) NOT NULL DEFAULT 'active',
                `hourly_rate` decimal(10,2) NOT NULL DEFAULT '0.00',
                `created_at` datetime(6) NOT NULL,
                `updated_at` datetime(6) NOT NULL,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS `parking_parkinglot`;"
        ),
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS `parking_parkingrecord` (
                `id` bigint NOT NULL AUTO_INCREMENT,
                `entry_time` datetime(6) NOT NULL,
                `exit_time` datetime(6) DEFAULT NULL,
                `fee` decimal(10,2) DEFAULT NULL,
                `is_paid` tinyint(1) NOT NULL DEFAULT '0',
                `notes` longtext NOT NULL,
                `card_id` bigint NOT NULL,
                `parking_lot_id` bigint NOT NULL,
                `parking_rate_id` bigint DEFAULT NULL,
                `vehicle_id` bigint NOT NULL,
                PRIMARY KEY (`id`),
                KEY `parking_parkingrecord_card_id` (`card_id`),
                KEY `parking_parkingrecord_parking_lot_id` (`parking_lot_id`),
                KEY `parking_parkingrecord_parking_rate_id` (`parking_rate_id`),
                KEY `parking_parkingrecord_vehicle_id` (`vehicle_id`),
                CONSTRAINT `parking_parkingrecord_card_id_fk` 
                    FOREIGN KEY (`card_id`) REFERENCES `cards_card` (`id`),
                CONSTRAINT `parking_parkingrecord_parking_lot_id_fk` 
                    FOREIGN KEY (`parking_lot_id`) REFERENCES `parking_parkinglot` (`id`),
                CONSTRAINT `parking_parkingrecord_vehicle_id_fk` 
                    FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles_vehicle` (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS `parking_parkingrecord`;"
        ),
    ]
