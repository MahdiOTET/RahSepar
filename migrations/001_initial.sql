CREATE TABLE users(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    moblie VARCHAR(15) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    wallet_balance NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_wallet_balance_non_negative
        CHECK(wallet_balance >= 0)

);

CREATE TABLE profiles(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    display_name VARCHAR(100) NOT NULL,
    profile_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT profile_type_valid
        CHECK(profile_type IN ('passenger', 'operator', 'driver')),
    
    CONSTRAINT profiles_user_type_unique
        UNIQUE(user_id, profile_type)
);

CREATE TABLE routes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT routes_origin_destination_different
        CHECK(lower(origin) <> lower(destination)),
    
    CONSTRAINT routes_origin_destination_unique
        UNIQUE(origin, destination)
);

CREATE TABLE buses(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_id BIGINT NOT NULL REFERENCES routes(id) ON DELETE RESTRICT,
    plate_number VARCHAR(20) NOT NULL UNIQUE,
    model VARCHAR(100),
    capacity SMALLINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT bus_capacity_valid
        CHECK(capacity BETWEEN 1 AND 100)

);

CREATE TABLE trips(

    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bus_id BIGINT NOT NULL REFERENCES buses(id) ON DELETE RESTRICT,
    driver_profile_id BIGINT NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    departure_time TIMESTAMPTZ NOT NULL,
    arrival_time TIMESTAMPTZ NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT price_positive
        CHECK(price > 0),
    
    CONSTRAINT valid_trip_schedule
        CHECK(arrival_time > departure_time),

    CONSTRAINT trip_status_valid
        CHECK(status IN ('scheduled', 'cancelled', 'completed'))

);


CREATE TABLE bookings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    passenger_profile_id BIGINT NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE RESTRICT,
    seat_number SMALLINT NOT NULL,
    paid_price NUMERIC(12, 2) NOT NULL,
    booked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    cancelled_at TIMESTAMPTZ,

    CONSTRAINT bookings_seat_positive
        CHECK(seat_number > 0),

    CONSTRAINT valid_status
        CHECK(status IN ('confirmed', 'cancelled')),

    CONSTRAINT booking_price_non_negative
        CHECK(paid_price >= 0 ),

    CONSTRAINT booking_cancellation_time_valid
        CHECK(
            (status = 'confirmed' AND cancelled_at IS NULL)
            OR
            (status = 'cancelled' AND cancelled_at IS NOT NULL) 
        )
);

CREATE TABLE wallet_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    booking_id BIGINT NOT NULL REFERENCES bookings(id) ON DELETE RESTRICT,
    transaction_type VARCHAR(20) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT amount_positive
        CHECK(amount > 0),

    CONSTRAINT valid_transaction_type
        CHECK (
            transaction_type IN (
                'wallet_credit',
                'booking_payment',
                'booking_refund'
            )
        ),

    CONSTRAINT wallet_and_booking_transaction_valid
        CHECK(
            (transaction_type = 'wallet_credit' AND booking_id IS NULL)
            OR
            (
                transaction_type IN ('booking_payment', 'booking_refund')
                AND booking_id IS NOT NULL
            )
        ),

    CONSTRAINT wallet_transactions_booking_type_unique
        UNIQUE (booking_id, transaction_type)
);


-- prevent two active bookings at the same time for the same ticket(seat)
CREATE UNIQUE INDEX unq_bookings_confirmed_trip_seat
    ON bookings (trip_id, seat_number)
    WHERE status = 'confirmed';

-- daily booking limit lookup
CREATE INDEX idx_bookings_profile_booked_at
    ON bookings (passenger_profile_id, booked_at);

-- hourly booking report
CREATE INDEX idx_bookings_status_booked_at
    ON bookings (status, booked_at);

-- used frequently to list future trips
CREATE INDEX idx_trips_status_departure
ON trips (status, departure_time);

