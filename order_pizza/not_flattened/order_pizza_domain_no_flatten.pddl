(define (domain place_order_no_flatten)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1)
    (Event_1o7q4l5)
    (Event_07029z3)
    (Activity_0078ezj)
    (Activity_0b3tky9)
    (Activity_13tgdd7)
    (Activity_1k7bzjg)
    (Event_0p3pi5l)
    (Event_1n3fu60)
    (Event_1ylp3d5)
    (Gateway_00a8n5n)
    (Gateway_1ushrpr)
    (done)
    (started)
  )

  (:action start_Pizza_Wanted
    :precondition (and (not (started))(not (StartEvent_1)))
    :effect (and (StartEvent_1) (started))
  )

  (:action Order_Pizza
    :precondition (and (StartEvent_1))
    :effect (and (Gateway_00a8n5n) (not (StartEvent_1)))
  )

  (:action Complain_to_Delivery_Service
    :precondition (and (Event_1n3fu60))
    :effect (and (Gateway_1ushrpr) (not (Event_1n3fu60)))
  )

  (:action Eat_Pizza
    :precondition (and (Event_0p3pi5l))
    :effect (and (Event_1o7q4l5) (not (Event_0p3pi5l)))
  )

  (:action Cancel_Order
    :precondition (and (Event_1ylp3d5))
    :effect (and (Event_07029z3) (not (Event_1ylp3d5)))
  )

  (:action event_Gateway_00a8n5n
    :precondition (and (Gateway_00a8n5n))
    :effect (and (oneof (Event_1n3fu60) (Event_0p3pi5l)) (not (Gateway_00a8n5n)))
  )

  (:action event_Gateway_1ushrpr
    :precondition (and (Gateway_1ushrpr))
    :effect (and (oneof (Event_0p3pi5l) (Event_1ylp3d5)) (not (Gateway_1ushrpr)))
  )

  (:action goal_Pizza_Eaten
    :precondition (and (Event_1o7q4l5))
    :effect (done)
  )

  (:action goal_Order_Cancelled
    :precondition (and (Event_07029z3))
    :effect (done)
  )

)