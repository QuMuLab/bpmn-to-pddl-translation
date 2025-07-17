(define (domain order_pizza_2)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1)
    (Event_1agqah2)
    (Event_0wb1u17)
    (Activity_16518vh)
    (Activity_0lm5nlf)
    (Activity_1isqzov)
    (Activity_1pxtnfx)
    (Event_1baygn5)
    (Event_18i1e7l)
    (Gateway_11vw55q)
    (Gateway_07nhnas)
    (done)
    (started)
  )

  (:action start_Pizza_Wanted
    :precondition (and (not (started))(not (StartEvent_1)))
    :effect (and (StartEvent_1) (started))
  )

  (:action Order_Pizza
    :precondition (and (StartEvent_1))
    :effect (and (Gateway_11vw55q) (not (StartEvent_1)))
  )

  (:action Eat_Pizza
    :precondition (and (Event_1baygn5))
    :effect (and (Event_1agqah2) (not (Event_1baygn5)))
  )

  (:action Cancel_Order
    :precondition (and (Activity_1isqzov))
    :effect (and (Event_0wb1u17) (not (Activity_1isqzov)))
  )

  (:action Complain_to_Delivery_Service
    :precondition (and (Activity_1pxtnfx))
    :effect (and (Gateway_11vw55q) (not (Activity_1pxtnfx)))
  )

  (:action event_Gateway_11vw55q
    :precondition (and (Gateway_11vw55q))
    :effect (and (oneof (Event_1baygn5) (and (Event_18i1e7l) (Gateway_07nhnas))) (not (Gateway_11vw55q)))
  )

  (:action exclusive_Gateway_07nhnas
    :precondition (and (Gateway_07nhnas))
    :effect (and (oneof (Activity_1isqzov) (Activity_1pxtnfx)) (not (Gateway_07nhnas)))
  )

  (:action goal_Pizza_Eaten
    :precondition (and (Event_1agqah2))
    :effect (done)
  )

  (:action goal_Order_Cancelled
    :precondition (and (Event_0wb1u17))
    :effect (done)
  )

)