timeslot(1..4).
room(r1,-1).
room(r2,-1).
roomType(r1,st_CLE).
roomType(r2,st_CLE).
roomType(r2,st_CLIL).
session(s1,st_CLE,2).
session(s2,st_CLE,2).
noOverlap(s1,s3).
breakSessionTimeslot(2,3).

H { scheduledSession(T,S) : timeslot(T) } H :- session(S,_,H).
1 { assignedSlot(T,S,R) : roomType(R,ST) } 1 :- scheduledSession(T,S), session(S,ST,_).



:- not { assignedSlot(T,S,R) : session(S,_,_) } 1, room(R,_), timeslot(T).
:- assignedSlot(_,S,R1), assignedSlot(_,S,R2), R1 != R2.
:- scheduledSession(T,S1), scheduledSession(T,S2), noTimeslotOverlapInSessions(S1,S2).
:- scheduledSession(T1,S), scheduledSession(T2,S), breakSessionTimeslot(T1,T2).
% :- scheduledSession(T1,S), scheduledSession(T2,S), T1 + 1 < T2, not scheduledSession(T,S) : T = T1+1..T2-1.
:- scheduledSession(T,S), not scheduledSession(T-1,S), not scheduledSession(T+1,S).

#show assignedSlot/3.
