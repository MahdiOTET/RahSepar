ALTER TABLE users
    RENAME COLUMN moblie TO mobile;

ALTER TABLE users
    RENAME CONSTRAINT users_moblie_key TO users_mobile_key;