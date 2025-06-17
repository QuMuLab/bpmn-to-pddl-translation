(define (domain pizza_order_flatten)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (event-StartEvent_1)
    (event-Event_1o7q4l5)
    (event-Event_07029z3)
    (event-Event_0p3pi5l)
    (event-Event_1n3fu60)
    (event-Event_18vc2ep)
    (event-Event_1ylp3d5)
    (event-Gateway_00a8n5n)
    (event-Gateway_1ushrpr)
    (event-Event_1o7q4l5_dup1)
  )

  (:action Order_Pizza
    :precondition (and (event-StartEvent_1))
    :effect (and (event-Gateway_00a8n5n))
  )

  (:action Complain_to_Delivery_Service
    :precondition (and (event-Event_1n3fu60))
    :effect (and (event-Gateway_1ushrpr))
  )

  (:action Eat_Pizza
    :precondition (and (event-Event_0p3pi5l))
    :effect (and (event-Event_1o7q4l5))
  )

  (:action Cancel_Order
    :precondition (and (event-Event_1ylp3d5))
    :effect (and (event-Event_07029z3))
  )

  (:action Gateway_00a8n5n
    :precondition (and (event-Gateway_00a8n5n))
    :effect (and (oneof (event-Event_0p3pi5l) (event-Event_1n3fu60)))
  )

  (:action Gateway_1ushrpr
    :precondition (and (event-Gateway_1ushrpr))
    :effect (and (oneof (event-Event_18vc2ep) (event-Event_1ylp3d5)))
  )

  (:action Eat_Pizza_copy_1
    :precondition (and (event-Event_18vc2ep))
    :effect (and (event-Event_1o7q4l5_dup1))
  )

)