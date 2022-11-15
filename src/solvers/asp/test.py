from clyngor import ASP

answers = ASP("""
H { roomBooked(T,U,R) : timesteps(T) , room(R) } H :- slotsPerSession(H,U).

:- roomBooked(T,U1,R), roomBooked(T,U2,R), U1 != U2.
:- roomBooked(_,U,R1), roomBooked(_,U,R2), R1 != R2.

#show roomBooked/3.

timesteps(1..5).

room(citius).
room(etse).
slotsPerSession(2, tfg1).
slotsPerSession(2, tfg2).
""")

for answer, optimization, optimality, answer_number in answers.with_answer_number:
    for a in answer:
        print(a[0], a[1])
    break
