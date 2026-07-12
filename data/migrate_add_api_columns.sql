-- Migration: เพิ่มคอลัมน์จาก API ทั้งหมด
-- รันก่อน: mysql -u root dam_forecast_db < migrate_add_api_columns.sql

ALTER TABLE `dam_records`
  ADD COLUMN `owner`          varchar(255) DEFAULT NULL AFTER `dam_name`,
  ADD COLUMN `region`         varchar(100) DEFAULT NULL AFTER `owner`,
  ADD COLUMN `capacity`       float DEFAULT NULL AFTER `region`,
  ADD COLUMN `storage`        float DEFAULT NULL AFTER `capacity`,
  ADD COLUMN `active_storage` float DEFAULT NULL AFTER `storage`,
  ADD COLUMN `dead_storage`   float DEFAULT NULL AFTER `active_storage`,
  ADD COLUMN `volume`         float DEFAULT NULL AFTER `dead_storage`;
