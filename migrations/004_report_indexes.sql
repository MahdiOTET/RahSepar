CREATE INDEX idx_trips_bus_departure
    ON trips (bus_id, departure_time)
    WHERE status <> 'cancelled';

CREATE INDEX idx_trips_driver_departure
    ON trips (driver_profile_id, departure_time)
    WHERE status <> 'cancelled';
