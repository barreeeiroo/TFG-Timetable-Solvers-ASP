class Constraints:
    ROOM_ALREADY_BOOKED = ":- roomBooked(T,U1,R), roomBooked(T,U2,R), U1 != U2."
    SESSION_IN_SAME_ROOM = ":- roomBooked(_,U,R1), roomBooked(_,U,R2), R1 != R2."
